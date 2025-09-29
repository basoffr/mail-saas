import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app


client = TestClient(app)


class TestTemplatesAPI:
    """Test templates API endpoints (read-only)."""
    
    @patch('app.core.auth.require_auth')
    def test_list_templates(self, mock_auth):
        """Test listing all hard-coded templates."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.get("/api/v1/templates")
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should have 16 templates (v1-v4, mail 1-4 each)
        assert data["total"] == 16
        assert len(data["items"]) == 16
        
        # Check structure of first template
        template = data["items"][0]
        assert "id" in template
        assert "name" in template
        assert "subject_template" in template
        assert "updated_at" in template
        assert "required_vars" in template
        
        # Check that names follow pattern
        names = [t["name"] for t in data["items"]]
        assert "V1 Mail 1" in names
        assert "V4 Mail 4" in names
    
    @patch('app.core.auth.require_auth')
    def test_get_template_detail(self, mock_auth):
        """Test getting template detail."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.get("/api/v1/templates/v1_mail1")
        
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Check structure
        assert data["id"] == "v1_mail1"
        assert data["name"] == "V1 Mail 1"
        assert "subject_template" in data
        assert "body_template" in data
        assert "required_vars" in data
        assert "assets" in data
        assert "variables" in data
        
        # Check assets (should have dashboard image)
        assert len(data["assets"]) == 1
        assert data["assets"][0]["key"] == "dashboard"
        assert data["assets"][0]["type"] == "image"
        
        # Check variables/placeholders
        assert "lead.company" in data["variables"]
        assert "lead.url" in data["variables"]
    
    @patch('app.core.auth.require_auth')
    def test_get_template_detail_not_found(self, mock_auth):
        """Test getting non-existent template."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.get("/api/v1/templates/nonexistent")
        
        assert response.status_code == 404
    
    @patch('app.core.auth.require_auth')
    def test_templates_require_auth(self, mock_auth):
        """Test that templates endpoints require authentication."""
        # No auth
        response = client.get("/api/v1/templates")
        assert response.status_code == 401  # Or whatever auth failure code
        
        response = client.get("/api/v1/templates/v1_mail1")
        assert response.status_code == 401
    
    @patch('app.core.auth.require_auth')
    def test_create_template_forbidden(self, mock_auth):
        """Test that creating templates is forbidden."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.post("/api/v1/templates", json={
            "name": "New Template",
            "subject": "Test Subject",
            "body": "Test Body"
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_update_template_forbidden(self, mock_auth):
        """Test that updating templates is forbidden."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.put("/api/v1/templates/v1_mail1", json={
            "name": "Updated Template",
            "subject": "Updated Subject"
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_patch_template_forbidden(self, mock_auth):
        """Test that patching templates is forbidden."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.patch("/api/v1/templates/v1_mail1", json={
            "subject": "Patched Subject"
        })
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_delete_template_forbidden(self, mock_auth):
        """Test that deleting templates is forbidden."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.delete("/api/v1/templates/v1_mail1")
        
        assert response.status_code == 405
        assert response.json()["detail"]["error"] == "templates_hard_coded"
    
    @patch('app.core.auth.require_auth')
    def test_all_versions_accessible(self, mock_auth):
        """Test that all template versions are accessible."""
        mock_auth.return_value = {"sub": "test-user"}
        
        # Test all 16 templates
        for version in [1, 2, 3, 4]:
            for mail in [1, 2, 3, 4]:
                template_id = f"v{version}_mail{mail}"
                response = client.get(f"/api/v1/templates/{template_id}")
                
                assert response.status_code == 200
                data = response.json()["data"]
                assert data["id"] == template_id
                assert data["name"] == f"V{version} Mail {mail}"
    
    @patch('app.core.auth.require_auth')
    def test_template_content_consistency(self, mock_auth):
        """Test that template content is consistent."""
        mock_auth.return_value = {"sub": "test-user"}
        
        # Get v1_mail1
        response = client.get("/api/v1/templates/v1_mail1")
        assert response.status_code == 200
        data = response.json()["data"]
        
        # Should contain expected placeholders
        subject = data["subject_template"]
        body = data["body_template"]
        
        assert "{{lead.company}}" in subject or "{{lead.company}}" in body
        assert "Christian" in body  # Mail 1 should be from Christian
        
        # Get v1_mail3 (Victor mail)
        response = client.get("/api/v1/templates/v1_mail3")
        assert response.status_code == 200
        data = response.json()["data"]
        
        body = data["body_template"]
        assert "Victor" in body  # Mail 3 should be from Victor
    
    @patch('app.core.auth.require_auth')
    def test_template_variables_extraction(self, mock_auth):
        """Test that template variables are correctly extracted."""
        mock_auth.return_value = {"sub": "test-user"}
        
        response = client.get("/api/v1/templates/v1_mail1")
        assert response.status_code == 200
        data = response.json()["data"]
        
        variables = data["variables"]
        required_vars = data["required_vars"]
        
        # Should be the same
        assert set(variables) == set(required_vars)
        
        # Should contain expected variables
        expected_vars = {"lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"}
        assert set(variables).issubset(expected_vars)
        assert "lead.company" in variables  # This should always be present
