"""
VPS-optimized Flannels scraper with enhanced network handling.
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


class FlannelsVPSScraper(VPSOptimizedBaseScraper):
    """VPS-optimized Flannels scraper with robust network handling."""
    
    def __init__(self):
        super().__init__("Flannels VPS")
        
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
        
        # VPS-specific settings
        self.max_pages = None  # No limit - scrape everything
        self.page_delay = 3  # Delay between pages
        self.retry_delay = 5  # Delay between retries
    
    def scrape_products(self) -> List[Product]:
        """Scrape products with VPS-optimized error handling."""
        products = []
        total_products_scanned = 0
        pages_navigated = 0
        
        print("🔍 Flannels VPS: Starting scraping...")
        self.logger.info("Starting Flannels VPS scraping")
        
        # Test connectivity first
        test_urls = [
            "https://www.flannels.com",
            "https://www.google.com",
            "https://httpbin.org/get"
        ]
        
        connectivity_results = self.test_connectivity(test_urls)
        working_urls = [url for url, status in connectivity_results.items() if status]
        
        if not working_urls:
            self.logger.error("❌ No connectivity to any test URLs - check VPS network settings")
            print("❌ Network connectivity issues detected")
            return products
        
        self.logger.info(f"✅ Connectivity test passed: {len(working_urls)}/{len(test_urls)} URLs accessible")
        print(f"✅ Network connectivity: {len(working_urls)}/{len(test_urls)} URLs accessible")
        
        try:
            page = 1
            
            while True:
                print(f"🔍 Flannels VPS Page {page}: Scraping...")
                pages_navigated += 1
                
                # Build URL with parameters
                params = self.base_params.copy()
                params["page"] = str(page)
                
                # Make request with enhanced error handling
                url = f"{self.base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
                
                self.logger.info(f"Fetching page {page}: {url}")
                
                # Get JSON data with retry logic
                json_data = self.get_json(url)
                
                if not json_data:
                    self.logger.warning(f"Failed to get data for page {page}, retrying...")
                    time.sleep(self.retry_delay)
                    
                    # Try one more time
                    json_data = self.get_json(url)
                    if not json_data:
                        self.logger.error(f"Failed to get data for page {page} after retry, stopping")
                        break
                
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
                
                # VPS-optimized delay between pages
                print(f"⏳ Waiting {self.page_delay}s before next page...")
                time.sleep(self.page_delay)
                
                page += 1
            
            # Print summary
            print(f"✅ Flannels VPS: Navigation Summary")
            print(f"   📄 Pages navigated: {pages_navigated}")
            print(f"   📦 Total products scanned: {total_products_scanned}")
            print(f"   🔥 High discount products found: {len(products)}")
            print(f"   📊 Success rate: {(len(products)/total_products_scanned*100):.1f}%" if total_products_scanned > 0 else "   📊 Success rate: 0%")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error scraping Flannels VPS: {str(e)}")
            print(f"❌ Error: {str(e)}")
            return products
    
    def _parse_products_from_json(self, json_data: Dict[Any, Any], page_number: int) -> tuple[List[Product], int]:
        """Parse products from JSON response with VPS-optimized error handling."""
        products = []
        
        try:
            if not json_data or 'products' not in json_data:
                self.logger.warning(f"Page {page_number}: No products data in JSON response")
                return products, 0
            
            product_list = json_data['products']
            total_scanned = len(product_list)
            
            print(f"📦 Page {page_number}: Found {total_scanned} total products")
            
            # Debug: Print first product structure
            if product_list and len(product_list) > 0:
                first_product = product_list[0]
                self.logger.debug(f"First product type: {type(first_product)}")
                self.logger.debug(f"First product keys: {list(first_product.keys()) if isinstance(first_product, dict) else 'Not a dict'}")
                self.logger.debug(f"First product sample: {str(first_product)[:200]}...")
            
            for i, product_data in enumerate(product_list):
                try:
                    # Skip if product_data is not a dict
                    if not isinstance(product_data, dict):
                        self.logger.warning(f"Product {i} is not a dict: {type(product_data)}")
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
        """Parse a single product with VPS-optimized error handling."""
        try:
            # Debug: Print the structure of product_data
            self.logger.debug(f"Product data type: {type(product_data)}")
            self.logger.debug(f"Product data keys: {list(product_data.keys()) if isinstance(product_data, dict) else 'Not a dict'}")
            
            # Handle case where product_data might be a string or different structure
            if not isinstance(product_data, dict):
                self.logger.warning(f"Product data is not a dict: {type(product_data)}")
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
            
            # Debug: Log all discounts found
            if discount_percentage > 0:
                self.logger.debug(f"Product: {name[:30]}... - {discount_percentage:.1f}% off (£{original_price:.0f} → £{sale_price:.0f})")
            
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
            "max_pages": "unlimited",
            "page_delay": self.page_delay,
            "retry_delay": self.retry_delay,
            "user_agents_count": len(self.user_agents),
            "session_timeout": self.session.timeout
        }
