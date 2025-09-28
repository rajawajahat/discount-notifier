"""
Flannels scraper implementation using API endpoint.
"""

from typing import List, Optional
import json
from scrapers.base import BaseScraper, Product


class FlannelsScraper(BaseScraper):
    """Scraper for Flannels men's clearance using API endpoint."""
    
    def __init__(self):
        super().__init__(
            name="Flannels",
            base_url="https://www.flannels.com/clearance/men/clothing"
        )
        self.api_base_url = "https://www.flannels.com/product/getforcategory"
    
    def scrape_products(self) -> List[Product]:
        """Scrape products from Flannels API endpoint."""
        products = []
        print("Scraping Flannels API endpoint")
        
        try:
            page = 1
            products_per_page = 59
            
            self.logger.info("Starting Flannels API scraping")
            
            while True:
                # Build API URL for current page
                api_url = self._build_api_url(page, products_per_page)
                print(f"🔍 Flannels Page {page}: {api_url}")
                self.logger.info(f"Fetching page {page}: {api_url}")
                
                # Get JSON data from API
                json_content = self.get_page(api_url)
                if not json_content:
                    print(f"❌ Page {page}: No content received")
                    self.logger.warning(f"No content received for page {page}")
                    break
                
                try:
                    data = json.loads(json_content)
                except json.JSONDecodeError as e:
                    print(f"❌ Page {page}: Failed to parse JSON")
                    self.logger.error(f"Failed to parse JSON for page {page}: {str(e)}")
                    break
                
                # Extract products from JSON
                page_products = data.get('products', [])
                
                if not page_products:
                    print(f"❌ Page {page}: No products found, stopping pagination")
                    self.logger.info(f"No products found on page {page}, stopping")
                    break
                
                print(f"📦 Page {page}: Found {len(page_products)} total products")
                self.logger.info(f"Found {len(page_products)} products on page {page}")
                
                # Process each product and count high discounts
                page_high_discount_count = 0
                for product_data in page_products:
                    product = self.parse_product_data(product_data)
                    if product:
                        products.append(product)
                        page_high_discount_count += 1
                        # Send notification immediately
                        self._send_notification(product)
                
                print(f"🔥 Page {page}: {page_high_discount_count} high discount products (≥70% off)")
                
                # Check if this looks like the last page
                if len(page_products) < products_per_page:
                    print(f"📄 Page {page}: Appears to be last page ({len(page_products)} products)")
                
                # Move to next page
                page += 1
                
                # Continue until no more products
                    
        except Exception as e:
            self.logger.error(f"Error scraping Flannels API: {str(e)}")
            
        self.logger.info(f"Successfully scraped {len(products)} products from Flannels")
        return products
    
    def _send_notification(self, product: Product) -> None:
        """Send Discord notification for a high discount product."""
        try:
            import os
            from notifications.discord_notifier import DiscordNotifier
            
            webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
            if not webhook_url:
                print(f"⚠️  No webhook URL set, skipping notification")
                return
                
            notifier = DiscordNotifier(webhook_url)
            
            # Create fancy title
            title = f"🔥 {self.name} Flash Sale - {product.discount_percentage:.0f}% OFF!"
            
            notifier.send_high_discount_alerts([product])
            print(f"📲 Notification sent: {product.name[:50]}... ({product.discount_percentage:.0f}% off)")
            
        except Exception as e:
            print(f"❌ Failed to send notification: {str(e)}")
    
    def _build_api_url(self, page: int, products_per_page: int) -> str:
        """Build the API URL for a specific page."""
        params = {
            'categoryId': 'FLAN_TOPCLEARMENCLOT',
            'page': page,
            'productsPerPage': products_per_page,
            'sortOption': 'rank',
            'selectedFilters': '',
            'isSearch': 'false',
            'searchText': '',
            'columns': '4',
            'mobileColumns': '2',
            'clearFilters': 'false',
            'pathName': '/clearance/men/clothing',
            'searchTermCategory': '',
            'selectedCurrency': 'GBP',
            'portalSiteId': '48',
            'searchCategory': ''
        }
        
        # Build query string
        query_params = '&'.join([f"{key}={value}" for key, value in params.items()])
        return f"{self.api_base_url}?{query_params}"
    
    def parse_product_data(self, product_data: dict) -> Optional[Product]:
        """Parse individual product data from JSON."""
        try:
            # Extract discount percentage from JSON
            discount_percent_text = product_data.get('discountPercentText')
            if not discount_percent_text:
                return None
            
            try:
                discount_percentage = float(discount_percent_text)
            except (ValueError, TypeError):
                self.logger.debug(f"Invalid discount percentage: {discount_percent_text}")
                return None
            
            # Only process products with 70% or higher discount
            if discount_percentage < 70:
                return None
            
            # Extract product name
            brand = product_data.get('brand', '').strip()
            name = product_data.get('name', '').strip()
            if not name:
                return None
            
            # Combine brand and name
            full_name = f"{brand} {name}".strip() if brand else name
            
            # Extract and build product URL
            url_path = product_data.get('url', '').strip()
            if not url_path:
                return None
            
            if url_path.startswith('/'):
                product_url = 'https://www.flannels.com' + url_path
            else:
                product_url = url_path
            
            # Extract prices
            # Current sale price
            price_unformatted = product_data.get('priceUnFormatted')
            if price_unformatted is None:
                # Try to parse from formatted price
                price_text = product_data.get('price', '').replace('£', '').strip()
                try:
                    sale_price = float(price_text)
                except (ValueError, TypeError):
                    return None
            else:
                sale_price = float(price_unformatted)
            
            # Original price (ticket price)
            ticket_price = product_data.get('ticketPrice', '').replace('£', '').strip()
            if not ticket_price:
                return None
            
            try:
                original_price = float(ticket_price)
            except (ValueError, TypeError):
                return None
            
            # Validate prices
            if original_price <= 0 or sale_price <= 0 or original_price <= sale_price:
                return None
            
            # Recalculate discount percentage to ensure accuracy
            calculated_discount = self.calculate_discount_percentage(original_price, sale_price)
            
            # Use the higher of calculated or provided discount
            final_discount = max(discount_percentage, calculated_discount)
            
            # Extract product image
            image_url = product_data.get('imageLarge') or product_data.get('image')
            if image_url and not image_url.startswith('http'):
                image_url = 'https://www.flannels.com' + image_url
            
            # Create product object
            product = Product(
                name=full_name,
                original_price=original_price,
                sale_price=sale_price,
                discount_percentage=final_discount,
                url=product_url,
                image_url=image_url,
                retailer=self.name
            )
            
            self.logger.debug(f"Parsed high discount product: {full_name} ({final_discount:.1f}% off)")
            return product
            
        except Exception as e:
            self.logger.debug(f"Failed to parse product data: {str(e)}")
            return None
