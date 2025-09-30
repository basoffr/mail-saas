"""
Unit tests for production SMTP sending.
Tests _send_via_smtp method with mocked SMTP server.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import smtplib
import asyncio

from app.models.campaign import Message, MessageStatus, Campaign
from app.models.lead import Lead, LeadStatus
from app.services.message_sender import MessageSender
from app.services.campaign_store import campaign_store
from app.services.template_store import template_store


class TestSMTPSending:
    """Test production SMTP sending functionality."""
    
    def setup_method(self):
        """Clear stores."""
        campaign_store.campaigns.clear()
        campaign_store.messages.clear()
        template_store.templates.clear()
        self.sender = MessageSender()
    
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@example.com',
        'SMTP_PASSWORD': 'testpass123'
    })
    def test_smtp_send_success(self, mock_smtp_class):
        """Test successful SMTP email sending."""
        # Setup mock SMTP server
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        # Create test template
        from app.schemas.template import TemplateCreate
        template = TemplateCreate(
            name="Test Template",
            subject="Test Subject",
            body_html="<html><body>Hello {{company}}</body></html>"
        )
        template_store.create(template)
        template_id = list(template_store.templates.keys())[0]
        
        # Create campaign
        campaign = Campaign(
            id="camp-smtp-1",
            name="Test Campaign",
            template_id=template_id,
            domain="punthelder-marketing.nl",
            status="draft"
        )
        campaign_store.campaigns[campaign.id] = campaign
        
        # Create message
        message = Message(
            id="msg-smtp-1",
            campaign_id=campaign.id,
            lead_id="lead-1",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.queued
        )
        
        # Create lead
        lead = Lead(
            id="lead-1",
            email="recipient@example.com",
            company="Test Co",
            status=LeadStatus.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Render template content
        template_content = "<html><body>Hello Test Co</body></html>"
        
        # Send via SMTP
        result = asyncio.run(self.sender._send_via_smtp(message, lead, template_content))
        
        # Verify success
        assert result is True
        
        # Verify SMTP methods were called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@example.com', 'testpass123')
        mock_server.send_message.assert_called_once()
        
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@example.com',
        'SMTP_PASSWORD': 'wrongpass'
    })
    def test_smtp_authentication_failure(self, mock_smtp_class):
        """Test SMTP authentication failure."""
        # Setup mock to raise auth error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, 'Authentication failed')
        mock_smtp_class.return_value.__enter__.return_value = mock_server
        
        # Create template
        from app.schemas.template import TemplateCreate
        template = TemplateCreate(
            name="Test Template",
            subject="Test Subject",
            body_html="<html><body>Test</body></html>"
        )
        template_store.create(template)
        template_id = list(template_store.templates.keys())[0]
        
        # Create campaign
        campaign = Campaign(
            id="camp-smtp-2",
            name="Test Campaign",
            template_id=template_id,
            domain="punthelder-marketing.nl",
            status="draft"
        )
        campaign_store.campaigns[campaign.id] = campaign
        
        # Create message and lead
        message = Message(
            id="msg-smtp-2",
            campaign_id=campaign.id,
            lead_id="lead-2",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.queued
        )
        
        lead = Lead(
            id="lead-2",
            email="test@example.com",
            company="Test",
            status=LeadStatus.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Try to send
        result = asyncio.run(self.sender._send_via_smtp(message, lead, "<html>Test</html>"))
        
        # Should fail
        assert result is False
        
    @patch.dict('os.environ', {}, clear=True)
    def test_smtp_missing_credentials(self):
        """Test SMTP with missing credentials."""
        # Create minimal setup
        from app.schemas.template import TemplateCreate
        template = TemplateCreate(
            name="Test",
            subject="Test",
            body_html="<html>Test</html>"
        )
        template_store.create(template)
        template_id = list(template_store.templates.keys())[0]
        
        campaign = Campaign(
            id="camp-smtp-3",
            name="Test",
            template_id=template_id,
            domain="punthelder-marketing.nl",
            status="draft"
        )
        campaign_store.campaigns[campaign.id] = campaign
        
        message = Message(
            id="msg-smtp-3",
            campaign_id=campaign.id,
            lead_id="lead-3",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.queued
        )
        
        lead = Lead(
            id="lead-3",
            email="test@example.com",
            company="Test",
            status=LeadStatus.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Try to send without credentials
        result = asyncio.run(self.sender._send_via_smtp(message, lead, "<html>Test</html>"))
        
        # Should fail gracefully
        assert result is False
        
    @patch('smtplib.SMTP')
    @patch.dict('os.environ', {
        'SMTP_HOST': 'smtp.test.com',
        'SMTP_PORT': '587',
        'SMTP_USER': 'test@example.com',
        'SMTP_PASSWORD': 'testpass'
    })
    def test_smtp_connection_failure(self, mock_smtp_class):
        """Test SMTP connection failure."""
        # Mock connection error
        mock_smtp_class.side_effect = smtplib.SMTPConnectError(421, 'Service not available')
        
        # Create minimal setup
        from app.schemas.template import TemplateCreate
        template = TemplateCreate(
            name="Test",
            subject="Test",
            body_html="<html>Test</html>"
        )
        template_store.create(template)
        template_id = list(template_store.templates.keys())[0]
        
        campaign = Campaign(
            id="camp-smtp-4",
            name="Test",
            template_id=template_id,
            domain="punthelder-marketing.nl",
            status="draft"
        )
        campaign_store.campaigns[campaign.id] = campaign
        
        message = Message(
            id="msg-smtp-4",
            campaign_id=campaign.id,
            lead_id="lead-4",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.queued
        )
        
        lead = Lead(
            id="lead-4",
            email="test@example.com",
            company="Test",
            status=LeadStatus.active,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Try to send
        result = asyncio.run(self.sender._send_via_smtp(message, lead, "<html>Test</html>"))
        
        # Should fail
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
