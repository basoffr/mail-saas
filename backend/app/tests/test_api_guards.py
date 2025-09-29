import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.models.campaign import CampaignStatus


client = TestClient(app)


class TestAPIGuards:
    """Test API guards for hard-coded sending policy."""
    
    @patch('app.core.auth.require_auth')
    def test_settings_post_forbidden_fields(self, mock_auth):
        """Test that sending policy fields cannot be updated via POST."""
        mock_auth.return_value = {"sub": "test-user"}
        
        # Try to update timezone (forbidden)
        response = client.post("/api/v1/settings", json={
            "timezone": "America/New_York"
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
        
        # Try to update throttle (forbidden)
        response = client.post("/api/v1/settings", json={
            "throttle_minutes": 30
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
        
        # Try to update sending window (forbidden)
        response = client.post("/api/v1/settings", json={
            "sending_window_start": "09:00"
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_settings_put_forbidden(self, mock_auth):
        """Test that PUT method is forbidden for settings."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.put("/api/v1/settings", json={
            "unsubscribe_text": "Test"
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_settings_patch_forbidden(self, mock_auth):
        """Test that PATCH method is forbidden for settings."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.patch("/api/v1/settings", json={
            "tracking_pixel_enabled": False
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_settings_allowed_fields_still_work(self, mock_auth):
        """Test that allowed fields can still be updated."""
        mock_auth.return_value = {"sub": "test-user"}
        
        # unsubscribe_text should still work
        response = client.post("/api/v1/settings", json={
            "unsubscribe_text": "Afmelden"
        })
        
        assert response.status_code == 200
        
        # tracking_pixel_enabled should still work
        response = client.post("/api/v1/settings", json={
            "tracking_pixel_enabled": False
        })
        
        assert response.status_code == 200
    
    @patch('app.core.auth.require_auth')
    @patch('app.services.campaign_store.campaign_store')
    def test_campaign_create_override_fields_forbidden(self, mock_store, mock_auth):
        """Test that campaign override fields are forbidden."""
        mock_auth.return_value = {"sub": "test-user"}
        mock_store.check_domain_busy.return_value = False
        
        # Try to create campaign with timezone override
        payload = {
            "name": "Test Campaign",
            "template_id": "template-1",
            "domains": ["test.com"],
            "timezone_override": "America/New_York",
            "audience": {
                "lead_ids": ["lead-1"],
                "exclude_suppressed": True,
                "exclude_recent_days": 30,
                "one_per_domain": True
            },
            "schedule": {
                "start_mode": "immediate"
            },
            "followup": {
                "enabled": False,
                "days": 3,
                "attach_report": False
            }
        }
        
        response = client.post("/api/v1/campaigns", json=payload)
        
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "campaign_overrides_forbidden"
    
    @patch('app.core.auth.require_auth')
    @patch('app.services.campaign_store.campaign_store')
    def test_campaign_create_domain_busy(self, mock_store, mock_auth):
        """Test that second campaign on same domain is forbidden."""
        mock_auth.return_value = {"sub": "test-user"}
        mock_store.check_domain_busy.return_value = True  # Domain is busy
        
        payload = {
            "name": "Test Campaign",
            "template_id": "template-1",
            "domains": ["busy-domain.com"],
            "audience": {
                "lead_ids": ["lead-1"],
                "exclude_suppressed": True,
                "exclude_recent_days": 30,
                "one_per_domain": True
            },
            "schedule": {
                "start_mode": "immediate"
            },
            "followup": {
                "enabled": False,
                "days": 3,
                "attach_report": False
            }
        }
        
        response = client.post("/api/v1/campaigns", json=payload)
        
        assert response.status_code == 409
        assert response.json()["detail"]["error"] == "domain_busy"
    
    @patch('app.core.auth.require_auth')
    @patch('app.services.campaign_store.campaign_store')
    def test_campaign_create_no_domain(self, mock_store, mock_auth):
        """Test that campaign without domain is invalid."""
        mock_auth.return_value = {"sub": "test-user"}
        
        payload = {
            "name": "Test Campaign",
            "template_id": "template-1",
            "domains": [],  # Empty domains
            "audience": {
                "lead_ids": ["lead-1"],
                "exclude_suppressed": True,
                "exclude_recent_days": 30,
                "one_per_domain": True
            },
            "schedule": {
                "start_mode": "immediate"
            },
            "followup": {
                "enabled": False,
                "days": 3,
                "attach_report": False
            }
        }
        
        response = client.post("/api/v1/campaigns", json=payload)
        
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "invalid_payload"
    
    @patch('app.core.auth.require_auth')
    def test_settings_get_returns_hard_coded_policy(self, mock_auth):
        """Test that GET /settings returns hard-coded sending policy."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.get("/api/v1/settings")
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Check hard-coded values are present
        assert data["timezone"] == "Europe/Amsterdam"
        assert data["window"]["days"] == ["Mon", "Tue", "Wed", "Thu", "Fri"]
        assert data["window"]["from"] == "08:00"
        assert data["window"]["to"] == "17:00"
        assert data["window"]["editable"] == False
        assert data["throttle"]["minutes"] == 20
        assert data["throttle"]["editable"] == False
        assert data["timezoneEditable"] == False
        assert data["dailyCapPerDomain"] == 27
        assert data["gracePeriodTo"] == "18:00"
