import pytest
from datetime import datetime, timedelta
import pytz

from app.core.campaign_flows import (
    DOMAIN_FLOWS, get_flow_for_domain, get_all_flows, 
    calculate_mail_schedule, get_alias_mapping, get_followup_headers,
    validate_domain, get_flow_summary
)


class TestCampaignFlows:
    """Test hard-coded campaign flows."""
    
    def test_domain_flows_exist(self):
        """Test that all 4 domain flows exist."""
        expected_domains = [
            "punthelder-marketing.nl",
            "punthelder-vindbaarheid.nl", 
            "punthelder-seo.nl",
            "punthelder-zoekmachine.nl"
        ]
        
        assert len(DOMAIN_FLOWS) == 4
        
        for domain in expected_domains:
            assert domain in DOMAIN_FLOWS
    
    def test_flow_versions(self):
        """Test that flows have correct versions."""
        assert DOMAIN_FLOWS["punthelder-marketing.nl"].version == 1
        assert DOMAIN_FLOWS["punthelder-vindbaarheid.nl"].version == 2
        assert DOMAIN_FLOWS["punthelder-seo.nl"].version == 3
        assert DOMAIN_FLOWS["punthelder-zoekmachine.nl"].version == 4
    
    def test_flow_steps_structure(self):
        """Test that all flows have correct step structure."""
        for domain, flow in DOMAIN_FLOWS.items():
            # Each flow should have 4 steps
            assert len(flow.steps) == 4
            
            # Check mail numbers
            mail_numbers = [step.mail_number for step in flow.steps]
            assert mail_numbers == [1, 2, 3, 4]
            
            # Check aliases (M1+M2=christian, M3+M4=victor)
            assert flow.steps[0].alias == "christian"  # Mail 1
            assert flow.steps[1].alias == "christian"  # Mail 2
            assert flow.steps[2].alias == "victor"     # Mail 3
            assert flow.steps[3].alias == "victor"     # Mail 4
            
            # Check workday offsets (+3 workdays interval)
            assert flow.steps[0].workdays_offset == 0  # Day 0
            assert flow.steps[1].workdays_offset == 3  # Day +3
            assert flow.steps[2].workdays_offset == 6  # Day +6
            assert flow.steps[3].workdays_offset == 9  # Day +9
    
    def test_get_flow_for_domain(self):
        """Test getting flow for specific domain."""
        flow = get_flow_for_domain("punthelder-marketing.nl")
        assert flow is not None
        assert flow.version == 1
        assert flow.domain == "punthelder-marketing.nl"
        
        # Non-existent domain should return None
        assert get_flow_for_domain("nonexistent.com") is None
    
    def test_get_all_flows(self):
        """Test getting all flows."""
        flows = get_all_flows()
        assert len(flows) == 4
        assert isinstance(flows, dict)
        
        # Should be a copy, not the original
        flows.clear()
        assert len(DOMAIN_FLOWS) == 4  # Original should be unchanged
    
    def test_flow_step_methods(self):
        """Test flow step helper methods."""
        flow = get_flow_for_domain("punthelder-marketing.nl")
        
        # Test get_step_by_mail_number
        step1 = flow.get_step_by_mail_number(1)
        assert step1.alias == "christian"
        assert step1.workdays_offset == 0
        
        step3 = flow.get_step_by_mail_number(3)
        assert step3.alias == "victor"
        assert step3.workdays_offset == 6
        
        # Non-existent mail number
        assert flow.get_step_by_mail_number(99) is None
        
        # Test get_alias_for_mail
        assert flow.get_alias_for_mail(1) == "christian"
        assert flow.get_alias_for_mail(2) == "christian"
        assert flow.get_alias_for_mail(3) == "victor"
        assert flow.get_alias_for_mail(4) == "victor"
        assert flow.get_alias_for_mail(99) == "christian"  # Default fallback
    
    def test_calculate_mail_schedule(self):
        """Test mail schedule calculation with workdays."""
        flow = get_flow_for_domain("punthelder-marketing.nl")
        tz = pytz.timezone("Europe/Amsterdam")
        
        # Start on a Monday
        monday = datetime(2025, 9, 29, 8, 0, tzinfo=tz)  # Monday 08:00
        schedule = calculate_mail_schedule(monday, flow)
        
        assert len(schedule) == 4
        
        # Mail 1 should be same day (Monday)
        assert schedule[1].strftime("%a") == "Mon"
        
        # Mail 2 should be +3 workdays = Thursday
        assert schedule[2].strftime("%a") == "Thu"
        
        # Mail 3 should be +6 workdays = Tuesday (next week)
        assert schedule[3].strftime("%a") == "Tue"
        
        # Mail 4 should be +9 workdays = Friday (next week)
        assert schedule[4].strftime("%a") == "Fri"
    
    def test_calculate_mail_schedule_weekend_skip(self):
        """Test that weekends are skipped in schedule calculation."""
        flow = get_flow_for_domain("punthelder-marketing.nl")
        tz = pytz.timezone("Europe/Amsterdam")
        
        # Start on a Friday
        friday = datetime(2025, 10, 3, 8, 0, tzinfo=tz)  # Friday 08:00
        schedule = calculate_mail_schedule(friday, flow)
        
        # Mail 1 should be same day (Friday)
        assert schedule[1].strftime("%a") == "Fri"
        
        # Mail 2 should be +3 workdays = Wednesday (skip weekend)
        assert schedule[2].strftime("%a") == "Wed"
    
    def test_alias_mapping(self):
        """Test alias configuration."""
        mapping = get_alias_mapping()
        
        assert "christian" in mapping
        assert "victor" in mapping
        
        christian = mapping["christian"]
        assert christian["name"] == "Christian"
        assert christian["email"] == "christian@punthelder.nl"
        assert christian["role"] == "initial_contact"
        
        victor = mapping["victor"]
        assert victor["name"] == "Victor"
        assert victor["email"] == "victor@punthelder.nl"
        assert victor["role"] == "follow_up"
    
    def test_followup_headers(self):
        """Test From/Reply-To headers for follow-ups."""
        # Mail 1 & 2 (Christian mails)
        headers1 = get_followup_headers(1)
        assert headers1["from"] == "christian@punthelder.nl"
        assert headers1["reply_to"] == "christian@punthelder.nl"
        
        headers2 = get_followup_headers(2)
        assert headers2["from"] == "christian@punthelder.nl"
        assert headers2["reply_to"] == "christian@punthelder.nl"
        
        # Mail 3 & 4 (Victor mails) - From=Victor, Reply-To=Christian
        headers3 = get_followup_headers(3)
        assert headers3["from"] == "victor@punthelder.nl"
        assert headers3["reply_to"] == "christian@punthelder.nl"
        
        headers4 = get_followup_headers(4)
        assert headers4["from"] == "victor@punthelder.nl"
        assert headers4["reply_to"] == "christian@punthelder.nl"
    
    def test_validate_domain(self):
        """Test domain validation."""
        # Valid domains
        assert validate_domain("punthelder-marketing.nl")
        assert validate_domain("punthelder-vindbaarheid.nl")
        assert validate_domain("punthelder-seo.nl")
        assert validate_domain("punthelder-zoekmachine.nl")
        
        # Invalid domains
        assert not validate_domain("invalid.com")
        assert not validate_domain("")
        assert not validate_domain("punthelder.nl")  # Missing subdomain
    
    def test_flow_summary(self):
        """Test flow summary for UI display."""
        summary = get_flow_summary()
        
        assert len(summary) == 4
        
        for flow_summary in summary:
            assert "domain" in flow_summary
            assert "version" in flow_summary
            assert "total_mails" in flow_summary
            assert "aliases" in flow_summary
            assert "duration_workdays" in flow_summary
            assert "steps" in flow_summary
            
            # Check structure
            assert flow_summary["total_mails"] == 4
            assert set(flow_summary["aliases"]) == {"christian", "victor"}
            assert flow_summary["duration_workdays"] == 9  # Max offset
            
            # Check steps structure
            steps = flow_summary["steps"]
            assert len(steps) == 4
            
            for step in steps:
                assert "mail" in step
                assert "alias" in step
                assert "day" in step
    
    def test_flow_immutability(self):
        """Test that flows are immutable (frozen dataclasses)."""
        flow = get_flow_for_domain("punthelder-marketing.nl")
        
        # Should not be able to modify flow
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            flow.version = 999
        
        # Should not be able to modify steps
        with pytest.raises(Exception):
            flow.steps[0].alias = "hacker"
