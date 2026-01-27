# Social Media Automation Pipeline

Automated social media posting system that fetches content from Notion, generates AI-powered posts with images, and publishes to Mastodon.

## Features

- 📝 **Notion Integration** - Fetch content from Notion pages
- 🤖 **AI-Powered Content** - Generate engaging posts using OpenRouter AI models
- 🎨 **Image Generation** - Create custom images using Replicate
- 📱 **Mastodon Publishing** - Automatically post to Mastodon with images
- 🔄 **Dry Run Mode** - Test pipeline without actually posting
- 🚀 **Vercel Deployment** - Easy deployment to Vercel serverless platform

## Architecture

```
┌─────────────┐
│   Notion    │ ──▶ Fetch content
└─────────────┘
       │
       ▼
┌─────────────┐
│ OpenRouter  │ ──▶ Generate post
│     AI      │     (caption, hashtags, image prompt)
└─────────────┘
       │
       ▼
┌─────────────┐
│  Replicate  │ ──▶ Generate image
└─────────────┘
       │
       ▼
┌─────────────┐
│  Mastodon   │ ──▶ Publish post
└─────────────┘
```

## Quick Start

### Prerequisites

- Python 3.9+
- API keys for:
  - Notion API
  - OpenRouter
  - Replicate
  - Mastodon instance

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file:
   ```env
   # Notion
   NOTION_API_KEY=your_notion_api_key
   NOTION_PAGE_ID=your_page_id
   
   # OpenRouter
   OPENROUTER_API_KEY=your_openrouter_key
   OPENROUTER_MODEL=openai/gpt-4o-mini
   
   # Mastodon
   MASTODON_ACCESS_TOKEN=your_mastodon_token
   MASTODON_BASE_URL=https://mastodon.social
   
   # Replicate
   REPLICATE_API_TOKEN=your_replicate_token
   ```

4. **Run locally**
   ```bash
   uvicorn api.index:app --reload
   ```

5. **Test the pipeline**
   ```bash
   curl -X POST "http://localhost:8000/run?dry_run=true"
   ```

## Deployment to Vercel

### 1. Prepare Your Repository

Ensure your repository has this structure:
```
repo/
├── api/
│   └── index.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── notion.py
│   ├── openrouter.py
│   ├── image_generation.py
│   ├── mastodon_posting.py
│   └── pipeline.py
├── .gitignore
├── requirements.txt
├── vercel.json
└── README.md
```

### 2. Deploy to Vercel

#### Option A: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow the prompts to link your project
```

#### Option B: GitHub Integration

1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click "New Project"
4. Import your GitHub repository
5. Vercel will auto-detect the configuration

### 3. Configure Environment Variables

In your Vercel project dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add the following variables:
   - `NOTION_API_KEY`
   - `NOTION_PAGE_ID`
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL` (optional, defaults to `openai/gpt-4o-mini`)
   - `MASTODON_ACCESS_TOKEN`
   - `MASTODON_BASE_URL`
   - `REPLICATE_API_TOKEN`

### 4. Deploy

```bash
vercel --prod
```

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "message": "Social Media Automation API is running",
  "version": "1.0.0"
}
```

### `POST /run?dry_run=true`
Execute the automation pipeline.

**Query Parameters:**
- `dry_run` (boolean, default: `true`) - If true, simulates posting without publishing

**Response (dry run):**
```json
{
  "success": true,
  "dry_run": true,
  "result": {
    "notion_chars": 1234,
    "post": {
      "caption": "Generated caption...",
      "caption_length": 150,
      "hashtags": "#ai #automation",
      "image_prompt": "..."
    },
    "steps_completed": ["notion_fetch", "post_generation", "image_generation", "mastodon_post"]
  }
}
```

### `GET /health`
Detailed health check with configuration validation.

**Response:**
```json
{
  "status": "healthy",
  "configuration": {
    "notion": true,
    "openrouter": true,
    "mastodon": true,
    "replicate": true
  }
}
```

## Usage Examples

### Dry Run (Testing)
```bash
curl -X POST "https://your-deployment.vercel.app/run?dry_run=true"
```

### Live Posting
```bash
curl -X POST "https://your-deployment.vercel.app/run?dry_run=false"
```

### Health Check
```bash
curl "https://your-deployment.vercel.app/health"
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NOTION_API_KEY` | Yes | - | Notion integration API key |
| `NOTION_PAGE_ID` | Yes | - | ID of the Notion page to fetch |
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key |
| `OPENROUTER_MODEL` | No | `openai/gpt-4o-mini` | AI model to use |
| `MASTODON_ACCESS_TOKEN` | Yes | - | Mastodon access token |
| `MASTODON_BASE_URL` | Yes | - | Mastodon instance URL |
| `REPLICATE_API_TOKEN` | Yes | - | Replicate API token |
| `MAX_STATUS_LENGTH` | No | `500` | Max characters for post |
| `MAX_CAPTION_LENGTH` | No | `400` | Max characters for caption |

### Getting API Keys

**Notion:**
1. Go to https://www.notion.so/my-integrations
2. Create new integration
3. Copy the API key
4. Share your page with the integration

**OpenRouter:**
1. Sign up at https://openrouter.ai
2. Go to API Keys section
3. Create new API key

**Mastodon:**
1. Go to your Mastodon instance → Settings → Development
2. Create new application
3. Copy access token

**Replicate:**
1. Sign up at https://replicate.com
2. Go to Account → API tokens
3. Create new token

## Development

### Project Structure

```
src/
├── __init__.py           # Package initialization
├── config.py             # Configuration and environment variables
├── notion.py             # Notion API integration
├── openrouter.py         # AI post generation
├── image_generation.py   # Image generation with Replicate
├── mastodon_posting.py   # Mastodon posting
└── pipeline.py           # Main pipeline orchestration

api/
└── index.py             # FastAPI application
```

### Adding New Features

1. **Add new integration:**
   - Create new module in `src/`
   - Update `pipeline.py` to include new step
   - Add configuration to `config.py`

2. **Modify post generation:**
   - Edit prompts in `openrouter.py`
   - Adjust `SocialMediaPost` model for new fields

3. **Change image generation:**
   - Update model parameters in `image_generation.py`
   - Can switch to different Replicate models

### Testing

```bash
# Test configuration
python -c "from src.config import validate_config; print(validate_config())"

# Test individual components
python -c "from src.pipeline import test_pipeline_components; print(test_pipeline_components())"

# Run full pipeline in dry-run mode
python -c "from src.pipeline import run_pipeline; run_pipeline(dry_run=True)"
```

## Troubleshooting

### Common Issues

**"Configuration error: Missing required environment variables"**
- Ensure all required environment variables are set in Vercel
- Check that variable names match exactly

**"Notion API error: Page not found"**
- Verify the Notion page ID is correct
- Ensure the integration has access to the page

**"Image generation failed"**
- Check REPLICATE_API_TOKEN is valid
- Verify you have sufficient Replicate credits

**"Mastodon posting failed"**
- Verify access token is valid
- Check MASTODON_BASE_URL is correct (with https://)
- Ensure your Mastodon app has write permissions

### Logs

View logs in Vercel dashboard:
1. Go to your project
2. Click "Deployments"
3. Click on a deployment
4. Click "Functions" tab to see logs

## Security Notes

- Never commit `.env` file or API keys to Git
- Use Vercel's environment variables for secrets
- Rotate API keys periodically
- Use dry-run mode for testing

## License

MIT

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review Vercel deployment logs