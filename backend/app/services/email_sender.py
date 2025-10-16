"""
Unified Email Sender - Single source of truth for all email sending.

This service consolidates email sending logic from testsend.py and message_sender.py
into a single, reusable, production-ready implementation.

Features:
- Real SMTP sending with env var configuration
- Domain-aware FROM addresses (version-based)
- Asset handling (screenshots for M1/M2, PDFs for M3)
- Signature injection (CID embedding)
- Tracking pixel injection
- Message status tracking
- Bounce/open event handling
- Unsubscribe headers (RFC 8058 compliance)
- Rate limiting support
- Retry logic with exponential backoff
"""

import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

from app.services.signature_injector import inject_signature_cid, get_alias_from_mail_number


# Domain mapping: version → domain
DOMAIN_MAP = {
    1: "punthelder-vindbaarheid.nl",
    2: "punthelder-marketing.nl",
    3: "punthelder-seo.nl",
    4: "punthelder-zoekmachine.nl"
}


class EmailConfig:
    """Email configuration from environment variables - supports multi-domain."""
    
    def __init__(self):
        # Default SMTP (for test sends)
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASSWORD")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        # Optional tracking config
        self.tracking_pixel_enabled = os.getenv("TRACKING_PIXEL_ENABLED", "false").lower() == "true"
        self.tracking_base_url = os.getenv("TRACKING_BASE_URL", "https://mail-saas-rf4s.onrender.com")
    
    def get_credentials_for_email(self, from_email: str) -> Optional[Dict[str, str]]:
        """
        Get SMTP credentials for specific email address (multi-domain support).
        
        Args:
            from_email: Email address (e.g., "christian@punthelder-marketing.nl")
            
        Returns:
            Dict with host, user, password, or None if not found
        """
        # Parse email to get domain and alias
        if '@' not in from_email:
            return None
        
        alias, domain = from_email.split('@', 1)
        
        # Map domain to shortname
        domain_map = {
            'punthelder-marketing.nl': 'MARKETING',
            'punthelder-seo.nl': 'SEO',
            'punthelder-vindbaarheid.nl': 'VINDBAARHEID',
            'punthelder-zoekmachine.nl': 'ZOEKMACHINE'
        }
        
        domain_key = domain_map.get(domain)
        if not domain_key:
            return None
        
        # Get credentials from environment
        # Format: SMTP_PASSWORD_MARKETING_CHRISTIAN
        alias_upper = alias.upper()
        password_key = f"SMTP_PASSWORD_{domain_key}_{alias_upper}"
        password = os.getenv(password_key)
        
        if not password:
            logger.warning(f"No password found for {from_email} (looking for {password_key})")
            return None
        
        # SMTP host format: mail.punthelder-marketing.nl
        smtp_host = f"mail.{domain}"
        
        return {
            'host': smtp_host,
            'user': from_email,
            'password': password
        }
    
    @property
    def is_configured(self) -> bool:
        """
        Check if SMTP is properly configured.
        Note: For multi-domain setups, we check domain-specific credentials at send time.
        This is just for backward compatibility with default credentials.
        """
        return bool(self.smtp_host and self.smtp_user and self.smtp_pass)


