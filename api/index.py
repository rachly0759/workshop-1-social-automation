"""
FastAPI entrypoint for Vercel deployment.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, '..')

from src.pipeline import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Social Media Automation API",
    description="Automated social media posting pipeline",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Social Media Automation API is running",
        "version": "1.0.0"
    }

@app.post("/run")
async def run(
    dry_run: bool = Query(
        True, 
        description="If True, performs a dry run without actually posting to Mastodon"
    )
):
    """
    Execute the full automation pipeline.
    
    Args:
        dry_run: If True, simulates posting without publishing to Mastodon
        
    Returns:
        JSON response with execution results
    """
    try:
        logger.info(f"Starting pipeline execution (dry_run={dry_run})")
        result = run_pipeline(dry_run=dry_run)
        logger.info("Pipeline execution completed successfully")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "dry_run": dry_run,
                "result": result,
                "message": "Pipeline executed successfully"
            }
        )
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline execution failed: {str(e)}"
        )

@app.get("/health")
def detailed_health():
    """Detailed health check with configuration validation."""
    from src.config import validate_config
    
    try:
        config_status = validate_config()
        return {
            "status": "healthy",
            "configuration": config_status
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )