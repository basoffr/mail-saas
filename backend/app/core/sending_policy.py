from dataclasses import dataclass
from typing import List
from datetime import time, datetime, timedelta
import pytz


@dataclass(frozen=True)
class SendingPolicy:
    """Hard-coded sending policy - NOT editable via API"""
    
    timezone: str = "Europe/Amsterdam"
    days: List[str] = None
    window_from: str = "08:00"
    window_to: str = "17:00"  # Exclusive - last slot at 16:40
    grace_to: str = "18:00"   # Grace period for delayed sends
    slot_every_minutes: int = 20
    daily_cap_per_domain: int = 27
    throttle_scope: str = "per_domain"
    
    def __post_init__(self):
        if self.days is None:
            object.__setattr__(self, 'days', ["Mon", "Tue", "Wed", "Thu", "Fri"])
    
    def get_daily_slots(self) -> List[str]:
        """Generate all valid sending slots for a day"""
        slots = []
        start_hour, start_min = map(int, self.window_from.split(':'))
        end_hour, end_min = map(int, self.window_to.split(':'))
        
        current_time = time(start_hour, start_min)
        end_time = time(end_hour, end_min)
        
        while current_time < end_time:
            slots.append(current_time.strftime("%H:%M"))
            # Add 20 minutes
            dt = datetime.combine(datetime.today(), current_time)
            dt += timedelta(minutes=self.slot_every_minutes)
            current_time = dt.time()
            
            # Safety check to prevent infinite loop
            if len(slots) >= 50:
                break
                
        return slots
    
    def is_valid_sending_day(self, date: datetime) -> bool:
        """Check if date is a valid sending day"""
        day_name = date.strftime("%a")
        return day_name in self.days
    
    def is_within_grace_period(self, current_time: datetime) -> bool:
        """Check if current time is within grace period"""
        tz = pytz.timezone(self.timezone)
        local_time = current_time.astimezone(tz)
        grace_hour, grace_min = map(int, self.grace_to.split(':'))
        grace_time = time(grace_hour, grace_min)
        
        return local_time.time() <= grace_time
    
    def get_next_valid_slot(self, from_datetime: datetime) -> datetime:
        """Get next valid sending slot from given datetime"""
        tz = pytz.timezone(self.timezone)
        current = from_datetime.astimezone(tz)
        
        # If weekend, move to next Monday
        weekend_skipped = False
        while not self.is_valid_sending_day(current):
            current += timedelta(days=1)
            weekend_skipped = True
        
        # If we skipped weekend, reset to window start
        if weekend_skipped:
            window_start_hour, window_start_min = map(int, self.window_from.split(':'))
            current = current.replace(hour=window_start_hour, minute=window_start_min, second=0, microsecond=0)
        
        # If before window, set to window start
        window_start_hour, window_start_min = map(int, self.window_from.split(':'))
        if current.time() < time(window_start_hour, window_start_min):
            current = current.replace(hour=window_start_hour, minute=window_start_min, second=0, microsecond=0)
        
        # If after window, move to next valid day
        window_end_hour, window_end_min = map(int, self.window_to.split(':'))
        if current.time() >= time(window_end_hour, window_end_min):
            current += timedelta(days=1)
            current = current.replace(hour=window_start_hour, minute=window_start_min, second=0, microsecond=0)
            # Check if new day is valid
            while not self.is_valid_sending_day(current):
                current += timedelta(days=1)
                current = current.replace(hour=window_start_hour, minute=window_start_min, second=0, microsecond=0)
        
        # Align to slot grid (:00, :20, :40)
        minutes = current.minute
        if minutes % 20 != 0:
            # Round up to next 20-minute mark
            next_slot_minutes = ((minutes // 20) + 1) * 20
            if next_slot_minutes >= 60:
                current += timedelta(hours=1)
                current = current.replace(minute=0)
            else:
                current = current.replace(minute=next_slot_minutes)
        
        return current


# Global singleton instance
SENDING_POLICY = SendingPolicy()
