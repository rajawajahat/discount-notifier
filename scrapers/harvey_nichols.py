"""
Harvey Nichols scraper implementation using API endpoint.
"""

from typing import List, Optional
import json
import time
from scrapers.base import BaseScraper, Product


class HarveyNicholsScraper(BaseScraper):
    """Scraper for Harvey Nichols men's sale page using API."""
    
    def __init__(self):
        super().__init__(
            name="Harvey Nichols",
            base_url="https://www.harveynichols.com/sale/mens/"
        )
        self.api_base_url = "https://integrations.harveynichols.com/hn-fh/api/Product/ProductsPage"
    
    def setup_session(self):
        """Setup session with Harvey Nichols specific headers."""
        super().setup_session()
        
        # Add Harvey Nichols specific headers matching the network request
        self.session.headers.update({
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://www.harveynichols.com',
            'Priority': 'u=1, i',
            'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        })
    
    def scrape_products(self) -> List[Product]:
        """Scrape products from Harvey Nichols using API endpoint."""
        products = []
        
        # Ensure session is set up
        if not hasattr(self, 'session') or self.session is None:
            self.setup_session()
        
        try:
            page = 1
            self.logger.info("Starting Harvey Nichols API scraping with pagination")
            
            while True:
                print(f"🔍 Harvey Nichols Page {page}: API request")
                self.logger.info(f"Fetching page {page} from Harvey Nichols API")
                
                # Build API payload matching the exact browser request
                payload = {
                    "region": "uk",
                    "sort": 0,
                    "page": page,
                    "limit": 60,
                    "keyword": "",
                    "channel": "Desktop",
                    "customerDepartment": "Mens",
                    "customerType": "Public",
                    "store": "",
                    "customerTier": None,
                    "filters": {
                        "categories": "cp43",
                        "dynamicCategoryId": "cp1033"
                    },
                    "pageType": 2,
                    "rowSize": 4,
                    "preview": False
                }
                
                try:
                    # Make POST request to API
                    response = self.session.post(
                        self.api_base_url,
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code != 200:
                        print(f"❌ Page {page}: API returned status {response.status_code}")
                        self.logger.warning(f"API returned status {response.status_code} for page {page}")
                        break
                    
                    data = response.json()
                    page_products = data.get('products', [])
                    
                    if not page_products:
                        print(f"❌ Page {page}: No products found, stopping pagination")
                        self.logger.info(f"No products found on page {page}, stopping")
                        break
                    
                    print(f"📦 Page {page}: Found {len(page_products)} total products")
                    self.logger.info(f"Found {len(page_products)} products on page {page}")
                    
                    page_high_discount_count = 0
                    for product_data in page_products:
                        product = self.parse_product_data(product_data)
                        if product:
                            products.append(product)
                            page_high_discount_count += 1
                            # Send notification immediately
                            self._send_notification(product)
                    
                    print(f"🔥 Page {page}: {page_high_discount_count} high discount products (≥70% off)")
                    self.logger.info(f"Processed {page_high_discount_count} high discount products from page {page}")
                    
                    # Check if we've reached the last page
                    total_pages = data.get('numberOfPages', 0)
                    if page >= total_pages:
                        print(f"📄 Page {page}: Last page reached ({total_pages} total pages)")
                        break
                    
                    # Continue until no more products
                    
                    page += 1
                    time.sleep(1)  # Be respectful to the API
                    
                except Exception as e:
                    print(f"❌ Page {page}: Error making API request - {str(e)}")
                    self.logger.error(f"Error making API request for page {page}: {str(e)}")
                    break
                    
        except Exception as e:
            self.logger.error(f"Error scraping Harvey Nichols API: {str(e)}")
            
        self.logger.info(f"Successfully scraped {len(products)} products from Harvey Nichols")
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
    
    def parse_product_data(self, product_data: dict) -> Optional[Product]:
        """Parse individual product data from API response."""
        try:
            # Extract basic product information
            brand = product_data.get('brand', '').strip()
            name = product_data.get('name', '').strip()
            full_name = f"{brand} {name}".strip() if brand else name
            
            if not full_name:
                return None
            
            # Extract pricing information
            price_gbp = product_data.get('priceGBP', 0)
            sale_price_gbp = product_data.get('salePriceGBP', 0)
            is_markdown = product_data.get('isMarkDown', False)
            
            # Convert to float if they're not already
            if isinstance(price_gbp, (str, int)):
                price_gbp = float(price_gbp)
            if isinstance(sale_price_gbp, (str, int)):
                sale_price_gbp = float(sale_price_gbp)
            
            # Skip products without proper pricing or no discount
            if not (price_gbp > 0 and sale_price_gbp > 0 and price_gbp > sale_price_gbp):
                return None
            
            # Calculate discount percentage
            discount_percentage = self.calculate_discount_percentage(price_gbp, sale_price_gbp)
            
            # Only return products with high discounts (≥70%)
            if discount_percentage < 70.0:
                return None
            
            # Extract product URL
            product_url = product_data.get('productUrl', '')
            if product_url and not product_url.startswith('http'):
                product_url = 'https://www.harveynichols.com' + product_url
            
            # Extract image URL
            image_url = product_data.get('itemImage', '')
            if image_url and not image_url.startswith('http'):
                image_url = 'https://www.harveynichols.com' + image_url
            
            product = Product(
                name=full_name,
                original_price=price_gbp,
                sale_price=sale_price_gbp,
                discount_percentage=discount_percentage,
                url=product_url,
                image_url=image_url,
                retailer=self.name
            )
            
            self.logger.debug(f"Parsed high discount product: {full_name} ({discount_percentage:.1f}% off)")
            return product
            
        except Exception as e:
            self.logger.debug(f"Failed to parse product data: {str(e)}")
            return None
