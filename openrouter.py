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


# ========================
# Original Functions (for backward compatibility)
# ========================

def summarize_content(content: str) -> str:
    """Summarize text into 1-2 sentences for a social media post."""
    MAX_INPUT_CHARS = 2000
    MAX_OUTPUT_TOKENS_SUMMARY = 80

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


def generate_post(content: str) -> SocialMediaPost:
    """
    Generate structured post from content (original function).
    
    This is the original function for backward compatibility.
    For RAG-enhanced generation, use generate_post_with_rag().
    """
    MAX_OUTPUT_TOKENS_POST = 200

    # Step 1: summarize (this handles the token limit)
    summary = summarize_content(content)

    # Step 2: generate JSON post
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


# ========================
# RAG-Enhanced Functions
# ========================

def generate_post_with_rag(
    context: str,
    topic: str,
    style_guidance: str = None,
    max_caption_length: int = 400
) -> SocialMediaPost:
    """
    Generate a social media post using RAG context.
    
    This function creates posts grounded in your knowledge base,
    ensuring accuracy and relevance to your actual content.
    
    Args:
        context: Retrieved context from RAG search
        topic: The topic/theme for the post
        style_guidance: Optional style instructions (e.g., "professional", "casual", "technical")
        max_caption_length: Maximum length for the caption
        
    Returns:
        SocialMediaPost object with caption, image_prompt, and hashtags
    """
    print(f"\n{'='*60}")
    print(f"🤖 LLM POST GENERATION WITH RAG")
    print(f"{'='*60}")
    print(f"Topic: {topic}")
    print(f"Context length: {len(context)} characters")
    if style_guidance:
        print(f"Style: {style_guidance}")
    print(f"Max caption length: {max_caption_length} chars")
    
    # Build system prompt with style guidance
    base_system = (
        "You are a social media manager creating engaging posts. "
        "Your posts should be concise, authentic, and based ONLY on the provided context. "
        "Generate a JSON object with: caption (engaging text), image_prompt (for image generation), "
        "and hashtags (relevant hashtags as a single string)."
    )
    
    if style_guidance:
        base_system += f"\n\nStyle guidance: {style_guidance}"
    
    # Build user prompt
    user_prompt = (
        f"Based on this context from our knowledge base:\n\n"
        f"{context}\n\n"
        f"Create a social media post about: {topic}\n\n"
        f"Requirements:\n"
        f"- Caption: Under {max_caption_length} characters, engaging and authentic\n"
        f"- Image prompt: Describe a relevant visual (not a screenshot, something creative)\n"
        f"- Hashtags: 2-3 relevant hashtags as a single string\n"
        f"- Use ONLY information from the context provided\n"
        f"- Output ONLY valid JSON matching the schema\n"
    )
    
    print(f"\n📤 Sending to LLM...")
    print(f"   Model: {model_name}")
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=300,
            messages=[
                {"role": "system", "content": base_system},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        
        print(f"✓ LLM response received")
        
        # Parse response
        json_response = json.loads(response.choices[0].message.content)
        post = SocialMediaPost(**json_response)
        
        # Enforce caption length limit
        if len(post.caption) > max_caption_length:
            print(f"⚠️  Caption too long ({len(post.caption)} chars), truncating...")
            post.caption = post.caption[:max_caption_length - 3] + "..."
        
        print(f"✓ Post structured and validated")
        print(f"{'='*60}\n")
        
        return post
        
    except Exception as e:
        print(f"❌ Error generating post with RAG: {e}")
        print(f"{'='*60}\n")
        # Return a fallback post
        return SocialMediaPost(
            caption=f"Exploring {topic}. Stay tuned for insights!",
            image_prompt=f"Abstract illustration representing {topic}",
            hashtags="#AI #Tech"
        )


def generate_query_from_notion(notion_content: str) -> str:
    """
    Generate a search query from Notion content.
    
    This helps bridge the gap between raw Notion content and relevant
    knowledge base searches. The LLM extracts key themes.
    
    Args:
        notion_content: Raw content from Notion page
        
    Returns:
        Search query string for RAG retrieval
    """
    MAX_NOTION_CHARS = 1000
    
    # Truncate if too long
    short_content = notion_content[:MAX_NOTION_CHARS]
    
    system_prompt = (
        "You extract key topics and themes from text. "
        "Output a concise search query (5-10 words) that captures the main theme."
    )
    
    user_prompt = f"Extract the main topic/theme from this text:\n\n{short_content}"
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            max_tokens=50,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        
        query = response.choices[0].message.content.strip()
        return query
        
    except Exception as e:
        print(f"Error generating query: {e}")
        # Fallback: use first sentence
        sentences = notion_content.split('.')
        return sentences[0][:100] if sentences else "general topic"


# ========================
# Example Usage
# ========================

if __name__ == "__main__":
    """
    Example: Generate a RAG-enhanced post
    """
    # Mock context (in real usage, this comes from rag_knowledgebase.py)
    mock_context = """
    [1. notion] (score: 0.85)
    Our AI consulting services help businesses integrate machine learning 
    into their operations. We specialize in custom model development, 
    data pipeline optimization, and AI strategy consulting.
    
    [2. notion] (score: 0.72)
    Recent projects include implementing recommendation systems for e-commerce,
    building fraud detection models for fintech, and developing chatbots
    for customer service automation.
    """
    
    topic = "AI consulting services"
    
    # Generate post
    post = generate_post_with_rag(
        context=mock_context,
        topic=topic,
        style_guidance="professional but approachable"
    )
    
    print(f"Generated post:")
    print(f"Caption ({len(post.caption)} chars): {post.caption}")
    print(f"Image prompt: {post.image_prompt}")
    print(f"Hashtags: {post.hashtags}")