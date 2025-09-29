import pytest
from app.core.templates_store import (
    HARD_CODED_TEMPLATES, get_template, get_templates_for_version,
    get_all_templates, get_template_for_flow, validate_template_id,
    get_templates_summary
)


class TestTemplatesStore:
    """Test hard-coded templates store."""
    
    def test_all_templates_exist(self):
        """Test that all 16 templates exist (v1-v4, mail 1-4 each)."""
        assert len(HARD_CODED_TEMPLATES) == 16
        
        # Check all combinations exist
        for version in [1, 2, 3, 4]:
            for mail in [1, 2, 3, 4]:
                template_id = f"v{version}_mail{mail}"
                assert template_id in HARD_CODED_TEMPLATES
    
    def test_template_structure(self):
        """Test that all templates have correct structure."""
        for template_id, template in HARD_CODED_TEMPLATES.items():
            # Check required fields
            assert template.id == template_id
            assert isinstance(template.version, int)
            assert isinstance(template.mail_number, int)
            assert isinstance(template.subject, str)
            assert isinstance(template.body, str)
            assert isinstance(template.placeholders, list)
            
            # Check version and mail number match ID
            expected_version = int(template_id.split('_')[0][1:])  # v1 -> 1
            expected_mail = int(template_id.split('_')[1][4:])     # mail1 -> 1
            
            assert template.version == expected_version
            assert template.mail_number == expected_mail
    
    def test_template_content_not_empty(self):
        """Test that all templates have non-empty content."""
        for template in HARD_CODED_TEMPLATES.values():
            assert len(template.subject.strip()) > 0
            assert len(template.body.strip()) > 0
            assert "{{lead.company}}" in template.subject or "{{lead.company}}" in template.body
    
    def test_template_placeholders(self):
        """Test that templates have expected placeholders."""
        expected_placeholders = {
            "lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"
        }
        
        for template in HARD_CODED_TEMPLATES.values():
            # All templates should have at least lead.company
            assert "lead.company" in template.placeholders
            
            # Check that placeholders are subset of expected
            template_placeholders = set(template.placeholders)
            assert template_placeholders.issubset(expected_placeholders)
    
    def test_alias_consistency(self):
        """Test that templates match expected alias pattern."""
        # Mail 1 & 2 should be from Christian
        # Mail 3 & 4 should be from Victor
        
        for template in HARD_CODED_TEMPLATES.values():
            if template.mail_number in [1, 2]:
                # Should mention Christian
                content = template.subject + " " + template.body
                assert "Christian" in content
            elif template.mail_number in [3, 4]:
                # Should mention Victor
                content = template.subject + " " + template.body
                assert "Victor" in content
    
    def test_get_template(self):
        """Test getting individual templates."""
        # Valid template
        template = get_template("v1_mail1")
        assert template is not None
        assert template.id == "v1_mail1"
        assert template.version == 1
        assert template.mail_number == 1
        
        # Invalid template
        assert get_template("invalid_template") is None
        assert get_template("") is None
    
    def test_get_templates_for_version(self):
        """Test getting templates for specific version."""
        v1_templates = get_templates_for_version(1)
        assert len(v1_templates) == 4
        
        for template in v1_templates:
            assert template.version == 1
            assert template.mail_number in [1, 2, 3, 4]
        
        # Check mail numbers are complete
        mail_numbers = [t.mail_number for t in v1_templates]
        assert sorted(mail_numbers) == [1, 2, 3, 4]
        
        # Invalid version
        invalid_templates = get_templates_for_version(99)
        assert len(invalid_templates) == 0
    
    def test_get_all_templates(self):
        """Test getting all templates."""
        all_templates = get_all_templates()
        assert len(all_templates) == 16
        assert isinstance(all_templates, dict)
        
        # Should be a copy, not the original
        all_templates.clear()
        assert len(HARD_CODED_TEMPLATES) == 16  # Original unchanged
    
    def test_get_template_for_flow(self):
        """Test getting template for specific flow step."""
        # Valid combinations
        template = get_template_for_flow(1, 1)  # v1_mail1
        assert template is not None
        assert template.id == "v1_mail1"
        
        template = get_template_for_flow(4, 3)  # v4_mail3
        assert template is not None
        assert template.id == "v4_mail3"
        
        # Invalid combinations
        assert get_template_for_flow(99, 1) is None
        assert get_template_for_flow(1, 99) is None
    
    def test_validate_template_id(self):
        """Test template ID validation."""
        # Valid IDs
        assert validate_template_id("v1_mail1")
        assert validate_template_id("v4_mail4")
        
        # Invalid IDs
        assert not validate_template_id("invalid")
        assert not validate_template_id("v5_mail1")  # Version doesn't exist
        assert not validate_template_id("v1_mail5")  # Mail doesn't exist
        assert not validate_template_id("")
    
    def test_template_render(self):
        """Test template rendering with variables."""
        template = get_template("v1_mail1")
        
        variables = {
            "lead.company": "Test Company",
            "lead.url": "https://test.com",
            "vars.keyword": "SEO services",
            "vars.google_rank": "15",
            "image.cid": "cid:dashboard"
        }
        
        rendered = template.render(variables)
        
        assert "subject" in rendered
        assert "body" in rendered
        
        # Check that variables were replaced
        assert "Test Company" in rendered["subject"]
        assert "Test Company" in rendered["body"]
        assert "https://test.com" in rendered["body"]
        assert "SEO services" in rendered["body"]
        assert "15" in rendered["body"]
    
    def test_template_render_partial_variables(self):
        """Test template rendering with partial variables."""
        template = get_template("v1_mail1")
        
        # Only provide some variables
        variables = {
            "lead.company": "Partial Company"
        }
        
        rendered = template.render(variables)
        
        # Provided variable should be replaced
        assert "Partial Company" in rendered["subject"]
        
        # Missing variables should remain as placeholders
        assert "{{lead.url}}" in rendered["body"]
        assert "{{vars.keyword}}" in rendered["body"]
    
    def test_get_placeholders(self):
        """Test placeholder extraction."""
        template = get_template("v1_mail1")
        placeholders = template.get_placeholders()
        
        # Should extract all unique placeholders
        expected = {"lead.company", "lead.url", "vars.keyword", "vars.google_rank", "image.cid"}
        assert set(placeholders) == expected
    
    def test_templates_summary(self):
        """Test templates summary for UI."""
        summary = get_templates_summary()
        
        assert len(summary) == 16
        
        # Check sorting (by version, then mail_number)
        for i in range(len(summary) - 1):
            current = summary[i]
            next_item = summary[i + 1]
            
            if current["version"] == next_item["version"]:
                assert current["mail_number"] <= next_item["mail_number"]
            else:
                assert current["version"] < next_item["version"]
        
        # Check structure
        for item in summary:
            assert "id" in item
            assert "version" in item
            assert "mail_number" in item
            assert "subject" in item
            assert "placeholders" in item
            assert "body_preview" in item
            
            # Body preview should be truncated
            if len(item["body_preview"]) > 100:
                assert item["body_preview"].endswith("...")
    
    def test_version_content_differences(self):
        """Test that different versions have different content."""
        # Get mail 1 from each version
        v1_mail1 = get_template("v1_mail1")
        v2_mail1 = get_template("v2_mail1")
        v3_mail1 = get_template("v3_mail1")
        v4_mail1 = get_template("v4_mail1")
        
        # Subjects should be different (except v4 which is copy of v2)
        subjects = [v1_mail1.subject, v2_mail1.subject, v3_mail1.subject, v4_mail1.subject]
        unique_subjects = set(subjects)
        assert len(unique_subjects) >= 3  # At least 3 unique (v4 = v2)
        
        # v4 should be copy of v2 (as specified)
        assert v4_mail1.subject != v1_mail1.subject
        assert v4_mail1.subject != v3_mail1.subject
    
    def test_template_immutability(self):
        """Test that templates are immutable (frozen dataclasses)."""
        template = get_template("v1_mail1")
        
        # Should not be able to modify template
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            template.version = 999
        
        with pytest.raises(Exception):
            template.subject = "Hacked subject"
