"""
Image generation using Replicate API.
"""
import os
import logging
from typing import Optional
import replicate

from .config import REPLICATE_API_TOKEN, IMAGE_OUTPUT_PATH

logger = logging.getLogger(__name__)


class ImageGenerationError(Exception):
    """Custom exception for image generation errors."""
    pass


def generate_image(prompt: str, output_path: Optional[str] = None) -> str:
    """
    Generate an image using Replicate's image generation model.
    
    Args:
        prompt: Text description for image generation
        output_path: Path to save the generated image (defaults to config value)
        
    Returns:
        Path to the generated image file
        
    Raises:
        ImageGenerationError: If image generation fails
    """
    if not REPLICATE_API_TOKEN:
        raise ImageGenerationError("REPLICATE_API_TOKEN is not set in environment variables")
    
    if not prompt or not prompt.strip():
        raise ImageGenerationError("Image prompt cannot be empty")
    
    # Use default path if not provided
    if output_path is None:
        output_path = IMAGE_OUTPUT_PATH
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Generating image with prompt: {prompt[:100]}...")

    try:
        output = replicate.run(
            "sundai-club/boba_img_generator:1c932d8ea15409fe6fa9a9dcf79d1ba952cad3e28375597c63e18e232014e731",
            input={
                "model": "dev",
                "prompt": prompt,
                "go_fast": False,
                "lora_scale": 1,
                "megapixels": "1",
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "webp",
                "guidance_scale": 3,
                "output_quality": 80,
                "prompt_strength": 0.8,
                "extra_lora_scale": 1,
                "num_inference_steps": 28
            }
        )

        # Output is a list; get the first element
        if not output or len(output) == 0:
            raise ImageGenerationError("No output received from image generation API")

        # Write to file
        with open(output_path, "wb") as f:
            f.write(output[0].read())

        file_size = os.path.getsize(output_path)
        logger.info(f"Image generated successfully: {output_path} ({file_size} bytes)")
        
        return output_path

    except replicate.exceptions.ReplicateError as e:
        logger.error(f"Replicate API error: {e}")
        raise ImageGenerationError(f"Replicate API error: {e}")
    except IOError as e:
        logger.error(f"Failed to write image file: {e}")
        raise ImageGenerationError(f"Failed to save image: {e}")
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise ImageGenerationError(f"Unexpected error during image generation: {e}")


def test_connection() -> bool:
    """
    Test Replicate API connection.
    
    Returns:
        True if REPLICATE_API_TOKEN is configured
    """
    return bool(REPLICATE_API_TOKEN)