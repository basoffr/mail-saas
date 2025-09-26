import pytest
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.models.campaign import CampaignStatus, MessageStatus
from app.schemas.campaign import CampaignCreatePayload, AudienceSelection, ScheduleSettings, FollowupSettings
from app.services.campaign_store import campaign_store
from app.services.campaign_scheduler import CampaignScheduler
from app.core.auth import require_auth

# Mock auth dependency
def mock_auth_dependency():
    return {"user_id": "test-user", "email": "test@example.com"}

app.dependency_overrides[require_auth] = mock_auth_dependency
client = TestClient(app)


@pytest.fixture
def sample_campaign_payload():
    return {
        "name": "Test Campaign",
        "template_id": "welcome-001",
        "audience": {
            "mode": "static",
            "lead_ids": ["lead-001", "lead-002", "lead-003"],
            "exclude_suppressed": True,
            "exclude_recent_days": 14,
            "one_per_domain": False
        },
        "schedule": {
            "start_mode": "now",
            "start_at": None
        },
        "domains": ["domain1.com", "domain2.com"],
        "followup": {
            "enabled": True,
            "days": 3,
            "attach_report": False
        }
    }


class TestCampaignAPI:
    
    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["data"]["ok"] is True
    
    def test_list_campaigns_ok(self):
        """Test successful campaign listing."""
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert isinstance(data["data"]["items"], list)
    
    def test_list_campaigns_with_filters(self):
        """Test campaign listing with filters."""
        response = client.get("/api/v1/campaigns?status=running&search=welcome&page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["total"] >= 0
    
    def test_create_campaign_ok(self, sample_campaign_payload):
        """Test successful campaign creation."""
        response = client.post("/api/v1/campaigns", json=sample_campaign_payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "id" in data["data"]
        
        campaign_id = data["data"]["id"]
        assert campaign_id is not None
    
    def test_create_campaign_validation(self):
        """Test campaign creation validation."""
        invalid_payload = {
            "name": "",  # Empty name should fail
            "template_id": "welcome-001",
            "audience": {"mode": "static", "lead_ids": []},
            "schedule": {"start_mode": "now"},
            "domains": [],  # Empty domains should fail
            "followup": {"enabled": False, "days": 3, "attach_report": False}
        }
        
        response = client.post("/api/v1/campaigns", json=invalid_payload)
        assert response.status_code == 422  # Validation error
    
    def test_get_campaign_detail_not_found(self):
        """Test getting non-existent campaign."""
        response = client.get("/api/v1/campaigns/non-existent-id")
        assert response.status_code == 404
    
    def test_get_campaign_detail_ok(self):
        """Test getting existing campaign detail."""
        # Use existing sample campaign
        response = client.get("/api/v1/campaigns/campaign-001")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        campaign = data["data"]
        assert "id" in campaign
        assert "kpis" in campaign
        assert "timeline" in campaign
        assert "domains_used" in campaign
    
    def test_pause_campaign_ok(self):
        """Test pausing a running campaign."""
        # First ensure we have a running campaign
        campaign_store.update_campaign_status("campaign-001", CampaignStatus.running)
        
        response = client.post("/api/v1/campaigns/campaign-001/pause")
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["ok"] is True
        assert "paused" in data["data"]["message"].lower()
    
    def test_pause_campaign_invalid_status(self):
        """Test pausing non-running campaign."""
        # Ensure campaign is not running
        campaign_store.update_campaign_status("campaign-001", CampaignStatus.draft)
        
        response = client.post("/api/v1/campaigns/campaign-001/pause")
        assert response.status_code == 400
    
    def test_resume_campaign_ok(self):
        """Test resuming a paused campaign."""
        # First ensure we have a paused campaign
        campaign_store.update_campaign_status("campaign-001", CampaignStatus.paused)
        
        response = client.post("/api/v1/campaigns/campaign-001/resume")
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["ok"] is True
        assert "resumed" in data["data"]["message"].lower()
    
    def test_stop_campaign_ok(self):
        """Test stopping a campaign."""
        # Ensure campaign can be stopped
        campaign_store.update_campaign_status("campaign-001", CampaignStatus.running)
        
        response = client.post("/api/v1/campaigns/campaign-001/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert data["data"]["ok"] is True
        assert "stopped" in data["data"]["message"].lower()
    
    def test_dry_run_campaign_ok(self):
        """Test campaign dry run."""
        response = client.post("/api/v1/campaigns/campaign-001/dry-run")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        dry_run = data["data"]
        assert "by_day" in dry_run
        assert "total_planned" in dry_run
        assert isinstance(dry_run["by_day"], list)
    
    def test_list_messages_ok(self):
        """Test listing messages."""
        response = client.get("/api/v1/campaigns/messages?campaign_id=campaign-001")
        assert response.status_code == 200
        
        data = response.json()
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    def test_resend_message_not_found(self):
        """Test resending non-existent message."""
        response = client.post("/api/v1/campaigns/messages/non-existent/resend", json={})
        assert response.status_code == 404
    
    def test_resend_message_invalid_status(self):
        """Test resending message with wrong status."""
        # Create a sent message (can't resend)
        message_id = "message-001"
        campaign_store.update_message_status(message_id, MessageStatus.sent)
        
        response = client.post(f"/api/v1/campaigns/messages/{message_id}/resend", json={})
        assert response.status_code == 400


class TestCampaignScheduler:
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = CampaignScheduler()
        assert scheduler.TIMEZONE.key == "Europe/Amsterdam"
        assert scheduler.WORK_DAYS == [0, 1, 2, 3, 4]
        assert scheduler.WORK_START_HOUR == 8
        assert scheduler.WORK_END_HOUR == 17
        assert scheduler.THROTTLE_MINUTES == 20
    
    def test_get_next_valid_slot_work_hours(self):
        """Test getting next valid slot during work hours."""
        scheduler = CampaignScheduler()
        
        # Tuesday 10:00 AM (valid work time) with timezone
        test_time = datetime(2025, 9, 23, 10, 0, tzinfo=scheduler.TIMEZONE)
        next_slot = scheduler._get_next_valid_slot(test_time)
        
        assert next_slot >= test_time
        assert next_slot.weekday() in scheduler.WORK_DAYS
        assert scheduler.WORK_START_HOUR <= next_slot.hour < scheduler.WORK_END_HOUR
    
    def test_get_next_valid_slot_weekend(self):
        """Test getting next valid slot on weekend."""
        scheduler = CampaignScheduler()
        
        # Saturday 10:00 AM (invalid - weekend) with timezone
        test_time = datetime(2025, 9, 27, 10, 0, tzinfo=scheduler.TIMEZONE)
        next_slot = scheduler._get_next_valid_slot(test_time)
        
        # Should move to Monday 08:00
        assert next_slot.weekday() == 0  # Monday
        assert next_slot.hour == scheduler.WORK_START_HOUR
    
    def test_get_next_valid_slot_after_hours(self):
        """Test getting next valid slot after work hours."""
        scheduler = CampaignScheduler()
        
        # Tuesday 18:00 (after work hours) with timezone
        test_time = datetime(2025, 9, 23, 18, 0, tzinfo=scheduler.TIMEZONE)
        next_slot = scheduler._get_next_valid_slot(test_time)
        
        # Should move to Wednesday 08:00
        assert next_slot.weekday() == 2  # Wednesday
        assert next_slot.hour == scheduler.WORK_START_HOUR
    
    def test_dry_run_planning(self):
        """Test dry run planning calculation."""
        scheduler = CampaignScheduler()
        
        domains = ["domain1.com", "domain2.com"]
        lead_count = 10
        
        dry_run = scheduler.dry_run_planning(lead_count, domains)
        
        assert len(dry_run) > 0
        total_planned = sum(day.planned for day in dry_run)
        assert total_planned == lead_count
    
    def test_create_campaign_messages(self):
        """Test creating campaign messages."""
        scheduler = CampaignScheduler()
        
        from app.models.campaign import Campaign
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="template-001",
            status=CampaignStatus.draft
        )
        
        lead_ids = ["lead-001", "lead-002", "lead-003"]
        domains = ["domain1.com", "domain2.com"]
        
        messages = scheduler.create_campaign_messages(campaign, lead_ids, domains)
        
        assert len(messages) == len(lead_ids)
        for message in messages:
            assert message.campaign_id == campaign.id
            assert message.lead_id in lead_ids
            assert message.domain_used in domains
            assert message.status == MessageStatus.queued


class TestTrackingAPI:
    
    def test_track_open_invalid_message(self):
        """Test tracking open for invalid message."""
        response = client.get("/api/v1/track/open.gif?m=invalid-id&t=invalid-token")
        assert response.status_code == 200  # Always returns pixel
        assert response.headers["content-type"] == "image/gif"
    
    def test_track_open_invalid_token(self):
        """Test tracking open with invalid token."""
        response = client.get("/api/v1/track/open.gif?m=message-001&t=invalid-token")
        assert response.status_code == 200  # Always returns pixel
        assert response.headers["content-type"] == "image/gif"
    
    def test_track_open_missing_params(self):
        """Test tracking open with missing parameters."""
        response = client.get("/api/v1/track/open.gif")
        assert response.status_code == 422  # Validation error


class TestCampaignStore:
    
    def test_create_campaign(self):
        """Test creating campaign in store."""
        from app.models.campaign import Campaign
        
        campaign = Campaign(
            id=str(uuid.uuid4()),
            name="Test Store Campaign",
            template_id="template-001",
            status=CampaignStatus.draft
        )
        
        created = campaign_store.create_campaign(campaign)
        assert created.id == campaign.id
        assert created.name == campaign.name
    
    def test_list_campaigns_filtering(self):
        """Test campaign listing with filters."""
        from app.schemas.campaign import CampaignQuery
        
        query = CampaignQuery(
            page=1,
            page_size=10,
            status=[CampaignStatus.running],
            search="welcome"
        )
        
        campaigns, total = campaign_store.list_campaigns(query)
        assert isinstance(campaigns, list)
        assert isinstance(total, int)
    
    def test_get_campaign_kpis(self):
        """Test KPI calculation."""
        kpis = campaign_store.get_campaign_kpis("campaign-001")
        
        assert hasattr(kpis, "total_planned")
        assert hasattr(kpis, "total_sent")
        assert hasattr(kpis, "total_opened")
        assert hasattr(kpis, "open_rate")
        assert 0.0 <= kpis.open_rate <= 1.0
    
    def test_get_campaign_timeline(self):
        """Test timeline data generation."""
        timeline = campaign_store.get_campaign_timeline("campaign-001")
        
        assert isinstance(timeline, list)
        for point in timeline:
            assert hasattr(point, "date")
            assert hasattr(point, "sent")
            assert hasattr(point, "opened")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
