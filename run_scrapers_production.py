#!/usr/bin/env python3
"""
Production-optimized script to run all scrapers.
Optimized for VPS deployment with minimal logging.
Usage: 
    python run_scrapers_production.py           # Use production webhook
    python run_scrapers_production.py --dev     # Use development webhook
"""

import sys
import os
import argparse
from datetime import datetime
import time
import logging
from pathlib import Path

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from scrapers.flannels import FlannelsScraper
from scrapers.harrods import HarrodsScraper
from scrapers.harvey_nichols import HarveyNicholsScraper
from scrapers.selfridges import SelfridgesScraper
from scrapers.end_clothing import EndClothingScraper


def setup_logging():
    """Setup logging with minimal console output for production."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create datetime-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"scraper_run_{timestamp}.log"
    
    # Setup logging configuration - minimal console output
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            # Only log errors to console in production
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set console handler to only show errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    
    logger = logging.getLogger("discount_notifier")
    logger.info(f"Logging initialized - Log file: {log_filename}")
    return logger


def setup_webhook_url(use_dev: bool = False):
    """Setup the appropriate webhook URL."""
    if use_dev:
        # Development webhook
        webhook_url = "https://discord.com/api/webhooks/1419426002094002347/WPX3QUO1Ow2QjAhKQMpZ2bC3H49f6nKZAF0JcwqVvfOTXmdvo2ROHBWkaaKroapFFZn5"
        print("🧪 Using DEVELOPMENT webhook for notifications")
    else:
        # Production webhook
        webhook_url = "https://discord.com/api/webhooks/1417784756954730596/oVMLzhto-F-0cEDNcvQ6e9NrapVyzQFVFpsxOR_4o8UytTkgAS0wxN8U8ivt6hYk1ppw"
        print("🚀 Using PRODUCTION webhook for notifications")
    
    os.environ['DISCORD_WEBHOOK_URL'] = webhook_url


def run_scraper(scraper_class, scraper_name):
    """Run a single scraper and return results."""
    print(f"🔍 Running {scraper_name}...")
    
    start_time = time.time()
    
    try:
        scraper = scraper_class()
        products = scraper.scrape_products()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ {scraper_name}: {len(products)} products found in {duration:.1f}s")
        
        return {
            'scraper': scraper_name,
            'success': True,
            'products': len(products),
            'duration': duration,
            'error': None
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"❌ {scraper_name}: Failed after {duration:.1f}s - {str(e)}")
        
        return {
            'scraper': scraper_name,
            'success': False,
            'products': 0,
            'duration': duration,
            'error': str(e)
        }


def main():
    """Main function to run all scrapers."""
    parser = argparse.ArgumentParser(description='Run discount scrapers (Production)')
    parser.add_argument('--dev', action='store_true', 
                       help='Use development webhook instead of production')
    
    # Individual scraper flags
    parser.add_argument('--flannel', action='store_true',
                       help='Run only Flannels scraper')
    parser.add_argument('--harrods', action='store_true',
                       help='Run only Harrods scraper')
    parser.add_argument('--harvey', action='store_true',
                       help='Run only Harvey Nichols scraper')
    parser.add_argument('--selfridges', action='store_true',
                       help='Run only Selfridges scraper')
    parser.add_argument('--end', action='store_true',
                       help='Run only END Clothing scraper')
    
    args = parser.parse_args()
    
    # Setup logging first
    logger = setup_logging()
    
    # Setup webhook
    setup_webhook_url(args.dev)
    
    print("🚀 Discount Notifier - Production Run")
    print("="*50)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S on %d/%m/%Y')}")
    
    # Define all available scrapers
    all_scrapers = [
        (FlannelsScraper, "Flannels", "flannel"),
        (HarrodsScraper, "Harrods", "harrods"),
        (HarveyNicholsScraper, "Harvey Nichols", "harvey"),
        (SelfridgesScraper, "Selfridges", "selfridges"),
        (EndClothingScraper, "END Clothing", "end")
    ]
    
    # Determine which scrapers to run based on arguments
    scrapers_to_run = []
    
    # Check if any specific scraper flags are set
    specific_scrapers = [
        (args.flannel, "flannel"),
        (args.harrods, "harrods"),
        (args.harvey, "harvey"),
        (args.selfridges, "selfridges"),
        (args.end, "end")
    ]
    
    if any(flag for flag, _ in specific_scrapers):
        # Run only the specified scrapers
        for flag, scraper_key in specific_scrapers:
            if flag:
                for scraper_class, scraper_name, key in all_scrapers:
                    if key == scraper_key:
                        scrapers_to_run.append((scraper_class, scraper_name))
                        break
    else:
        # Run all scrapers if no specific flags are set
        scrapers_to_run = [(scraper_class, scraper_name) for scraper_class, scraper_name, _ in all_scrapers]
    
    scrapers = scrapers_to_run
    
    results = []
    total_start_time = time.time()
    
    # Run each scraper
    for scraper_class, scraper_name in scrapers:
        logger.info(f"Starting scraper: {scraper_name}")
        result = run_scraper(scraper_class, scraper_name)
        results.append(result)
        logger.info(f"Completed scraper: {scraper_name} - Success: {result['success']}, Products: {result['products']}")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*50}")
    print("📊 FINAL SUMMARY")
    print(f"{'='*50}")
    
    successful_scrapers = [r for r in results if r['success']]
    failed_scrapers = [r for r in results if not r['success']]
    total_products = sum(r['products'] for r in results)
    
    print(f"✅ Successful: {len(successful_scrapers)}/{len(scrapers)}")
    print(f"❌ Failed: {len(failed_scrapers)}")
    print(f"📦 Total products: {total_products}")
    print(f"⏰ Runtime: {total_duration:.1f}s")
    
    if successful_scrapers:
        print(f"\n🎉 SUCCESS:")
        for result in successful_scrapers:
            print(f"   ✅ {result['scraper']}: {result['products']} products")
    
    if failed_scrapers:
        print(f"\n❌ FAILED:")
        for result in failed_scrapers:
            print(f"   ❌ {result['scraper']}: {result['error'][:50]}...")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%H:%M:%S on %d/%m/%Y')}")
    
    # Log final summary
    logger.info(f"Scraping completed - Total products: {total_products}, Duration: {total_duration:.1f}s")
    
    if total_products > 0:
        print(f"\n🎉 Found {total_products} deals!")
        logger.info(f"Found {total_products} high discount products - notifications sent")
    else:
        print(f"\n😔 No high discount products found.")
        logger.info("No high discount products found this run")


if __name__ == "__main__":
    main()
