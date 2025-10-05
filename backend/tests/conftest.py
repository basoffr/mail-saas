"""
Pytest configuration and shared fixtures for API tests
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os
import tempfile
from datetime import datetime

from app.main import app


@pytest.fixture(scope="session")
def test_app():
    """FastAPI test application"""
    return app


@pytest.fixture
def auth_headers():
    """Authentication headers for API requests"""
    return {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }


@pytest.fixture
def mock_auth():
    """Mock authentication dependency"""
    with patch('app.core.auth.require_auth') as mock:
        mock.return_value = {
            "sub": "test-user-123",
            "email": "test@example.com",
            "aud": "authenticated",
            "role": "authenticated"
        }
        yield mock


@pytest.fixture
def client(mock_auth):
    """Test client with mocked authentication"""
    return TestClient(app)


@pytest.fixture
def async_client(mock_auth):
    """Async test client with mocked authentication"""
    return httpx.AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def temp_file():
    """Create temporary file for upload tests"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("email,company,url\n")
        f.write("test1@example.com,Test Company 1,https://test1.com\n")
        f.write("test2@example.com,Test Company 2,https://test2.com\n")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing"""
    return {
        "id": "test-lead-123",
        "email": "test@example.com",
        "company": "Test Company",
        "url": "https://test.com",
        "domain": "test.com",
        "status": "active",
        "vars": {
            "keyword": "test keyword",
            "google_rank": "5",
            "industry": "Technology"
        },
        "image_key": "test-image-key",
        "list_name": "test-list",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_campaign_data():
    """Sample campaign data for testing"""
    return {
        "id": "test-campaign-123",
        "name": "Test Campaign",
        "template_id": "v1m1",
        "domain": "punthelder-vindbaarheid.nl",
        "status": "draft",
        "followup_enabled": True,
        "followup_days": 3,
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_template_data():
    """Sample template data for testing"""
    return {
        "id": "v1m1",
        "name": "V1 Mail 1",
        "subject_template": "Test Subject for {lead.company}",
        "body_template": "Hello {lead.company}, your keyword is {vars.keyword}",
        "required_vars": ["lead.company", "vars.keyword"],
        "updated_at": "2025-09-26T00:00:00Z"
    }


@pytest.fixture
def sample_report_data():
    """Sample report data for testing"""
    return {
        "id": "test-report-123",
        "filename": "test-report.pdf",
        "type": "pdf",
        "size_bytes": 1024,
        "storage_path": "/reports/test-report.pdf",
        "checksum": "abc123",
        "created_at": datetime.now().isoformat(),
        "uploaded_by": "test-user-123"
    }


@pytest.fixture
def sample_stats_data():
    """Sample statistics data for testing"""
    return {
        "total_leads": 100,
        "active_leads": 85,
        "campaigns_sent": 5,
        "emails_sent": 425,
        "opens": 127,
        "clicks": 23,
        "bounces": 3,
        "unsubscribes": 2,
        "open_rate": 29.9,
        "click_rate": 5.4,
        "bounce_rate": 0.7,
        "unsubscribe_rate": 0.5
    }


@pytest.fixture
def mock_supabase_storage():
    """Mock Supabase storage service"""
    with patch('app.services.supabase_storage.supabase_storage') as mock:
        mock.get_signed_url.return_value = "https://example.com/signed-url"
        mock.upload_file.return_value = {"path": "/uploads/test.pdf"}
        yield mock


@pytest.fixture
def mock_email_service():
    """Mock email sending service"""
    with patch('app.services.testsend.testsend_service') as mock:
        mock.send_test_email.return_value = {
            "success": True,
            "message": "Test email sent successfully"
        }
        yield mock


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically"""
    for item in items:
        # Add auth marker to all API tests
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.auth)
        
        # Add slow marker to upload/import tests
        if any(keyword in item.name.lower() for keyword in ["upload", "import", "bulk"]):
            item.add_marker(pytest.mark.slow)


# Helper functions for tests
def assert_response_format(response_data):
    """Assert that response follows {data, error} format"""
    assert "data" in response_data, "Response missing 'data' field"
    assert "error" in response_data, "Response missing 'error' field"
    
    # Either data or error should be set, not both
    if response_data["data"] is not None:
        assert response_data["error"] is None, "Both data and error are set"
    else:
        assert response_data["error"] is not None, "Neither data nor error is set"


def assert_success_response(response_data, expected_data_keys=None):
    """Assert successful response format"""
    assert_response_format(response_data)
    assert response_data["error"] is None, f"Expected success but got error: {response_data['error']}"
    assert response_data["data"] is not None, "Expected data but got None"
    
    if expected_data_keys:
        for key in expected_data_keys:
            assert key in response_data["data"], f"Missing expected key '{key}' in response data"


def assert_error_response(response_data, expected_error_substring=None):
    """Assert error response format"""
    assert_response_format(response_data)
    assert response_data["data"] is None, f"Expected no data but got: {response_data['data']}"
    assert response_data["error"] is not None, "Expected error but got None"
    
    if expected_error_substring:
        assert expected_error_substring.lower() in response_data["error"].lower(), \
            f"Expected error containing '{expected_error_substring}' but got: {response_data['error']}"
