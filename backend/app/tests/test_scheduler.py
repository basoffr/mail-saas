import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.services.campaign_scheduler import CampaignScheduler
from app.models.campaign import Campaign, CampaignStatus, MessageStatus
from app.core.sending_policy import SENDING_POLICY


class TestCampaignScheduler:
    """Test campaign scheduler with flow-based scheduling."""
    
    def setup_method(self):
        """Setup fresh scheduler for each test."""
        self.scheduler = CampaignScheduler()
        self.tz = ZoneInfo(SENDING_POLICY.timezone)
    
    def test_schedule_campaign_basic(self):
        """Test basic campaign scheduling."""
        campaign = Campaign(
            id="test-campaign-1",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        lead_ids = ["lead-1", "lead-2"]
        
        result = self.scheduler.schedule_campaign(campaign, lead_ids)
        
        # Check result structure
        assert result["campaign_id"] == "test-campaign-1"
        assert result["domain"] == "punthelder-marketing.nl"
        assert result["total_messages"] == 8  # 2 leads × 4 mails
        assert result["flow_version"] == 1
        assert "mail_schedule" in result
        
        # Check mail schedule has 4 entries
        assert len(result["mail_schedule"]) == 4
        assert 1 in result["mail_schedule"]
        assert 4 in result["mail_schedule"]
        
        # Check domain is marked as busy
        assert self.scheduler.active_campaigns["punthelder-marketing.nl"] == "test-campaign-1"
        
        # Check queue has messages
        assert "punthelder-marketing.nl" in self.scheduler.domain_queues
        assert len(self.scheduler.domain_queues["punthelder-marketing.nl"]) == 8
    
    def test_schedule_campaign_domain_busy(self):
        """Test that scheduling fails when domain is busy."""
        # Schedule first campaign
        campaign1 = Campaign(
            id="campaign-1",
            name="Campaign 1",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        self.scheduler.schedule_campaign(campaign1, ["lead-1"])
        
        # Try to schedule second campaign on same domain
        campaign2 = Campaign(
            id="campaign-2",
            name="Campaign 2",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        with pytest.raises(ValueError, match="Domain .* is busy"):
            self.scheduler.schedule_campaign(campaign2, ["lead-2"])
    
    def test_schedule_campaign_invalid_domain(self):
        """Test that scheduling fails for invalid domain."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="invalid-domain.com",
            status=CampaignStatus.draft
        )
        
        with pytest.raises(ValueError, match="No flow configured"):
            self.scheduler.schedule_campaign(campaign, ["lead-1"])
    
    def test_mail_schedule_workdays(self):
        """Test that mail schedule respects +3 workdays intervals."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)  # Monday
        )
        
        result = self.scheduler.schedule_campaign(campaign, ["lead-1"])
        schedule = result["mail_schedule"]
        
        # Mail 1: Monday (day 0)
        assert schedule[1].strftime("%a") == "Mon"
        
        # Mail 2: Thursday (day +3 workdays)
        assert schedule[2].strftime("%a") == "Thu"
        
        # Mail 3: Tuesday next week (day +6 workdays)
        assert schedule[3].strftime("%a") == "Tue"
        
        # Mail 4: Friday next week (day +9 workdays)
        assert schedule[4].strftime("%a") == "Fri"
    
    def test_mail_schedule_weekend_skip(self):
        """Test that weekend is skipped in scheduling."""
        # Start on Friday after window
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 10, 3, 17, 30, tzinfo=self.tz)  # Friday 17:30 (after window)
        )
        
        result = self.scheduler.schedule_campaign(campaign, ["lead-1"])
        schedule = result["mail_schedule"]
        
        # Mail 1 should move to Monday 08:00 (after window)
        assert schedule[1].strftime("%a") == "Mon"
        assert schedule[1].hour == 8
        assert schedule[1].minute == 0
    
    def test_get_next_messages_to_send(self):
        """Test getting next messages to send (FIFO)."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)  # Monday 08:00
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1", "lead-2"])
        
        # Get messages ready to send at 08:00
        current_time = datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)
        ready_messages = self.scheduler.get_next_messages_to_send("punthelder-marketing.nl", current_time)
        
        # Should get 2 messages (mail 1 for both leads)
        assert len(ready_messages) == 2
        
        # All should be mail number 1
        for message in ready_messages:
            assert message.mail_number == 1
            assert message.alias == "christian"
    
    def test_throttling_enforcement(self):
        """Test that throttling (20 minutes) is enforced."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1"])
        
        # Send first message at 08:00
        current_time = datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)
        ready_messages = self.scheduler.get_next_messages_to_send("punthelder-marketing.nl", current_time)
        assert len(ready_messages) == 1
        
        # Try to send again at 08:10 (only 10 minutes later)
        current_time = datetime(2025, 9, 29, 8, 10, tzinfo=self.tz)
        ready_messages = self.scheduler.get_next_messages_to_send("punthelder-marketing.nl", current_time)
        assert len(ready_messages) == 0  # Throttled
        
        # Try again at 08:20 (20 minutes later)
        current_time = datetime(2025, 9, 29, 8, 20, tzinfo=self.tz)
        ready_messages = self.scheduler.get_next_messages_to_send("punthelder-marketing.nl", current_time)
        # Should be available if there are more messages scheduled for this time
    
    def test_grace_period_enforcement(self):
        """Test that grace period (until 18:00) is enforced."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 9, 29, 17, 0, tzinfo=self.tz)  # 17:00
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1"])
        
        # Try to send at 18:30 (outside grace period)
        current_time = datetime(2025, 9, 29, 18, 30, tzinfo=self.tz)
        ready_messages = self.scheduler.get_next_messages_to_send("punthelder-marketing.nl", current_time)
        
        # Should return empty list (outside grace period)
        assert len(ready_messages) == 0
    
    def test_move_remaining_to_next_day(self):
        """Test that remaining messages are moved to next day after grace period."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 9, 29, 17, 30, tzinfo=self.tz)  # Late start
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1"])
        
        # Trigger grace period check at 18:30
        current_time = datetime(2025, 9, 29, 18, 30, tzinfo=self.tz)
        self.scheduler.get_next_messages_to_send("punthelder-marketing.nl", current_time)
        
        # Check that messages were rescheduled to next day
        queue = self.scheduler.domain_queues["punthelder-marketing.nl"]
        for item in queue:
            message = item["message"]
            scheduled_at = item["scheduled_at"]
            
            # Should be rescheduled to next valid day
            if message.scheduled_at.date() == current_time.date():
                assert scheduled_at.date() > current_time.date()
    
    def test_complete_campaign(self):
        """Test campaign completion and domain cleanup."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1"])
        
        # Domain should be busy
        assert "punthelder-marketing.nl" in self.scheduler.active_campaigns
        
        # Complete campaign
        self.scheduler.complete_campaign("test-campaign", "punthelder-marketing.nl")
        
        # Domain should be available
        assert "punthelder-marketing.nl" not in self.scheduler.active_campaigns
    
    def test_get_domain_status(self):
        """Test getting domain status overview."""
        # Schedule campaign on one domain
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1", "lead-2"])
        
        status = self.scheduler.get_domain_status()
        
        # Check all 4 domains are included
        expected_domains = [
            "punthelder-marketing.nl", "punthelder-vindbaarheid.nl",
            "punthelder-seo.nl", "punthelder-zoekmachine.nl"
        ]
        
        for domain in expected_domains:
            assert domain in status
            assert "active_campaign" in status[domain]
            assert "queue_size" in status[domain]
            assert "last_send" in status[domain]
            assert "is_busy" in status[domain]
        
        # Marketing domain should be busy
        assert status["punthelder-marketing.nl"]["is_busy"] == True
        assert status["punthelder-marketing.nl"]["active_campaign"] == "test-campaign"
        assert status["punthelder-marketing.nl"]["queue_size"] == 8  # 2 leads × 4 mails
        
        # Other domains should be free
        assert status["punthelder-vindbaarheid.nl"]["is_busy"] == False
        assert status["punthelder-vindbaarheid.nl"]["active_campaign"] is None
        assert status["punthelder-vindbaarheid.nl"]["queue_size"] == 0
    
    def test_alias_assignment(self):
        """Test that correct aliases are assigned to mails."""
        campaign = Campaign(
            id="test-campaign",
            name="Test Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        self.scheduler.schedule_campaign(campaign, ["lead-1"])
        
        # Check messages in queue
        queue = self.scheduler.domain_queues["punthelder-marketing.nl"]
        
        # Group by mail number
        messages_by_mail = {}
        for item in queue:
            message = item["message"]
            mail_num = message.mail_number
            if mail_num not in messages_by_mail:
                messages_by_mail[mail_num] = []
            messages_by_mail[mail_num].append(message)
        
        # Mail 1 & 2 should be Christian
        for message in messages_by_mail[1]:
            assert message.alias == "christian"
            assert message.from_email == "christian@punthelder.nl"
            assert message.reply_to_email == "christian@punthelder.nl"
        
        for message in messages_by_mail[2]:
            assert message.alias == "christian"
            assert message.from_email == "christian@punthelder.nl"
            assert message.reply_to_email == "christian@punthelder.nl"
        
        # Mail 3 & 4 should be Victor (From=Victor, Reply-To=Christian)
        for message in messages_by_mail[3]:
            assert message.alias == "victor"
            assert message.from_email == "victor@punthelder.nl"
            assert message.reply_to_email == "christian@punthelder.nl"
        
        for message in messages_by_mail[4]:
            assert message.alias == "victor"
            assert message.from_email == "victor@punthelder.nl"
            assert message.reply_to_email == "christian@punthelder.nl"
