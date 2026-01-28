from openrouter import generate_post
from mastodon_posting import post_to_mastodon
from notion import get_page_content  # Fixed: was fetch_notion_page
from config import NOTION_PAGE_ID
from image_generation import generate_image
from telegram_hitl import request_approval  # NEW: Import approval function


def main(dry_run: bool = True):
    # Step 1: fetch Notion content
    notion_text = get_page_content(NOTION_PAGE_ID)
    print(f"Fetched {len(notion_text)} characters from Notion")

    # Step 2: generate structured post
    post_idea = generate_post(notion_text)
    
    # Fix hashtags if they're a list
    if isinstance(post_idea.hashtags, list):
        post_idea.hashtags = ' '.join(post_idea.hashtags)
    
    print(f"\nGenerated post:")
    print(f"Caption: {post_idea.caption}")
    print(f"Image prompt: {post_idea.image_prompt}")
    print(f"Hashtags: {post_idea.hashtags}")

    image_path = None

    # Step 3: generate image
    if post_idea.image_prompt:
        print("\nGenerating image...")
        image_path = generate_image(
            prompt=post_idea.image_prompt,
            output_path="generated.webp"
        )
        print(f"Image saved to {image_path}")

    # NEW: Step 3.5: Get human approval via Telegram
    print("\n👤 Sending for human approval...")
    decision, feedback = request_approval(post_idea, image_path)
    
    if decision == "reject":
        print(f"\n❌ Post rejected. Feedback: {feedback}")
        print("⛔ Not posting to Mastodon.")
        return  # Exit early, don't post
    
    print("\n✅ Post approved by human!")

    # Step 4: post to Mastodon (dry-run by default)
    post_to_mastodon(post_idea, image_path=image_path, dry_run=dry_run)


if __name__ == "__main__":
    # Run in dry-run mode for testing
    main(dry_run=False)  # Changed to True for safety during testing