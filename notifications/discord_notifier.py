"""
Discord webhook notification system for high-discount alerts.
"""

import requests
import logging
from typing import List, Optional
from datetime import datetime
from scrapers.base import Product
from .notification_tracker import NotificationTracker


class DiscordNotifier:
    """
    Discord webhook notifier for sending product discount alerts.
    
    Sends formatted messages with product images and links when
    products have high discounts (>70%).
    """
    
    def __init__(self, webhook_url: str, enable_idempotency: bool = True):
        self.webhook_url = webhook_url
        self.logger = logging.getLogger("discord_notifier")
        self.enable_idempotency = enable_idempotency
        
        # Initialize notification tracker for idempotency
        if self.enable_idempotency:
            self.tracker = NotificationTracker()
            self.logger.info("Idempotency enabled - duplicate notifications will be prevented")
        else:
            self.tracker = None
            self.logger.info("Idempotency disabled - all notifications will be sent")
        
    def send_high_discount_alerts(self, products: List[Product]) -> bool:
        """
        Send Discord alerts for products with >70% discount.
        
        Args:
            products: List of products to check and potentially alert on
            
        Returns:
            bool: True if all alerts sent successfully, False otherwise
        """
        high_discount_products = [p for p in products if p.is_high_discount]
        
        if not high_discount_products:
            self.logger.info("No high discount products found")
            return True
            
        self.logger.info(f"Found {len(high_discount_products)} high discount products")
        
        success = True
        for product in high_discount_products:
            if not self._send_product_alert(product):
                success = False
                
        return success
    
    def _send_product_alert(self, product: Product) -> bool:
        """
        Send individual product alert to Discord.
        
        Args:
            product: Product to send alert for
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        # Check for duplicate notifications if idempotency is enabled
        if self.enable_idempotency and self.tracker:
            if self.tracker.has_been_sent(
                product.url, 
                product.retailer, 
                product.discount_percentage, 
                product.name
            ):
                self.logger.info(f"Skipping duplicate notification for {product.name}")
                return True  # Return True since we "successfully" handled it (by skipping)
        
        try:
            embed = self._create_product_embed(product)
            payload = {
                "username": "Fashion Discount Bot",
                "avatar_url": "https://cdn.discordapp.com/attachments/123/456/fashion-bot-avatar.png",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            # Mark as sent if idempotency is enabled
            if self.enable_idempotency and self.tracker:
                self.tracker.mark_as_sent(
                    product.url, 
                    product.retailer, 
                    product.discount_percentage, 
                    product.name
                )
            
            self.logger.info(f"Successfully sent alert for {product.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert for {product.name}: {str(e)}")
            return False
    
    def _create_product_embed(self, product: Product) -> dict:
        """
        Create Discord embed for product alert.
        
        Args:
            product: Product to create embed for
            
        Returns:
            dict: Discord embed payload
        """
        # Format prices
        original_price_str = f"£{product.original_price:.2f}"
        sale_price_str = f"£{product.sale_price:.2f}"
        savings = product.original_price - product.sale_price
        savings_str = f"£{savings:.2f}"
        
        embed = {
            "title": f"🔥 {product.discount_percentage}% OFF - {product.name}",
            "url": product.url,
            "color": 0xFF0000,  # Red color for high discounts
            "fields": [
                {
                    "name": "💰 Price",
                    "value": f"~~{original_price_str}~~ **{sale_price_str}**",
                    "inline": True
                },
                {
                    "name": "📊 Discount",
                    "value": f"**{product.discount_percentage}%** off",
                    "inline": True
                },
                {
                    "name": "💸 You Save",
                    "value": f"**{savings_str}**",
                    "inline": True
                },
                {
                    "name": "🏪 Retailer",
                    "value": product.retailer,
                    "inline": True
                },
                {
                    "name": "🕐 Found At",
                    "value": product.scraped_at.strftime("%H:%M on %d/%m/%Y"),
                    "inline": True
                },
                {
                    "name": "🔗 Shop Now",
                    "value": f"[View Product]({product.url})",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Fashion Discount Notifier • High Discount Alert"
            },
            "timestamp": product.scraped_at.isoformat()
        }
        
        # Add product image if available
        if product.image_url:
            embed["image"] = {"url": product.image_url}
        
        return embed
    
    def send_summary_report(self, total_products: int, high_discount_count: int, 
                          retailers_checked: List[str]) -> bool:
        """
        Send summary report of scraping session.
        
        Args:
            total_products: Total number of products scraped
            high_discount_count: Number of high discount products found
            retailers_checked: List of retailer names checked
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            embed = {
                "title": "📊 Scraping Session Summary",
                "color": 0x00FF00 if high_discount_count > 0 else 0x808080,
                "fields": [
                    {
                        "name": "🛍️ Products Checked",
                        "value": str(total_products),
                        "inline": True
                    },
                    {
                        "name": "🔥 High Discounts Found",
                        "value": str(high_discount_count),
                        "inline": True
                    },
                    {
                        "name": "🏪 Retailers Checked",
                        "value": ", ".join(retailers_checked),
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Fashion Discount Notifier • Session Summary"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            payload = {
                "username": "Fashion Discount Bot",
                "embeds": [embed]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info("Successfully sent summary report")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send summary report: {str(e)}")
            return False
    
    def test_webhook(self) -> bool:
        """
        Test if webhook is working by sending a simple message.
        
        Returns:
            bool: True if webhook is working, False otherwise
        """
        try:
            payload = {
                "username": "Fashion Discount Bot",
                "content": "🧪 Webhook test - Fashion Discount Notifier is online!"
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info("Webhook test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook test failed: {str(e)}")
            return False
    
    def get_notification_stats(self) -> dict:
        """
        Get statistics about sent notifications.
        
        Returns:
            dict: Statistics about notification tracking
        """
        if self.enable_idempotency and self.tracker:
            return self.tracker.get_stats()
        else:
            return {"idempotency_enabled": False}
