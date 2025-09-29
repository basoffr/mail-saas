import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.leads import store

client = TestClient(app)

AUTH = {"Authorization": "Bearer demo"}


def test_stop_lead_ok():
    """Test stopping a lead successfully."""
    # Ensure lead exists
    lead_id = "lead-001"
    
    response = client.post(f"/api/v1/leads/{lead_id}/stop", headers=AUTH)
    assert response.status_code == 200
    
    data = response.json()
    assert data["data"]["ok"] is True
    assert data["data"]["lead_id"] == lead_id
    assert data["data"]["stopped"] is True
    assert "canceled" in data["data"]
    assert data["error"] is None


def test_stop_lead_not_found():
    """Test stopping a non-existent lead."""
    response = client.post("/api/v1/leads/nonexistent/stop", headers=AUTH)
    assert response.status_code == 404
    assert "lead_not_found" in response.json()["detail"]


def test_stop_lead_idempotent():
    """Test that stopping a lead is idempotent."""
    lead_id = "lead-002"
    
    # Stop first time
    response1 = client.post(f"/api/v1/leads/{lead_id}/stop", headers=AUTH)
    assert response1.status_code == 200
    
    # Stop second time - should still work
    response2 = client.post(f"/api/v1/leads/{lead_id}/stop", headers=AUTH)
    assert response2.status_code == 200
    
    data = response2.json()
    assert data["data"]["stopped"] is True


def test_stopped_lead_check():
    """Test that stopped leads are properly flagged."""
    lead_id = "lead-001"
    
    # Stop the lead
    client.post(f"/api/v1/leads/{lead_id}/stop", headers=AUTH)
    
    # Check if lead is stopped
    assert store.is_stopped(lead_id) is True
