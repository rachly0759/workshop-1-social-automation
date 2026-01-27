from notion import get_page_content
from config import NOTION_PAGE_ID

if __name__ == "__main__":
    content = get_page_content(NOTION_PAGE_ID)

    print("----- PAGE CONTENT -----")
    print(content)
