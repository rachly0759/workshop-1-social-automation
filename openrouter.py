import os
import json
from openai import OpenAI
from pydantic import BaseModel
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

# Check API key
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not set in .env. Please add it.")

# Structured output model
class SocialMediaPost(BaseModel):
    caption: str
    image_prompt: str
    hashtags: str

# Initialize OpenRouter client
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

model_name = OPENROUTER_MODEL or "openai/gpt-4o-mini"

# Helper: summarize Notion content
def summarize_content(content: str) -> str:
    # Limit to ~500 tokens of input (roughly 2000 chars to be safe)
    MAX_INPUT_CHARS = 2000
    MAX_OUTPUT_TOKENS_SUMMARY = 100

    short_content = content[:MAX_INPUT_CHARS]

    summary_prompt = f"Summarize this text into 1-2 sentences for a social media post:\n\n{short_content}"

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You summarize text briefly."},
            {"role": "user", "content": summary_prompt},
        ],
        max_tokens=MAX_OUTPUT_TOKENS_SUMMARY,
    )

    return response.choices[0].message.content.strip()

# Generate structured post
def generate_post(content: str) -> SocialMediaPost:
    MAX_OUTPUT_TOKENS_POST = 300

    # Step 1: summarize (this handles the token limit)
    summary = summarize_content(content)

    # Step 2: generate JSON post (summary is already short, so no token issues)
    system_prompt = (
        "You are a creative social media assistant. "
        "Given a short summary, generate a JSON object with three fields: "
        "caption (engaging post text, max 500 characters total including hashtags), "
        "image_prompt (description for image generation), "
        "and hashtags (relevant hashtags). "
        "Keep the caption concise and under 500 characters."
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a social media post for: {summary}"},
        ],
        max_tokens=MAX_OUTPUT_TOKENS_POST,
        response_format={"type": "json_object"},
    )

    # Parse the JSON response
    json_response = json.loads(response.choices[0].message.content)
    
    # Create the Pydantic model
    post = SocialMediaPost(**json_response)
    
    # Enforce 500 character limit on caption
    if len(post.caption) > 500:
        post.caption = post.caption[:497] + "..."
    
    return post