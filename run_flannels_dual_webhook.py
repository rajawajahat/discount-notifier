#!/usr/bin/env python3
"""
Local Flannels runner with dual webhook notifications and retry logic.
Runs Flannels scraper locally and sends notifications to both dev and production webhooks.
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from scrapers.flannels_vps import FlannelsVPSScraper
from notifications.discord_notifier import DiscordNotifier

# Setup logging
def setup_logging():
    """Setup logging for local Flannels runner."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"flannels_local_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("flannels_local")

def send_notification_with_retry(notifier, webhook_name, max_retries=3, retry_delay=60):
    """Send notification with retry logic."""
    logger = logging.getLogger("flannels_local")
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to send notification to {webhook_name} (attempt {attempt + 1}/{max_retries})")
            
            # Test the webhook
            if notifier.test_webhook():
                logger.info(f"Successfully sent notification to {webhook_name}")
                return True
            else:
                logger.warning(f"Failed to send notification to {webhook_name} (attempt {attempt + 1}/{max_retries})")
                
        except Exception as e:
            logger.error(f"Error sending notification to {webhook_name}: {str(e)}")
        
        if attempt < max_retries - 1:
            logger.info(f"Waiting {retry_delay} seconds before retry...")
            time.sleep(retry_delay)
    
    logger.error(f"Failed to send notification to {webhook_name} after {max_retries} attempts")
    return False

def main():
    """Main function to run Flannels scraper with dual webhook notifications."""
    logger = setup_logging()
    
    # Webhook URLs
    production_webhook = "https://discord.com/api/webhooks/1417784756954730596/oVMLzhto-F-0cEDNcvQ6e9NrapVyzQFVFpsxOR_4o8UytTkgAS0wxN8U8ivt6hYk1ppw"
    dev_webhook = "https://discord.com/api/webhooks/1419426002094002347/WPX3QUO1Ow2QjAhKQMpZ2bC3H49f6nKZAF0JcwqVvfOTXmdvo2ROHBWkaaKroapFFZn5"
    
    logger.info("Starting local Flannels scraper with dual webhook notifications")
    
    try:
        # Run Flannels scraper
        logger.info("Running Flannels scraper...")
        scraper = FlannelsVPSScraper()
        products = scraper.scrape_products()
        
        if products:
            logger.info(f"Found {len(products)} high discount products")
            
            # Send to production webhook
            logger.info("Sending notification to production webhook")
            prod_notifier = DiscordNotifier(production_webhook, enable_idempotency=True)
            send_notification_with_retry(prod_notifier, "Production")
            
            # Wait 30 seconds between webhook calls
            time.sleep(30)
            
            # Send to development webhook
            logger.info("Sending notification to development webhook")
            dev_notifier = DiscordNotifier(dev_webhook, enable_idempotency=True)
            send_notification_with_retry(dev_notifier, "Development")
            
        else:
            logger.info("No high discount products found")
            
    except Exception as e:
        logger.error(f"Error running Flannels scraper: {str(e)}")
        return 1
    
    logger.info("Local Flannels scraper run completed")
    return 0

if __name__ == "__main__":
    sys.exit(main())
