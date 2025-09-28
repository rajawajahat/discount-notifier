#!/usr/bin/env python3
"""
VPS-optimized runner for Selfridges scraper with Chrome handling.
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from notifications.discord_notifier import DiscordNotifier
from scrapers.selfridges_vps import SelfridgesVpsScraper


def setup_logging():
    """Setup logging for VPS environment."""
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/selfridges_vps_run_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger("selfridges_vps_runner")


def run_selfridges_vps_scraper():
    """Run the VPS-optimized Selfridges scraper."""
    logger = setup_logging()
    
    print("=" * 60)
    print("🚀 Selfridges VPS Scraper - Starting")
    print("=" * 60)
    
    # Get webhook URL
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    if not webhook_url:
        print("❌ No DISCORD_WEBHOOK_URL environment variable set")
        print("Please set it with: export DISCORD_WEBHOOK_URL='your_webhook_url'")
        return False
    
    try:
        # Create notifier
        notifier = DiscordNotifier(webhook_url)
        
        # Create scraper
        scraper = SelfridgesVpsScraper()
        
        # Run scraper
        start_time = datetime.now()
        products = scraper.scrape_products()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Selfridges VPS: Completed in {duration:.1f}s")
        print(f"📦 Selfridges VPS: Found {len(products)} high discount products")
        
        if products:
            print("🔥 High discount products found:")
            for product in products:
                print(f"   💰 {product.name[:50]}... - {product.discount_percentage:.0f}% off (£{product.original_price:.0f} → £{product.sale_price:.0f})")
        else:
            print("❌ Selfridges VPS: No high discount products found")
        
        return True
        
    except Exception as e:
        logger.error(f"Error running Selfridges VPS scraper: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Selfridges VPS scraper')
    parser.add_argument('--dev', action='store_true', 
                       help='Use development webhook instead of production')
    
    args = parser.parse_args()
    
    if args.dev:
        # Set development webhook for testing
        dev_webhook = "https://discord.com/api/webhooks/YOUR_DEV_WEBHOOK_URL"
        os.environ['DISCORD_WEBHOOK_URL'] = dev_webhook
        print("🔧 Using development webhook")
    
    success = run_selfridges_vps_scraper()
    sys.exit(0 if success else 1)
