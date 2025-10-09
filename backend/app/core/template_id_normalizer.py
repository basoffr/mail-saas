"""
Template ID Normalizer
Converts frontend template IDs (v1m1, v2m3) to backend format (v1_mail1, v2_mail3)
"""
import re
from typing import Optional


def normalize_template_id(template_id: str) -> str:
    """
    Normalize template IDs to v{version}_mail{number} format.
    Supports both compact (v1m1) and verbose (v1_mail1) formats.
    
    Examples:
        v1m1 -> v1_mail1
        v2m3 -> v2_mail3
        v1_mail1 -> v1_mail1 (unchanged)
        v3_mail2 -> v3_mail2 (unchanged)
    
    Args:
        template_id: Template identifier from frontend or database
    
    Returns:
        Normalized template ID in v{version}_mail{number} format
    """
    if not template_id:
        return template_id
    
    # Pattern: v{digit}m{digit} -> v{digit}_mail{digit}
    # Matches: v1m1, v2m3, v4m2, etc.
    match = re.match(r'^v(\d+)m(\d+)$', template_id)
    if match:
        version, mail_num = match.groups()
        normalized = f"v{version}_mail{mail_num}"
        return normalized
    
    # Already in correct format (v1_mail1) or invalid format
    # Return unchanged
    return template_id


def validate_template_id(template_id: str) -> bool:
    """
    Validate if template ID matches expected format.
    
    Valid formats:
        - v1m1, v2m3 (compact)
        - v1_mail1, v2_mail3 (verbose)
    
    Args:
        template_id: Template identifier to validate
    
    Returns:
        True if valid format, False otherwise
    """
    if not template_id:
        return False
    
    # Check compact format: v{digit}m{digit}
    compact_match = re.match(r'^v(\d+)m(\d+)$', template_id)
    if compact_match:
        return True
    
    # Check verbose format: v{digit}_mail{digit}
    verbose_match = re.match(r'^v(\d+)_mail(\d+)$', template_id)
    if verbose_match:
        return True
    
    return False


def extract_version_and_mail(template_id: str) -> Optional[tuple[int, int]]:
    """
    Extract version and mail number from template ID.
    
    Args:
        template_id: Template identifier
    
    Returns:
        Tuple of (version, mail_number) or None if invalid format
    
    Examples:
        v1m1 -> (1, 1)
        v2_mail3 -> (2, 3)
        invalid -> None
    """
    if not template_id:
        return None
    
    # Try compact format
    compact_match = re.match(r'^v(\d+)m(\d+)$', template_id)
    if compact_match:
        version, mail_num = compact_match.groups()
        return (int(version), int(mail_num))
    
    # Try verbose format
    verbose_match = re.match(r'^v(\d+)_mail(\d+)$', template_id)
    if verbose_match:
        version, mail_num = verbose_match.groups()
        return (int(version), int(mail_num))
    
    return None
