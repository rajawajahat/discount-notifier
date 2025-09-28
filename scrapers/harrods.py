"""
Harrods scraper implementation using JSON-LD + HTML parsing.
"""

from typing import List, Optional
from bs4 import BeautifulSoup
import json
import re
from scrapers.base import BaseScraper, Product


class HarrodsScraper(BaseScraper):
    """Scraper for Harrods men's sale page using JSON-LD and HTML parsing."""
    
    def __init__(self):
        super().__init__(
            name="Harrods",
            base_url="https://www.harrods.com/en-gb/sale/men"
        )
    
    def scrape_products(self) -> List[Product]:
        """Scrape products from Harrods sale pages using pagination."""
        products = []
        
        try:
            page = 1
            self.logger.info("Starting Harrods scraping with pagination")
            
            while True:
                # Build page URL
                page_url = f"{self.base_url}?page={page}" if page > 1 else self.base_url
                print(f"🔍 Harrods Page {page}: {page_url}")
                self.logger.info(f"Fetching page {page}: {page_url}")
                
                # Get page content
                html_content = self.get_page(page_url)
                if not html_content:
                    print(f"❌ Page {page}: No content received")
                    self.logger.warning(f"No content received for page {page}")
                    break
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Extract JSON-LD data
                json_ld_data = self._extract_json_ld_data(soup)
                if not json_ld_data:
                    print(f"❌ Page {page}: No JSON-LD data found, stopping pagination")
                    self.logger.info(f"No JSON-LD data found on page {page}, stopping")
                    break
                
                # Extract product elements from HTML
                product_elements = soup.find_all('article', {'data-test-id': 'product-item'})
                
                if not product_elements:
                    print(f"❌ Page {page}: No product elements found, stopping pagination")
                    self.logger.info(f"No product elements found on page {page}, stopping")
                    break
                
                print(f"📦 Page {page}: Found {len(product_elements)} total products")
                self.logger.info(f"Found {len(product_elements)} products on page {page}")
                
                # Process each product by combining JSON-LD and HTML data
                page_products = self._process_page_products(json_ld_data, product_elements)
                products.extend(page_products)
                
                # Send notifications for high discount products
                for product in page_products:
                    self._send_notification(product)
                
                high_discount_count = len(page_products)
                print(f"🔥 Page {page}: {high_discount_count} high discount products (≥70% off)")
                self.logger.info(f"Processed {len(page_products)} high discount products from page {page}")
                
                # Check if this looks like the last page (fewer products than expected)
                if len(product_elements) < 50:  # Harrods typically shows 60 per page
                    print(f"📄 Page {page}: Appears to be last page ({len(product_elements)} products)")
                
                # Check if we should continue (basic pagination limit)
                page += 1
                # Continue until no more products
                    
        except Exception as e:
            self.logger.error(f"Error scraping Harrods: {str(e)}")
            
        self.logger.info(f"Successfully scraped {len(products)} products from Harrods")
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
    
    def _extract_json_ld_data(self, soup: BeautifulSoup) -> Optional[List[dict]]:
        """Extract product data from JSON-LD script tags."""
        try:
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if data.get('@type') == 'ItemList':
                        items = data.get('itemListElement', [])
                        if items:
                            return [item['item'] for item in items]
                except json.JSONDecodeError:
                    continue
            
            return None
        except Exception as e:
            self.logger.error(f"Error extracting JSON-LD data: {str(e)}")
            return None
    
    def _process_page_products(self, json_ld_items: List[dict], product_elements: List) -> List[Product]:
        """Process products by combining JSON-LD data with HTML elements."""
        products = []
        
        # Create a mapping of product IDs to JSON-LD data
        json_ld_map = {}
        for item in json_ld_items:
            sku = item.get('sku')
            if sku:
                json_ld_map[sku] = item
        
        # Process each HTML product element
        for element in product_elements:
            try:
                product_id = element.get('data-product-card-id')
                if not product_id:
                    continue
                
                # Get corresponding JSON-LD data
                json_data = json_ld_map.get(product_id)
                if not json_data:
                    continue
                
                # Parse product using both data sources
                product = self.parse_product_data(json_data, element)
                if product:
                    products.append(product)
                    
            except Exception as e:
                self.logger.debug(f"Error processing product element: {str(e)}")
                continue
        
        return products
    
    def parse_product_data(self, json_data: dict, html_element) -> Optional[Product]:
        """Parse product data combining JSON-LD and HTML sources."""
        try:
            # Extract basic info from JSON-LD
            name = json_data.get('name', '').strip()
            brand_data = json_data.get('brand', {})
            brand_name = brand_data.get('name', '') if isinstance(brand_data, dict) else str(brand_data)
            
            # Combine brand and product name
            full_name = f"{brand_name} {name}".strip() if brand_name else name
            if not full_name:
                return None
            
            # Product URL from JSON-LD
            product_url = json_data.get('url', '')
            if not product_url:
                return None
            
            # Sale price from JSON-LD offers
            offers = json_data.get('offers', {})
            if not offers:
                return None
            
            price_spec = offers.get('priceSpecification', {})
            sale_price = price_spec.get('price')
            if not sale_price:
                return None
            
            sale_price = float(sale_price)
            
            # Original price from HTML element text
            original_price = self._extract_original_price_from_html(html_element, sale_price)
            if not original_price or original_price <= sale_price:
                return None
            
            # Calculate discount percentage
            discount_percentage = self.calculate_discount_percentage(original_price, sale_price)
            
            # Only process products with ≥70% discount
            if discount_percentage < 70.0:
                return None
            
            # Product image from JSON-LD
            image_url = json_data.get('image')
            if isinstance(image_url, list) and image_url:
                image_url = image_url[0]
            
            # Ensure absolute URL
            if image_url and not image_url.startswith('http'):
                image_url = 'https://www.harrods.com' + image_url
            
            product = Product(
                name=full_name,
                original_price=original_price,
                sale_price=sale_price,
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
    
    def _extract_original_price_from_html(self, html_element, sale_price: float) -> Optional[float]:
        """Extract original price from HTML element text."""
        try:
            # Get all text from the element
            text_content = html_element.get_text(separator=' ', strip=True)
            
            # Look for price patterns in the text
            price_pattern = re.compile(r'£([\d,]+(?:\.\d{2})?)')
            price_matches = price_pattern.findall(text_content)
            
            if not price_matches:
                return None
            
            # Clean and convert prices to float
            prices = []
            for price_text in price_matches:
                cleaned_price = self.clean_price(price_text)
                if cleaned_price > 0:
                    prices.append(cleaned_price)
            
            # Remove duplicates and sort
            unique_prices = sorted(set(prices), reverse=True)
            
            # The original price should be higher than the sale price
            for price in unique_prices:
                if price > sale_price:
                    return price
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting original price: {str(e)}")
            return None
