"""
OpenRouter API integration for generating social media posts.
"""
import json
import logging
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Optional

from .config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
    MAX_SUMMARY_TOKENS,
    MAX_POST_TOKENS,
    MAX_CAPTION_LENGTH
)

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Custom exception for OpenRouter API errors."""
    pass


class SocialMediaPost(BaseModel):
    """Structured social media post with caption, image prompt, and hashtags."""
    caption: str = Field(..., description="Engaging post caption")
    image_prompt: str = Field(..., description="Prompt for image generation")
    hashtags: str = Field(..., description="Relevant hashtags")


def _get_client() -> OpenAI:
    """
    Initialize and return OpenRouter client.
    
    Returns:
        Configured OpenAI client for OpenRouter
        
    Raises:
        OpenRouterError: If API key is not configured
    """
    if not OPENROUTER_API_KEY:
        raise OpenRouterError("OPENROUTER_API_KEY is not set in environment variables")
    
    return OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
    )


def summarize_content(content: str, max_chars: int = 2000) -> str:
    """
    Summarize long content into 1-2 sentences.
    
    Args:
        content: Text content to summarize
        max_chars: Maximum characters to process (to avoid token limits)
        
    Returns:
        Concise summary of the content
        
    Raises:
        OpenRouterError: If summarization fails
    """
    client = _get_client()
    short_content = content[:max_chars]

    logger.info(f"Summarizing {len(short_content)} characters of content")

    summary_prompt = (
        f"Summarize this text into 1-2 sentences for a social media post:\n\n"
        f"{short_content}"
    )

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": "You are a concise summarization assistant."},
                {"role": "user", "content": summary_prompt},
            ],
            max_tokens=MAX_SUMMARY_TOKENS,
            temperature=0.7,
        )

        summary = response.choices[0].message.content.strip()
        logger.info(f"Generated summary: {summary[:100]}...")
        return summary

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise OpenRouterError(f"Failed to summarize content: {e}")


def generate_post(content: str) -> SocialMediaPost:
    """
    Generate a structured social media post from content.
    
    Args:
        content: Source content to create post from
        
    Returns:
        Structured SocialMediaPost object
        
    Raises:
        OpenRouterError: If post generation fails
    """
    client = _get_client()

    logger.info("Generating social media post")

    # Step 1: Summarize long content
    summary = summarize_content(content)

    # Step 2: Generate structured post
    system_prompt = (
        "You are a creative social media content creator. "
        f"Generate engaging social media posts with captions under {MAX_CAPTION_LENGTH} characters. "
        "Create a JSON object with three fields: "
        "'caption' (engaging post text), "
        "'image_prompt' (detailed description for image generation), "
        "and 'hashtags' (relevant hashtags, separated by spaces). "
        "Make the caption concise, engaging, and appropriate for the platform."
    )

    user_prompt = f"Create an engaging social media post about: {summary}"

    try:
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_POST_TOKENS,
            temperature=0.8,
            response_format={"type": "json_object"},
        )

        # Parse JSON response
        json_response = json.loads(response.choices[0].message.content)
        logger.debug(f"Raw response: {json_response}")

        # Create Pydantic model
        post = SocialMediaPost(**json_response)

        # Enforce caption length limit
        if len(post.caption) > MAX_CAPTION_LENGTH:
            post.caption = post.caption[:MAX_CAPTION_LENGTH - 3] + "..."
            logger.warning(f"Caption truncated to {MAX_CAPTION_LENGTH} characters")

        logger.info("Successfully generated social media post")
        logger.info(f"Caption length: {len(post.caption)} chars")
        
        return post

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise OpenRouterError(f"Invalid JSON response from API: {e}")
    except Exception as e:
        logger.error(f"Post generation failed: {e}")
        raise OpenRouterError(f"Failed to generate post: {e}")


def test_connection() -> bool:
    """
    Test OpenRouter API connection.
    
    Returns:
        True if connection is successful
    """
    try:
        client = _get_client()
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10,
        )
        return bool(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False