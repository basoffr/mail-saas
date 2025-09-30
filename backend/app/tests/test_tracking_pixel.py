"""
Unit tests for tracking pixel endpoint.
Tests /track/open.gif endpoint functionality.
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.campaign import Message, MessageStatus
from app.services.campaign_store import campaign_store
from app.services.message_sender import MessageSender


class TestTrackingPixelEndpoint:
    """Test /track/open.gif endpoint."""
    
    def setup_method(self):
        """Clear store and create test client."""
        campaign_store.messages.clear()
        campaign_store.events.clear()
        self.client = TestClient(app)
        self.sender = MessageSender()
    
    def test_tracking_pixel_returns_gif(self):
        """Test that endpoint returns valid GIF image."""
        # Create test message
        message = Message(
            id="test-msg-pixel",
            campaign_id="camp-1",
            lead_id="lead-1",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        # Generate valid token
        token = self.sender._generate_token(message.id)
        
        # Call tracking endpoint
        response = self.client.get(f"/api/v1/track/open.gif?m={message.id}&t={token}")
        
        # Check response
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"
        assert len(response.content) > 0
        
        # Check cache headers
        assert "no-cache" in response.headers.get("cache-control", "")
        
    def test_tracking_pixel_with_invalid_token(self):
        """Test that invalid token still returns pixel but doesn't log."""
        message = Message(
            id="test-msg-invalid-token",
            campaign_id="camp-1",
            lead_id="lead-1",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        # Use wrong token
        response = self.client.get(f"/api/v1/track/open.gif?m={message.id}&t=wrong-token")
        
        # Still returns pixel (graceful degradation)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"
        
    def test_tracking_pixel_with_nonexistent_message(self):
        """Test that nonexistent message still returns pixel."""
        token = self.sender._generate_token("fake-id")
        
        response = self.client.get(f"/api/v1/track/open.gif?m=fake-id&t={token}")
        
        # Should still return pixel (graceful)
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/gif"
        
    def test_tracking_pixel_logs_open_event(self):
        """Test that valid tracking creates open event."""
        message = Message(
            id="test-msg-open-event",
            campaign_id="camp-1",
            lead_id="lead-1",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent,
            sent_at=datetime.utcnow()
        )
        campaign_store.messages[message.id] = message
        
        # Generate valid token
        token = self.sender._generate_token(message.id)
        
        # Track open
        response = self.client.get(f"/api/v1/track/open.gif?m={message.id}&t={token}")
        
        assert response.status_code == 200
        
        # Check message was updated
        updated_msg = campaign_store.get_message(message.id)
        assert updated_msg.open_at is not None
        assert updated_msg.status == MessageStatus.opened
        
    def test_tracking_pixel_missing_parameters(self):
        """Test endpoint behavior with missing parameters."""
        # Missing message ID
        response = self.client.get("/api/v1/track/open.gif?t=some-token")
        assert response.status_code == 422  # Validation error
        
        # Missing token
        response = self.client.get("/api/v1/track/open.gif?m=some-id")
        assert response.status_code == 422  # Validation error
        
    def test_tracking_pixel_gif_format(self):
        """Test that returned GIF is valid format."""
        message = Message(
            id="test-msg-gif-format",
            campaign_id="camp-1",
            lead_id="lead-1",
            domain_used="punthelder-marketing.nl",
            scheduled_at=datetime.utcnow(),
            status=MessageStatus.sent
        )
        campaign_store.messages[message.id] = message
        
        token = self.sender._generate_token(message.id)
        response = self.client.get(f"/api/v1/track/open.gif?m={message.id}&t={token}")
        
        # Check GIF signature (starts with GIF89a)
        assert response.content.startswith(b'GIF89a')
        
        # Check it's a 1x1 pixel
        assert len(response.content) == 43  # Size of 1x1 transparent GIF


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
