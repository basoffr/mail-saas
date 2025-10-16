"""
Test Email Service - Wrapper around unified email_sender.py

This service provides test email sending with rate limiting.
All actual email sending logic is delegated to email_sender.py.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger

from app.services.email_sender import email_sender


class TestsendService:
    """
    Service for sending test emails with rate limiting.
    
    Delegates actual email sending to unified email_sender.py.
    """
    
    def __init__(self):
        self.rate_limit_store = {}  # In production, use Redis
        self.max_sends_per_minute = 5
        self.email_sender = email_sender
    
    def check_rate_limit(self, user_id: str) -> bool:
        """Check if user is within rate limit"""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old entries
        if user_id in self.rate_limit_store:
            self.rate_limit_store[user_id] = [
                timestamp for timestamp in self.rate_limit_store[user_id]
                if timestamp > minute_ago
            ]
        else:
            self.rate_limit_store[user_id] = []
        
        # Check limit
        return len(self.rate_limit_store[user_id]) < self.max_sends_per_minute
    
    def record_send(self, user_id: str):
        """Record a send for rate limiting"""
        now = datetime.utcnow()
        if user_id not in self.rate_limit_store:
            self.rate_limit_store[user_id] = []
        self.rate_limit_store[user_id].append(now)
    
    async def send_test_email(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str, 
        text_body: str,
        user_id: str = "default",
        mail_number: int = 1,
        domain: str = None,  # Auto-detected from version if None
        image_key: Optional[str] = None,
        report_filename: Optional[str] = None,
        version: int = 1
    ) -> Dict[str, Any]:
        """
        Send test email via unified email sender.
        
        Features:
        - Rate limiting (5 per minute per user)
        - Domain-aware FROM address (auto-detected from version)
        - Asset handling (screenshots + PDFs)
        - Signature injection
        - Real SMTP or simulation
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_body: HTML body
            text_body: Plain text body
            user_id: User ID for rate limiting
            mail_number: Mail number (1-4)
            domain: Optional domain (auto-detected if None)
            image_key: Optional screenshot key for M1/M2
            report_filename: Optional PDF filename for M3
            version: Template version (1-4)
            
        Returns:
            Dict with success status
        """
        # Check rate limit
        if not self.check_rate_limit(user_id):
            logger.warning(f"❌ Rate limit exceeded for user {user_id}")
            return {
                'success': False,
                'error': f'Rate limit exceeded. Maximum {self.max_sends_per_minute} test emails per minute.'
            }
        
        # Delegate to unified email sender
        # Generate mock IDs for testing (to match campaign send behavior)
        import uuid
        mock_message_id = f"test-{uuid.uuid4().hex[:12]}"
        mock_lead_id = f"test-lead-{uuid.uuid4().hex[:8]}"
        
        logger.info(f"📧 Test email request: V{version}M{mail_number} to {to_email}")
        logger.debug(f"Test send with mock IDs - message: {mock_message_id}, lead: {mock_lead_id}")
        
        result = await self.email_sender.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            version=version,
            mail_number=mail_number,
            lead_id=mock_lead_id,         # Mock lead ID for unsubscribe headers
            message_id=mock_message_id,   # Mock message ID for tracking
            image_key=image_key,
            report_filename=report_filename,
            enable_tracking=True  # Match campaign behavior (tracking pixel + unsubscribe)
        )
        
        # Record successful send for rate limiting
        if result['success']:
            self.record_send(user_id)
            logger.info(f"✅ Test email sent successfully to {to_email}")
        else:
            logger.error(f"❌ Test email failed: {result.get('error', 'Unknown error')}")
        
        return result


# Global instance
testsend_service = TestsendService()
