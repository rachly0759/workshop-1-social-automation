from openrouter import generate_post

notion_text = """
I went to Flour Bakery today and had a croissant and iced latte.
The croissant was buttery and flaky, and the latte was slightly bitter but perfect.
I also bought a chocolate chip cookie for later.
"""

post_idea = generate_post(notion_text)
print(post_idea.model_dump())
