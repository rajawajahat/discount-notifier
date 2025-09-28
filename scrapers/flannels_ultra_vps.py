"""
Ultra VPS-optimized Flannels scraper with maximum resilience.
Designed for unstable VPS connections with aggressive retry logic.
"""

import json
import re
import time
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from scrapers.vps_optimized_base import VPSOptimizedBaseScraper
from scrapers.base import Product
from notifications.discord_notifier import DiscordNotifier


class FlannelsUltraVPSScraper(VPSOptimizedBaseScraper):
    """Ultra VPS-optimized Flannels scraper with maximum resilience."""
    
    def __init__(self):
        super().__init__("Flannels Ultra VPS")
        
        # Flannels API endpoints
        self.base_url = "https://www.flannels.com/product/getforcategory"
        self.base_params = {
            "categoryId": "FLAN_TOPCLEARMENCLOT",
            "productsPerPage": "59",
            "sortOption": "rank",
            "selectedFilters": "",
            "isSearch": "false",
            "searchText": "",
            "columns": "4",
            "mobileColumns": "2",
            "clearFilters": "false",
            "pathName": "/clearance/men/clothing",
            "searchTermCategory": "",
            "selectedCurrency": "GBP",
            "portalSiteId": "48",
            "searchCategory": ""
        }
        
        # Initialize Discord notifier
        webhook_url = "https://discord.com/api/webhooks/1419426002094002347/WPX3QUO1Ow2QjAhKQMpZ2bC3H49f6nKZAF0JcwqVvfOTXmdvo2ROHBWkaaKroapFFZn5"
        self.discord_notifier = DiscordNotifier(webhook_url, enable_idempotency=True)
        
        # Ultra VPS-specific settings
        self.max_pages = 20  # Reduced for VPS stability
        self.page_delay = 5   # Increased delay
        self.retry_delay = 10 # Increased retry delay
        self.max_retries = 2  # Reduced retries to fail fast
        self.timeout_multiplier = 0.5  # Shorter timeouts
        
        # Override session settings for ultra VPS
        self.session.timeout = (5, 30)  # Much shorter timeouts
        
    def scrape_products(self) -> List[Product]:
        """Scrape products with ultra VPS-optimized error handling."""
        products = []
        total_products_scanned = 0
        pages_navigated = 0
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        print("🔍 Flannels Ultra VPS: Starting scraping...")
        self.logger.info("Starting Flannels Ultra VPS scraping")
        
        # Quick connectivity test
        test_urls = ["https://www.google.com"]
        connectivity_results = self.test_connectivity(test_urls)
        
        if not any(connectivity_results.values()):
            self.logger.error("❌ No connectivity to test URLs - aborting")
            print("❌ Network connectivity issues detected")
            return products
        
        self.logger.info(f"✅ Connectivity test passed: {sum(connectivity_results.values())}/{len(test_urls)} URLs accessible")
        print(f"✅ Network connectivity: {sum(connectivity_results.values())}/{len(test_urls)} URLs accessible")
        
        try:
            page = 1
            
            while page <= self.max_pages and consecutive_failures < max_consecutive_failures:
                print(f"🔍 Flannels Ultra VPS Page {page}: Scraping...")
                pages_navigated += 1
                
                # Build URL with parameters
                params = self.base_params.copy()
                params["page"] = str(page)
                
                url = f"{self.base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
                
                self.logger.info(f"Fetching page {page}: {url}")
                
                # Get JSON data with ultra-aggressive retry logic
                json_data = self.get_json(url)
                
                if not json_data:
                    consecutive_failures += 1
                    self.logger.warning(f"Failed to get data for page {page} (failure {consecutive_failures}/{max_consecutive_failures})")
                    
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error(f"Too many consecutive failures ({consecutive_failures}), stopping")
                        break
                    
                    # Wait longer before retry
                    wait_time = self.retry_delay * consecutive_failures
                    print(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                
                # Reset failure counter on success
                consecutive_failures = 0
                
                # Parse products from JSON
                page_products, page_total_scanned = self._parse_products_from_json(json_data, page)
                products.extend(page_products)
                total_products_scanned += page_total_scanned
                
                # Send notifications for high discount products
                for product in page_products:
                    self._send_notification(product)
                
                print(f"✅ Page {page}: Found {len(page_products)} high discount products (scanned {page_total_scanned} total products)")
                
                # Check if we should continue
                if page_total_scanned == 0:
                    print(f"📄 Page {page}: No products found, stopping")
                    break
                
                # Ultra VPS-optimized delay between pages
                if page < self.max_pages:
                    print(f"⏳ Waiting {self.page_delay}s before next page...")
                    time.sleep(self.page_delay)
                
                page += 1
            
            # Print summary
            print(f"✅ Flannels Ultra VPS: Navigation Summary")
            print(f"   📄 Pages navigated: {pages_navigated}")
            print(f"   📦 Total products scanned: {total_products_scanned}")
            print(f"   🔥 High discount products found: {len(products)}")
            print(f"   📊 Success rate: {(len(products)/total_products_scanned*100):.1f}%" if total_products_scanned > 0 else "   📊 Success rate: 0%")
            print(f"   ⚠️  Consecutive failures: {consecutive_failures}")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error scraping Flannels Ultra VPS: {str(e)}")
            print(f"❌ Error: {str(e)}")
            return products
    
    def _parse_products_from_json(self, json_data: Dict[Any, Any], page_number: int) -> tuple[List[Product], int]:
        """Parse products from JSON response with ultra VPS-optimized error handling."""
        products = []
        
        try:
            if not json_data or 'products' not in json_data:
                self.logger.warning(f"Page {page_number}: No products data in JSON response")
                return products, 0
            
            product_list = json_data['products']
            total_scanned = len(product_list)
            
            print(f"📦 Page {page_number}: Found {total_scanned} total products")
            
            for i, product_data in enumerate(product_list):
                try:
                    # Skip if product_data is not a dict
                    if not isinstance(product_data, dict):
                        continue
                        
                    product = self._parse_single_product(product_data)
                    if product:
                        products.append(product)
                        print(f"   💰 Found: {product.name[:50]}... - {product.discount_percentage:.0f}% off (£{product.original_price:.0f} → £{product.sale_price:.0f})")
                        
                except Exception as e:
                    self.logger.warning(f"Error parsing product {i} on page {page_number}: {str(e)}")
                    continue
            
            return products, total_scanned
            
        except Exception as e:
            self.logger.error(f"Error parsing products from page {page_number}: {str(e)}")
            return products, 0
    
    def _parse_single_product(self, product_data: Dict[Any, Any]) -> Optional[Product]:
        """Parse a single product with ultra VPS-optimized error handling."""
        try:
            # Handle case where product_data might be a string or different structure
            if not isinstance(product_data, dict):
                return None
            
            # Extract product information with safe access
            name = product_data.get('name', 'Unknown Product')
            url = f"https://www.flannels.com{product_data.get('url', '')}"
            
            # Price information - handle different possible structures
            price_data = product_data.get('price', {})
            if isinstance(price_data, dict):
                original_price = float(price_data.get('value', 0))
                sale_price = float(price_data.get('salePrice', original_price))
            else:
                # If price is not a dict, try to extract from other fields
                original_price = float(product_data.get('originalPrice', 0))
                sale_price = float(product_data.get('salePrice', original_price))
            
            # Calculate discount percentage
            if original_price > 0 and sale_price < original_price:
                discount_percentage = ((original_price - sale_price) / original_price) * 100
            else:
                discount_percentage = 0
            
            # Only return products with high discount (≥70%)
            if discount_percentage >= 70:
                return Product(
                    name=name,
                    original_price=original_price,
                    sale_price=sale_price,
                    discount_percentage=discount_percentage,
                    url=url,
                    retailer="Flannels"
                )
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error parsing single product: {str(e)}")
            return None
    
    def _send_notification(self, product: Product):
        """Send notification for a product."""
        try:
            success = self.discord_notifier.send_high_discount_alerts([product])
            if success:
                print(f"📲 Notification sent: {product.name[:50]}... ({product.discount_percentage:.0f}% off)")
            else:
                self.logger.warning(f"Failed to send notification for {product.name}")
        except Exception as e:
            self.logger.error(f"Error sending notification for {product.name}: {str(e)}")
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics for monitoring."""
        return {
            "scraper_name": self.scraper_name,
            "max_pages": self.max_pages,
            "page_delay": self.page_delay,
            "retry_delay": self.retry_delay,
            "max_retries": self.max_retries,
            "timeout_multiplier": self.timeout_multiplier,
            "user_agents_count": len(self.user_agents),
            "session_timeout": self.session.timeout
        }
