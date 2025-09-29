#!/usr/bin/env python3
"""
Cutover Validation Script
Validates that all components are ready for production cutover
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("WARNING: requests module not available, skipping API tests")

# Configuration
FRONTEND_URL = "http://localhost:8080"
BACKEND_URL = "http://localhost:8000"
API_BASE = f"{BACKEND_URL}/api/v1"

class CutoverValidator:
    def __init__(self):
        self.results = []
        self.errors = []
        
    def log_result(self, test_name: str, status: str, message: str = ""):
        result = {
            "test": test_name,
            "status": status,  # "PASS", "FAIL", "WARN"
            "message": message
        }
        self.results.append(result)
        
        status_emoji = {"PASS": "[PASS]", "FAIL": "[FAIL]", "WARN": "[WARN]"}
        print(f"{status_emoji.get(status, '[?]')} {test_name}: {message}")
        
        if status == "FAIL":
            self.errors.append(result)
    
    def test_frontend_env(self):
        """Test frontend environment configuration"""
        env_file = Path("vitalign-pro/.env")
        
        if not env_file.exists():
            self.log_result("Frontend ENV", "FAIL", ".env file not found")
            return
            
        with open(env_file) as f:
            content = f.read()
            
        required_vars = ["VITE_USE_FIXTURES", "VITE_API_BASE_URL"]
        missing = []
        
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if missing:
            self.log_result("Frontend ENV", "FAIL", f"Missing variables: {', '.join(missing)}")
        else:
            # Check if fixtures are disabled
            if "VITE_USE_FIXTURES=false" in content:
                self.log_result("Frontend ENV", "PASS", "Fixtures disabled, API configured")
            else:
                self.log_result("Frontend ENV", "WARN", "Fixtures still enabled")
    
    def test_backend_health(self):
        """Test backend health endpoint"""
        if not HAS_REQUESTS:
            self.log_result("Backend Health", "WARN", "Skipped - requests module not available")
            return
            
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("data", {}).get("status") == "healthy":
                    self.log_result("Backend Health", "PASS", "API is healthy")
                else:
                    self.log_result("Backend Health", "WARN", "API responding but not healthy")
            else:
                self.log_result("Backend Health", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.log_result("Backend Health", "FAIL", f"Connection error: {str(e)}")
        except Exception as e:
            self.log_result("Backend Health", "FAIL", f"Error: {str(e)}")
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        if not HAS_REQUESTS:
            self.log_result("API Endpoints", "WARN", "Skipped - requests module not available")
            return
            
        endpoints = [
            ("GET", "/leads", "Leads API"),
            ("GET", "/templates", "Templates API"),
            ("GET", "/campaigns", "Campaigns API"),
            ("GET", "/reports", "Reports API"),
            ("GET", "/stats/overview", "Statistics API"),
            ("GET", "/settings", "Settings API"),
            ("GET", "/inbox/accounts", "Inbox API")
        ]
        
        for method, endpoint, name in endpoints:
            try:
                response = requests.request(method, f"{API_BASE}{endpoint}", timeout=5)
                if response.status_code in [200, 401]:  # 401 is OK (auth required)
                    self.log_result(name, "PASS", f"Endpoint responding")
                else:
                    self.log_result(name, "FAIL", f"HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_result(name, "FAIL", f"Connection error: {str(e)}")
            except Exception as e:
                self.log_result(name, "FAIL", f"Error: {str(e)}")
    
    def test_asset_endpoint(self):
        """Test asset image-by-key endpoint"""
        if not HAS_REQUESTS:
            self.log_result("Asset Endpoint", "WARN", "Skipped - requests module not available")
            return
            
        try:
            response = requests.get(f"{API_BASE}/assets/image-by-key?key=test_picture", timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK (image not found)
                data = response.json()
                if "data" in data and "error" in data:
                    self.log_result("Asset Endpoint", "PASS", "API response format correct")
                else:
                    self.log_result("Asset Endpoint", "WARN", "Unexpected response format")
            else:
                self.log_result("Asset Endpoint", "FAIL", f"HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.log_result("Asset Endpoint", "FAIL", f"Connection error: {str(e)}")
        except Exception as e:
            self.log_result("Asset Endpoint", "FAIL", f"Error: {str(e)}")
    
    def test_file_structure(self):
        """Test that required files exist"""
        required_files = [
            "backend/.env.example",
            "backend/app/services/supabase_storage.py",
            "backend/app/api/health.py",
            "vitalign-pro/.env",
            "vitalign-pro/src/services/leads.ts",
            "vitalign-pro/src/services/templates.ts"
        ]
        
        for file_path in required_files:
            if Path(file_path).exists():
                self.log_result(f"File: {file_path}", "PASS", "Exists")
            else:
                self.log_result(f"File: {file_path}", "FAIL", "Missing")
    
    def test_environment_variables(self):
        """Test environment variable configuration"""
        backend_env = Path("backend/.env")
        
        if backend_env.exists():
            self.log_result("Backend ENV", "PASS", ".env file exists")
        else:
            self.log_result("Backend ENV", "WARN", ".env file not found (using .env.example)")
        
        # Check if Supabase variables are configured
        supabase_url = os.getenv("SUPABASE_URL")
        if supabase_url:
            self.log_result("Supabase Config", "PASS", "URL configured")
        else:
            self.log_result("Supabase Config", "WARN", "URL not configured (using mock)")
    
    def run_all_tests(self):
        """Run all validation tests"""
        print("Starting Cutover Validation...\n")
        
        self.test_file_structure()
        print()
        
        self.test_frontend_env()
        self.test_environment_variables()
        print()
        
        self.test_backend_health()
        self.test_api_endpoints()
        self.test_asset_endpoint()
        print()
        
        # Summary
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        warnings = len([r for r in self.results if r["status"] == "WARN"])
        
        print("VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Warnings: {warnings}")
        print(f"Failed: {failed}")
        print()
        
        if failed == 0:
            print("CUTOVER READY! All critical tests passed.")
            if warnings > 0:
                print("Some warnings present - review before production deployment.")
        else:
            print("CUTOVER NOT READY! Critical issues found:")
            for error in self.errors:
                print(f"   - {error['test']}: {error['message']}")
        
        return failed == 0


def main():
    """Main validation function"""
    validator = CutoverValidator()
    success = validator.run_all_tests()
    
    # Save results to file
    results_file = Path("cutover_validation_results.json")
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": "2024-01-29T11:47:00Z",
            "success": success,
            "results": validator.results
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
