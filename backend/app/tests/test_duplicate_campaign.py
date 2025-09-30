"""
Unit tests for campaign duplication functionality.
Tests for:
- Campaign store duplicate_campaign() method
- API endpoint POST /campaigns/{id}/duplicate
- Audience copying
- Counter resets
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.campaign import Campaign, CampaignAudience, CampaignStatus
from app.services.campaign_store import campaign_store


class TestCampaignStoreDuplicate:
    """Test campaign_store.duplicate_campaign() method."""
    
    def setup_method(self):
        """Clear store before each test."""
        campaign_store.campaigns.clear()
        campaign_store.audiences.clear()
    
    def test_duplicate_campaign_success(self):
        """Test successful campaign duplication."""
        # Create original campaign
        original = Campaign(
            id="original-123",
            name="Test Campaign",
            template_id="tpl-1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.running,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            start_at=datetime.utcnow()
        )
        campaign_store.create_campaign(original)
        
        # Duplicate campaign
        duplicate = campaign_store.duplicate_campaign("original-123")
        
        # Assertions
        assert duplicate is not None
        assert duplicate.id != original.id
        assert duplicate.name == "Test Campaign (Copy)"
        assert duplicate.template_id == original.template_id
        assert duplicate.domain == original.domain
        assert duplicate.status == CampaignStatus.draft
        assert duplicate.start_at is None
        
        # Check follow-up settings copied
        assert duplicate.followup_enabled == original.followup_enabled
        assert duplicate.followup_days == original.followup_days
        assert duplicate.followup_attach_report == original.followup_attach_report
        
        # Check duplicate exists in store
        assert duplicate.id in campaign_store.campaigns
        
    def test_duplicate_campaign_with_audience(self):
        """Test campaign duplication includes audience copy."""
        # Create original campaign
        original = Campaign(
            id="original-456",
            name="Campaign with Audience",
            template_id="tpl-2",
            domain="punthelder-seo.nl",
            status=CampaignStatus.draft,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        campaign_store.create_campaign(original)
        
        # Create audience
        audience = CampaignAudience(
            id="aud-1",
            campaign_id="original-456",
            lead_ids=["lead-1", "lead-2", "lead-3"],
            created_at=datetime.utcnow()
        )
        campaign_store.create_audience(audience)
        
        # Duplicate campaign
        duplicate = campaign_store.duplicate_campaign("original-456")
        
        # Find duplicated audience
        dup_audience = None
        for aud in campaign_store.audiences.values():
            if aud.campaign_id == duplicate.id:
                dup_audience = aud
                break
        
        assert dup_audience is not None
        assert dup_audience.id != audience.id
        assert dup_audience.campaign_id == duplicate.id
        assert dup_audience.lead_ids == ["lead-1", "lead-2", "lead-3"]
        
    def test_duplicate_nonexistent_campaign(self):
        """Test duplicating a campaign that doesn't exist."""
        result = campaign_store.duplicate_campaign("nonexistent-id")
        assert result is None


class TestDuplicateCampaignAPI:
    """Test /campaigns/{id}/duplicate API endpoint."""
    
    def setup_method(self):
        """Clear store and create test client."""
        campaign_store.campaigns.clear()
        campaign_store.audiences.clear()
        self.client = TestClient(app)
    
    def test_duplicate_campaign_endpoint_success(self):
        """Test successful duplication via API endpoint."""
        # Create original campaign
        original = Campaign(
            id="api-test-1",
            name="API Test Campaign",
            template_id="tpl-1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.completed,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        campaign_store.create_campaign(original)
        
        # Call duplicate endpoint (mock auth for testing)
        response = self.client.post(
            f"/api/v1/campaigns/api-test-1/duplicate",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        campaign_data = data["data"]
        
        assert campaign_data["id"] != "api-test-1"
        assert campaign_data["name"] == "API Test Campaign (Copy)"
        assert campaign_data["template_id"] == "tpl-1"
        assert campaign_data["domain"] == "punthelder-marketing.nl"
        assert campaign_data["status"] == "draft"
        
    def test_duplicate_campaign_endpoint_not_found(self):
        """Test duplication of nonexistent campaign via API."""
        response = self.client.post(
            "/api/v1/campaigns/nonexistent-id/duplicate",
            headers={"Authorization": "Bearer mock-token"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Campaign not found"
    
    def test_duplicate_campaign_endpoint_no_auth(self):
        """Test endpoint without authentication."""
        response = self.client.post("/api/v1/campaigns/any-id/duplicate")
        
        # Should return 401 or 403 for missing auth
        assert response.status_code in [401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
