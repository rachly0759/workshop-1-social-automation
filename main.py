from pathlib import Path
from openrouter import generate_post
from mastodon_posting import post_to_mastodon
from notion import get_page_content
from config import NOTION_PAGE_ID
from image_generation import generate_image
from telegram_hitl import request_approval


def main(dry_run: bool = True, use_rag: bool = False):
    """
    Main pipeline with optional RAG.
    
    Args:
        dry_run: If True, don't actually post to Mastodon
        use_rag: If True, use RAG-enhanced generation instead of direct summarization
    """
    print("\n" + "="*70)
    print("🚀 SOCIAL MEDIA AUTOMATION PIPELINE")
    print("="*70)
    print(f"Mode: {'RAG-ENHANCED' if use_rag else 'STANDARD'}")
    print(f"Dry Run: {dry_run}")
    print("="*70 + "\n")
    
    # Step 1: fetch Notion content
    print("📋 STEP 1: Fetching Notion Content")
    print("-" * 70)
    notion_text = get_page_content(NOTION_PAGE_ID)
    print(f"✓ Fetched {len(notion_text)} characters from Notion")
    preview = notion_text[:150].replace('\n', ' ')
    print(f"  Preview: {preview}...\n")

    # Step 2: generate structured post
    if use_rag:
        print("🧠 STEP 2: RAG-Enhanced Post Generation")
        print("-" * 70)
        
        # Import RAG modules only if needed
        from rag_knowledgebase import init_database, retrieve_context, DATABASE_PATH
        from openrouter import generate_post_with_rag, generate_query_from_notion
        
        # Initialize knowledge base
        print(f"📂 Opening knowledge base: {DATABASE_PATH}")
        db = init_database(DATABASE_PATH)
        print(f"✓ Database connected\n")
        
        # Generate topic from Notion content
        print("🎯 Extracting topic from Notion content...")
        topic = generate_query_from_notion(notion_text)
        print(f"✓ Generated search query: '{topic}'\n")
        
        # Retrieve context (this will show detailed RAG retrieval)
        context, results = retrieve_context(db, topic, top_k=5)
        
        # Generate post with RAG
        print("✍️  Generating post with retrieved context...")
        post_idea = generate_post_with_rag(context, topic)
        print(f"✓ Post generated using {len(results)} context chunks\n")
        
        db.close()
    else:
        print("✍️  STEP 2: Standard Post Generation")
        print("-" * 70)
        print("Summarizing Notion content and generating post...")
        # Original non-RAG generation
        post_idea = generate_post(notion_text)
        print(f"✓ Post generated from summary\n")
    
    # Fix hashtags if they're a list
    if isinstance(post_idea.hashtags, list):
        post_idea.hashtags = ' '.join(post_idea.hashtags)
    
    print("📝 GENERATED POST:")
    print("-" * 70)
    print(f"Caption ({len(post_idea.caption)} chars):\n  {post_idea.caption}")
    print(f"\nImage prompt:\n  {post_idea.image_prompt}")
    print(f"\nHashtags:\n  {post_idea.hashtags}")
    print()

    image_path = None

    # Step 3: generate image
    print("🎨 STEP 3: Image Generation")
    print("-" * 70)
    if post_idea.image_prompt:
        print("Generating image from prompt...")
        image_path = generate_image(
            prompt=post_idea.image_prompt,
            output_path="generated.webp"
        )
        print(f"✓ Image saved to {image_path}\n")
    else:
        print("No image prompt provided, skipping image generation\n")

    # Step 3.5: Get human approval via Telegram
    print("👤 STEP 4: Human-in-the-Loop Approval")
    print("-" * 70)
    print("Sending post to Telegram for approval...")
    decision, feedback = request_approval(post_idea, image_path)
    
    if decision == "reject":
        print(f"\n❌ POST REJECTED")
        print(f"Feedback: {feedback}")
        print("⛔ Not posting to Mastodon.")
        print("="*70 + "\n")
        return
    
    print(f"✅ POST APPROVED by human!\n")

    # Step 4: post to Mastodon (dry-run by default)
    print("📤 STEP 5: Posting to Mastodon")
    print("-" * 70)
    post_to_mastodon(post_idea, image_path=image_path, dry_run=dry_run)
    
    print("\n" + "="*70)
    print("✅ PIPELINE COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    # Run with RAG enabled
    main(dry_run=False, use_rag=True)