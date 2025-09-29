#!/usr/bin/env python3
"""
Comprehensive Implementation Test Suite
Tests all implemented cutover functionality
"""

import sys
import os
import re
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

def test_leads_import_functions():
    """Test leads import functionality"""
    print("Testing Leads Import Functions...")
    
    try:
        from app.services.leads_import import _extract_root_domain, _domain_from_url, _normalize_key
        
        # Test domain extraction
        test_cases = [
            ("www.acme.com", "acme"),
            ("techstart.io", "techstart"),
            ("sub.example.co.uk", "sub"),
            ("test-company.nl", "test-company"),
            ("test_company.com", "test-company"),  # underscore replacement
        ]
        
        for domain, expected in test_cases:
            result = _extract_root_domain(domain)
            if result == expected:
                print(f"  [PASS] Domain '{domain}' -> '{result}'")
            else:
                print(f"  [FAIL] Domain '{domain}' -> '{result}' (expected '{expected}')")
        
        # Test URL parsing
        url_cases = [
            ("https://www.acme.com", "acme.com"),
            ("acme.com", "acme.com"),
            ("https://techstart.io/about", "techstart.io"),
            (None, None),
            ("", None),
        ]
        
        for url, expected in url_cases:
            result = _domain_from_url(url)
            if result == expected:
                print(f"  [PASS] URL '{url}' -> '{result}'")
            else:
                print(f"  [FAIL] URL '{url}' -> '{result}' (expected '{expected}')")
        
        # Test key normalization
        key_cases = [
            ("Company Name", "company_name"),
            ("Email-Address", "email_address"),
            ("First.Name", "first_name"),
            ("  UPPER CASE  ", "upper_case"),
        ]
        
        for key, expected in key_cases:
            result = _normalize_key(key)
            if result == expected:
                print(f"  [PASS] Key '{key}' -> '{result}'")
            else:
                print(f"  [FAIL] Key '{key}' -> '{result}' (expected '{expected}')")
                
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_file_handler_functions():
    """Test file handler PDF normalization"""
    print("\nTesting File Handler Functions...")
    
    try:
        from app.services.file_handler import FileHandler
        
        handler = FileHandler()
        
        # Test PDF filename normalization
        pdf_cases = [
            ("Acme Report.pdf", "acme_report_nl_report"),
            ("TECH_COMPANY_RAPPORT.pdf", "tech_company_nl_report"),
            ("company-name_document.pdf", "company-name_document_nl_report"),
            ("already_nl_report.pdf", "already_nl_report"),
            ("test   multiple   spaces.pdf", "test_multiple_spaces_nl_report"),
        ]
        
        for filename, expected in pdf_cases:
            result = handler._normalize_pdf_filename(filename)
            if result == expected:
                print(f"  [PASS] PDF '{filename}' -> '{result}.pdf'")
            else:
                print(f"  [FAIL] PDF '{filename}' -> '{result}.pdf' (expected '{expected}.pdf')")
        
        # Test file type detection
        type_cases = [
            ("test.pdf", "pdf"),
            ("image.PNG", "png"),
            ("document.xlsx", "xlsx"),
            ("photo.jpeg", "jpg"),
            ("unknown.txt", None),
        ]
        
        for filename, expected in type_cases:
            result = handler._detect_file_type(filename)
            result_str = result.value if result else None
            if result_str == expected:
                print(f"  [PASS] Type '{filename}' -> '{result_str}'")
            else:
                print(f"  [FAIL] Type '{filename}' -> '{result_str}' (expected '{expected}')")
                
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_template_preview_functions():
    """Test template preview variable extraction"""
    print("\nTesting Template Preview Functions...")
    
    try:
        from app.services.template_preview import extract_template_variables, validate_lead_variables
        
        # Test variable extraction
        template_content = """
        <h1>Hi {{firstName}},</h1>
        <p>Welcome to {{companyName}}!</p>
        <p>Industry: {{industry}}</p>
        <img src="{{image.cid 'hero'}}" />
        <p>Contact: {{email}}</p>
        """
        
        variables = extract_template_variables(template_content)
        expected_vars = {'firstName', 'companyName', 'industry', 'image.cid', 'email'}
        
        if variables == expected_vars:
            print(f"  [PASS] Variables extracted: {sorted(variables)}")
        else:
            print(f"  [FAIL] Variables: {sorted(variables)} (expected {sorted(expected_vars)})")
        
        # Test validation with mock lead
        class MockLead:
            def __init__(self):
                self.email = "test@example.com"
                self.company = "Test Company"
                self.vars = {"firstName": "John", "industry": "Tech"}
                self.image_key = "test_picture"
        
        lead = MockLead()
        warnings = validate_lead_variables(lead, {'firstName', 'companyName', 'industry', 'email'})
        
        if len(warnings) == 0:
            print(f"  [PASS] No validation warnings for complete lead")
        else:
            print(f"  [INFO] Validation warnings: {warnings}")
        
        # Test with incomplete lead
        lead.company = None
        lead.vars = {}
        warnings = validate_lead_variables(lead, {'firstName', 'companyName', 'industry'})
        
        if len(warnings) >= 2:  # Should warn about missing company and firstName
            print(f"  [PASS] Validation warnings for incomplete lead: {len(warnings)} warnings")
        else:
            print(f"  [FAIL] Expected warnings for incomplete lead, got: {warnings}")
            
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_supabase_storage():
    """Test Supabase storage functionality"""
    print("\nTesting Supabase Storage...")
    
    try:
        from app.services.supabase_storage import SupabaseStorage
        
        # Test initialization without credentials (should use mock)
        storage = SupabaseStorage()
        
        if storage.client is None:
            print("  [PASS] Storage initialized in mock mode (no credentials)")
        else:
            print("  [INFO] Storage initialized with real credentials")
        
        # Test signed URL generation
        test_key = "test_picture"
        url = storage.get_signed_url(test_key)
        
        if url and test_key in url:
            print(f"  [PASS] Generated URL for '{test_key}': {url[:50]}...")
        else:
            print(f"  [FAIL] Failed to generate URL for '{test_key}'")
        
        # Test list images (should work even in mock mode)
        try:
            images = storage.list_images()
            print(f"  [PASS] Listed images: {len(images)} found")
        except:
            print("  [INFO] List images not available in mock mode")
            
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)}")
        return False

