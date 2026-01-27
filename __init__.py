"""
Social Media Automation Package

This package provides automated social media posting functionality that:
1. Fetches content from Notion
2. Generates engaging posts using AI
3. Creates images using image generation models
4. Posts to Mastodon

Main entry point: pipeline.run_pipeline()
"""

__version__ = "1.0.0"

from .pipeline import run_pipeline, test_pipeline_components
from .config import validate_config, get_config_summary

__all__ = [
    "run_pipeline",
    "test_pipeline_components",
    "validate_config",
    "get_config_summary",
]