import pytest
from datetime import datetime

from app.services.campaign_store import CampaignStore
from app.models.campaign import Campaign, CampaignStatus


class TestDomainBusy:
    """Test domain busy logic for max 1 active campaign per domain."""
    
    def setup_method(self):
        """Setup fresh campaign store for each test."""
        self.store = CampaignStore()
        # Clear sample data
        self.store.campaigns.clear()
    
    def test_check_domain_busy_empty(self):
        """Test that empty store reports no busy domains."""
        assert not self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_draft_campaign(self):
        """Test that draft campaigns don't make domain busy."""
        campaign = Campaign(
            id="test-1",
            name="Test Campaign",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.draft
        )
        self.store.campaigns[campaign.id] = campaign
        
        assert not self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_running_campaign(self):
        """Test that running campaigns make domain busy."""
        campaign = Campaign(
            id="test-1",
            name="Test Campaign",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.running
        )
        self.store.campaigns[campaign.id] = campaign
        
        assert self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_draft_campaign_not_busy(self):
        """Test that draft campaigns don't make domain busy."""
        campaign = Campaign(
            id="test-1",
            name="Test Campaign",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.draft
        )
        self.store.campaigns[campaign.id] = campaign
        
        assert not self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_completed_campaign(self):
        """Test that completed campaigns don't make domain busy."""
        campaign = Campaign(
            id="test-1",
            name="Test Campaign",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.completed
        )
        self.store.campaigns[campaign.id] = campaign
        
        assert not self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_stopped_campaign(self):
        """Test that stopped campaigns don't make domain busy."""
        campaign = Campaign(
            id="test-1",
            name="Test Campaign",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.stopped
        )
        self.store.campaigns[campaign.id] = campaign
        
        assert not self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_paused_campaign(self):
        """Test that paused campaigns don't make domain busy."""
        campaign = Campaign(
            id="test-1",
            name="Test Campaign",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.paused
        )
        self.store.campaigns[campaign.id] = campaign
        
        assert not self.store.check_domain_busy("test.com")
    
    def test_check_domain_busy_different_domains(self):
        """Test that different domains don't interfere."""
        campaign1 = Campaign(
            id="test-1",
            name="Test Campaign 1",
            template_id="template-1",
            domain="domain1.com",
            status=CampaignStatus.running
        )
        campaign2 = Campaign(
            id="test-2",
            name="Test Campaign 2",
            template_id="template-1",
            domain="domain2.com",
            status=CampaignStatus.running
        )
        
        self.store.campaigns[campaign1.id] = campaign1
        self.store.campaigns[campaign2.id] = campaign2
        
        # Both domains should be busy
        assert self.store.check_domain_busy("domain1.com")
        assert self.store.check_domain_busy("domain2.com")
        
        # Other domain should not be busy
        assert not self.store.check_domain_busy("domain3.com")
    
    def test_get_active_campaigns_by_domain(self):
        """Test getting active campaigns grouped by domain."""
        campaign1 = Campaign(
            id="test-1",
            name="Test Campaign 1",
            template_id="template-1",
            domain="domain1.com",
            status=CampaignStatus.running
        )
        campaign2 = Campaign(
            id="test-2",
            name="Test Campaign 2",
            template_id="template-1",
            domain="domain1.com",
            status=CampaignStatus.running
        )
        campaign3 = Campaign(
            id="test-3",
            name="Test Campaign 3",
            template_id="template-1",
            domain="domain2.com",
            status=CampaignStatus.running
        )
        campaign4 = Campaign(
            id="test-4",
            name="Test Campaign 4",
            template_id="template-1",
            domain="domain2.com",
            status=CampaignStatus.draft  # Should not appear
        )
        
        self.store.campaigns[campaign1.id] = campaign1
        self.store.campaigns[campaign2.id] = campaign2
        self.store.campaigns[campaign3.id] = campaign3
        self.store.campaigns[campaign4.id] = campaign4
        
        active_by_domain = self.store.get_active_campaigns_by_domain()
        
        # Should have 2 domains
        assert len(active_by_domain) == 2
        
        # domain1.com should have 2 active campaigns
        assert len(active_by_domain["domain1.com"]) == 2
        assert campaign1 in active_by_domain["domain1.com"]
        assert campaign2 in active_by_domain["domain1.com"]
        
        # domain2.com should have 1 active campaign
        assert len(active_by_domain["domain2.com"]) == 1
        assert campaign3 in active_by_domain["domain2.com"]
        
        # campaign4 (draft) should not appear anywhere
        all_campaigns = []
        for campaigns in active_by_domain.values():
            all_campaigns.extend(campaigns)
        assert campaign4 not in all_campaigns
    
    def test_multiple_active_campaigns_same_domain_violation(self):
        """Test that having multiple active campaigns on same domain is detected."""
        # This test simulates a violation of the "max 1 active per domain" rule
        campaign1 = Campaign(
            id="test-1",
            name="Test Campaign 1",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.running
        )
        campaign2 = Campaign(
            id="test-2",
            name="Test Campaign 2",
            template_id="template-1",
            domain="test.com",
            status=CampaignStatus.running
        )
        
        # Manually add both (simulating a bug or race condition)
        self.store.campaigns[campaign1.id] = campaign1
        self.store.campaigns[campaign2.id] = campaign2
        
        # Domain should be reported as busy
        assert self.store.check_domain_busy("test.com")
        
        # Should detect multiple active campaigns
        active_by_domain = self.store.get_active_campaigns_by_domain()
        assert len(active_by_domain["test.com"]) == 2
