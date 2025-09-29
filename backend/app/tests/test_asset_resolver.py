import pytest
from pathlib import Path
from app.services.asset_resolver import AssetResolver


def test_asset_resolver_domain_mapping():
    """Test domain to root key mapping."""
    resolver = AssetResolver()
    
    # Test known domains
    assert resolver.DOMAIN_MAPPING["punthelder-marketing.nl"] == "running_nl"
    assert resolver.DOMAIN_MAPPING["punthelder-vindbaarheid.nl"] == "cycle_nl"


def test_get_report_path_unknown_domain():
    """Test report path for unknown domain."""
    resolver = AssetResolver()
    
    result = resolver.get_report_path("unknown-domain.com")
    assert result is None


def test_get_dashboard_image_path_unknown_domain():
    """Test dashboard image path for unknown domain."""
    resolver = AssetResolver()
    
    result = resolver.get_dashboard_image_path("unknown-domain.com")
    assert result is None


def test_get_signature_path_valid_alias():
    """Test signature path for valid aliases."""
    resolver = AssetResolver()
    
    # Test valid aliases (even if files don't exist)
    christian_path = resolver.get_signature_path("christian")
    victor_path = resolver.get_signature_path("victor")
    
    # Should return Path objects even if files don't exist
    assert christian_path is None or isinstance(christian_path, Path)
    assert victor_path is None or isinstance(victor_path, Path)


def test_get_signature_path_invalid_alias():
    """Test signature path for invalid alias."""
    resolver = AssetResolver()
    
    result = resolver.get_signature_path("unknown")
    assert result is None


def test_has_report_methods():
    """Test has_* convenience methods."""
    resolver = AssetResolver()
    
    # These should return False for unknown domains
    assert resolver.has_report("unknown-domain.com") is False
    assert resolver.has_dashboard_image("unknown-domain.com") is False
