#!/usr/bin/env python3
"""
Local testing script for the social media automation pipeline.

This script helps you test the pipeline locally before deploying to Vercel.
"""
import sys
from pathlib import Path

# Add project root to path so "src" is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import validate_config, get_config_summary
from src.pipeline import run_pipeline, test_pipeline_components


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main():
    """Run local tests."""
    print("\n🚀 Social Media Automation - Local Test Suite\n")
    
    # Test 1: Configuration
    print_section("1. Configuration Check")
    try:
        config_summary = get_config_summary()
        for key, value in config_summary.items():
            print(f"  {key}: {value}")
        
        validate_config()
        print("\n✅ Configuration is valid!")
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set.")
        return 1
    
    # Test 2: Component Tests
    print_section("2. Component Tests")
    try:
        results = test_pipeline_components()
        for component, status in results.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}: {'OK' if status else 'FAILED'}")
        
        if not all(results.values()):
            print("\n⚠️  Some components failed. Check the logs above.")
    except Exception as e:
        print(f"\n❌ Component test error: {e}")
    
    # Test 3: Pipeline Dry Run
    print_section("3. Pipeline Dry Run")
    print("Running pipeline with dry_run=True (no actual posting)...\n")
    
    try:
        result = run_pipeline(dry_run=True)
        
        print("\n✅ Pipeline completed successfully!")
        print(f"\nSteps completed: {', '.join(result.get('steps_completed', []))}")
        
        if 'post' in result:
            post = result['post']
            print(f"\nGenerated Post:")
            print(f"  Caption ({post['caption_length']} chars): {post['caption'][:100]}...")
            print(f"  Hashtags: {post['hashtags']}")
            print(f"  Image prompt: {post['image_prompt'][:100]}...")
        
        if result.get('errors'):
            print(f"\n⚠️  Warnings: {result['errors']}")
            
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print_section("Test Summary")
    print("✅ All tests completed!")
    print("\nNext steps:")
    print("  1. Review the dry run output above")
    print("  2. If everything looks good, deploy to Vercel")
    print("  3. See DEPLOYMENT.md for deployment instructions")
    print("\nTo test actual posting (be careful!):")
    print("  python -c \"from src.pipeline import run_pipeline; run_pipeline(dry_run=False)\"")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())