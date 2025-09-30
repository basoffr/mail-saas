"""
Unit tests for unsubscribe endpoint.
Tests /track/unsubscribe endpoint functionality.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.campaign import Message, MessageStatus
from app.models.lead import Lead, LeadStatus
from app.services.campaign_store import campaign_store
from app.services.leads_store import leads_store
from app.services.message_sender import MessageSender


class TestUnsubscribeEndpoint:
    """Test /track/unsubscribe endpoint."""
    
    def setup_method(self):
        """Clear stores and create test client."""
        campaign_store.messages.clear()
        campaign_store.events.clear()
        leads_store._leads.clear()  # Clear internal list
        self.client = TestClient(app)
        self.sender = MessageSender()
    
    def test_unsubscribe_success(self):
        """Test successful unsubscribe."""
        # Create test lead via upsert
        _, lead_rec = leads_store.upsert(
            email="test@example.com",
            company="Test Co",
            status=LeadStatus.active
        )
        lead_id = lead_rec.id
        
        # Create test message
        message = Message(
            id="msg-unsub-1",
            campaign_id="camp-1",
            lead_id=lead_id,
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent,
            sent_at=datetime.utcnow()
        )
        campaign_store.messages[message.id] = message
        
        # Generate valid token
        token = self.sender._generate_token(message.id)
        
        # Call unsubscribe endpoint
        response = self.client.post(f"/api/v1/track/unsubscribe?m={message.id}&t={token}")
        
        # Check response
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "successfully unsubscribed" in response.text.lower()
        assert "test@example.com" in response.text
        
        # Check lead was suppressed
        updated_lead = leads_store.get(lead_id)
        assert updated_lead.status == LeadStatus.suppressed
        
    def test_unsubscribe_already_unsubscribed(self):
        """Test unsubscribe for already suppressed lead."""
        # Create suppressed lead
        _, lead_rec = leads_store.upsert(
            email="already@example.com",
            company="Test Co",
            status=LeadStatus.suppressed  # Already suppressed
        )
        lead_id = lead_rec.id
        
        # Create message
        message = Message(
            id="msg-unsub-2",
            campaign_id="camp-1",
            lead_id=lead_id,
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        token = self.sender._generate_token(message.id)
        
        # Call unsubscribe
        response = self.client.post(f"/api/v1/track/unsubscribe?m={message.id}&t={token}")
        
        assert response.status_code == 200
        assert "already unsubscribed" in response.text.lower()
        
    def test_unsubscribe_invalid_token(self):
        """Test unsubscribe with invalid token."""
        _, lead_rec = leads_store.upsert(
            email="test3@example.com",
            company="Test Co",
            status=LeadStatus.active
        )
        lead_id = lead_rec.id
        
        message = Message(
            id="msg-unsub-3",
            campaign_id="camp-1",
            lead_id=lead_id,
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        # Use wrong token
        response = self.client.post(f"/api/v1/track/unsubscribe?m={message.id}&t=wrong-token")
        
        assert response.status_code == 400
        assert "invalid or expired" in response.text.lower()
        
        # Lead should NOT be suppressed
        updated_lead = leads_store.get(lead_id)
        assert updated_lead.status == LeadStatus.active
        
    def test_unsubscribe_nonexistent_message(self):
        """Test unsubscribe with nonexistent message."""
        token = self.sender._generate_token("fake-id")
        
        response = self.client.post(f"/api/v1/track/unsubscribe?m=fake-id&t={token}")
        
        assert response.status_code == 400
        assert "invalid" in response.text.lower()
        
    def test_unsubscribe_nonexistent_lead(self):
        """Test unsubscribe when lead doesn't exist."""
        # Create message with nonexistent lead
        message = Message(
            id="msg-unsub-4",
            campaign_id="camp-1",
            lead_id="nonexistent-lead",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        token = self.sender._generate_token(message.id)
        
        response = self.client.post(f"/api/v1/track/unsubscribe?m={message.id}&t={token}")
        
        assert response.status_code == 400
        assert "lead not found" in response.text.lower()
        
    def test_unsubscribe_missing_parameters(self):
        """Test endpoint with missing parameters."""
        # Missing token
        response = self.client.post("/api/v1/track/unsubscribe?m=some-id")
        assert response.status_code == 422  # Validation error
        
        # Missing message ID
        response = self.client.post("/api/v1/track/unsubscribe?t=some-token")
        assert response.status_code == 422
        
    def test_unsubscribe_creates_event(self):
        """Test that unsubscribe creates an event."""
        _, lead_rec = leads_store.upsert(
            email="event@example.com",
            company="Test Co",
            status=LeadStatus.active
        )
        lead_id = lead_rec.id
        
        message = Message(
            id="msg-unsub-5",
            campaign_id="camp-1",
            lead_id=lead_id,
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        token = self.sender._generate_token(message.id)
        
        # Check no events before
        initial_event_count = len(campaign_store.events)
        
        # Unsubscribe
        response = self.client.post(f"/api/v1/track/unsubscribe?m={message.id}&t={token}")
        assert response.status_code == 200
        
        # Check event was created
        assert len(campaign_store.events) == initial_event_count + 1
        
        # Find the new event
        events = [e for e in campaign_store.events.values() if e.message_id == message.id]
        assert len(events) == 1
        assert events[0].meta.get("reason") == "unsubscribed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