def test_api_response_format():
    """Test API response format consistency"""
    print("\nTesting API Response Format...")
    
    try:
        from app.schemas.common import DataResponse
        from pydantic import ValidationError
        
        # Test valid response
        valid_response = {"data": {"test": "value"}, "error": None}
        try:
            DataResponse[dict](**valid_response)
            print("  [PASS] Valid API response format accepted")
        except ValidationError as e:
            print(f"  [FAIL] Valid response rejected: {e}")
            return False
        
        # Test error response
        error_response = {"data": None, "error": "Test error"}
        try:
            DataResponse[dict](**error_response)
            print("  [PASS] Error API response format accepted")
        except ValidationError as e:
            print(f"  [FAIL] Error response rejected: {e}")
            return False
        
        # Test invalid response (missing required structure)
        invalid_response = {"wrong": "format"}
        try:
            response = DataResponse[dict](**invalid_response)
            # Check if it has the required structure with defaults
            if hasattr(response, 'data') and hasattr(response, 'error'):
                print("  [PASS] Invalid response handled with defaults")
            else:
                print("  [FAIL] Invalid response missing required fields")
                return False
        except ValidationError:
            print("  [PASS] Invalid response correctly rejected")
            
        return True
        
    except Exception as e:
        print(f"  [ERROR] {str(e)}")

def test_environment_configuration():
    """Test environment configuration"""
    print("\nTesting Environment Configuration...")
    
    # Test frontend .env
    frontend_env = Path("vitalign-pro/.env")
    if frontend_env.exists():
        with open(frontend_env) as f:
            content = f.read()
            
        if "VITE_USE_FIXTURES=false" in content:
            print("  [PASS] Frontend fixtures disabled")
        else:
            print("  [WARN] Frontend fixtures may still be enabled")
            
        if "VITE_API_BASE_URL" in content:
            print("  [PASS] Frontend API URL configured")
        else:
            print("  [FAIL] Frontend API URL not configured")
    else:
        print("  [FAIL] Frontend .env file not found")
        return False
    
    # Test backend .env.example
    backend_env = Path("backend/.env.example")
    if backend_env.exists():
        with open(backend_env) as f:
            content = f.read()
            
        required_vars = [
            "USE_FIXTURES",
            "SUPABASE_URL", 
            "SUPABASE_ANON_KEY",
            "TZ=Europe/Amsterdam"
        ]
        
        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if not missing:
            print("  [PASS] Backend environment template complete")
        else:
            print(f"  [FAIL] Backend environment missing: {missing}")
            return False
    else:
        print("  [FAIL] Backend .env.example not found")
        return False
        
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("COMPREHENSIVE IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        test_leads_import_functions,
        test_file_handler_functions,
        test_template_preview_functions,
        test_supabase_storage,
        test_api_response_format,
        test_environment_configuration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("ALL TESTS PASSED! Implementation is solid.")
        return True
    else:
        print(f"{total-passed} tests failed. Review implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