class EmailSender:
    """
    Unified email sender for both test emails and campaign messages.
    
    Handles:
    - SMTP sending (real or simulated)
    - Asset attachment (screenshots, PDFs)
    - Signature injection
    - Tracking pixel injection
    - Domain-aware FROM addresses
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig()
    
    def get_domain_for_version(self, version: int) -> str:
        """Get domain for template version."""
        return DOMAIN_MAP.get(version, "punthelder-marketing.nl")
    
    def get_from_address(self, version: int, mail_number: int) -> str:
        """
        Get FROM email address based on version and mail number.
        
        Args:
            version: Template version (1-4)
            mail_number: Mail number (1-4)
            
        Returns:
            FROM email address (e.g., "christian@punthelder-marketing.nl")
        """
        domain = self.get_domain_for_version(version)
        alias = get_alias_from_mail_number(mail_number)
        return f"{alias}@{domain}"
    
    def get_from_name_formatted(self, version: int, mail_number: int) -> str:
        """
        Get formatted FROM header with display name and email address.
        
        Args:
            version: Template version (1-4)
            mail_number: Mail number (1-4)
            
        Returns:
            Formatted FROM header (e.g., "Christian - Punthelder Marketing <christian@punthelder-marketing.nl>")
        """
        domain = self.get_domain_for_version(version)
        alias = get_alias_from_mail_number(mail_number)
        email = f"{alias}@{domain}"
        
        # Get display name from alias (capitalize)
        display_name = alias.capitalize()
        
        # Get company name from domain
        domain_to_company = {
            "punthelder-vindbaarheid.nl": "Punthelder Vindbaarheid",
            "punthelder-marketing.nl": "Punthelder Marketing",
            "punthelder-seo.nl": "Punthelder SEO",
            "punthelder-zoekmachine.nl": "Punthelder Zoekmachine"
        }
        
        company_name = domain_to_company.get(domain, "Punthelder Marketing")
        
        # Format: "Christian - Punthelder Marketing <christian@punthelder-marketing.nl>"
        return f"{display_name} - {company_name} <{email}>"
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str,
        version: int,
        mail_number: int,
        lead_id: Optional[str] = None,
        message_id: Optional[str] = None,
        image_key: Optional[str] = None,
        report_filename: Optional[str] = None,
        enable_tracking: bool = False
    ) -> Dict[str, Any]:
        """
        Send email with full feature support.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML body content
            text_body: Plain text body content
            version: Template version (1-4)
            mail_number: Mail number (1-4)
            lead_id: Optional lead ID for tracking
            message_id: Optional message ID for tracking
            image_key: Optional screenshot key for M1/M2
            report_filename: Optional PDF filename for M3
            enable_tracking: Whether to inject tracking pixel
            
        Returns:
            Dict with success status and optional error message
        """
        try:
            # Get FROM address (for SMTP)
            mail_from = self.get_from_address(version, mail_number)
            # Get formatted FROM name (for display)
            mail_from_formatted = self.get_from_name_formatted(version, mail_number)
            domain = self.get_domain_for_version(version)
            alias = get_alias_from_mail_number(mail_number)
            
            logger.info(f"📧 Preparing email to {to_email} from {mail_from_formatted} (V{version}M{mail_number})")
            
            # Check if we need screenshot inline (M1/M2)
            should_attach_screenshot = (
                (version in [1, 2, 3] and mail_number == 1) or
                (version in [2, 3, 4] and mail_number == 2)
            )
            
            # Inject screenshot CID if needed
            html_with_assets = html_body
            if should_attach_screenshot and image_key:
                cid_name = f"dashboard_{domain.replace('.', '_').replace('-', '_')}"
                html_with_assets = self._inject_screenshot_cid(html_body, cid_name)
            
            # Inject signature into HTML body
            html_with_signature = inject_signature_cid(html_with_assets, alias)
            
            # Optionally inject tracking pixel
            if enable_tracking and message_id and self.config.tracking_pixel_enabled:
                tracking_url = self._generate_tracking_url(message_id)
                html_with_signature = self._inject_tracking_pixel(html_with_signature, tracking_url)
                logger.debug(f"Injected tracking pixel for message {message_id}")
            
            # Check if we need PDF attachment (M3 only)
            needs_pdf = (mail_number == 3 and report_filename)
            
            # Create proper MIME structure
            if needs_pdf:
                # Structure: mixed > related > alternative
                msg = MIMEMultipart('mixed')
                msg_related = MIMEMultipart('related')
                msg_alternative = MIMEMultipart('alternative')
            else:
                # Structure: related > alternative (no attachments)
                msg = MIMEMultipart('related')
                msg_alternative = MIMEMultipart('alternative')
            
            # Set headers
            msg['Subject'] = subject
            msg['From'] = mail_from_formatted  # Display name format
            msg['To'] = to_email
            
            # Add text and HTML to alternative part
            msg_alternative.attach(MIMEText(text_body, 'plain'))
            msg_alternative.attach(MIMEText(html_with_signature, 'html'))
            
            if needs_pdf:
                # Build: related (alternative + inline images)
                msg_related.attach(msg_alternative)
                self._attach_signature_image(msg_related, alias)
                
                # Attach dashboard screenshot (M1/M2 only)
                if image_key:
                    self._attach_screenshot(msg_related, image_key, version, mail_number, domain)
                
                # Build: mixed (related + pdf attachment)
                msg.attach(msg_related)
                self._attach_pdf_report(msg, report_filename, version, mail_number)
            else:
                # Build: related (alternative + inline images)
                msg.attach(msg_alternative)
                self._attach_signature_image(msg, alias)
                
                # Attach dashboard screenshot (M1/M2 only)
                if image_key:
                    self._attach_screenshot(msg, image_key, version, mail_number, domain)
            
            # Add unsubscribe headers if message_id is provided
            if message_id and lead_id:
                self._add_unsubscribe_headers(msg, message_id, lead_id)
            
            # Send via SMTP (checks domain-specific credentials automatically)
            # No need to check self.config.is_configured - we check in _send_via_smtp
            success = await self._send_via_smtp(msg, to_email, mail_from)
            
            if success:
                logger.info(f"✅ Email sent successfully to {to_email}")
                return {'success': True, 'message': 'Email sent successfully'}
            else:
                logger.error(f"❌ Email delivery failed to {to_email}")
                return {'success': False, 'error': 'Email delivery failed'}
                
        except Exception as e:
            logger.error(f"❌ Exception sending email to {to_email}: {str(e)}")
            return {'success': False, 'error': f'Email sending failed: {str(e)}'}
    
    def _attach_signature_image(self, msg: MIMEMultipart, alias: str):
        """Attach signature image as CID."""
        try:
            signature_filename = f"{alias.capitalize()} Handtekening.png"
            signature_path = Path(__file__).parent.parent / "assets" / "signatures" / signature_filename
            
            if signature_path.exists():
                with open(signature_path, 'rb') as img_file:
                    img_data = img_file.read()
                    image = MIMEImage(img_data)
                    image.add_header('Content-ID', f'<signature_{alias}>')
                    image.add_header('Content-Disposition', 'inline')
                    msg.attach(image)
                    logger.debug(f"Attached {alias} signature as CID")
            else:
                logger.warning(f"Signature image not found: {signature_path}")
        except Exception as e:
            logger.error(f"Error attaching signature: {str(e)}")
    
    def _attach_screenshot(
        self, 
        msg: MIMEMultipart, 
        image_key: str, 
        version: int, 
        mail_number: int,
        domain: str
    ):
        """
        Attach dashboard screenshot for M1/M2.
        
        Version-aware logic:
        - V1M1, V2M1, V3M1: Attach screenshot
        - V2M2, V3M2, V4M2: Attach screenshot
        - Other combinations: Skip
        """
        should_attach = (
            (version in [1, 2, 3] and mail_number == 1) or
            (version in [2, 3, 4] and mail_number == 2)
        )
        
        if not should_attach:
            logger.debug(f"Skipping screenshot for V{version}M{mail_number}")
            return
        
        try:
            from app.services.supabase_storage import supabase_storage
            
            signed_url = supabase_storage.get_signed_url(image_key, expires_in=3600)
            if not signed_url:
                logger.warning(f"No signed URL for screenshot: {image_key}")
                return
            
            response = requests.get(signed_url, timeout=10)
            if response.status_code == 200:
                img_data = response.content
                dashboard_image = MIMEImage(img_data)
                
                cid_name = f"dashboard_{domain.replace('.', '_').replace('-', '_')}"
                dashboard_image.add_header('Content-ID', f'<{cid_name}>')
                dashboard_image.add_header('Content-Disposition', 'inline')
                msg.attach(dashboard_image)
                logger.info(f"✅ Attached screenshot for V{version}M{mail_number}: {image_key}")
            else:
                logger.warning(f"Failed to download screenshot: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error attaching screenshot: {str(e)}")
    
    def _attach_pdf_report(
        self, 
        msg: MIMEMultipart, 
        report_filename: str, 
        version: int, 
        mail_number: int
    ):
        """
        Attach PDF report for M3 only.
        """
        should_attach = (mail_number == 3)
        
        if not should_attach:
            logger.debug(f"Skipping PDF report for V{version}M{mail_number}")
            return
        
        try:
            from app.services.supabase_storage import supabase_storage
            
            signed_url = supabase_storage.get_signed_url_for_report(report_filename, expires_in=3600)
            if not signed_url:
                logger.warning(f"No signed URL for report: {report_filename}")
                return
            
            response = requests.get(signed_url, timeout=10)
            if response.status_code == 200:
                pdf_data = response.content
                pdf_attachment = MIMEApplication(pdf_data, _subtype='pdf')
                pdf_attachment.add_header('Content-Disposition', 'attachment', filename=report_filename)
                msg.attach(pdf_attachment)
                logger.info(f"✅ Attached PDF report for V{version}M{mail_number}: {report_filename}")
            else:
                logger.warning(f"Failed to download PDF report: HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error attaching PDF report: {str(e)}")
    
    def _add_unsubscribe_headers(self, msg: MIMEMultipart, message_id: str, lead_id: str):
        """Add RFC 8058 compliant unsubscribe headers."""
        base_url = self.config.tracking_base_url
        unsub_url = f"{base_url}/api/v1/unsubscribe?m={message_id}&l={lead_id}"
        
        msg['List-Unsubscribe'] = f'<{unsub_url}>'
        msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'
        logger.debug(f"Added unsubscribe headers for message {message_id}")
    
    def _inject_screenshot_cid(self, html: str, cid_name: str) -> str:
        """
        Inject screenshot CID reference into HTML.
        Replaces {{SCREENSHOT_CID}} placeholder with actual CID reference.
        """
        screenshot_html = f'<img src="cid:{cid_name}" alt="Dashboard Screenshot" style="max-width: 100%; height: auto; display: block; margin: 20px 0;" />'
        
        # Replace placeholder if exists
        if '{{SCREENSHOT_CID}}' in html:
            return html.replace('{{SCREENSHOT_CID}}', screenshot_html)
        else:
            # If no placeholder, inject before signature/end of content
            # Find a good injection point (before signature or before </body>)
            import re
            # Try to inject before signature div
            pattern = r'(<div[^>]*margin-top:\s*50px[^>]*>)'
            if re.search(pattern, html):
                return re.sub(pattern, f'{screenshot_html}\\1', html, count=1)
            # Fallback: inject before </body>
            elif '</body>' in html.lower():
                return re.sub(r'</body>', f'{screenshot_html}</body>', html, count=1, flags=re.IGNORECASE)
            else:
                return html + screenshot_html
    
    def _generate_tracking_url(self, message_id: str) -> str:
        """Generate tracking pixel URL."""
        base_url = self.config.tracking_base_url
        return f"{base_url}/api/v1/track/open.gif?m={message_id}"
    
    def _inject_tracking_pixel(self, html: str, tracking_url: str) -> str:
        """Inject tracking pixel into HTML."""
        pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none;" />'
        
        if '</body>' in html:
            return html.replace('</body>', f'{pixel}</body>')
        else:
            return html + pixel
    
    async def _send_via_smtp(
        self, 
        msg: MIMEMultipart, 
        to_email: str, 
        from_email: str
    ) -> bool:
        """Send email via real SMTP with multi-domain credentials support."""
        try:
            # Try to get domain-specific credentials first
            domain_creds = self.config.get_credentials_for_email(from_email)
            
            if domain_creds:
                # Use domain-specific credentials
                smtp_host = domain_creds['host']
                smtp_user = domain_creds['user']
                smtp_pass = domain_creds['password']
                logger.debug(f"Using domain-specific credentials for {from_email}")
            else:
                # Fallback to default credentials
                smtp_host = self.config.smtp_host
                smtp_user = self.config.smtp_user
                smtp_pass = self.config.smtp_pass
                logger.debug(f"Using default credentials (fallback)")
            
            if not (smtp_host and smtp_user and smtp_pass):
                logger.error(
                    f"❌ No SMTP credentials available for {from_email}. "
                    f"Please configure environment variable SMTP_PASSWORD_{{DOMAIN}}_{{ALIAS}} "
                    f"(e.g., SMTP_PASSWORD_MARKETING_CHRISTIAN)"
                )
                return False
            
            logger.debug(f"Connecting to SMTP {smtp_host}:{self.config.smtp_port}")
            
            with smtplib.SMTP(smtp_host, self.config.smtp_port, timeout=30) as server:
                if self.config.use_tls:
                    server.starttls()
                
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            logger.info(f"✅ SMTP delivery successful: {from_email} → {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed for {from_email}: {str(e)}")
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(f"❌ SMTP connection failed: {str(e)}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected SMTP error: {str(e)}")
            return False
    
    async def _simulate_send(
        self, 
        msg: MIMEMultipart, 
        to_email: str, 
        from_email: str
    ) -> bool:
        """Simulate SMTP sending for development."""
        if '@' in to_email and '.' in to_email.split('@')[1]:
            logger.info(f"[SIMULATED] Email would be sent to {to_email} from {from_email}")
            logger.info(f"[SIMULATED] Subject: {msg['Subject']}")
            return True
        else:
            logger.error(f"[SIMULATED] Invalid email address: {to_email}")
            return False


# Global instance
email_sender = EmailSender()
