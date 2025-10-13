"""Stream A/B calculator for dual-stream scheduling.

Stream A (M1, M3): :00/:20/:40
Stream B (M2, M4): :10/:30/:50
"""
from datetime import datetime, timedelta
from typing import Literal

StreamType = Literal["A", "B"]


def get_stream_for_mail(mail_number: int) -> StreamType:
    """Get stream (A or B) for mail number.
    
    Args:
        mail_number: Mail number (1, 2, 3, or 4)
        
    Returns:
        "A" for M1/M3, "B" for M2/M4
        
    Raises:
        ValueError: If mail_number is not 1-4
    """
    if mail_number in [1, 3]:
        return "A"
    elif mail_number in [2, 4]:
        return "B"
    else:
        raise ValueError(f"Invalid mail number: {mail_number}. Must be 1-4.")


def get_stream_slot_minutes(stream: StreamType) -> list[int]:
    """Get minute offsets for a stream.
    
    Args:
        stream: Stream type ("A" or "B")
        
    Returns:
        List of valid minutes for the stream
    """
    if stream == "A":
        return [0, 20, 40]  # :00, :20, :40
    else:  # stream == "B"
        return [10, 30, 50]  # :10, :30, :50


def snap_to_stream_slot(dt: datetime, stream: StreamType) -> datetime:
    """Snap datetime to nearest valid slot in stream.
    
    Args:
        dt: Datetime to snap
        stream: Stream type ("A" or "B")
        
    Returns:
        Datetime snapped to nearest stream slot
        
    Example:
        >>> snap_to_stream_slot(datetime(2025, 10, 13, 8, 15), "A")
        datetime(2025, 10, 13, 8, 20)  # Snaps to :20
        
        >>> snap_to_stream_slot(datetime(2025, 10, 13, 8, 15), "B")
        datetime(2025, 10, 13, 8, 30)  # Snaps to :30
    """
    stream_minutes = get_stream_slot_minutes(stream)
    current_minute = dt.minute
    
    # Find next valid minute in stream
    for minute in stream_minutes:
        if current_minute <= minute:
            return dt.replace(minute=minute, second=0, microsecond=0)
    
    # No valid minute found in current hour, go to next hour's first slot
    next_hour = dt.replace(minute=stream_minutes[0], second=0, microsecond=0)
    return next_hour + timedelta(hours=1)


def is_valid_stream_time(dt: datetime, stream: StreamType) -> bool:
    """Check if datetime is on a valid stream slot.
    
    Args:
        dt: Datetime to check
        stream: Stream type ("A" or "B")
        
    Returns:
        True if datetime is on a valid stream slot
    """
    stream_minutes = get_stream_slot_minutes(stream)
    return dt.minute in stream_minutes
