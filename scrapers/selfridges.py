"""
Selfridges scraper implementation using Selenium with fresh browser sessions.
"""

from typing import List, Optional
from bs4 import BeautifulSoup
import time
import random
from scrapers.base import BaseScraper, Product
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


class SelfridgesScraper(BaseScraper):
    """Scraper for Selfridges men's sale page using Selenium."""
    
    def __init__(self):
        super().__init__(
            name="Selfridges",
            base_url="https://www.selfridges.com/GB/en/cat/mens/on_sale/"
        )
    
    def scrape_products(self) -> List[Product]:
        """Scrape products from Selfridges using Selenium with fresh browser sessions."""
        print("🔍 Selfridges: Starting scraping with Selenium...")
        self.logger.info("Starting Selfridges scraping")
        
        products = []
        page = 1
        
        while True:
            print(f"🔍 Selfridges Page {page}: Scraping...")
            
            # Get HTML content using fresh browser
            html_content = self._get_page_with_selenium(page)
            if not html_content:
                print(f"❌ Page {page}: Failed to load")
                break
            
            # Parse products from HTML
            page_products = self._parse_products_from_html(html_content, page)
            products.extend(page_products)
            
            # Send notifications for high discount products
            for product in page_products:
                self._send_notification(product)
            
            print(f"✅ Page {page}: Found {len(page_products)} high discount products")
            
            # Stop if no products found (end of results)
            if not page_products:
                print(f"📄 Page {page}: No products found, stopping")
                break
            
            # Delay between pages
            time.sleep(random.uniform(8, 15))
            page += 1
        
        print(f"✅ Selfridges: Total {len(products)} high discount products found")
        return products
    
    def _create_fresh_browser(self) -> webdriver.Chrome:
        """Create a fresh Chrome browser instance."""
        options = Options()
        # Remove headless for debugging - can be re-enabled for production
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        selected_ua = random.choice(user_agents)
        options.add_argument(f'--user-agent={selected_ua}')
        
        try:
            driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
        except Exception:
            driver = webdriver.Chrome(options=options)
        
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(30)
        return driver
    
    def _get_page_with_selenium(self, page_number: int) -> Optional[str]:
        """Get page HTML content using a fresh browser session."""
        driver = None
        try:
            driver = self._create_fresh_browser()
            url = f"{self.base_url}?pn={page_number}" if page_number > 1 else self.base_url
            
            driver.get(url)
            time.sleep(5)  # Wait for page to load
            
            html_content = driver.page_source
            return html_content
            
        except Exception as e:
            print(f"❌ Selenium error on page {page_number}: {str(e)}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass
    
    def _parse_products_from_html(self, html_content: str, page_number: int) -> List[Product]:
        """Parse products from HTML content."""
        products = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all product containers
        product_containers = soup.find_all('li', {'data-analytics-link-target': 'product_card_link'})
        print(f"📦 Page {page_number}: Found {len(product_containers)} products")
        
        for product_element in product_containers:
            try:
                # Extract product details
                brand_elem = product_element.find('h2')
                name_elem = product_element.find('a')
                brand = brand_elem.get_text(strip=True) if brand_elem else ""
                name = name_elem.get_text(strip=True) if name_elem else ""
                full_name = f"{brand} {name}".strip()
                
                if not full_name:
                    continue
                
                # Extract URL
                url_elem = product_element.find('a', href=True)
                if not url_elem:
                    continue
                product_url = url_elem['href']
                if not product_url.startswith('http'):
                    product_url = 'https://www.selfridges.com' + product_url
                
                # Extract prices
                discount_price = 0.0
                previous_prices = []
                
                price_items = product_element.find_all('li', {'data-testid': 'product-price'})
                for price_item in price_items:
                    price_text = price_item.get_text(strip=True)
                    if 'discount price:' in price_text.lower():
                        price_part = price_text.split(':')[-1].strip()
                        discount_price = self.clean_price(price_part)
                    elif 'previous price:' in price_text.lower():
                        price_part = price_text.split(':')[-1].strip()
                        prev_price = self.clean_price(price_part)
                        if prev_price > 0:
                            previous_prices.append(prev_price)
                
                # Use highest previous price as original
                original_price = max(previous_prices) if previous_prices else 0.0
                
                # Skip if invalid prices
                if original_price <= 0 or discount_price <= 0 or original_price <= discount_price:
                    continue
                
                # Calculate discount
                discount_percentage = self.calculate_discount_percentage(original_price, discount_price)
                
                # Only include products with ≥70% discount
                if discount_percentage >= 70.0:
                    # Extract image
                    img_elem = product_element.find('img')
                    image_url = None
                    if img_elem:
                        image_url = img_elem.get('src')
                        if image_url and image_url.startswith('//'):
                            image_url = 'https:' + image_url
                    
                    product = Product(
                        name=full_name,
                        original_price=original_price,
                        sale_price=discount_price,
                        discount_percentage=discount_percentage,
                        url=product_url,
                        image_url=image_url,
                        retailer=self.name
                    )
                    products.append(product)
                    
            except Exception as e:
                continue
        
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
    
    def parse_product_data(self, product_element) -> Optional[Product]:
        """Parse individual product data from HTML element (required by base class)."""
        # This method is not used in the Selenium-based approach,
        # but is required by the abstract base class
        return None