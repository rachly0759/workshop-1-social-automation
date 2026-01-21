import os
from mastodon import Mastodon
from config import MASTODON_BASE_URL, MASTODON_ACCESS_TOKEN
from openrouter import SocialMediaPost

# ------------------------
# Initialize Mastodon client
# ------------------------
if not MASTODON_ACCESS_TOKEN or not MASTODON_BASE_URL:
    raise RuntimeError("Mastodon API credentials not set in .env")

mastodon = Mastodon(
    access_token=MASTODON_ACCESS_TOKEN,
    api_base_url=MASTODON_BASE_URL,
)

# ------------------------
# Function to post content
# ------------------------
def post_to_mastodon(post: SocialMediaPost, dry_run: bool = True):
    """
    Posts a SocialMediaPost to Mastodon.
    If dry_run=True, just prints what would be posted.
    """
    # Combine caption + hashtags
    MAX_STATUS_LENGTH = 500
    content = f"{post.caption}\n\n{post.hashtags}"
    content = content[:MAX_STATUS_LENGTH]  # truncate to Mastodon limit

    if dry_run:
        print("=== DRY RUN ===")
        print("Caption + Hashtags:")
        print(content)
        print("Image prompt (optional, not posted):", post.image_prompt)
        print("================")
        return

    try:
        mastodon.status_post(content)
        print("✅ Successfully posted to Mastodon!")
    except Exception as e:
        print("❌ Failed to post to Mastodon:", e)


