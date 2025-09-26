import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TestsendService:
    """Service for sending test emails"""
    
    def __init__(self):
        self.rate_limit_store = {}  # In production, use Redis
        self.max_sends_per_minute = 5
    
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
        user_id: str = "default"
    ) -> Dict[str, Any]:
        """Send test email via SMTP"""
        
        # Check rate limit
        if not self.check_rate_limit(user_id):
            return {
                'success': False,
                'error': f'Rate limit exceeded. Maximum {self.max_sends_per_minute} test emails per minute.'
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = 'noreply@example.com'  # TODO: Get from settings
            msg['To'] = to_email
            
            # Add unsubscribe header (required)
            msg['List-Unsubscribe'] = '<mailto:unsubscribe@example.com>, <https://example.com/unsubscribe>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # For MVP, we'll simulate sending (no real SMTP)
            # In production, replace with actual SMTP sending
            success = await self._simulate_smtp_send(msg, to_email)
            
            if success:
                self.record_send(user_id)
                logger.info(f"Test email sent successfully to {to_email}")
                return {'success': True, 'message': 'Test email sent successfully'}
            else:
                logger.error(f"Failed to send test email to {to_email}")
                return {'success': False, 'error': 'SMTP delivery failed'}
                
        except Exception as e:
            logger.error(f"Error sending test email: {str(e)}")
            return {'success': False, 'error': f'Email sending failed: {str(e)}'}
    
    async def _simulate_smtp_send(self, msg: MIMEMultipart, to_email: str) -> bool:
        """Simulate SMTP sending for MVP"""
        # In production, replace with:
        # server = smtplib.SMTP('smtp.example.com', 587)
        # server.starttls()
        # server.login(username, password)
        # server.send_message(msg)
        # server.quit()
        
        # For now, just validate email format and simulate success
        if '@' in to_email and '.' in to_email.split('@')[1]:
            logger.info(f"[SIMULATED] Test email would be sent to {to_email}")
            logger.info(f"[SIMULATED] Subject: {msg['Subject']}")
            return True
        else:
            return False
    
    async def _real_smtp_send(self, msg: MIMEMultipart, smtp_config: Dict[str, str]) -> bool:
        """Real SMTP sending (for production)"""
        try:
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            if smtp_config.get('use_tls'):
                server.starttls()
            if smtp_config.get('username'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            server.send_message(msg)
            server.quit()
            return True
            
        except Exception as e:
            logger.error(f"SMTP error: {str(e)}")
            return False


# Global instance
testsend_service = TestsendService()
