#!/usr/bin/env python3
"""
Ultra VPS-optimized script for maximum resilience on unstable connections.
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

from scrapers.flannels_ultra_vps import FlannelsUltraVPSScraper


def setup_ultra_vps_logging():
    """Setup logging optimized for ultra VPS deployment."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create datetime-based filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = logs_dir / f"ultra_vps_scraper_run_{timestamp}.log"
    
    # Setup logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger("ultra_vps_discount_notifier")
    logger.info(f"Ultra VPS logging initialized - Log file: {log_filename}")
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


def run_ultra_vps_scraper(scraper_class, scraper_name):
    """Run an ultra VPS-optimized scraper and return results."""
    print(f"🔍 Running {scraper_name} (Ultra VPS Optimized)...")
    
    start_time = time.time()
    
    try:
        scraper = scraper_class()
        
        # Get network stats before scraping
        network_stats = scraper.get_network_stats()
        print(f"📊 Ultra VPS Network Configuration:")
        for key, value in network_stats.items():
            print(f"   {key}: {value}")
        
        # Run the scraper
        products = scraper.scrape_products()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ {scraper_name}: {len(products)} products found in {duration:.1f}s")
        
        return {
            'scraper': scraper_name,
            'success': True,
            'products': len(products),
            'duration': duration,
            'error': None,
            'network_stats': network_stats
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
            'error': str(e),
            'network_stats': None
        }


def main():
    """Main function to run ultra VPS-optimized scrapers."""
    parser = argparse.ArgumentParser(description='Run Ultra VPS-optimized discount scrapers')
    parser.add_argument('--dev', action='store_true', 
                       help='Use development webhook instead of production')
    parser.add_argument('--flannel', action='store_true',
                       help='Run only Flannels Ultra VPS scraper')
    
    args = parser.parse_args()
    
    # Setup logging first
    logger = setup_ultra_vps_logging()
    
    # Setup webhook
    setup_webhook_url(args.dev)
    
    print("🚀 Discount Notifier - Ultra VPS Optimized Run")
    print("="*70)
    print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S on %d/%m/%Y')}")
    print(f"🖥️  Ultra VPS Optimized: Maximum resilience for unstable connections")
    
    # Define ultra VPS-optimized scrapers
    scrapers_to_run = []
    
    if args.flannel:
        scrapers_to_run.append((FlannelsUltraVPSScraper, "Flannels Ultra VPS"))
    else:
        # Default to Flannels Ultra VPS if no specific scraper specified
        scrapers_to_run.append((FlannelsUltraVPSScraper, "Flannels Ultra VPS"))
    
    results = []
    total_start_time = time.time()
    
    # Run each scraper
    for scraper_class, scraper_name in scrapers_to_run:
        logger.info(f"Starting Ultra VPS scraper: {scraper_name}")
        result = run_ultra_vps_scraper(scraper_class, scraper_name)
        results.append(result)
        logger.info(f"Completed Ultra VPS scraper: {scraper_name} - Success: {result['success']}, Products: {result['products']}")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 ULTRA VPS OPTIMIZED SUMMARY")
    print(f"{'='*70}")
    
    successful_scrapers = [r for r in results if r['success']]
    failed_scrapers = [r for r in results if not r['success']]
    total_products = sum(r['products'] for r in results)
    
    print(f"✅ Successful: {len(successful_scrapers)}/{len(scrapers_to_run)}")
    print(f"❌ Failed: {len(failed_scrapers)}")
    print(f"📦 Total products: {total_products}")
    print(f"⏰ Runtime: {total_duration:.1f}s")
    
    if successful_scrapers:
        print(f"\n🎉 SUCCESS:")
        for result in successful_scrapers:
            print(f"   ✅ {result['scraper']}: {result['products']} products")
            if result['network_stats']:
                print(f"      📊 Network: {result['network_stats']['user_agents_count']} user agents, {result['network_stats']['page_delay']}s delay")
    
    if failed_scrapers:
        print(f"\n❌ FAILED:")
        for result in failed_scrapers:
            print(f"   ❌ {result['scraper']}: {result['error'][:50]}...")
    
    print(f"\n⏰ Completed at: {datetime.now().strftime('%H:%M:%S on %d/%m/%Y')}")
    
    # Log final summary
    logger.info(f"Ultra VPS scraping completed - Total products: {total_products}, Duration: {total_duration:.1f}s")
    
    if total_products > 0:
        print(f"\n🎉 Found {total_products} deals!")
        logger.info(f"Found {total_products} high discount products - notifications sent")
    else:
        print(f"\n😔 No high discount products found.")
        logger.info("No high discount products found this run")
    
    # Ultra VPS-specific recommendations
    if failed_scrapers:
        print(f"\n🔧 ULTRA VPS TROUBLESHOOTING:")
        print(f"   • Check VPS network stability: ping -c 10 google.com")
        print(f"   • Verify VPS resources: free -h && df -h")
        print(f"   • Check system load: uptime && top -bn1")
        print(f"   • Consider upgrading VPS plan if timeouts persist")


if __name__ == "__main__":
    main()
