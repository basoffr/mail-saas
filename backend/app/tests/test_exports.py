import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

AUTH = {"Authorization": "Bearer demo"}


def test_export_sends_csv_ok():
    """Test CSV export endpoint."""
    response = client.get("/api/v1/exports/sends.csv", headers=AUTH)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]
    assert "sends_log_" in response.headers["content-disposition"]


def test_export_sends_csv_headers():
    """Test that CSV has correct headers."""
    response = client.get("/api/v1/exports/sends.csv", headers=AUTH)
    assert response.status_code == 200
    
    content = response.content.decode('utf-8')
    lines = content.strip().split('\n')
    
    # Check header row
    header = lines[0]
    expected_columns = [
        "campaign_id", "lead_id", "domain", "alias", "step_no", 
        "template_id", "scheduled_at", "sent_at", "status", 
        "with_image", "with_report", "error_code", "error_message"
    ]
    
    for column in expected_columns:
        assert column in header


def test_export_sends_csv_requires_auth():
    """Test that CSV export requires authentication."""
    response = client.get("/api/v1/exports/sends.csv")
    assert response.status_code in [401, 403]  # Either unauthorized or forbidden
