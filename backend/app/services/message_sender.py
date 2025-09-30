import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from app.models.campaign import Message, MessageStatus, MessageEvent, MessageEventType
from app.models.lead import Lead, LeadStatus


class MessageSender:
    """
    Handles email sending with SMTP simulation, bounce detection,
    and unsubscribe header compliance.
    """
    
    def __init__(self):
        # SMTP simulation for MVP
        self.smtp_enabled = False
        self.bounce_rate = 0.05  # 5% simulated bounce rate
        self.delivery_success_rate = 0.95
    
    async def send_message(self, message: Message, lead: Lead, template_content: str) -> bool:
        """
        Send a single message with bounce detection and status updates.
        Returns True if sent successfully, False if failed.
        """
        
        try:
            # Check if lead is suppressed
            if lead.status in [LeadStatus.suppressed, LeadStatus.bounced]:
                logger.warning(f"Skipping message {message.id} - lead {lead.id} is {lead.status}")
                await self._update_message_status(message, MessageStatus.canceled, "Lead is suppressed")
                return False
            
            # Simulate SMTP sending
            if self.smtp_enabled:
                success = await self._send_via_smtp(message, lead, template_content)
            else:
                success = await self._simulate_send(message, lead)
            
            if success:
                # Mark as sent
                await self._update_message_status(message, MessageStatus.sent)
                await self._create_event(message, MessageEventType.sent)
                
                # Update lead last emailed timestamp
                lead.last_emailed_at = datetime.utcnow()
                
                logger.info(f"Message {message.id} sent successfully to {lead.email}")
                return True
            else:
                # Handle failure
                await self._handle_send_failure(message, lead)
                return False
                
        except Exception as e:
            logger.error(f"Error sending message {message.id}: {str(e)}")
            await self._update_message_status(message, MessageStatus.failed, str(e))
            return False
    
    async def handle_bounce(self, message: Message, lead: Lead, bounce_reason: str) -> None:
        """Handle bounced email - update message and lead status."""
        
        # Update message status
        await self._update_message_status(message, MessageStatus.bounced, bounce_reason)
        await self._create_event(message, MessageEventType.bounced, {"reason": bounce_reason})
        
        # Update lead status to bounced (suppress future emails)
        lead.status = LeadStatus.bounced
        
        logger.warning(f"Message {message.id} bounced: {bounce_reason}")
    
    async def handle_open(self, message: Message, user_agent: str = None, ip_address: str = None) -> None:
        """Handle email open event."""
        
        # Update message open timestamp
        message.open_at = datetime.utcnow()
        if message.status == MessageStatus.sent:
            message.status = MessageStatus.opened
        
        # Create open event
        await self._create_event(
            message, 
            MessageEventType.opened,
            {"user_agent": user_agent, "ip_address": ip_address}
        )
        
        # Update lead last open timestamp
        # Note: Would need lead reference here in production
        
        logger.info(f"Message {message.id} opened")
    
    async def retry_failed_message(self, message: Message, lead: Lead, template_content: str) -> bool:
        """Retry a failed message with exponential backoff."""
        
        if message.status != MessageStatus.failed:
            raise ValueError("Can only retry failed messages")
        
        if message.retry_count >= 2:  # Max 2 retries as per superprompt
            logger.warning(f"Message {message.id} exceeded max retries")
            return False
        
        # Increment retry count
        message.retry_count += 1
        
        # Reset status to queued for retry
        message.status = MessageStatus.queued
        
        # Attempt send again
        return await self.send_message(message, lead, template_content)
    
    def generate_unsubscribe_headers(self, message: Message, lead: Lead) -> Dict[str, str]:
        """Generate List-Unsubscribe headers for RFC 8058 compliance."""
        import os
        base_url = os.getenv('API_BASE_URL', 'https://mail-saas-rf4s.onrender.com')
        token = self._generate_token(message.id)
        
        unsubscribe_url = f"{base_url}/api/v1/unsubscribe?m={message.id}&t={token}"
        unsubscribe_mailto = f"unsubscribe-{message.id}@mail-saas-rf4s.onrender.com"
        
        return {
            "List-Unsubscribe": f"<{unsubscribe_url}>, <mailto:{unsubscribe_mailto}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
        }
    
    def generate_tracking_pixel_url(self, message: Message) -> str:
        """Generate tracking pixel URL for open tracking."""
        import os
        base_url = os.getenv('API_BASE_URL', 'https://mail-saas-rf4s.onrender.com')
        token = self._generate_token(message.id)
        return f"{base_url}/api/v1/track/open.gif?m={message.id}&t={token}"
    
    async def _send_via_smtp(self, message: Message, lead: Lead, template_content: str) -> bool:
        """Send email via actual SMTP (production implementation)."""
        import smtplib
        import os
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.utils import formataddr
        
        # Check if tracking pixel should be added
        from app.services.settings import settings_service
        from app.services.template_renderer import inject_tracking_pixel
        
        settings = settings_service.get_settings()
        
        if settings.tracking_pixel_enabled:
            pixel_url = self.generate_tracking_pixel_url(message)
            template_content = inject_tracking_pixel(template_content, pixel_url)
            logger.debug(f"Injected tracking pixel for message {message.id}")
        
        # Get unsubscribe headers
        unsub_headers = self.generate_unsubscribe_headers(message, lead)
        
        # Get SMTP credentials from environment
        smtp_host = os.getenv("SMTP_HOST", "smtp.vimexx.nl")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        if not smtp_user or not smtp_password:
            logger.error("SMTP credentials not configured in environment")
            return False
        
        # Get campaign to determine template subject
        campaign = campaign_store.get_campaign(message.campaign_id)
        if not campaign:
            logger.error(f"Campaign {message.campaign_id} not found for message {message.id}")
            return False
        
        # Get template for subject
        from app.services.template_store import template_store
        template = template_store.get(campaign.template_id)
        if not template:
            logger.error(f"Template {campaign.template_id} not found")
            return False
        
        # Determine From address based on domain
        from_name = "Christian"
        from_email = f"christian@{message.domain_used}"
        reply_to = from_email
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = formataddr((from_name, from_email))
            msg['To'] = lead.email
            msg['Subject'] = template.subject
            msg['Reply-To'] = reply_to
            
            # Add unsubscribe headers
            for key, value in unsub_headers.items():
                msg[key] = value
            
            # Add HTML body
            html_part = MIMEText(template_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Connect to SMTP server
            logger.debug(f"Connecting to SMTP server {smtp_host}:{smtp_port}")
            
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                # Start TLS
                server.starttls()
                
                # Login
                logger.debug(f"Authenticating as {smtp_user}")
                server.login(smtp_user, smtp_password)
                
                # Send email
                server.send_message(msg)
                
            logger.info(f"Successfully sent email via SMTP for message {message.id} to {lead.email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed for message {message.id}: {str(e)}")
            return False
            
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed for message {message.id}: {str(e)}")
            return False
            
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending message {message.id}: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending message {message.id} via SMTP: {str(e)}")
            return False
    
    async def _simulate_send(self, message: Message, lead: Lead) -> bool:
        """Simulate email sending for MVP."""
        import random
        
        # Simulate delivery success/failure
        if random.random() < self.delivery_success_rate:
            return True
        else:
            # Simulate different failure types
            failure_types = ["temporary_failure", "bounce", "smtp_error"]
            failure_type = random.choice(failure_types)
            
            if failure_type == "bounce":
                await self.handle_bounce(message, lead, "Simulated bounce")
            
            return False
    
    async def _update_message_status(
        self, 
        message: Message, 
        status: MessageStatus, 
        error: str = None
    ) -> None:
        """Update message status and timestamps."""
        
        message.status = status
        
        if status == MessageStatus.sent:
            message.sent_at = datetime.utcnow()
        elif status in [MessageStatus.failed, MessageStatus.bounced]:
            message.last_error = error
        
        # In production: save to database
        logger.debug(f"Updated message {message.id} status to {status}")
    
    async def _create_event(
        self, 
        message: Message, 
        event_type: MessageEventType,
        meta: Dict[str, Any] = None
    ) -> MessageEvent:
        """Create a message event record."""
        
        event = MessageEvent(
            id=str(uuid.uuid4()),
            message_id=message.id,
            event_type=event_type,
            meta=meta or {}
        )
        
        # In production: save to database
        logger.debug(f"Created {event_type} event for message {message.id}")
        return event
    
    async def _handle_send_failure(self, message: Message, lead: Lead) -> None:
        """Handle various types of send failures."""
        
        # Determine if this is a temporary or permanent failure
        # For simulation, treat as temporary failure that can be retried
        error_message = "Simulated send failure"
        
        await self._update_message_status(message, MessageStatus.failed, error_message)
        await self._create_event(message, MessageEventType.failed, {"error": error_message})
    
    def _generate_token(self, message_id: str) -> str:
        """Generate secure token for tracking/unsubscribe links."""
        # In production: use proper cryptographic signing
        import hashlib
        return hashlib.md5(f"{message_id}_secret_key".encode()).hexdigest()[:16]
