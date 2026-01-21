import requests
from config import NOTION_API_KEY

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def get_page_content(page_id: str) -> str:
    """
    Fetches all readable text content from a Notion page.

    Args:
        page_id (str): The Notion page ID (with or without dashes)

    Returns:
        str: Concatenated plain-text content of the page
    """
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    url = f"{NOTION_API_BASE}/blocks/{page_id}/children"

    all_text = []
    has_more = True
    start_cursor = None

    while has_more:
        params = {"start_cursor": start_cursor} if start_cursor else {}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()

        for block in data["results"]:
            text = extract_text_from_block(block)
            if text:
                all_text.append(text)

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return "\n".join(all_text)


def extract_text_from_block(block: dict) -> str | None:
    """
    Extracts plain text from a Notion block if it contains text.

    Supports common block types used in workshops.
    """
    block_type = block["type"]
    block_data = block.get(block_type, {})

    if "rich_text" not in block_data:
        return None

    return "".join(
        text["plain_text"]
        for text in block_data["rich_text"]
        if text["type"] == "text"
    )