"""
END Clothing scraper implementation.
"""

from typing import List, Optional
import re
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper, Product


class EndClothingScraper(BaseScraper):
    """Scraper for END Clothing men's sale page."""
    
    def __init__(self):
        super().__init__(
            name="END Clothing",
            base_url="https://www.endclothing.com/gb/sale"
        )
    
    def scrape_products(self) -> List[Product]:
        """Scrape products from END Clothing sale page."""
        products = []
        total_products_scanned = 0
        pages_navigated = 0
        
        print("🔍 END Clothing: Starting scraping...")
        self.logger.info("Starting END Clothing scraping")
        
        try:
            page = 1
            
            while True:
                print(f"🔍 END Clothing Page {page}: Scraping...")
                pages_navigated += 1
                
                # Build URL for current page
                if page == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}?page={page}"
                
                # Get page content
                html_content = self.get_page(url)
                if not html_content:
                    print(f"❌ Page {page}: Failed to load")
                    break
                
                # Parse products from HTML
                page_products, page_total_scanned = self._parse_products_from_html(html_content, page)
                products.extend(page_products)
                total_products_scanned += page_total_scanned
                
                # Send notifications for high discount products
                for product in page_products:
                    self._send_notification(product)
                
                print(f"✅ Page {page}: Found {len(page_products)} high discount products (scanned {page_total_scanned} total products)")
                
                # Stop if no product containers found (end of results)
                if page_total_scanned == 0:
                    print(f"📄 Page {page}: No product containers found, stopping")
                    break
                
                # Move to next page
                page += 1
                
                # Add delay between pages
                import time
                time.sleep(2)
            
            
            print(f"✅ END Clothing: Navigation Summary")
            print(f"   📄 Pages navigated: {pages_navigated}")
            print(f"   📦 Total products scanned: {total_products_scanned}")
            print(f"   🔥 High discount products found: {len(products)}")
            print(f"   📊 Success rate: {(len(products)/total_products_scanned*100):.1f}%" if total_products_scanned > 0 else "   📊 Success rate: 0%")
            
            return products
            
        except Exception as e:
            self.logger.error(f"Error scraping END Clothing: {str(e)}")
            return products
    
    def _parse_products_from_html(self, html_content: str, page_number: int) -> tuple[List[Product], int]:
        """Parse products from HTML content."""
        products = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all product containers using the specific selector
        product_containers = soup.find_all("a", {"data-test-id": "ProductCard__ProductCardSC"})
        
        print(f"📦 Page {page_number}: Found {len(product_containers)} product containers")
        
        for product_element in product_containers:
            try:
                product = self.parse_product_data(product_element)
                if product:
                    products.append(product)
                    print(f"   💰 Found: {product.name[:50]}... - {product.discount_percentage:.0f}% off (£{product.original_price:.0f} → £{product.sale_price:.0f})")
                else:
                    # Only log high discounts, skip verbose logging for low discounts
                    pass
                    
            except Exception as e:
                continue
        
        return products, len(product_containers)
    
    def _send_notification(self, product: Product) -> None:
        """Send Discord notification for a high discount product."""
        try:
            import os
            from notifications.discord_notifier import DiscordNotifier
            
            webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
            if not webhook_url:
                print(f"⚠️  No webhook URL set, skipping notification")
                return
                
            # Initialize notifier with idempotency enabled
            notifier = DiscordNotifier(webhook_url, enable_idempotency=True)
            
            # Send notification (will automatically check for duplicates)
            success = notifier.send_high_discount_alerts([product])
            
            if success:
                print(f"📲 Notification sent: {product.name[:50]}... ({product.discount_percentage:.0f}% off)")
            else:
                print(f"❌ Failed to send notification for {product.name[:50]}...")
            
        except Exception as e:
            print(f"❌ Failed to send notification: {str(e)}")
    
    def parse_product_data(self, product_element) -> Optional[Product]:
        """Parse individual product data from HTML element."""
        try:
            # Extract product URL
            product_url = product_element.get("href")
            if not product_url:
                return None
            
            if not product_url.startswith('http'):
                product_url = 'https://www.endclothing.com' + product_url
            
            # Extract discount information using the specific selector
            discount_elem = product_element.find("span", {"class": "styles__DiscountSC-sc-d3b68a1e-7"})
            if not discount_elem:
                return None
            
            discount_text = discount_elem.get_text(strip=True)
            if not discount_text:
                return None
            
            # Extract discount percentage from text (e.g., "40% off")
            discount_match = re.search(r'(\d+)% off', discount_text)
            if not discount_match:
                return None
            
            discount_percentage = float(discount_match.group(1))
            
            # Only include products with ≥70% discount
            if discount_percentage < 70.0:
                return None
            
            # Extract product name - look for the main product name span
            # Based on the HTML structure, the product name appears to be in a span
            name_elem = None
            
            # Try to find the product name span (usually the second span with substantial text)
            spans = product_element.find_all('span')
            for span in spans:
                text = span.get_text(strip=True)
                # Look for spans that contain product names (longer text, not just labels)
                if text and len(text) > 10 and len(text) < 100 and not text.endswith('% off') and not text.startswith('£'):
                    name_elem = span
                    break
            
            if not name_elem:
                return None
            
            product_name = name_elem.get_text(strip=True)
            if not product_name:
                return None
            
            # Extract prices - look for price elements
            price_elements = product_element.find_all(['span', 'div'], class_=re.compile(r'price'))
            
            original_price = 0.0
            sale_price = 0.0
            
            # Look for price patterns in text
            price_text = product_element.get_text()
            
            # Pattern 1: £199£11940% off (original price, sale price, discount)
            price_pattern = r'£(\d+)£(\d+)(\d+)% off'
            match = re.search(price_pattern, price_text)
            if match:
                original_price = float(match.group(1))
                sale_price = float(match.group(2))
            else:
                # Pattern 2: Look for separate price elements
                prices = re.findall(r'£(\d+)', price_text)
                if len(prices) >= 2:
                    # Assume higher price is original, lower is sale
                    prices_float = [float(p) for p in prices]
                    prices_float.sort(reverse=True)
                    original_price = prices_float[0]
                    sale_price = prices_float[1]
            
            # Skip if we couldn't extract valid prices
            if original_price <= 0 or sale_price <= 0 or original_price <= sale_price:
                return None
            
            # Extract image
            img_elem = product_element.find('img')
            image_url = None
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = 'https://www.endclothing.com' + image_url
            
            product = Product(
                name=product_name,
                original_price=original_price,
                sale_price=sale_price,
                discount_percentage=discount_percentage,
                url=product_url,
                image_url=image_url,
                retailer=self.name
            )
            
            return product
            
        except Exception as e:
            self.logger.debug(f"Failed to parse product: {str(e)}")
            return None
