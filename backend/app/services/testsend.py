import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import os

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
        user_id: str = "default",
        mail_number: int = 1,
        domain: str = "punthelder-marketing.nl"
    ) -> Dict[str, Any]:
        """
        Send test email via SMTP with proper logging and assets.
        
        Uses real SMTP if configured, otherwise falls back to simulation.
        Includes signature CID embedding like production campaigns.
        Logs all send attempts as mail_send_ok or mail_send_err.
        """
        
        # Check rate limit
        if not self.check_rate_limit(user_id):
            logger.warning(f"❌ mail_send_err: Rate limit exceeded for user {user_id}")
            return {
                'success': False,
                'error': f'Rate limit exceeded. Maximum {self.max_sends_per_minute} test emails per minute.'
            }
        
        try:
            # Inject signature CID (same as campaigns)
            from app.services.signature_injector import inject_signature_cid, get_alias_from_mail_number
            alias = get_alias_from_mail_number(mail_number)
            html_body = inject_signature_cid(html_body, alias)
            logger.debug(f"Injected {alias} signature for test email")
            
            # Get SMTP configuration from environment
            smtp_host = os.getenv('SMTP_HOST', '')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', '')
            smtp_pass = os.getenv('SMTP_PASS', '')
            mail_from = os.getenv('MAIL_FROM', f'christian@{domain}')
            mail_from_name = os.getenv('MAIL_FROM_NAME', 'Christian')
            
            # Create message with 'related' multipart for CID images
            msg = MIMEMultipart('related')  # Changed from 'alternative' to support CID
            msg['Subject'] = subject
            msg['From'] = f"{mail_from_name} <{mail_from}>"
            msg['To'] = to_email
            
            # Add unsubscribe headers (compliance)
            unsubscribe_email = os.getenv('UNSUBSCRIBE_EMAIL', f'unsubscribe@{domain}')
            msg['List-Unsubscribe'] = f'<mailto:{unsubscribe_email}>'
            msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Attach signature image as CID (same as campaigns)
            from email.mime.image import MIMEImage
            from pathlib import Path
            
            signature_filename = f"{alias.capitalize()} Handtekening.png"
            signature_path = Path(__file__).parent.parent / "assets" / "signatures" / signature_filename
            
            if signature_path.exists():
                with open(signature_path, 'rb') as img_file:
                    img_data = img_file.read()
                    image = MIMEImage(img_data)
                    image.add_header('Content-ID', f'<signature_{alias}>')
                    image.add_header('Content-Disposition', 'inline', filename=signature_filename)
                    msg.attach(image)
                    logger.debug(f"Attached {alias} signature image as CID for test email")
            else:
                logger.warning(f"Signature image not found: {signature_path}")
            
            # Determine if we should use real SMTP or simulation
            use_real_smtp = bool(smtp_host and smtp_user and smtp_pass)
            
            if use_real_smtp:
                logger.info(f"📧 Attempting real SMTP send to {to_email} via {smtp_host}")
                success = await self._real_smtp_send(msg, {
                    'host': smtp_host,
                    'port': smtp_port,
                    'username': smtp_user,
                    'password': smtp_pass,
                    'use_tls': True
                })
            else:
                logger.warning(f"⚠️  No SMTP config found, using simulation mode for {to_email}")
                success = await self._simulate_smtp_send(msg, to_email)
            
            if success:
                self.record_send(user_id)
                logger.info(f"✅ mail_send_ok: Test email sent to {to_email} from {mail_from}")
                return {'success': True, 'message': 'Test email sent successfully'}
            else:
                logger.error(f"❌ mail_send_err: SMTP delivery failed to {to_email}")
                return {'success': False, 'error': 'SMTP delivery failed'}
                
        except Exception as e:
            logger.error(f"❌ mail_send_err: Exception sending to {to_email}: {str(e)}")
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
        """
        Real SMTP sending with detailed logging.
        
        Logs each step of the SMTP process for debugging.
        """
        try:
            logger.info(f"🔌 Connecting to SMTP: {smtp_config['host']}:{smtp_config['port']}")
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'], timeout=30)
            
            if smtp_config.get('use_tls'):
                logger.info("🔒 Starting TLS encryption...")
                server.starttls()
            
            if smtp_config.get('username'):
                logger.info(f"🔑 Authenticating as {smtp_config['username']}")
                server.login(smtp_config['username'], smtp_config['password'])
            
            logger.info(f"📧 Sending message to {msg['To']}")
            server.send_message(msg)
            
            logger.info("✅ SMTP send successful, closing connection")
            server.quit()
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed: {str(e)}")
            logger.error(f"   Check SMTP_USER and SMTP_PASS environment variables")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error during SMTP send: {type(e).__name__}: {str(e)}")
            return False


# Global instance
testsend_service = TestsendService()
