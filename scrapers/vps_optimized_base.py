"""
VPS-optimized base scraper with enhanced network handling.
Includes retry logic, user agent rotation, and timeout management.
"""

import requests
import time
import random
import logging
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup


class VPSOptimizedBaseScraper:
    """Base scraper optimized for VPS deployment with robust network handling."""
    
    def __init__(self, scraper_name: str):
        self.scraper_name = scraper_name
        self.logger = logging.getLogger(f"scraper.{scraper_name}")
        
        # Enhanced session with retry logic
        self.session = self._create_optimized_session()
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        # Request headers
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _create_optimized_session(self) -> requests.Session:
        """Create a session with optimized retry logic for VPS."""
        session = requests.Session()
        
        # Retry strategy with exponential backoff
        retry_strategy = Retry(
            total=5,  # Total number of retries
            backoff_factor=2,  # Exponential backoff: 1, 2, 4, 8, 16 seconds
            status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]  # Methods to retry
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set timeouts
        session.timeout = (10, 60)  # (connect timeout, read timeout)
        
        return session
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(self.user_agents)
    
    def _make_request(self, url: str, max_retries: int = 3, delay: float = 2.0) -> Optional[requests.Response]:
        """
        Make a request with enhanced error handling and retry logic.
        
        Args:
            url: URL to request
            max_retries: Maximum number of retries
            delay: Initial delay between retries
            
        Returns:
            Response object or None if all retries failed
        """
        for attempt in range(max_retries + 1):
            try:
                # Rotate user agent
                headers = self.headers.copy()
                headers['User-Agent'] = self._get_random_user_agent()
                
                self.logger.info(f"Attempt {attempt + 1}/{max_retries + 1}: Fetching {url}")
                
                # Make request with timeout
                response = self.session.get(
                    url, 
                    headers=headers,
                    timeout=(15, 90),  # 15s connect, 90s read timeout
                    allow_redirects=True,
                    verify=True
                )
                
                # Check if response is successful
                if response.status_code == 200:
                    self.logger.info(f"Successfully fetched {url} (Status: {response.status_code})")
                    return response
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    if response.status_code in [429, 503, 504]:  # Rate limited or server error
                        wait_time = delay * (2 ** attempt) + random.uniform(1, 3)
                        self.logger.info(f"Rate limited, waiting {wait_time:.1f}s before retry")
                        time.sleep(wait_time)
                        continue
                    elif response.status_code == 403:  # Forbidden
                        self.logger.warning(f"Access forbidden for {url}, trying different user agent")
                        continue
                    else:
                        self.logger.error(f"HTTP {response.status_code} for {url}")
                        return None
                        
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt) + random.uniform(2, 5)
                    self.logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All retries failed due to timeout for {url}")
                    
            except requests.exceptions.ConnectionError as e:
                self.logger.warning(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt) + random.uniform(3, 8)
                    self.logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All retries failed due to connection error for {url}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All retries failed for {url}: {str(e)}")
                    
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"All retries failed for {url}: {str(e)}")
        
        self.logger.error(f"Failed to fetch {url} after {max_retries + 1} attempts")
        return None
    
    def get_page(self, url: str) -> Optional[str]:
        """
        Get page content with VPS-optimized error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string or None if failed
        """
        try:
            response = self._make_request(url)
            if response:
                return response.text
            else:
                self.logger.error(f"Failed to get page content for {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting page {url}: {str(e)}")
            return None
    
    def get_json(self, url: str) -> Optional[Dict[Any, Any]]:
        """
        Get JSON data with VPS-optimized error handling.
        
        Args:
            url: URL to fetch
            
        Returns:
            JSON data as dict or None if failed
        """
        try:
            response = self._make_request(url)
            if response:
                return response.json()
            else:
                self.logger.error(f"Failed to get JSON data for {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting JSON from {url}: {str(e)}")
            return None
    
    def test_connectivity(self, test_urls: list[str]) -> Dict[str, bool]:
        """
        Test connectivity to multiple URLs to diagnose network issues.
        
        Args:
            test_urls: List of URLs to test
            
        Returns:
            Dictionary mapping URLs to connectivity status
        """
        results = {}
        
        for url in test_urls:
            self.logger.info(f"Testing connectivity to {url}")
            response = self._make_request(url, max_retries=1, delay=1.0)
            results[url] = response is not None
            
            if response:
                self.logger.info(f"✅ {url} - Connected successfully")
            else:
                self.logger.warning(f"❌ {url} - Connection failed")
        
        return results
