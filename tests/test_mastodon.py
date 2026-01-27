from openrouter import generate_post
from mastodon_posting import post_to_mastodon

notion_text = """
I went to Flour Bakery today and had a croissant and iced latte.
The croissant was buttery and flaky, and the latte was slightly bitter but perfect.
I also bought a chocolate chip cookie for later.
"""

# Step 1: Generate structured post
post_idea = generate_post(notion_text)

# Step 2: Post to Mastodon (dry-run)
post_to_mastodon(post_idea, dry_run=True)

# Step 2b: When ready, post for real
post_to_mastodon(post_idea, dry_run=False)
