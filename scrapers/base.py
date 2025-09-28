"""
Base scraper classes for the discount notification system.
Provides abstract interfaces for extensible scraper implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime


@dataclass
class Product:
    """Data class representing a scraped product."""
    name: str
    original_price: float
    sale_price: float
    discount_percentage: float
    url: str
    image_url: Optional[str] = None
    retailer: str = ""
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
    
    @property
    def is_high_discount(self) -> bool:
        """Check if product has 70% or more discount."""
        return self.discount_percentage >= 70.0


class BaseScraper(ABC):
    """
    Abstract base class for all retailer scrapers.
    
    This class defines the interface that all scrapers must implement,
    ensuring consistency and making it easy to add new retailers.
    """
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.logger = logging.getLogger(f"scraper.{name}")
        self.session = None
        
    @abstractmethod
    def scrape_products(self) -> List[Product]:
        """
        Scrape products from the retailer's sale page.
        
        Returns:
            List[Product]: List of scraped products with discount information
        """
        pass
    
    @abstractmethod
    def parse_product_data(self, product_element) -> Optional[Product]:
        """
        Parse individual product data from HTML element.
        
        Args:
            product_element: HTML element containing product information
            
        Returns:
            Product: Parsed product object or None if parsing fails
        """
        pass
    
    def setup_session(self) -> None:
        """Setup HTTP session with appropriate headers and settings."""
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        
        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Common headers to avoid detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not_A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
    
    def get_page(self, url: str, **kwargs) -> Optional[str]:
        """
        Fetch page content with error handling.
        
        Args:
            url: URL to fetch
            **kwargs: Additional arguments for requests
            
        Returns:
            str: Page content or None if fetch fails
        """
        if not self.session:
            self.setup_session()
            
        try:
            self.logger.info(f"Fetching page: {url}")
            
            # Add a small delay to be respectful
            import time
            time.sleep(1)
            
            response = self.session.get(url, timeout=30, **kwargs)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch {url}: {str(e)}")
            return None
    
    def calculate_discount_percentage(self, original_price: float, sale_price: float) -> float:
        """Calculate discount percentage."""
        if original_price <= 0:
            return 0.0
        return round(((original_price - sale_price) / original_price) * 100, 2)
    
    def clean_price(self, price_text: str) -> float:
        """
        Clean and parse price text to float.
        
        Args:
            price_text: Raw price text (e.g., "£99.99", "$150.00")
            
        Returns:
            float: Cleaned price value
        """
        import re
        if not price_text:
            return 0.0
            
        # Remove currency symbols and extra whitespace
        cleaned = re.sub(r'[£$€,\s]', '', price_text.strip())
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            self.logger.warning(f"Could not parse price: {price_text}")
            return 0.0
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"
