"""
Configuration module with environment variable management and validation.
"""
import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Required environment variables
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MASTODON_ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
MASTODON_BASE_URL = os.getenv("MASTODON_BASE_URL")

# Optional environment variables with defaults
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Application settings
MAX_STATUS_LENGTH = int(os.getenv("MAX_STATUS_LENGTH", "500"))
MAX_CAPTION_LENGTH = int(os.getenv("MAX_CAPTION_LENGTH", "400"))
IMAGE_OUTPUT_PATH = os.getenv("IMAGE_OUTPUT_PATH", "/tmp/generated.webp")

# Notion API settings
NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# OpenRouter settings
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MAX_SUMMARY_TOKENS = 80
MAX_POST_TOKENS = 200


def validate_config() -> Dict[str, Any]:
    """
    Validate that all required environment variables are set.
    
    Returns:
        Dict with validation status for each component
        
    Raises:
        ValueError: If critical configuration is missing
    """
    status = {
        "notion": bool(NOTION_API_KEY and NOTION_PAGE_ID),
        "openrouter": bool(OPENROUTER_API_KEY),
        "mastodon": bool(MASTODON_ACCESS_TOKEN and MASTODON_BASE_URL),
        "replicate": bool(REPLICATE_API_TOKEN),
    }
    
    missing = []
    if not status["notion"]:
        missing.append("Notion (NOTION_API_KEY, NOTION_PAGE_ID)")
    if not status["openrouter"]:
        missing.append("OpenRouter (OPENROUTER_API_KEY)")
    if not status["mastodon"]:
        missing.append("Mastodon (MASTODON_ACCESS_TOKEN, MASTODON_BASE_URL)")
    if not status["replicate"]:
        missing.append("Replicate (REPLICATE_API_TOKEN)")
    
    if missing:
        raise ValueError(
            f"Missing required environment variables for: {', '.join(missing)}"
        )
    
    return status


def get_config_summary() -> Dict[str, str]:
    """Get a summary of current configuration (without sensitive values)."""
    return {
        "notion_configured": "✓" if NOTION_API_KEY else "✗",
        "openrouter_configured": "✓" if OPENROUTER_API_KEY else "✗",
        "mastodon_configured": "✓" if MASTODON_ACCESS_TOKEN else "✗",
        "replicate_configured": "✓" if REPLICATE_API_TOKEN else "✗",
        "openrouter_model": OPENROUTER_MODEL,
        "max_status_length": str(MAX_STATUS_LENGTH),
    }