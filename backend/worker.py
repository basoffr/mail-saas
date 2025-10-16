"""
Campaign Worker Entry Point

This script runs the campaign worker continuously.
Deploy this as a separate worker process on Render.com.
"""
import asyncio
import sys
from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

async def main():
    """Run campaign worker continuously."""
    from app.services.campaign_worker import campaign_worker
    
    logger.info("🚀 Starting Campaign Worker...")
    logger.info("⏰ Worker will check every 60 seconds")
    logger.info("📧 Campaigns will be activated and messages sent automatically")
    
    try:
        await campaign_worker.run_continuous(interval_seconds=60)
    except KeyboardInterrupt:
        logger.info("👋 Worker stopped by user")
    except Exception as e:
        logger.error(f"❌ Worker crashed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
