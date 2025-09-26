import pytest
import io
import zipfile
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Mock auth header
AUTH_HEADER = {"Authorization": "Bearer mock-jwt-token"}


def test_health():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"data": {"ok": True}, "error": None}


def test_list_reports_requires_auth():
    """Test that reports list requires authentication."""
    response = client.get("/api/v1/reports")
    assert response.status_code in [401, 403]


def test_list_reports_ok():
    """Test listing reports."""
    response = client.get("/api/v1/reports", headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    assert "data" in data
    assert "error" in data
    assert data["error"] is None
    
    reports_data = data["data"]
    assert "items" in reports_data
    assert "total" in reports_data
    assert isinstance(reports_data["items"], list)
    assert isinstance(reports_data["total"], int)


def test_list_reports_with_filters():
    """Test listing reports with filters."""
    response = client.get(
        "/api/v1/reports?types=pdf,xlsx&bound_filter=bound&page=1&page_size=10",
        headers=AUTH_HEADER
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None


def test_get_report_by_id():
    """Test getting report by ID."""
    # First get list to find a report ID
    list_response = client.get("/api/v1/reports", headers=AUTH_HEADER)
    reports = list_response.json()["data"]["items"]
    
    if reports:
        report_id = reports[0]["id"]
        
        response = client.get(f"/api/v1/reports/{report_id}", headers=AUTH_HEADER)
        assert response.status_code == 200
        
        data = response.json()
        assert data["error"] is None
        assert data["data"]["id"] == report_id


def test_get_report_not_found():
    """Test getting non-existent report."""
    response = client.get("/api/v1/reports/nonexistent", headers=AUTH_HEADER)
    assert response.status_code == 404


def test_upload_report_requires_auth():
    """Test that report upload requires authentication."""
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    response = client.post("/api/v1/reports/upload", files=files)
    assert response.status_code in [401, 403]


def test_upload_report_valid_pdf():
    """Test uploading a valid PDF file."""
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    
    response = client.post("/api/v1/reports/upload", files=files, headers=AUTH_HEADER)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["filename"] == "test.pdf"
    assert data["data"]["type"] == "pdf"


def test_upload_report_with_lead_binding():
    """Test uploading report with lead binding."""
    files = {"file": ("test.xlsx", b"fake xlsx content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    form_data = {"lead_id": "lead-001"}
    
    response = client.post(
        "/api/v1/reports/upload", 
        files=files, 
        data=form_data,
        headers=AUTH_HEADER
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert data["data"]["bound_to"] is not None
    assert data["data"]["bound_to"]["kind"] == "lead"


def test_upload_report_invalid_type():
    """Test uploading invalid file type."""
    files = {"file": ("test.txt", b"text content", "text/plain")}
    
    response = client.post("/api/v1/reports/upload", files=files, headers=AUTH_HEADER)
    assert response.status_code == 422


def test_upload_report_both_bindings():
    """Test uploading with both lead and campaign binding (should fail)."""
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    form_data = {"lead_id": "lead-001", "campaign_id": "campaign-001"}
    
    response = client.post(
        "/api/v1/reports/upload",
        files=files,
        data=form_data,
        headers=AUTH_HEADER
    )
    assert response.status_code == 422


def test_bulk_upload_requires_auth():
    """Test that bulk upload requires authentication."""
    # Create a simple ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr("test.pdf", b"fake pdf content")
    zip_buffer.seek(0)
    
    files = {"file": ("bulk.zip", zip_buffer.getvalue(), "application/zip")}
    
    response = client.post("/api/v1/reports/bulk?mode=by_email", files=files)
    assert response.status_code in [401, 403]


def test_bulk_upload_valid_zip():
    """Test bulk upload with valid ZIP."""
    # Create a ZIP with test files
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr("test1.pdf", b"fake pdf content 1")
        zip_file.writestr("test2.xlsx", b"fake xlsx content 2")
    zip_buffer.seek(0)
    
    files = {"file": ("bulk.zip", zip_buffer.getvalue(), "application/zip")}
    
    response = client.post(
        "/api/v1/reports/bulk?mode=by_email",
        files=files,
        headers=AUTH_HEADER
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert "total" in data["data"]
    assert "uploaded" in data["data"]
    assert "failed" in data["data"]
    assert "mappings" in data["data"]


def test_bulk_upload_invalid_mode():
    """Test bulk upload with invalid mode."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr("test.pdf", b"fake pdf content")
    zip_buffer.seek(0)
    
    files = {"file": ("bulk.zip", zip_buffer.getvalue(), "application/zip")}
    
    response = client.post(
        "/api/v1/reports/bulk?mode=invalid_mode",
        files=files,
        headers=AUTH_HEADER
    )
    assert response.status_code == 422


def test_bind_report():
    """Test binding report to lead."""
    # First upload a report
    files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
    upload_response = client.post("/api/v1/reports/upload", files=files, headers=AUTH_HEADER)
    report_id = upload_response.json()["data"]["id"]
    
    # Bind to lead
    bind_payload = {"report_id": report_id, "lead_id": "lead-001"}
    response = client.post("/api/v1/reports/bind", json=bind_payload, headers=AUTH_HEADER)
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is None
    assert data["data"]["ok"] is True


def test_bind_report_both_entities():
    """Test binding report to both lead and campaign (should fail)."""
    bind_payload = {
        "report_id": "report-001",
        "lead_id": "lead-001",
        "campaign_id": "campaign-001"
    }
    response = client.post("/api/v1/reports/bind", json=bind_payload, headers=AUTH_HEADER)
    assert response.status_code == 422


def test_bind_nonexistent_report():
    """Test binding non-existent report."""
    bind_payload = {"report_id": "nonexistent", "lead_id": "lead-001"}
    response = client.post("/api/v1/reports/bind", json=bind_payload, headers=AUTH_HEADER)
    assert response.status_code == 404


def test_unbind_report():
    """Test unbinding report."""
    # Use existing report from sample data
    unbind_payload = {"report_id": "report-001"}
    response = client.post("/api/v1/reports/unbind", json=unbind_payload, headers=AUTH_HEADER)
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is None
    assert data["data"]["ok"] is True


def test_unbind_nonexistent_report():
    """Test unbinding non-existent report."""
    unbind_payload = {"report_id": "nonexistent"}
    response = client.post("/api/v1/reports/unbind", json=unbind_payload, headers=AUTH_HEADER)
    assert response.status_code == 404


def test_download_report():
    """Test getting download URL for report."""
    # Use existing report from sample data
    response = client.get("/api/v1/reports/report-001/download", headers=AUTH_HEADER)
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] is None
    assert "url" in data["data"]
    assert "expires_at" in data["data"]


def test_download_nonexistent_report():
    """Test downloading non-existent report."""
    response = client.get("/api/v1/reports/nonexistent/download", headers=AUTH_HEADER)
    assert response.status_code == 404


def test_reports_endpoints_require_auth():
    """Test that all reports endpoints require authentication."""
    endpoints = [
        ("GET", "/api/v1/reports"),
        ("GET", "/api/v1/reports/report-001"),
        ("POST", "/api/v1/reports/bind"),
        ("POST", "/api/v1/reports/unbind"),
        ("GET", "/api/v1/reports/report-001/download")
    ]
    
    for method, endpoint in endpoints:
        if method == "GET":
            response = client.get(endpoint)
        else:
            response = client.post(endpoint, json={})
        
        assert response.status_code in [401, 403], f"Endpoint {method} {endpoint} should require auth"
