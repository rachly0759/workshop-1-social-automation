# Social Media Automation with RAG 🤖

Automated social media posting pipeline that generates posts from your Notion knowledge base using AI and RAG (Retrieval-Augmented Generation).

## What It Does

1. **Fetches** content from your Notion page
2. **Retrieves** relevant context from knowledge base using RAG
3. **Generates** post with AI (caption + image prompt + hashtags)
4. **Creates** image using AI image generation
5. **Requests** human approval via Telegram
6. **Posts** to Mastodon if approved

## Why RAG?

**Without RAG:** AI summarizes your entire Notion page → generic posts  
**With RAG:** AI finds the most relevant chunks from your knowledge base → specific, accurate posts grounded in your actual content

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv add fastembed sqlite-vec numpy replicate mastodon.py python-telegram-bot openai python-dotenv requests pydantic

# Or using pip
pip install -r requirements.txt
```

### 2. Set Up Environment

Create `.env` file:

```env
NOTION_API_KEY=your_notion_key
NOTION_PAGE_ID=your_page_id
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openai/gpt-4o-mini
MASTODON_ACCESS_TOKEN=your_mastodon_token
MASTODON_BASE_URL=https://your.instance
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
REPLICATE_API_TOKEN=your_replicate_token
```

### 3. Initialize Knowledge Base

```bash
uv run setup_rag.py
```

This creates `knowledge_base.db` and indexes your Notion content.

### 4. Run Pipeline

```bash
# With RAG (recommended)
uv run main_rag.py

# Without RAG (original method)
uv run main.py
```

## Project Structure

```
├── config.py                  # Environment variables
├── notion.py                  # Notion API integration
├── rag_knowledgebase.py      # RAG: chunking, embeddings, search
├── openrouter_with_rag.py    # AI post generation with RAG
├── image_generation.py        # Replicate AI image generation
├── telegram_hitl.py           # Human approval via Telegram
├── mastodon_posting.py        # Post to Mastodon
├── main_rag.py               # Main pipeline (with RAG option)
└── setup_rag.py              # One-time RAG setup
```

## How RAG Works

### Indexing (One-Time)
```
Notion Content → Chunk into paragraphs → Generate embeddings → Store in SQLite
```

### Retrieval (Every Post)
```
Query → Hybrid Search (keywords + semantics) → Top 5 chunks → AI generates post
```

**Hybrid Search:** Combines keyword matching (30%) + semantic similarity (70%) for best results.

## Features

- ✅ **RAG-powered posts** - Grounded in your actual content
- ✅ **Hybrid search** - BM25 + semantic embeddings
- ✅ **Human-in-the-loop** - Telegram approval before posting
- ✅ **AI image generation** - Custom images for each post
- ✅ **Local embeddings** - No API costs for embeddings
- ✅ **Dry-run mode** - Test without posting

## Example

**Notion Page:** 6000 words about mafanmifan food blog brand guide

**Query:** "matcha croissant post"

**RAG Retrieves:**
- Caption style: "minimal, observational, deadpan"
- Example: "matcha croissant from fulful. strong matcha, still sweet enough. flaky."
- Emojis: 1-3 max, use 🥐 for bakery
- Hashtags: #bostonfood #matcha (2-3 max)

**Generated Post:**
```
Caption: "matcha croissant from fulful. high quality matcha, 
strong but balanced. croissant actually flaky. 🥐"
Image: [AI-generated croissant image]
Hashtags: #bostonfood #matcha
```

## Update Knowledge Base

```bash
# Re-sync Notion content
uv run -c "
from rag_knowledgebase import init_database, sync_notion_page
from config import NOTION_PAGE_ID
db = init_database()
sync_notion_page(db, NOTION_PAGE_ID)
db.close()
"
```

## Troubleshooting

**"sqlite3.OperationalError: A LIMIT or 'k = ?' constraint is required"**
- Update `rag_knowledgebase.py` to use `AND k = ?` instead of `LIMIT ?`

**No relevant results from RAG**
- Check your Notion page has content (run `setup_rag.py` again)
- Increase `top_k` in `retrieve_context()` calls

**Posts are too generic**
- Add more detailed content to your Notion page
- Write in paragraphs (3-5 sentences each)
- Include specific examples and details

## Tech Stack

- **AI Models:** OpenRouter (GPT-4o-mini), Replicate (image generation)
- **RAG:** FastEmbed (local embeddings), SQLite + FTS5 + sqlite-vec
- **Integrations:** Notion API, Mastodon API, Telegram Bot API
- **Language:** Python 3.11+

## License

MIT

---

Built for Workshop Series on AI Automation