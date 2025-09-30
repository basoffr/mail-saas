"""
Unit tests for flow-based dry-run planning.
Tests that dry_run_planning matches actual campaign scheduling logic.
"""
import pytest
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.campaign_scheduler import CampaignScheduler


class TestDryRunFlowBased:
    """Test dry_run_planning with flow-based scheduling."""
    
    def setup_method(self):
        """Create scheduler instance."""
        self.scheduler = CampaignScheduler()
        self.tz = ZoneInfo("Europe/Amsterdam")
    
    def test_dry_run_with_single_lead(self):
        """Test dry-run for single lead (should have 4 mails across 9 workdays)."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)  # Wednesday
        
        result = self.scheduler.dry_run_planning(
            lead_count=1,
            domains=["punthelder-marketing.nl"],
            start_at=start_at
        )
        
        # Single lead should generate 4 mails total
        total_mails = sum(day.planned for day in result)
        assert total_mails == 4, f"Expected 4 mails, got {total_mails}"
        
        # Mails should be spread across days (not all on same day)
        assert len(result) > 1, "Mails should be spread across multiple days"
        
    def test_dry_run_with_multiple_leads(self):
        """Test dry-run for 10 leads (should have 40 mails total)."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)
        
        result = self.scheduler.dry_run_planning(
            lead_count=10,
            domains=["punthelder-marketing.nl"],
            start_at=start_at
        )
        
        # 10 leads × 4 mails = 40 total mails
        total_mails = sum(day.planned for day in result)
        assert total_mails == 40, f"Expected 40 mails, got {total_mails}"
        
    def test_dry_run_respects_flow_timing(self):
        """Test that dry-run respects flow timing (workday offsets)."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)  # Wednesday
        
        result = self.scheduler.dry_run_planning(
            lead_count=1,
            domains=["punthelder-seo.nl"],
            start_at=start_at
        )
        
        # Check dates are sequential
        dates = sorted([day.date for day in result])
        assert len(dates) == 4, "Should have mails on 4 different days"
        
        # First mail should be on start date
        assert dates[0] == "2025-10-01"
        
    def test_dry_run_with_no_domain(self):
        """Test dry-run with empty domains list."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)
        
        result = self.scheduler.dry_run_planning(
            lead_count=5,
            domains=[],
            start_at=start_at
        )
        
        # Should return empty result
        assert len(result) == 0
        
    def test_dry_run_with_unknown_domain_falls_back(self):
        """Test dry-run with unknown domain uses fallback logic."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)
        
        result = self.scheduler.dry_run_planning(
            lead_count=3,
            domains=["unknown-domain.com"],
            start_at=start_at
        )
        
        # Fallback should still return results
        assert len(result) > 0
        total_mails = sum(day.planned for day in result)
        assert total_mails == 3  # Fallback uses 1 mail per lead
        
    def test_dry_run_format(self):
        """Test dry-run return format."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)
        
        result = self.scheduler.dry_run_planning(
            lead_count=2,
            domains=["punthelder-vindbaarheid.nl"],
            start_at=start_at
        )
        
        # Check result format
        assert isinstance(result, list)
        assert all(hasattr(day, 'date') for day in result)
        assert all(hasattr(day, 'planned') for day in result)
        
        # Dates should be sorted
        dates = [day.date for day in result]
        assert dates == sorted(dates)
        
    def test_dry_run_consistency(self):
        """Test dry-run produces consistent results for same input."""
        start_at = datetime(2025, 10, 1, 8, 0, tzinfo=self.tz)
        
        result1 = self.scheduler.dry_run_planning(
            lead_count=5,
            domains=["punthelder-zoekmachine.nl"],
            start_at=start_at
        )
        
        result2 = self.scheduler.dry_run_planning(
            lead_count=5,
            domains=["punthelder-zoekmachine.nl"],
            start_at=start_at
        )
        
        # Results should be identical
        assert len(result1) == len(result2)
        for day1, day2 in zip(result1, result2):
            assert day1.date == day2.date
            assert day1.planned == day2.planned


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
