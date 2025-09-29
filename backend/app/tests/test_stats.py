import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.services.stats import StatsService
from app.models.campaign import Message, Campaign, MessageStatus


client = TestClient(app)


@pytest.fixture
def mock_auth_header():
    """Mock JWT token for testing"""
    return {"Authorization": "Bearer mock_token"}


@pytest.fixture
def mock_auth():
    """Mock the auth dependency"""
    with patch("app.core.auth.require_auth") as mock:
        mock.return_value = {"sub": "test-user"}
        yield mock


def test_health():
    """Test health endpoint is accessible"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "ok"


def test_stats_summary_requires_auth():
    """Test that stats summary requires authentication"""
    response = client.get("/api/v1/stats/summary")
    assert response.status_code == 401


def test_stats_summary_ok(mock_auth):
    """Test successful stats summary retrieval"""
    response = client.get("/api/v1/stats/summary", headers={"Authorization": "Bearer mock_token"})
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "error" in data
    assert data["error"] is None
    
    summary = data["data"]
    assert "global_stats" in summary
    assert "domains" in summary
    assert "campaigns" in summary
    assert "timeline" in summary
    
    # Check global stats structure
    global_stats = summary["global_stats"]
    assert "total_sent" in global_stats
    assert "total_opens" in global_stats
    assert "open_rate" in global_stats
    assert "bounces" in global_stats
    assert isinstance(global_stats["total_sent"], int)
    assert isinstance(global_stats["open_rate"], float)


def test_stats_summary_with_date_range(mock_auth):
    """Test stats summary with date range"""
    from_date = (date.today() - timedelta(days=7)).isoformat()
    to_date = date.today().isoformat()
    
    response = client.get(
        f"/api/v1/stats/summary?from={from_date}&to={to_date}",
        headers=mock_auth_header
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None


def test_stats_summary_invalid_date_format(mock_auth):
    """Test stats summary with invalid date format"""
    response = client.get(
        "/api/v1/stats/summary?from=invalid-date",
        headers={"Authorization": "Bearer mock_token"}
    )
    assert response.status_code == 400
    assert "Invalid from date format" in response.json()["detail"]


def test_stats_summary_invalid_date_range(mock_auth):
    """Test stats summary with invalid date range"""
    from_date = date.today().isoformat()
    to_date = (date.today() - timedelta(days=1)).isoformat()
    
    response = client.get(
        f"/api/v1/stats/summary?from={from_date}&to={to_date}",
        headers=mock_auth_header
    )
    assert response.status_code == 400
    assert "From date must be before" in response.json()["detail"]


def test_stats_export_requires_auth():
    """Test that stats export requires authentication"""
    response = client.get("/api/v1/stats/export?scope=global")
    assert response.status_code == 401


def test_stats_export_global(mock_auth_header):
    """Test global stats CSV export"""
    response = client.get(
        "/api/v1/stats/export?scope=global",
        headers=mock_auth_header
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    
    # Check CSV content
    csv_content = response.text
    lines = csv_content.strip().split('\n')
    assert len(lines) >= 1  # At least header
    assert "Date,Sent,Opens,Bounces,Open_Rate" in lines[0]


def test_stats_export_domain(mock_auth_header):
    """Test domain stats CSV export"""
    response = client.get(
        "/api/v1/stats/export?scope=domain",
        headers=mock_auth_header
    )
    assert response.status_code == 200
    
    csv_content = response.text
    lines = csv_content.strip().split('\n')
    assert "Domain,Sent,Opens,Open_Rate,Bounces,Last_Activity" in lines[0]


def test_stats_export_campaign(mock_auth_header):
    """Test campaign stats CSV export"""
    response = client.get(
        "/api/v1/stats/export?scope=campaign",
        headers=mock_auth_header
    )
    assert response.status_code == 200
    
    csv_content = response.text
    lines = csv_content.strip().split('\n')
    assert "Campaign_ID,Campaign_Name,Sent,Opens,Open_Rate,Bounces,Status,Start_Date" in lines[0]


def test_stats_export_invalid_scope(mock_auth_header):
    """Test stats export with invalid scope"""
    response = client.get(
        "/api/v1/stats/export?scope=invalid",
        headers=mock_auth_header
    )
    assert response.status_code == 422  # Validation error


def test_domain_stats_endpoint(mock_auth_header):
    """Test optional domain stats endpoint"""
    response = client.get("/api/v1/stats/domains", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    
    if data["data"]:  # If there's data
        domain_stat = data["data"][0]
        assert "domain" in domain_stat
        assert "sent" in domain_stat
        assert "opens" in domain_stat
        assert "open_rate" in domain_stat


def test_campaign_stats_endpoint(mock_auth_header):
    """Test optional campaign stats endpoint"""
    response = client.get("/api/v1/stats/campaigns", headers=mock_auth_header)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    
    if data["data"]:  # If there's data
        campaign_stat = data["data"][0]
        assert "id" in campaign_stat
        assert "name" in campaign_stat
        assert "sent" in campaign_stat
        assert "opens" in campaign_stat


# Service-level tests
def test_stats_service_global_calculations():
    """Test StatsService global calculations"""
    service = StatsService()
    
    # Test with sample data
    summary = service.get_stats_summary()
    
    assert summary.global_stats.total_sent >= 0
    assert summary.global_stats.total_opens >= 0
    assert summary.global_stats.bounces >= 0
    assert 0 <= summary.global_stats.open_rate <= 1


def test_stats_service_domain_aggregation():
    """Test StatsService domain aggregation"""
    service = StatsService()
    
    summary = service.get_stats_summary()
    
    # Should have domain data
    assert len(summary.domains) > 0
    
    for domain_stat in summary.domains:
        assert domain_stat.domain
        assert domain_stat.sent >= 0
        assert domain_stat.opens >= 0
        assert 0 <= domain_stat.open_rate <= 1


def test_stats_service_campaign_aggregation():
    """Test StatsService campaign aggregation"""
    service = StatsService()
    
    summary = service.get_stats_summary()
    
    # Should have campaign data
    assert len(summary.campaigns) > 0
    
    for campaign_stat in summary.campaigns:
        assert campaign_stat.id
        assert campaign_stat.name
        assert campaign_stat.sent >= 0
        assert campaign_stat.opens >= 0


def test_stats_service_timeline_calculation():
    """Test StatsService timeline calculation"""
    service = StatsService()
    
    summary = service.get_stats_summary()
    
    # Should have timeline data
    assert len(summary.timeline.sent_by_day) >= 0
    assert len(summary.timeline.opens_by_day) >= 0
    
    for point in summary.timeline.sent_by_day:
        assert point.date
        assert point.sent >= 0
        assert point.opens >= 0


def test_stats_service_date_filtering():
    """Test StatsService date filtering"""
    service = StatsService()
    
    # Test with specific date range
    from_date = date.today() - timedelta(days=7)
    to_date = date.today()
    
    summary = service.get_stats_summary(from_date=from_date, to_date=to_date)
    
    # Should return valid data (might be empty for recent dates)
    assert summary.global_stats.total_sent >= 0


def test_stats_service_csv_export():
    """Test StatsService CSV export functionality"""
    service = StatsService()
    
    # Test global export
    csv_content = service.export_csv("global")
    assert "Date,Sent,Opens,Bounces,Open_Rate" in csv_content
    
    # Test domain export
    csv_content = service.export_csv("domain")
    assert "Domain,Sent,Opens,Open_Rate,Bounces,Last_Activity" in csv_content
    
    # Test campaign export
    csv_content = service.export_csv("campaign")
    assert "Campaign_ID,Campaign_Name,Sent,Opens,Open_Rate,Bounces,Status,Start_Date" in csv_content


def test_stats_service_empty_data_handling():
    """Test StatsService handles empty data gracefully"""
    service = StatsService()
    
    # Clear messages for empty test
    original_messages = service.messages.copy()
    service.messages = []
    
    try:
        summary = service.get_stats_summary()
        
        # Should return zeros, not errors
        assert summary.global_stats.total_sent == 0
        assert summary.global_stats.total_opens == 0
        assert summary.global_stats.open_rate == 0.0
        assert summary.global_stats.bounces == 0
        assert len(summary.domains) == 0
        assert len(summary.campaigns) == 0
        
    finally:
        # Restore original data
        service.messages = original_messages


def test_stats_endpoints_require_auth():
    """Test all stats endpoints require authentication"""
    endpoints = [
        "/api/v1/stats/summary",
        "/api/v1/stats/export?scope=global",
        "/api/v1/stats/domains",
        "/api/v1/stats/campaigns"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401
