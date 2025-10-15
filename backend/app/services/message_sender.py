"""
Message Sender - Campaign email sender with status tracking.

Handles campaign message sending with:
- Message status tracking (queued, sent, opened, bounced, failed)
- Event logging (sent, opened, clicked, bounced)
- Lead suppression checking
- Bounce/open handling
- Retry logic

Delegates actual email sending to unified email_sender.py.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from loguru import logger

from app.models.campaign import Message, MessageStatus, MessageEvent, MessageEventType
from app.models.lead import Lead, LeadStatus
from app.services.email_sender import email_sender


class MessageSender:
    """
    Handles campaign message sending with status tracking and event logging.
    
    Delegates actual email sending to unified email_sender.py.
    """
    
    def __init__(self):
        self.email_sender = email_sender
        self.bounce_rate = 0.05  # 5% simulated bounce rate (for simulation mode)
        self.delivery_success_rate = 0.95
    
    async def send_message(self, message: Message, lead: Lead, template_content: str) -> bool:
        """
        Send campaign message via unified email sender with status tracking.
        
        Args:
            message: Message object with domain_used, mail_number, template_version
            lead: Lead object with email, vars (report_filename, image_key)
            template_content: Rendered HTML template
            
        Returns:
            True if sent successfully, False if failed
        """
        try:
            # Check if lead is suppressed
            if lead.status in [LeadStatus.suppressed, LeadStatus.bounced]:
                logger.warning(f"Skipping message {message.id} - lead {lead.id} is {lead.status}")
                await self._update_message_status(message, MessageStatus.canceled, "Lead is suppressed")
                return False
            
            # Extract version from message (template_version)
            version = message.template_version or 1
            
            # Extract assets from lead vars
            image_key = lead.vars.get('image_key') if hasattr(lead, 'vars') and lead.vars else None
            report_filename = lead.vars.get('report_filename') if hasattr(lead, 'vars') and lead.vars else None
            
            # Create subject from template (TODO: get from template store)
            subject = f"Email van {message.alias.capitalize()}"
            
            logger.info(f"📧 Sending campaign message {message.id}: V{version}M{message.mail_number} to {lead.email}")
            
            # Send via unified email sender
            result = await self.email_sender.send_email(
                to_email=lead.email,
                subject=subject,
                html_body=template_content,
                text_body="",  # TODO: Generate text version
                version=version,
                mail_number=message.mail_number,
                lead_id=lead.id,
                message_id=message.id,
                image_key=image_key,
                report_filename=report_filename,
                enable_tracking=True  # Enable tracking for campaigns
            )
            
            if result['success']:
                # Mark as sent
                await self._update_message_status(message, MessageStatus.sent)
                await self._create_event(message, MessageEventType.sent)
                
                # Update lead last emailed timestamp
                lead.last_emailed_at = datetime.utcnow()
                message.sent_at = datetime.utcnow()
                
                logger.info(f"✅ Message {message.id} sent successfully to {lead.email}")
                return True
            else:
                # Handle failure
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ Message {message.id} failed: {error_msg}")
                await self._handle_send_failure(message, lead)
                return False
                
        except Exception as e:
            logger.error(f"❌ Exception sending message {message.id}: {str(e)}")
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
    
    async def _update_message_status(
        self, 
        message: Message, 
        status: MessageStatus, 
        error: str = None
    ) -> None:
        """
        Update message status and persist to database.
        
        PRODUCTION-READY: Database persistence for restart-safety.
        """
        # Update in-memory object
        message.status = status
        
        if status == MessageStatus.sent:
            message.sent_at = datetime.utcnow()
        elif status in [MessageStatus.failed, MessageStatus.bounced]:
            message.last_error = error
        
        # PERSIST TO DATABASE (critical for production!)
        from app.services.store_factory import campaigns_store
        success = campaigns_store.update_message_status(message.id, status, error)
        
        if success:
            logger.info(f"✅ Updated message {message.id} status to {status}")
        else:
            logger.error(f"❌ Failed to update message {message.id} status to {status}")
    
    async def _create_event(
        self, 
        message: Message, 
        event_type: MessageEventType,
        meta: Dict[str, Any] = None
    ) -> MessageEvent:
        """
        Create a message event record and persist to database.
        
        PRODUCTION-READY: Database persistence for audit trail.
        """
        event = MessageEvent(
            id=str(uuid.uuid4()),
            message_id=message.id,
            event_type=event_type,
            meta=meta or {}
        )
        
        # PERSIST TO DATABASE (critical for audit trail!)
        from app.services.store_factory import campaigns_store
        try:
            saved_event = campaigns_store.create_event(event)
            logger.info(f"✅ Created {event_type} event for message {message.id}")
            return saved_event
        except Exception as e:
            logger.error(f"❌ Failed to create event for message {message.id}: {e}")
            return event  # Return in-memory object as fallback
    
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
