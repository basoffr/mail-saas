import pytest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch

from app.services.campaign_scheduler import CampaignScheduler
from app.models.campaign import Campaign, CampaignStatus
from app.core.sending_policy import SENDING_POLICY
from app.core.campaign_flows import get_flow_for_domain, calculate_mail_schedule


class TestE2EScenarios:
    """End-to-end tests voor kritieke business scenarios."""
    
    def setup_method(self):
        """Setup voor elke test."""
        self.scheduler = CampaignScheduler()
        self.tz = ZoneInfo(SENDING_POLICY.timezone)
    
    def test_campaign_friday_evening_to_monday_morning(self):
        """Test: Campagne start vrijdag 16:50 → Mail 1 schuift naar maandag 08:00."""
        # Vrijdag 16:50 (na laatste slot 16:40)
        friday_late = datetime(2025, 10, 3, 16, 50, tzinfo=self.tz)
        
        campaign = Campaign(
            id="friday-campaign",
            name="Friday Late Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=friday_late
        )
        
        result = self.scheduler.schedule_campaign(campaign, ["lead-1"])
        mail_schedule = result["mail_schedule"]
        
        # Mail 1 should be scheduled for Monday 08:00
        mail1_time = mail_schedule[1]
        assert mail1_time.strftime("%a") == "Mon"
        assert mail1_time.hour == 8
        assert mail1_time.minute == 0
        
        # Mail 2 should be Thursday (+3 workdays from Monday)
        mail2_time = mail_schedule[2]
        assert mail2_time.strftime("%a") == "Thu"
        
        # Mail 3 should be Tuesday next week (+6 workdays from Monday)
        mail3_time = mail_schedule[3]
        assert mail3_time.strftime("%a") == "Tue"
        
        # Mail 4 should be Friday next week (+9 workdays from Monday)
        mail4_time = mail_schedule[4]
        assert mail4_time.strftime("%a") == "Fri"
    
    def test_campaign_thursday_to_tuesday_workdays(self):
        """Test: Campagne start donderdag → Mail 2 komt dinsdag (3 werkdagen)."""
        # Donderdag 08:00
        thursday = datetime(2025, 10, 2, 8, 0, tzinfo=self.tz)
        
        campaign = Campaign(
            id="thursday-campaign",
            name="Thursday Campaign",
            template_id="v2_mail1",
            domain="punthelder-vindbaarheid.nl",
            status=CampaignStatus.draft,
            start_at=thursday
        )
        
        result = self.scheduler.schedule_campaign(campaign, ["lead-1"])
        mail_schedule = result["mail_schedule"]
        
        # Mail 1: Thursday (same day)
        assert mail_schedule[1].strftime("%a") == "Thu"
        
        # Mail 2: Tuesday next week (+3 workdays: Fri +1, Mon +2, Tue +3)
        assert mail_schedule[2].strftime("%a") == "Tue"
        
        # Verify it's actually next week
        assert mail_schedule[2].date() > thursday.date() + timedelta(days=3)
    
    def test_grace_period_overflow_to_next_day(self):
        """Test: Overschot na 18:00 → volgende werkdag 08:00."""
        # Start campagne laat op de dag
        late_start = datetime(2025, 9, 29, 17, 30, tzinfo=self.tz)  # Monday 17:30
        
        campaign = Campaign(
            id="late-campaign",
            name="Late Start Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=late_start
        )
        
        # Schedule campaign with multiple leads
        result = self.scheduler.schedule_campaign(campaign, ["lead-1", "lead-2", "lead-3"])
        
        # Simulate time passing to 18:30 (outside grace period)
        outside_grace = datetime(2025, 9, 29, 18, 30, tzinfo=self.tz)
        
        # Try to get messages to send
        ready_messages = self.scheduler.get_next_messages_to_send(
            "punthelder-marketing.nl", 
            outside_grace
        )
        
        # Should return empty list (outside grace period)
        assert len(ready_messages) == 0
        
        # Check that remaining messages were rescheduled to next day
        queue = self.scheduler.domain_queues["punthelder-marketing.nl"]
        
        # Some messages should be rescheduled to next day
        next_day_messages = [
            item for item in queue 
            if item["scheduled_at"].date() > outside_grace.date()
        ]
        assert len(next_day_messages) > 0
        
        # Next day messages should be at 08:00
        for item in next_day_messages:
            if item["scheduled_at"].date() == outside_grace.date() + timedelta(days=1):
                assert item["scheduled_at"].hour == 8
                assert item["scheduled_at"].minute == 0
    
    def test_domain_busy_enforcement(self):
        """Test: Max 1 actieve campagne per domein enforcement."""
        # Schedule first campaign
        campaign1 = Campaign(
            id="campaign-1",
            name="First Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        result1 = self.scheduler.schedule_campaign(campaign1, ["lead-1"])
        assert result1["domain"] == "punthelder-marketing.nl"
        
        # Try to schedule second campaign on same domain
        campaign2 = Campaign(
            id="campaign-2",
            name="Second Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        # Should fail with domain busy error
        with pytest.raises(ValueError, match="Domain .* is busy"):
            self.scheduler.schedule_campaign(campaign2, ["lead-2"])
        
        # Complete first campaign
        self.scheduler.complete_campaign("campaign-1", "punthelder-marketing.nl")
        
        # Now second campaign should work
        result2 = self.scheduler.schedule_campaign(campaign2, ["lead-2"])
        assert result2["domain"] == "punthelder-marketing.nl"
        assert result2["campaign_id"] == "campaign-2"
    
    def test_cross_domain_parallel_processing(self):
        """Test: Cross-domain parallel processing werkt correct."""
        domains = [
            "punthelder-marketing.nl",
            "punthelder-vindbaarheid.nl", 
            "punthelder-seo.nl",
            "punthelder-zoekmachine.nl"
        ]
        
        campaigns = []
        
        # Schedule campaign on each domain
        for i, domain in enumerate(domains, 1):
            campaign = Campaign(
                id=f"campaign-{i}",
                name=f"Campaign {i}",
                template_id=f"v{i}_mail1",
                domain=domain,
                status=CampaignStatus.draft
            )
            
            result = self.scheduler.schedule_campaign(campaign, [f"lead-{i}"])
            campaigns.append(result)
            
            # Each should succeed
            assert result["domain"] == domain
            assert result["flow_version"] == i
        
        # All domains should be busy now
        status = self.scheduler.get_domain_status()
        for domain in domains:
            assert status[domain]["is_busy"] == True
            assert status[domain]["queue_size"] == 4  # 1 lead × 4 mails
        
        # Should be able to get messages from all domains simultaneously
        current_time = datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)  # Monday 08:00
        
        total_ready = 0
        for domain in domains:
            ready = self.scheduler.get_next_messages_to_send(domain, current_time)
            total_ready += len(ready)
        
        # Should have 4 messages ready (1 from each domain)
        assert total_ready == 4
    
    def test_flow_completion_stats(self):
        """Test: Flow completion stats tonen hoeveel leads M1–M4 doorlopen hebben."""
        # Schedule campaign with multiple leads
        campaign = Campaign(
            id="stats-campaign",
            name="Stats Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft
        )
        
        leads = ["lead-1", "lead-2", "lead-3"]
        result = self.scheduler.schedule_campaign(campaign, leads)
        
        # Should have 12 messages total (3 leads × 4 mails)
        assert result["total_messages"] == 12
        
        # Check queue structure
        queue = self.scheduler.domain_queues["punthelder-marketing.nl"]
        assert len(queue) == 12
        
        # Group by mail number
        mail_counts = {}
        for item in queue:
            mail_num = item["message"].mail_number
            mail_counts[mail_num] = mail_counts.get(mail_num, 0) + 1
        
        # Should have 3 of each mail (1 per lead)
        for mail_num in [1, 2, 3, 4]:
            assert mail_counts[mail_num] == 3
        
        # Check alias distribution
        alias_counts = {}
        for item in queue:
            alias = item["message"].alias
            alias_counts[alias] = alias_counts.get(alias, 0) + 1
        
        # Should have 6 Christian mails (M1+M2) and 6 Victor mails (M3+M4)
        assert alias_counts["christian"] == 6  # 3 leads × 2 mails
        assert alias_counts["victor"] == 6     # 3 leads × 2 mails
    
    def test_fifo_queue_ordering(self):
        """Test: FIFO queueing per domein werkt correct."""
        # Schedule campaign with leads at different times
        campaign = Campaign(
            id="fifo-campaign",
            name="FIFO Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)
        )
        
        # Schedule with multiple leads
        leads = ["lead-1", "lead-2", "lead-3"]
        result = self.scheduler.schedule_campaign(campaign, leads)
        
        # Get messages ready to send at 08:00
        current_time = datetime(2025, 9, 29, 8, 0, tzinfo=self.tz)
        ready_messages = self.scheduler.get_next_messages_to_send(
            "punthelder-marketing.nl", 
            current_time
        )
        
        # Should get first message (FIFO)
        assert len(ready_messages) == 1
        first_message = ready_messages[0]
        assert first_message.mail_number == 1
        
        # Try again after 20 minutes (throttle period)
        current_time += timedelta(minutes=20)
        ready_messages = self.scheduler.get_next_messages_to_send(
            "punthelder-marketing.nl", 
            current_time
        )
        
        # Should get second message
        assert len(ready_messages) == 1
        second_message = ready_messages[0]
        assert second_message.mail_number == 1  # Still mail 1, different lead
        assert second_message.lead_id != first_message.lead_id
    
    def test_weekend_skip_comprehensive(self):
        """Test: Comprehensive weekend skip scenario."""
        # Start campaign on Friday afternoon
        friday = datetime(2025, 10, 3, 14, 0, tzinfo=self.tz)  # Friday 14:00
        
        campaign = Campaign(
            id="weekend-campaign",
            name="Weekend Campaign",
            template_id="v1_mail1",
            domain="punthelder-marketing.nl",
            status=CampaignStatus.draft,
            start_at=friday
        )
        
        result = self.scheduler.schedule_campaign(campaign, ["lead-1"])
        mail_schedule = result["mail_schedule"]
        
        # Mail 1: Friday (same day)
        assert mail_schedule[1].strftime("%a") == "Fri"
        assert mail_schedule[1].date() == friday.date()
        
        # Mail 2: Monday next week (+3 workdays, skip weekend)
        mail2_date = mail_schedule[2]
        assert mail2_date.strftime("%a") == "Mon"
        
        # Should be the Monday after the weekend
        expected_monday = friday.date() + timedelta(days=4)  # Fri -> Mon
        assert mail2_date.date() == expected_monday
        
        # Mail 3: Thursday next week (+6 workdays from Friday)
        mail3_date = mail_schedule[3]
        assert mail3_date.strftime("%a") == "Thu"
        
        # Mail 4: Tuesday week after (+9 workdays from Friday)
        mail4_date = mail_schedule[4]
        assert mail4_date.strftime("%a") == "Tue"
    
    def test_slot_alignment_to_grid(self):
        """Test: Slots worden correct uitgelijnd op :00/:20/:40 grid."""
        # Start at misaligned time
        misaligned_time = datetime(2025, 9, 29, 8, 15, tzinfo=self.tz)  # 08:15
        
        next_slot = SENDING_POLICY.get_next_valid_slot(misaligned_time)
        
        # Should align to next 20-minute mark (08:20)
        assert next_slot.minute in [0, 20, 40]
        assert next_slot.minute == 20
        assert next_slot.hour == 8
        
        # Test alignment at different times
        test_times = [
            (datetime(2025, 9, 29, 8, 5, tzinfo=self.tz), 20),   # 08:05 -> 08:20
            (datetime(2025, 9, 29, 8, 25, tzinfo=self.tz), 40),  # 08:25 -> 08:40
            (datetime(2025, 9, 29, 8, 45, tzinfo=self.tz), 0),   # 08:45 -> 09:00
        ]
        
        for test_time, expected_minute in test_times:
            aligned = SENDING_POLICY.get_next_valid_slot(test_time)
            assert aligned.minute == expected_minute
    
    def test_daily_cap_enforcement(self):
        """Test: Dagcap van 27 emails per domein wordt gehandhaafd."""
        # Generate 27 slots for one day
        slots = SENDING_POLICY.get_daily_slots()
        assert len(slots) == 27
        
        # First slot should be 08:00
        assert slots[0] == "08:00"
        
        # Last slot should be 16:40 (27th slot)
        assert slots[-1] == "16:40"
        
        # Verify 20-minute intervals
        for i in range(1, len(slots)):
            prev_time = datetime.strptime(slots[i-1], "%H:%M").time()
            curr_time = datetime.strptime(slots[i], "%H:%M").time()
            
            prev_dt = datetime.combine(datetime.today(), prev_time)
            curr_dt = datetime.combine(datetime.today(), curr_time)
            
            diff_minutes = (curr_dt - prev_dt).total_seconds() / 60
            assert diff_minutes == 20
        
        # Verify no slots after 16:40
        last_slot_time = datetime.strptime(slots[-1], "%H:%M").time()
        window_end = datetime.strptime("17:00", "%H:%M").time()
        
        assert last_slot_time < window_end
