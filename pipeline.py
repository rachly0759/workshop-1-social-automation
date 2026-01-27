"""
Main pipeline orchestration for social media automation.
"""
import logging
from typing import Dict, Any, Optional

from .notion import get_page_content, NotionError
from .openrouter import generate_post, OpenRouterError
from .image_generation import generate_image, ImageGenerationError
from .mastodon_posting import post_to_mastodon, MastodonPostingError
from .config import NOTION_PAGE_ID

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    """Custom exception for pipeline execution errors."""
    pass


def run_pipeline(dry_run: bool = True) -> Dict[str, Any]:
    """
    Execute the complete social media automation pipeline.
    
    Pipeline steps:
    1. Fetch content from Notion
    2. Generate structured social media post using AI
    3. Generate image based on prompt
    4. Post to Mastodon (or simulate if dry_run=True)
    
    Args:
        dry_run: If True, simulates posting without actually publishing
        
    Returns:
        Dictionary with execution results and status information
        
    Raises:
        PipelineError: If any step of the pipeline fails
    """
    results = {
        "dry_run": dry_run,
        "steps_completed": [],
        "errors": [],
    }

    try:
        # Step 1: Fetch Notion content
        logger.info("Step 1/4: Fetching content from Notion...")
        
        if not NOTION_PAGE_ID:
            raise PipelineError("NOTION_PAGE_ID not configured")
        
        try:
            notion_content = get_page_content(NOTION_PAGE_ID)
            results["steps_completed"].append("notion_fetch")
            results["notion_chars"] = len(notion_content)
            logger.info(f"✓ Fetched {len(notion_content)} characters from Notion")
        except NotionError as e:
            logger.error(f"✗ Notion fetch failed: {e}")
            raise PipelineError(f"Failed to fetch Notion content: {e}")

        # Step 2: Generate post content
        logger.info("Step 2/4: Generating social media post...")
        
        try:
            post = generate_post(notion_content)
            results["steps_completed"].append("post_generation")
            results["post"] = {
                "caption": post.caption,
                "caption_length": len(post.caption),
                "hashtags": post.hashtags,
                "image_prompt": post.image_prompt,
            }
            logger.info(f"✓ Generated post (caption: {len(post.caption)} chars)")
        except OpenRouterError as e:
            logger.error(f"✗ Post generation failed: {e}")
            raise PipelineError(f"Failed to generate post: {e}")

        # Step 3: Generate image
        image_path: Optional[str] = None
        
        if post.image_prompt and post.image_prompt.strip():
            logger.info("Step 3/4: Generating image...")
            
            try:
                image_path = generate_image(post.image_prompt)
                results["steps_completed"].append("image_generation")
                results["image_path"] = image_path
                logger.info(f"✓ Generated image: {image_path}")
            except ImageGenerationError as e:
                logger.error(f"✗ Image generation failed: {e}")
                results["errors"].append(f"Image generation failed: {e}")
                # Continue without image - not a fatal error
                logger.warning("Continuing without image...")
        else:
            logger.info("Step 3/4: Skipping image generation (no prompt provided)")
            results["steps_completed"].append("image_skipped")

        # Step 4: Post to Mastodon
        logger.info(f"Step 4/4: {'Simulating' if dry_run else 'Publishing'} post to Mastodon...")
        
        try:
            posting_result = post_to_mastodon(
                post=post,
                image_path=image_path,
                dry_run=dry_run
            )
            results["steps_completed"].append("mastodon_post")
            results["mastodon"] = posting_result
            
            if dry_run:
                logger.info("✓ Dry run completed successfully")
            else:
                logger.info("✓ Successfully posted to Mastodon")
                
        except MastodonPostingError as e:
            logger.error(f"✗ Mastodon posting failed: {e}")
            raise PipelineError(f"Failed to post to Mastodon: {e}")

        # Pipeline completed successfully
        results["success"] = True
        results["message"] = "Pipeline completed successfully"
        
        logger.info("=" * 50)
        logger.info("Pipeline execution completed successfully!")
        logger.info(f"Steps completed: {', '.join(results['steps_completed'])}")
        logger.info("=" * 50)
        
        return results

    except PipelineError:
        # Re-raise pipeline errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}", exc_info=True)
        raise PipelineError(f"Pipeline failed with unexpected error: {e}")


def test_pipeline_components() -> Dict[str, bool]:
    """
    Test all pipeline components without executing the full pipeline.
    
    Returns:
        Dictionary with test results for each component
    """
    from .openrouter import test_connection as test_openrouter
    from .mastodon_posting import test_connection as test_mastodon
    from .image_generation import test_connection as test_replicate
    
    logger.info("Testing pipeline components...")
    
    results = {
        "notion": False,
        "openrouter": False,
        "mastodon": False,
        "replicate": False,
    }
    
    # Test Notion
    try:
        if NOTION_PAGE_ID:
            content = get_page_content(NOTION_PAGE_ID)
            results["notion"] = len(content) > 0
    except Exception as e:
        logger.error(f"Notion test failed: {e}")
    
    # Test OpenRouter
    try:
        results["openrouter"] = test_openrouter()
    except Exception as e:
        logger.error(f"OpenRouter test failed: {e}")
    
    # Test Mastodon
    try:
        results["mastodon"] = test_mastodon()
    except Exception as e:
        logger.error(f"Mastodon test failed: {e}")
    
    # Test Replicate
    try:
        results["replicate"] = test_replicate()
    except Exception as e:
        logger.error(f"Replicate test failed: {e}")
    
    logger.info(f"Component test results: {results}")
    return results