"""
Mastodon posting functionality with dry-run support.
"""
import os
import logging
from typing import Optional
from mastodon import Mastodon, MastodonError

from .config import (
    MASTODON_BASE_URL,
    MASTODON_ACCESS_TOKEN,
    MAX_STATUS_LENGTH
)
from .openrouter import SocialMediaPost

logger = logging.getLogger(__name__)


class MastodonPostingError(Exception):
    """Custom exception for Mastodon posting errors."""
    pass


def _get_mastodon_client() -> Mastodon:
    """
    Initialize and return Mastodon client.
    
    Returns:
        Configured Mastodon client
        
    Raises:
        MastodonPostingError: If credentials are not configured
    """
    if not MASTODON_ACCESS_TOKEN or not MASTODON_BASE_URL:
        raise MastodonPostingError(
            "Mastodon credentials not set. "
            "Please set MASTODON_ACCESS_TOKEN and MASTODON_BASE_URL"
        )

    try:
        return Mastodon(
            access_token=MASTODON_ACCESS_TOKEN,
            api_base_url=MASTODON_BASE_URL,
        )
    except Exception as e:
        raise MastodonPostingError(f"Failed to initialize Mastodon client: {e}")


def post_to_mastodon(
    post: SocialMediaPost,
    image_path: Optional[str] = None,
    dry_run: bool = True
) -> dict:
    """
    Post content to Mastodon.
    
    Args:
        post: SocialMediaPost object with caption, hashtags, and image_prompt
        image_path: Optional path to image file to attach
        dry_run: If True, simulates posting without actually publishing
        
    Returns:
        Dictionary with posting results
        
    Raises:
        MastodonPostingError: If posting fails (only in non-dry-run mode)
    """
    # Combine caption and hashtags
    content = f"{post.caption}\n\n{post.hashtags}"
    
    # Truncate to Mastodon's limit
    if len(content) > MAX_STATUS_LENGTH:
        content = content[:MAX_STATUS_LENGTH - 3] + "..."
        logger.warning(f"Content truncated to {MAX_STATUS_LENGTH} characters")

    # Validate image path if provided
    if image_path and not os.path.exists(image_path):
        logger.warning(f"Image file not found: {image_path}")
        image_path = None

    # Dry run mode - just log what would be posted
    if dry_run:
        logger.info("=" * 50)
        logger.info("DRY RUN - No actual posting")
        logger.info("=" * 50)
        logger.info(f"Caption + Hashtags ({len(content)} chars):")
        logger.info(content)
        logger.info("-" * 50)
        
        if image_path:
            logger.info(f"Image: {image_path}")
            logger.info(f"Image prompt: {post.image_prompt}")
        else:
            logger.info("No image attached")
        
        logger.info("=" * 50)
        
        return {
            "success": True,
            "dry_run": True,
            "content_length": len(content),
            "has_image": bool(image_path),
            "message": "Dry run completed - no actual posting"
        }

    # Actual posting
    try:
        mastodon = _get_mastodon_client()
        media_ids = None

        # Upload image if provided
        if image_path:
            logger.info(f"Uploading image: {image_path}")
            try:
                media = mastodon.media_post(
                    image_path,
                    description=post.image_prompt  # Alt text for accessibility
                )
                media_ids = [media["id"]]
                logger.info(f"Image uploaded successfully (ID: {media['id']})")
            except MastodonError as e:
                logger.error(f"Failed to upload image: {e}")
                # Continue without image rather than failing completely
                logger.warning("Proceeding without image attachment")

        # Create status post
        logger.info("Publishing status to Mastodon...")
        status = mastodon.status_post(
            status=content,
            media_ids=media_ids
        )

        logger.info("✅ Successfully posted to Mastodon!")
        logger.info(f"Status ID: {status['id']}")
        logger.info(f"Status URL: {status.get('url', 'N/A')}")

        return {
            "success": True,
            "dry_run": False,
            "status_id": status["id"],
            "status_url": status.get("url"),
            "content_length": len(content),
            "has_image": bool(media_ids),
            "message": "Successfully posted to Mastodon"
        }

    except MastodonError as e:
        logger.error(f"❌ Mastodon API error: {e}")
        raise MastodonPostingError(f"Failed to post to Mastodon: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error posting to Mastodon: {e}")
        raise MastodonPostingError(f"Unexpected error: {e}")


def test_connection() -> bool:
    """
    Test Mastodon API connection.
    
    Returns:
        True if connection is successful
    """
    try:
        mastodon = _get_mastodon_client()
        account = mastodon.account_verify_credentials()
        logger.info(f"Connected to Mastodon as: @{account['username']}")
        return True
    except Exception as e:
        logger.error(f"Mastodon connection test failed: {e}")
        return False