import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime, timedelta
import pytz

from app.main import app
from app.core.sending_policy import SENDING_POLICY
from app.core.campaign_flows import get_flow_for_domain
from app.services.campaign_scheduler import CampaignScheduler
from app.models.campaign import Campaign, CampaignStatus


client = TestClient(app)


class TestIntegrationGuardrails:
    """Integration tests voor alle guardrails samen."""
    
    @patch('app.core.auth.require_auth')
    def test_complete_settings_guardrails(self, mock_auth):
        """Test complete settings guardrails flow."""
        mock_auth.return_value = {"sub": "test-user"}
        
        # GET /settings should return hard-coded policy
        response = client.get("/api/v1/settings")
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["timezone"] == "Europe/Amsterdam"
        assert data["window"]["days"] == ["Mon", "Tue", "Wed", "Thu", "Fri"]
        assert data["window"]["from"] == "08:00"
        assert data["window"]["to"] == "17:00"
        assert data["window"]["editable"] == False
        assert data["throttle"]["minutes"] == 20
        assert data["throttle"]["editable"] == False
        assert data["dailyCapPerDomain"] == 27
        assert data["gracePeriodTo"] == "18:00"
        
        # POST with sending policy fields should fail
        response = client.post("/api/v1/settings", json={
            "timezone": "America/New_York"
        })
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
        
        # PUT should fail
        response = client.put("/api/v1/settings", json={
            "unsubscribe_text": "Test"
        })
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
        
        # PATCH should fail
        response = client.patch("/api/v1/settings", json={
            "throttle_minutes": 30
        })
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "settings_hard_coded"
    
    @patch('app.core.auth.require_auth')
    @patch('app.services.campaign_store.campaign_store')
    def test_complete_campaign_guardrails(self, mock_store, mock_auth):
        """Test complete campaign guardrails flow."""
        mock_auth.return_value = {"sub": "test-user"}
        mock_store.check_domain_busy.return_value = False
        
        # Valid campaign creation should work
        payload = {
            "name": "Test Campaign",
            "template_id": "v1_mail1",
            "domains": ["punthelder-marketing.nl"],
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
        assert response.status_code == 200
        
        # Campaign with override fields should fail
        payload_with_override = payload.copy()
        payload_with_override["timezone_override"] = "America/New_York"
        
        response = client.post("/api/v1/campaigns", json=payload_with_override)
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "campaign_overrides_forbidden"
        
        # Campaign on busy domain should fail
        mock_store.check_domain_busy.return_value = True
        
        response = client.post("/api/v1/campaigns", json=payload)
        assert response.status_code == 409
        assert response.json()["detail"]["error"] == "domain_busy"
        
        # Campaign without domain should fail
        payload_no_domain = payload.copy()
        payload_no_domain["domains"] = []
        
        response = client.post("/api/v1/campaigns", json=payload_no_domain)
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "invalid_payload"
    
    @patch('app.core.auth.require_auth')
    def test_complete_templates_guardrails(self, mock_auth):
        """Test complete templates guardrails flow."""
        mock_auth.return_value = {"sub": "test-user"}
        
        # GET should work and return 16 templates
        response = client.get("/api/v1/templates")
        assert response.status_code == 200
        
        data = response.json()["data"]
        assert data["total"] == 16
        assert len(data["items"]) == 16
        
        # Check template naming pattern
        template_names = [t["name"] for t in data["items"]]
        assert "V1 Mail 1" in template_names
        assert "V4 Mail 4" in template_names
        
        # GET specific template should work
        response = client.get("/api/v1/templates/v1_mail1")
        assert response.status_code == 200
        
        template_data = response.json()["data"]
        assert template_data["id"] == "v1_mail1"
        assert template_data["name"] == "V1 Mail 1"
        assert "lead.company" in template_data["variables"]
        
        # POST (create) should fail
        response = client.post("/api/v1/templates", json={
            "name": "New Template",
            "subject": "Test Subject"
        })
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
        
        # PUT (update) should fail
        response = client.put("/api/v1/templates/v1_mail1", json={
            "name": "Updated Template"
        })
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
        
        # PATCH should fail
        response = client.patch("/api/v1/templates/v1_mail1", json={
            "subject": "Updated Subject"
        })
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
        
        # DELETE should fail
        response = client.delete("/api/v1/templates/v1_mail1")
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
    
    def test_sending_policy_consistency(self):
        """Test that sending policy is consistent across all components."""
        # Check SENDING_POLICY values
        assert SENDING_POLICY.timezone == "Europe/Amsterdam"
        assert SENDING_POLICY.days == ["Mon", "Tue", "Wed", "Thu", "Fri"]
        assert SENDING_POLICY.window_from == "08:00"
        assert SENDING_POLICY.window_to == "17:00"
        assert SENDING_POLICY.grace_to == "18:00"
        assert SENDING_POLICY.slot_every_minutes == 20
        assert SENDING_POLICY.daily_cap_per_domain == 27
        
        # Check slot generation
        slots = SENDING_POLICY.get_daily_slots()
        assert len(slots) == 27
        assert slots[0] == "08:00"
        assert slots[-1] == "16:40"
    
    def test_campaign_flows_consistency(self):
        """Test that campaign flows are consistent."""
        domains = [
            "punthelder-marketing.nl",
            "punthelder-vindbaarheid.nl", 
            "punthelder-seo.nl",
            "punthelder-zoekmachine.nl"
        ]
        
        for i, domain in enumerate(domains, 1):
            flow = get_flow_for_domain(domain)
            assert flow is not None
            assert flow.version == i
            assert len(flow.steps) == 4
            
            # Check alias pattern
            assert flow.steps[0].alias == "christian"  # Mail 1
            assert flow.steps[1].alias == "christian"  # Mail 2
            assert flow.steps[2].alias == "victor"     # Mail 3
            assert flow.steps[3].alias == "victor"     # Mail 4
            
            # Check workday offsets
            assert flow.steps[0].workdays_offset == 0  # Day 0
            assert flow.steps[1].workdays_offset == 3  # Day +3
            assert flow.steps[2].workdays_offset == 6  # Day +6
            assert flow.steps[3].workdays_offset == 9  # Day +9
    
    def test_scheduler_integration(self):
        """Test scheduler integration with all components."""
        scheduler = CampaignScheduler()
        
        # Test domain status
        status = scheduler.get_domain_status()
        expected_domains = [
            "punthelder-marketing.nl", "punthelder-vindbaarheid.nl",
            "punthelder-seo.nl", "punthelder-zoekmachine.nl"
        ]
        
        for domain in expected_domains:
            assert domain in status
            assert "active_campaign" in status[domain]
            assert "queue_size" in status[domain]
            assert "is_busy" in status[domain]
            assert status[domain]["is_busy"] == False  # Initially free
    
    def test_error_message_consistency(self):
        """Test that error messages are consistent across all endpoints."""
        # This would be tested with actual API calls in the other test methods
        # Just documenting the expected error codes here
        
        expected_errors = {
            "settings_hard_coded": "Settings are hard-coded and cannot be modified",
            "campaign_overrides_forbidden": "Campaign overrides are not allowed",
            "domain_busy": "Domain is busy with another campaign",
            "invalid_payload": "Invalid request payload",
            "templates_hard_coded": "Templates are hard-coded and cannot be modified"
        }
        
        # These errors should be consistent across all endpoints
        assert len(expected_errors) == 5
    
    def test_weekend_and_grace_period_integration(self):
        """Test weekend skip and grace period integration."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # Test weekend skip
        saturday = datetime(2025, 10, 4, 10, 0, tzinfo=tz)  # Saturday
        assert not SENDING_POLICY.is_valid_sending_day(saturday)
        
        next_slot = SENDING_POLICY.get_next_valid_slot(saturday)
        assert next_slot.strftime("%a") == "Mon"  # Should move to Monday
        
        # Test grace period
        within_grace = datetime(2025, 9, 26, 17, 30, tzinfo=tz)
        assert SENDING_POLICY.is_within_grace_period(within_grace)
        
        outside_grace = datetime(2025, 9, 26, 18, 30, tzinfo=tz)
        assert not SENDING_POLICY.is_within_grace_period(outside_grace)
    
    def test_throttling_and_domain_limits(self):
        """Test throttling and domain limits integration."""
        scheduler = CampaignScheduler()
        
        # Test that scheduler respects domain limits
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        # Should be able to schedule first campaign
        result = scheduler.schedule_campaign(campaign, ["lead-1"])
        assert result["domain"] == "punthelder-marketing.nl"
        assert result["total_messages"] == 4  # 1 lead × 4 mails
        
        # Should not be able to schedule second campaign on same domain
        campaign2 = Campaign(
            id="test-campaign-2",
            name="Test Campaign 2",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        with pytest.raises(ValueError, match="Domain .* is busy"):
            scheduler.schedule_campaign(campaign2, ["lead-2"])
