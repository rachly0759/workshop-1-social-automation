"""
Notion API integration for fetching page content.
"""
import requests
import logging
from typing import Optional

from .config import NOTION_API_KEY, NOTION_API_BASE, NOTION_VERSION

logger = logging.getLogger(__name__)


class NotionError(Exception):
    """Custom exception for Notion API errors."""
    pass


def get_page_content(page_id: str) -> str:
    """
    Fetches all readable text content from a Notion page.

    Args:
        page_id: The Notion page ID (with or without dashes)

    Returns:
        Concatenated plain-text content of the page

    Raises:
        NotionError: If the API request fails or configuration is invalid
    """
    if not NOTION_API_KEY:
        raise NotionError("NOTION_API_KEY is not set in environment variables")
    
    if not page_id:
        raise NotionError("Page ID is required")

    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    # Clean page ID (remove dashes if present)
    clean_page_id = page_id.replace("-", "")
    url = f"{NOTION_API_BASE}/blocks/{clean_page_id}/children"

    all_text = []
    has_more = True
    start_cursor = None
    page_count = 0
    max_pages = 100  # Prevent infinite loops

    logger.info(f"Fetching content from Notion page: {page_id}")

    try:
        while has_more and page_count < max_pages:
            params = {"start_cursor": start_cursor} if start_cursor else {}
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            page_count += 1

            for block in data.get("results", []):
                text = extract_text_from_block(block)
                if text:
                    all_text.append(text)

            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")

        content = "\n".join(all_text)
        logger.info(f"Successfully fetched {len(content)} characters from Notion")
        
        if not content.strip():
            logger.warning("Notion page appears to be empty")
            
        return content

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise NotionError(f"Page not found: {page_id}")
        elif e.response.status_code == 401:
            raise NotionError("Invalid Notion API key or insufficient permissions")
        else:
            raise NotionError(f"Notion API error: {e}")
    except requests.exceptions.RequestException as e:
        raise NotionError(f"Network error while fetching Notion page: {e}")
    except Exception as e:
        raise NotionError(f"Unexpected error fetching Notion page: {e}")


def extract_text_from_block(block: dict) -> Optional[str]:
    """
    Extracts plain text from a Notion block if it contains text.

    Supports common block types used in documents.

    Args:
        block: Notion block object

    Returns:
        Plain text content or None if block has no text
    """
    block_type = block.get("type")
    if not block_type:
        return None

    block_data = block.get(block_type, {})

    if "rich_text" not in block_data:
        return None

    try:
        text_parts = []
        for text_obj in block_data["rich_text"]:
            if text_obj.get("type") == "text":
                text_parts.append(text_obj.get("plain_text", ""))
        
        return "".join(text_parts) if text_parts else None
    except (KeyError, TypeError) as e:
        logger.warning(f"Error extracting text from block: {e}")
        return None