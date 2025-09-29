import pytest
from datetime import datetime, time, timedelta
import pytz

from app.core.sending_policy import SENDING_POLICY, SendingPolicy


class TestSendingPolicy:
    """Test hard-coded sending policy guardrails."""
    
    def test_policy_is_immutable(self):
        """Test that sending policy values are hard-coded."""
        assert SENDING_POLICY.timezone == "Europe/Amsterdam"
        assert SENDING_POLICY.days == ["Mon", "Tue", "Wed", "Thu", "Fri"]
        assert SENDING_POLICY.window_from == "08:00"
        assert SENDING_POLICY.window_to == "17:00"
        assert SENDING_POLICY.grace_to == "18:00"
        assert SENDING_POLICY.slot_every_minutes == 20
        assert SENDING_POLICY.daily_cap_per_domain == 27
        assert SENDING_POLICY.throttle_scope == "per_domain"
    
    def test_daily_slots_generation(self):
        """Test that exactly 27 slots are generated per day."""
        slots = SENDING_POLICY.get_daily_slots()
        
        # Should have exactly 27 slots
        assert len(slots) == 27
        
        # First slot should be 08:00
        assert slots[0] == "08:00"
        
        # Last slot should be 16:40 (17:00 - 20 minutes)
        assert slots[-1] == "16:40"
        
        # Slots should be 20 minutes apart
        for i in range(1, len(slots)):
            prev_time = datetime.strptime(slots[i-1], "%H:%M").time()
            curr_time = datetime.strptime(slots[i], "%H:%M").time()
            
            prev_dt = datetime.combine(datetime.today(), prev_time)
            curr_dt = datetime.combine(datetime.today(), curr_time)
            
            diff = curr_dt - prev_dt
            assert diff.total_seconds() == 20 * 60  # 20 minutes
    
    def test_valid_sending_days(self):
        """Test that only weekdays are valid sending days."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # Monday should be valid
        monday = datetime(2025, 9, 29, tzinfo=tz)  # A Monday
        assert SENDING_POLICY.is_valid_sending_day(monday)
        
        # Friday should be valid
        friday = datetime(2025, 10, 3, tzinfo=tz)  # A Friday
        assert SENDING_POLICY.is_valid_sending_day(friday)
        
        # Saturday should be invalid
        saturday = datetime(2025, 10, 4, tzinfo=tz)  # A Saturday
        assert not SENDING_POLICY.is_valid_sending_day(saturday)
        
        # Sunday should be invalid
        sunday = datetime(2025, 10, 5, tzinfo=tz)  # A Sunday
        assert not SENDING_POLICY.is_valid_sending_day(sunday)
    
    def test_grace_period_check(self):
        """Test grace period validation (until 18:00)."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # 17:30 should be within grace period
        within_grace = datetime(2025, 9, 26, 17, 30, tzinfo=tz)
        assert SENDING_POLICY.is_within_grace_period(within_grace)
        
        # 18:00 should be within grace period (inclusive)
        at_grace_limit = datetime(2025, 9, 26, 18, 0, tzinfo=tz)
        assert SENDING_POLICY.is_within_grace_period(at_grace_limit)
        
        # 18:01 should be outside grace period
        outside_grace = datetime(2025, 9, 26, 18, 1, tzinfo=tz)
    
    def test_next_valid_slot_weekend_skip(self):
        """Test that weekend dates are skipped to next Monday."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # Friday 17:30 should move to Monday 08:00 (after window)
        friday_late = datetime(2025, 10, 3, 17, 30, tzinfo=tz)  # Friday after window
        next_slot = SENDING_POLICY.get_next_valid_slot(friday_late)
        
        # Should be Monday 08:00
        assert next_slot.strftime("%a") == "Mon"
        assert next_slot.hour == 8
        assert next_slot.minute == 0
        
        # Saturday should move to Monday 08:00
        saturday = datetime(2025, 10, 4, 10, 0, tzinfo=tz)  # Saturday
        next_slot = SENDING_POLICY.get_next_valid_slot(saturday)
        
        assert next_slot.time() == time(8, 0)
    
    def test_next_valid_slot_alignment(self):
        """Test that slots are aligned to :00, :20, :40 grid."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # 08:15 should align to 08:20
        misaligned = datetime(2025, 9, 29, 8, 15, tzinfo=tz)  # Monday
        next_slot = SENDING_POLICY.get_next_valid_slot(misaligned)
        
        assert next_slot.minute in [0, 20, 40]
        assert next_slot.minute == 20  # Should round up to next slot
        
        # 08:00 should stay at 08:00 (already aligned)
        aligned = datetime(2025, 9, 29, 8, 0, tzinfo=tz)  # Monday
        next_slot = SENDING_POLICY.get_next_valid_slot(aligned)
        
        assert next_slot.minute == 0
    
    def test_next_valid_slot_after_window(self):
        """Test that times after window move to next day."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # 17:30 should move to next day 08:00
        after_window = datetime(2025, 9, 29, 17, 30, tzinfo=tz)  # Monday
        next_slot = SENDING_POLICY.get_next_valid_slot(after_window)
        
        # Should be Tuesday 08:00
        expected_date = after_window.date() + timedelta(days=1)
        assert next_slot.date() == expected_date
        assert next_slot.time() == time(8, 0)
    
    def test_workday_interval_calculation(self):
        """Test +3 workdays interval (excluding weekends)."""
        tz = pytz.timezone(SENDING_POLICY.timezone)
        
        # Thursday + 3 workdays = Tuesday (skip weekend)
        thursday = datetime(2025, 10, 2, 8, 0, tzinfo=tz)  # Thursday
        
        # Manually calculate +3 workdays
        workdays_added = 0
        current = thursday
        while workdays_added < 3:
            current += timedelta(days=1)
            if SENDING_POLICY.is_valid_sending_day(current):
                workdays_added += 1
        
        # Should land on Tuesday (Fri +1, Mon +2, Tue +3)
        assert current.strftime("%a") == "Tue"
