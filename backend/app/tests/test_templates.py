import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test auth headers
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["ok"] is True
    assert data["error"] is None


def test_list_templates_requires_auth():
    """Test that templates list requires authentication"""
    response = client.get("/api/v1/templates")
    assert response.status_code == 401


def test_list_templates_ok():
    """Test templates list endpoint"""
    response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    assert "data" in data
    assert "items" in data["data"]
    assert "total" in data["data"]
    
    # Should have seed templates
    templates = data["data"]["items"]
    assert len(templates) >= 2
    
    # Check template structure
    template = templates[0]
    assert "id" in template
    assert "name" in template
    assert "subject_template" in template
    assert "updated_at" in template
    assert "required_vars" in template


def test_get_template_detail_ok():
    """Test template detail endpoint"""
    # First get list to get a valid ID
    list_response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    templates = list_response.json()["data"]["items"]
    template_id = templates[0]["id"]
    
    # Get detail
    response = client.get(f"/api/v1/templates/{template_id}", headers=AUTH_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    
    template = data["data"]
    assert template["id"] == template_id
    assert "name" in template
    assert "subject_template" in template
    assert "body_template" in template
    assert "updated_at" in template
    assert "required_vars" in template
    assert "assets" in template
    assert "variables" in template
    
    # Check variables structure
    if template["variables"]:
        var = template["variables"][0]
        assert "key" in var
        assert "required" in var
        assert "source" in var


def test_get_template_detail_not_found():
    """Test template detail with invalid ID"""
    response = client.get("/api/v1/templates/invalid-id", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_template_preview_without_lead():
    """Test template preview without lead ID (uses dummy data)"""
    # Get a valid template ID
    list_response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    templates = list_response.json()["data"]["items"]
    template_id = templates[0]["id"]
    
    # Preview without lead
    response = client.get(f"/api/v1/templates/{template_id}/preview", headers=AUTH_HEADERS)
    assert response.status_code == 200
    
    data = response.json()
    assert data["error"] is None
    
    preview = data["data"]
    assert "html" in preview
    assert "text" in preview
    assert "warnings" in preview
    
    # Should have HTML content
    assert len(preview["html"]) > 0
    assert len(preview["text"]) > 0
    
    # Should have warning about dummy data
    assert preview["warnings"] is not None
    assert any("dummy data" in warning.lower() for warning in preview["warnings"])


def test_template_preview_with_lead():
    """Test template preview with lead ID"""
    # Get a valid template ID
    list_response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    templates = list_response.json()["data"]["items"]
    template_id = templates[0]["id"]
    
    # Get a valid lead ID
    leads_response = client.get("/api/v1/leads", headers=AUTH_HEADERS)
    if leads_response.status_code == 200:
        leads = leads_response.json()["data"]["items"]
        if leads:
            lead_id = leads[0]["id"]
            
            # Preview with lead
            response = client.get(
                f"/api/v1/templates/{template_id}/preview?lead_id={lead_id}", 
                headers=AUTH_HEADERS
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["error"] is None
            
            preview = data["data"]
            assert "html" in preview
            assert "text" in preview
            assert "warnings" in preview
        else:
            # Skip test if no leads available
            pytest.skip("No leads available for testing")
    else:
        # Skip test if leads endpoint not available
        pytest.skip("Leads endpoint not available")


def test_template_preview_invalid_template():
    """Test template preview with invalid template ID"""
    response = client.get("/api/v1/templates/invalid-id/preview", headers=AUTH_HEADERS)
    assert response.status_code == 404


def test_testsend_valid_email():
    """Test sending test email with valid email"""
    # Get a valid template ID
    list_response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    templates = list_response.json()["data"]["items"]
    template_id = templates[0]["id"]
    
    # Send test email
    payload = {
        "to": "test@example.com",
        "leadId": None
    }
    
    response = client.post(
        f"/api/v1/templates/{template_id}/testsend",
        json=payload,
        headers=AUTH_HEADERS
    )
    assert response.status_code == 200
    
    data = response.json()
    # Should succeed (simulated)
    if data["error"] is None:
        assert data["data"]["ok"] is True
        assert "message" in data["data"]


def test_testsend_invalid_email():
    """Test sending test email with invalid email"""
    # Get a valid template ID
    list_response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    templates = list_response.json()["data"]["items"]
    template_id = templates[0]["id"]
    
    # Send test email with invalid email
    payload = {
        "to": "invalid-email",
        "leadId": None
    }
    
    response = client.post(
        f"/api/v1/templates/{template_id}/testsend",
        json=payload,
        headers=AUTH_HEADERS
    )
    # Should fail validation at Pydantic level
    assert response.status_code == 422


def test_testsend_with_lead():
    """Test sending test email with lead ID"""
    # Get a valid template ID
    list_response = client.get("/api/v1/templates", headers=AUTH_HEADERS)
    templates = list_response.json()["data"]["items"]
    template_id = templates[0]["id"]
    
    # Get a valid lead ID
    leads_response = client.get("/api/v1/leads", headers=AUTH_HEADERS)
    if leads_response.status_code == 200:
        leads = leads_response.json()["data"]["items"]
        if leads:
            lead_id = leads[0]["id"]
            
            payload = {
                "to": "test@example.com",
                "leadId": lead_id
            }
            
            response = client.post(
                f"/api/v1/templates/{template_id}/testsend",
                json=payload,
                headers=AUTH_HEADERS
            )
            assert response.status_code == 200
        else:
            pytest.skip("No leads available for testing")
    else:
        pytest.skip("Leads endpoint not available")


def test_testsend_invalid_template():
    """Test sending test email with invalid template ID"""
    payload = {
        "to": "test@example.com",
        "leadId": None
    }
    
    response = client.post(
        "/api/v1/templates/invalid-id/testsend",
        json=payload,
        headers=AUTH_HEADERS
    )
    assert response.status_code == 404


def test_testsend_requires_auth():
    """Test that testsend requires authentication"""
    payload = {
        "to": "test@example.com",
        "leadId": None
    }
    
    response = client.post("/api/v1/templates/test-id/testsend", json=payload)
    assert response.status_code == 401


def test_template_renderer_variables():
    """Test template variable extraction and rendering"""
    from app.services.template_renderer import TemplateRenderer
    
    renderer = TemplateRenderer()
    
    # Test variable extraction
    template = "Hello {{lead.email}}, welcome to {{campaign.name}}!"
    variables = renderer.extract_variables(template)
    assert "lead.email" in variables
    assert "campaign.name" in variables
    
    # Test rendering
    context = {
        'lead': {'email': 'test@example.com'},
        'campaign': {'name': 'Test Campaign'}
    }
    
    rendered, warnings = renderer.render(template, context)
    assert "test@example.com" in rendered
    assert "Test Campaign" in rendered
    assert len(warnings) == 0


def test_template_renderer_warnings():
    """Test template renderer warnings for missing variables"""
    from app.services.template_renderer import TemplateRenderer
    
    renderer = TemplateRenderer()
    
    template = "Hello {{lead.email}}, your score is {{vars.missing_var}}!"
    context = {
        'lead': {'email': 'test@example.com'},
        'vars': {}
    }
    
    rendered, warnings = renderer.render(template, context)
    assert "test@example.com" in rendered
    assert len(warnings) > 0
    assert any("missing_var" in warning for warning in warnings)
