"""
Notification tracking system to prevent duplicate notifications.
Implements idempotency for product discount alerts.
"""

import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Set, Dict, Any
from pathlib import Path
import logging


class NotificationTracker:
    """
    Tracks sent notifications to prevent duplicates.
    
    Uses product fingerprinting to create unique identifiers
    and stores them persistently to ensure idempotency.
    """
    
    def __init__(self, storage_file: str = "notifications_sent.json"):
        self.storage_file = Path(storage_file)
        self.logger = logging.getLogger("notification_tracker")
        self.sent_notifications: Set[str] = set()
        self._load_sent_notifications()
    
    def _load_sent_notifications(self) -> None:
        """Load previously sent notifications from storage."""
        try:
            if self.storage_file.exists():
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self.sent_notifications = set(data.get('sent_notifications', []))
                    self.logger.info(f"Loaded {len(self.sent_notifications)} previously sent notifications")
            else:
                self.logger.info("No previous notifications found, starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load notification history: {str(e)}")
            self.sent_notifications = set()
    
    def _save_sent_notifications(self) -> None:
        """Save sent notifications to storage."""
        try:
            data = {
                'sent_notifications': list(self.sent_notifications),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.debug(f"Saved {len(self.sent_notifications)} sent notifications")
        except Exception as e:
            self.logger.error(f"Failed to save notification history: {str(e)}")
    
    def create_product_fingerprint(self, product_url: str, retailer: str, 
                                 discount_percentage: float, product_name: str) -> str:
        """
        Create a unique fingerprint for a product.
        
        Args:
            product_url: Product URL
            retailer: Retailer name
            discount_percentage: Discount percentage
            product_name: Product name
            
        Returns:
            str: Unique fingerprint hash
        """
        # Create a unique identifier based on key product attributes
        fingerprint_data = f"{product_url}|{retailer}|{discount_percentage:.1f}|{product_name.strip()}"
        
        # Create hash for consistent, short identifier
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        self.logger.debug(f"Created fingerprint for {product_name}: {fingerprint}")
        return fingerprint
    
    def has_been_sent(self, product_url: str, retailer: str, 
                     discount_percentage: float, product_name: str) -> bool:
        """
        Check if a notification for this product has already been sent.
        
        Args:
            product_url: Product URL
            retailer: Retailer name
            discount_percentage: Discount percentage
            product_name: Product name
            
        Returns:
            bool: True if notification was already sent, False otherwise
        """
        fingerprint = self.create_product_fingerprint(
            product_url, retailer, discount_percentage, product_name
        )
        
        has_sent = fingerprint in self.sent_notifications
        
        if has_sent:
            self.logger.info(f"Notification already sent for {product_name} ({discount_percentage:.0f}% off)")
        else:
            self.logger.info(f"New notification for {product_name} ({discount_percentage:.0f}% off)")
            
        return has_sent
    
    def mark_as_sent(self, product_url: str, retailer: str, 
                    discount_percentage: float, product_name: str) -> None:
        """
        Mark a product notification as sent.
        
        Args:
            product_url: Product URL
            retailer: Retailer name
            discount_percentage: Discount percentage
            product_name: Product name
        """
        fingerprint = self.create_product_fingerprint(
            product_url, retailer, discount_percentage, product_name
        )
        
        self.sent_notifications.add(fingerprint)
        self._save_sent_notifications()
        
        self.logger.info(f"Marked notification as sent for {product_name}")
    
    def cleanup_old_notifications(self, days_to_keep: int = 30) -> None:
        """
        Clean up old notifications to prevent storage bloat.
        
        Args:
            days_to_keep: Number of days to keep notification history
        """
        try:
            if not self.storage_file.exists():
                return
                
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            # For now, we'll keep all notifications since we don't have timestamps
            # In a more advanced implementation, we'd store timestamps and clean up
            self.logger.info(f"Notification cleanup: keeping {len(self.sent_notifications)} notifications")
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old notifications: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about sent notifications.
        
        Returns:
            dict: Statistics about notification tracking
        """
        return {
            'total_sent_notifications': len(self.sent_notifications),
            'storage_file': str(self.storage_file),
            'file_exists': self.storage_file.exists()
        }
