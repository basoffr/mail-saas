import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Mock auth header
AUTH_HEADER = {"Authorization": "Bearer mock-jwt-token"}


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"data": {"ok": True}, "error": None}


def test_get_settings_requires_auth():
    """Test that settings endpoint requires authentication"""
    response = client.get("/api/v1/settings")
    assert response.status_code in [401, 403]  # Either is acceptable


def test_get_settings_ok():
    """Test getting settings successfully"""
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "error" in data
    assert data["error"] is None
    
    settings = data["data"]
    
    # Check all required fields are present
    assert "timezone" in settings
    assert "window" in settings
    assert "throttle" in settings
    assert "domains" in settings
    assert "unsubscribeText" in settings
    assert "unsubscribeUrl" in settings
    assert "trackingPixelEnabled" in settings
    assert "emailInfra" in settings
    
    # Check default values
    assert settings["timezone"] == "Europe/Amsterdam"
    assert settings["unsubscribeText"] == "Uitschrijven"
    assert settings["trackingPixelEnabled"] is True
    
    # Check window structure
    window = settings["window"]
    assert "days" in window
    assert "from" in window
    assert "to" in window
    assert window["from"] == "08:00"
    assert window["to"] == "17:00"
    
    # Check throttle structure
    throttle = settings["throttle"]
    assert "emailsPer" in throttle
    assert "minutes" in throttle
    assert throttle["emailsPer"] == 1
    assert throttle["minutes"] == 20
    
    # Check email infra structure
    email_infra = settings["emailInfra"]
    assert "current" in email_infra
    assert "provider" in email_infra
    assert "providerEnabled" in email_infra
    assert "dns" in email_infra
    assert email_infra["current"] == "SMTP"
    assert email_infra["providerEnabled"] is False


def test_update_settings_requires_auth():
    """Test that update settings endpoint requires authentication"""
    response = client.post("/api/v1/settings", json={"unsubscribeText": "Test"})
    assert response.status_code in [401, 403]  # Either is acceptable


def test_update_unsubscribe_text():
    """Test updating unsubscribe text successfully"""
    new_text = "Afmelden"
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"unsubscribeText": new_text}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["unsubscribeText"] == new_text


def test_update_tracking_toggle():
    """Test updating tracking pixel toggle"""
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"trackingPixelEnabled": False}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["trackingPixelEnabled"] is False


def test_update_both_editable_fields():
    """Test updating both editable fields at once"""
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={
            "unsubscribeText": "Uitschrijven hier",
            "trackingPixelEnabled": True
        }
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["unsubscribeText"] == "Uitschrijven hier"
    assert data["data"]["trackingPixelEnabled"] is True


def test_update_invalid_unsubscribe_text_empty():
    """Test updating with empty unsubscribe text fails"""
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"unsubscribeText": ""}
    )
    assert response.status_code == 422


def test_update_invalid_unsubscribe_text_too_long():
    """Test updating with too long unsubscribe text fails"""
    long_text = "a" * 51  # 51 characters, over the limit
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"unsubscribeText": long_text}
    )
    assert response.status_code == 422


def test_update_readonly_fields_fails():
    """Test that trying to update read-only fields doesn't change them"""
    # Get original domains
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    original_domains = response.json()["data"]["domains"]
    
    # Try to update domains (read-only) - should be ignored
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"domains": ["new-domain.com"]}
    )
    assert response.status_code == 200
    
    # Verify domains didn't change
    assert response.json()["data"]["domains"] == original_domains


def test_update_provider_fails():
    """Test that trying to update provider doesn't change it"""
    # Get original provider
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    original_provider = response.json()["data"]["emailInfra"]["current"]
    
    # Try to update provider (read-only) - should be ignored
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"provider": "Postmark"}
    )
    assert response.status_code == 200
    
    # Verify provider didn't change
    assert response.json()["data"]["emailInfra"]["current"] == original_provider


def test_update_timezone_fails():
    """Test that trying to update timezone doesn't change it"""
    # Get original timezone
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    original_timezone = response.json()["data"]["timezone"]
    
    # Try to update timezone (read-only) - should be ignored
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"timezone": "UTC"}
    )
    assert response.status_code == 200
    
    # Verify timezone didn't change
    assert response.json()["data"]["timezone"] == original_timezone


def test_settings_persistence():
    """Test that settings updates persist across requests"""
    # Update unsubscribe text
    new_text = "Klik hier om uit te schrijven"
    response = client.post(
        "/api/v1/settings",
        headers=AUTH_HEADER,
        json={"unsubscribeText": new_text}
    )
    assert response.status_code == 200
    
    # Get settings again and verify persistence
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    assert data["data"]["unsubscribeText"] == new_text


def test_unsubscribe_url_generation():
    """Test that unsubscribe URL is generated"""
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    unsubscribe_url = data["data"]["unsubscribeUrl"]
    
    assert unsubscribe_url.startswith("https://")
    assert "unsubscribe" in unsubscribe_url
    assert "token=" in unsubscribe_url


def test_dns_status_structure():
    """Test DNS status structure in response"""
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    dns = data["data"]["emailInfra"]["dns"]
    
    assert "spf" in dns
    assert "dkim" in dns
    assert "dmarc" in dns
    assert isinstance(dns["spf"], bool)
    assert isinstance(dns["dkim"], bool)
    assert isinstance(dns["dmarc"], bool)


def test_domains_list():
    """Test that domains list is present and has expected structure"""
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    domains = data["data"]["domains"]
    
    assert isinstance(domains, list)
    assert len(domains) == 4  # Hard-coded 4 Punthelder domains in MVP
    assert all(isinstance(domain, str) for domain in domains)
    assert all("punthelder-" in domain for domain in domains)  # Punthelder domain validation
    assert all(".nl" in domain for domain in domains)  # Dutch domains


def test_domains_config_structure():
    """Test extended domain configuration structure"""
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    domains_config = data["data"]["domainsConfig"]
    
    assert isinstance(domains_config, list)
    assert len(domains_config) == 4  # 4 Punthelder domains
    
    # Test first domain structure
    domain = domains_config[0]
    assert "domain" in domain
    assert "displayName" in domain
    assert "smtpHost" in domain
    assert "smtpPort" in domain
    assert "useTls" in domain
    assert "aliases" in domain
    assert "dailyLimit" in domain
    assert "throttleMinutes" in domain
    assert "dnsStatus" in domain
    assert "reputationScore" in domain
    assert "active" in domain
    
    # Test aliases structure
    aliases = domain["aliases"]
    assert isinstance(aliases, list)
    assert len(aliases) == 2  # Christian & Victor per domain
    
    alias = aliases[0]
    assert "email" in alias
    assert "name" in alias
    assert "active" in alias
    
    # Test DNS status structure
    dns_status = domain["dnsStatus"]
    assert "spf" in dns_status
    assert "dkim" in dns_status
    assert "dmarc" in dns_status


def test_domain_aliases_content():
    """Test that domain aliases contain Christian and Victor"""
    response = client.get("/api/v1/settings", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    domains_config = data["data"]["domainsConfig"]
    
    for domain_config in domains_config:
        aliases = domain_config["aliases"]
        assert len(aliases) == 2
        
        # Check that we have Christian and Victor
        emails = [alias["email"] for alias in aliases]
        names = [alias["name"] for alias in aliases]
        
        assert any("christian@" in email for email in emails)
        assert any("victor@" in email for email in emails)
        assert any("Christian" in name for name in names)
        assert any("Victor" in name for name in names)
