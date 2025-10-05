import pytest
import httpx
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io

from app.main import app
from app.services.leads_store import LeadsStore
from app.models.lead import Lead, LeadStatus


@pytest.fixture
def client():
    """Test client with mocked authentication"""
    with patch('app.core.auth.require_auth') as mock_auth:
        mock_auth.return_value = {"sub": "test-user", "email": "test@example.com"}
        yield TestClient(app)


@pytest.fixture
def mock_leads_store():
    """Mock leads store with sample data"""
    with patch('app.api.leads.store') as mock_store:
        # Sample lead
        sample_lead = Lead(
            id="test-lead-1",
            email="test@example.com",
            company="Test Company",
            url="https://test.com",
            domain="test.com",
            status=LeadStatus.active,
            vars={"keyword": "test", "google_rank": "5"},
            image_key="test-image",
            list_name="test-list"
        )
        
        mock_store.query.return_value = ([sample_lead], 1)
        mock_store.get.return_value = sample_lead
        mock_store.soft_delete_bulk.return_value = (["test-lead-1"], [])
        mock_store.restore_bulk.return_value = (["test-lead-1"], [])
        mock_store.get_deleted_leads.return_value = ([], 0)
        mock_store.stop_lead.return_value = 2
        
        yield mock_store


class TestLeadsAPI:
    """Test suite for Leads API endpoints"""
    
    def test_list_leads_success(self, client, mock_leads_store):
        """Test successful leads listing"""
        response = client.get("/api/v1/leads")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "error" in data
        assert data["error"] is None
        assert "items" in data["data"]
        assert "total" in data["data"]
        
        mock_leads_store.query.assert_called_once()
    
    def test_list_leads_with_filters(self, client, mock_leads_store):
        """Test leads listing with filters"""
        response = client.get(
            "/api/v1/leads?page=2&page_size=50&search=test&has_image=true"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        
        # Verify filters were passed to store
        mock_leads_store.query.assert_called_once()
        call_args = mock_leads_store.query.call_args[1]
        assert call_args["page"] == 2
        assert call_args["page_size"] == 50
        assert call_args["search"] == "test"
        assert call_args["has_image"] is True
    
    def test_get_lead_success(self, client, mock_leads_store):
        """Test successful lead retrieval"""
        response = client.get("/api/v1/leads/test-lead-1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["id"] == "test-lead-1"
        assert data["data"]["email"] == "test@example.com"
        
        mock_leads_store.get.assert_called_once_with("test-lead-1")
    
    def test_get_lead_not_found(self, client, mock_leads_store):
        """Test lead not found"""
        mock_leads_store.get.return_value = None
        
        response = client.get("/api/v1/leads/non-existent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"] is None
        assert data["error"] == "Not Found"
    
    def test_get_lead_variables(self, client, mock_leads_store):
        """Test lead variables endpoint"""
        with patch('app.api.leads.get_lead_variables_detail') as mock_vars:
            mock_vars.return_value = {
                "all_variables": ["lead.company", "vars.keyword"],
                "filled": 2,
                "missing": [],
                "percentage": 100
            }
            
            response = client.get("/api/v1/leads/test-lead-1/variables")
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert "all_variables" in data["data"]
    
    def test_import_leads_success(self, client):
        """Test successful leads import"""
        with patch('app.api.leads.process_import_file') as mock_import:
            mock_import.return_value = {
                "inserted": 5,
                "updated": 2,
                "skipped": 1,
                "jobId": "test-job-123"
            }
            
            # Create test CSV file
            csv_content = "email,company,url\ntest@example.com,Test Co,https://test.com"
            csv_file = io.BytesIO(csv_content.encode())
            
            response = client.post(
                "/api/v1/import/leads",
                files={"file": ("test.csv", csv_file, "text/csv")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["inserted"] == 5
            assert data["data"]["jobId"] == "test-job-123"
    
    def test_get_asset_url_success(self, client):
        """Test asset URL retrieval"""
        with patch('app.api.leads.supabase_storage') as mock_storage:
            mock_storage.get_signed_url.return_value = "https://example.com/signed-url"
            
            response = client.get("/api/v1/assets/image-by-key?key=test-image")
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["url"] == "https://example.com/signed-url"
    
    def test_get_asset_url_not_found(self, client):
        """Test asset not found"""
        with patch('app.api.leads.supabase_storage') as mock_storage:
            mock_storage.get_signed_url.return_value = None
            
            response = client.get("/api/v1/assets/image-by-key?key=non-existent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"] is None
            assert "not found" in data["error"]
    
    def test_preview_render_success(self, client):
        """Test template preview rendering"""
        with patch('app.api.leads.render_preview') as mock_render:
            mock_render.return_value = {
                "html": "<html>Test</html>",
                "text": "Test",
                "warnings": []
            }
            
            payload = {
                "template_id": "v1m1",
                "lead_id": "test-lead-1"
            }
            
            response = client.post("/api/v1/previews/render", json=payload)
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["html"] == "<html>Test</html>"
    
    def test_get_import_job_success(self, client):
        """Test import job status retrieval"""
        with patch('app.api.leads.import_job_store') as mock_job_store:
            from datetime import datetime
            from dataclasses import dataclass
            
            @dataclass
            class MockJob:
                id: str = "test-job-123"
                filename: str = "test.csv"
                status: str = "completed"
                progress: float = 100.0
                inserted: int = 5
                updated: int = 2
                skipped: int = 1
                errors: list = None
                startedAt: datetime = datetime.now()
                finishedAt: datetime = datetime.now()
                
                def __post_init__(self):
                    if self.errors is None:
                        self.errors = []
            
            mock_job_store.get.return_value = MockJob()
            
            response = client.get("/api/v1/import/jobs/test-job-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["error"] is None
            assert data["data"]["id"] == "test-job-123"
            assert data["data"]["status"] == "completed"
    
    def test_stop_lead_success(self, client, mock_leads_store):
        """Test lead stop functionality"""
        response = client.post("/api/v1/leads/test-lead-1/stop")
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["ok"] is True
        assert data["data"]["stopped"] is True
        assert data["data"]["canceled"] == 2
        
        mock_leads_store.stop_lead.assert_called_once_with("test-lead-1")
    
    def test_stop_lead_not_found(self, client, mock_leads_store):
        """Test stop non-existent lead"""
        mock_leads_store.get.return_value = None
        
        response = client.post("/api/v1/leads/non-existent/stop")
        
        assert response.status_code == 404
        data = response.json()
        assert data["data"] is None
        assert "not found" in data["error"].lower()
    
    def test_soft_delete_leads_success(self, client, mock_leads_store):
        """Test soft delete leads"""
        payload = {"lead_ids": ["test-lead-1", "test-lead-2"]}
        
        response = client.post("/api/v1/leads/delete", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["deleted_count"] == 1
        assert "test-lead-1" in data["data"]["deleted_ids"]
    
    def test_restore_leads_success(self, client, mock_leads_store):
        """Test restore leads"""
        payload = {"lead_ids": ["test-lead-1"]}
        
        response = client.post("/api/v1/leads/restore", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert data["data"]["restored_count"] == 1
    
    def test_list_deleted_leads_success(self, client, mock_leads_store):
        """Test list deleted leads"""
        response = client.get("/api/v1/leads/deleted")
        
        assert response.status_code == 200
        data = response.json()
        assert data["error"] is None
        assert "items" in data["data"]
        assert "total" in data["data"]
        
        mock_leads_store.get_deleted_leads.assert_called_once()
    
    def test_response_format_consistency(self, client, mock_leads_store):
        """Test that all endpoints return consistent {data, error} format"""
        endpoints = [
            "/api/v1/leads",
            "/api/v1/leads/test-lead-1",
            "/api/v1/leads/test-lead-1/variables",
            "/api/v1/assets/image-by-key?key=test",
            "/api/v1/leads/deleted"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            
            # Every response must have data and error fields
            assert "data" in data, f"Missing 'data' field in {endpoint}"
            assert "error" in data, f"Missing 'error' field in {endpoint}"
            
            # Either data or error should be set, not both
            if data["data"] is not None:
                assert data["error"] is None, f"Both data and error set in {endpoint}"
            else:
                assert data["error"] is not None, f"Neither data nor error set in {endpoint}"


class TestLeadsAPIErrorHandling:
    """Test error handling in Leads API"""
    
    def test_invalid_pagination_parameters(self, client, mock_leads_store):
        """Test invalid pagination parameters"""
        response = client.get("/api/v1/leads?page=0&page_size=1000")
        
        # Should return 422 for validation error
        assert response.status_code == 422
        data = response.json()
        assert data["data"] is None
        assert data["error"] is not None
    
    def test_internal_server_error_handling(self, client, mock_leads_store):
        """Test internal server error handling"""
        mock_leads_store.query.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/leads")
        
        assert response.status_code == 500
        data = response.json()
        assert data["data"] is None
        assert "Internal server error" in data["error"]
    
    def test_authentication_required(self, client):
        """Test that authentication is required"""
        # Create client without mocked auth
        with TestClient(app) as unauth_client:
            response = unauth_client.get("/api/v1/leads")
            
            # Should return 401 or 403
            assert response.status_code in [401, 403]
            data = response.json()
            assert data["data"] is None
            assert data["error"] is not None
