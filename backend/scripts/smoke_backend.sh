#!/bin/bash

# 🔥 BACKEND SMOKE TESTS - All Endpoints
# Tests all API endpoints with proper authentication
# Exit non-zero on any failure

set -e  # Exit on first error

# Configuration
BASE_URL="${API_BASE_URL:-https://mail-saas-rf4s.onrender.com/api/v1}"
AUTH_TOKEN="${API_AUTH_TOKEN:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpwbmtsaWhyeWhwa2FpeXVia2ZuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTkxNDMzNDIsImV4cCI6MjA3NDcxOTM0Mn0.P8Rx3r--uu8V-HCEH2s5qH3Ud0HhpLBUWaidrahO0jY}"
TEMP_DIR="/tmp/smoke_test_$$"
RESULTS_FILE="$TEMP_DIR/results.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

echo -e "${BLUE}🔥 BACKEND SMOKE TESTS STARTING${NC}"
echo "Base URL: $BASE_URL"
echo "Auth Token: ${AUTH_TOKEN:0:20}..."
echo ""

# Create temp directory
mkdir -p "$TEMP_DIR"

# Helper function to test endpoint
test_endpoint() {
    local method="$1"
    local endpoint="$2"
    local expected_status="$3"
    local description="$4"
    local data="$5"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing: $description... "
    
    # Build curl command
    local curl_cmd="curl -s -w '%{http_code}' -o '$TEMP_DIR/response.json'"
    curl_cmd="$curl_cmd -H 'Authorization: Bearer $AUTH_TOKEN'"
    curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    curl_cmd="$curl_cmd -X $method '$BASE_URL$endpoint'"
    
    # Execute request
    local status_code
    status_code=$(eval "$curl_cmd")
    
    # Check status code
    if [ "$status_code" = "$expected_status" ]; then
        # Check response format
        if jq -e '.data != null or .error != null' "$TEMP_DIR/response.json" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAIL (Invalid response format)${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            cat "$TEMP_DIR/response.json"
        fi
    else
        echo -e "${RED}❌ FAIL (Expected $expected_status, got $status_code)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        cat "$TEMP_DIR/response.json"
    fi
}

# Helper function to test file upload
test_upload() {
    local endpoint="$1"
    local description="$2"
    local expected_status="$3"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing: $description... "
    
    # Create dummy file
    echo "email,company,url" > "$TEMP_DIR/test.csv"
    echo "test@example.com,Test Company,https://test.com" >> "$TEMP_DIR/test.csv"
    
    # Upload file
    local status_code
    status_code=$(curl -s -w '%{http_code}' -o "$TEMP_DIR/response.json" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -F "file=@$TEMP_DIR/test.csv" \
        -X POST "$BASE_URL$endpoint")
    
    # Check result
    if [ "$status_code" = "$expected_status" ]; then
        if jq -e '.data != null or .error != null' "$TEMP_DIR/response.json" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ PASS${NC}"
            PASSED_TESTS=$((PASSED_TESTS + 1))
        else
            echo -e "${RED}❌ FAIL (Invalid response format)${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
    else
        echo -e "${RED}❌ FAIL (Expected $expected_status, got $status_code)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo -e "${YELLOW}📋 TESTING LEADS MODULE${NC}"
test_endpoint "GET" "/leads" "200" "List leads"
test_endpoint "GET" "/leads?page=1&page_size=10" "200" "List leads with pagination"
test_endpoint "GET" "/leads?search=test" "200" "Search leads"
test_endpoint "GET" "/leads/non-existent-id" "200" "Get non-existent lead (should return null)"
test_upload "/import/leads" "Import leads CSV" "200"
test_endpoint "GET" "/assets/image-by-key?key=test" "200" "Get asset by key"

echo ""
echo -e "${YELLOW}📣 TESTING CAMPAIGNS MODULE${NC}"
test_endpoint "GET" "/campaigns" "200" "List campaigns"
test_endpoint "GET" "/campaigns?page=1&page_size=10" "200" "List campaigns with pagination"
test_endpoint "GET" "/campaigns/non-existent-id" "404" "Get non-existent campaign"

echo ""
echo -e "${YELLOW}📄 TESTING TEMPLATES MODULE${NC}"
test_endpoint "GET" "/templates" "200" "List templates"
test_endpoint "GET" "/templates/v1m1" "200" "Get template detail"
test_endpoint "GET" "/templates/v1m1/preview" "200" "Preview template without lead"
test_endpoint "GET" "/templates/v1m1/variables" "200" "Get template variables"
test_endpoint "GET" "/templates/variables/all" "200" "Get all template variables"

echo ""
echo -e "${YELLOW}📊 TESTING REPORTS MODULE${NC}"
test_endpoint "GET" "/reports" "200" "List reports"
test_endpoint "GET" "/reports?page=1&page_size=10" "200" "List reports with pagination"
test_endpoint "GET" "/reports/non-existent-id" "404" "Get non-existent report"

echo ""
echo -e "${YELLOW}📈 TESTING STATS MODULE${NC}"
test_endpoint "GET" "/stats/summary" "200" "Get stats summary"
test_endpoint "GET" "/stats/summary?from=2025-01-01&to=2025-12-31" "200" "Get stats with date range"
test_endpoint "GET" "/stats/export?scope=global" "200" "Export global stats"
test_endpoint "GET" "/stats/domains" "200" "Get domain stats"
test_endpoint "GET" "/stats/campaigns" "200" "Get campaign stats"

echo ""
echo -e "${YELLOW}⚙️ TESTING SETTINGS MODULE${NC}"
test_endpoint "GET" "/settings" "200" "Get settings"
test_endpoint "GET" "/settings/inbox/accounts" "200" "Get IMAP accounts"

echo ""
echo -e "${YELLOW}❤️ TESTING HEALTH MODULE${NC}"
test_endpoint "GET" "/health" "200" "Health check"

# Test authentication failure
echo ""
echo -e "${YELLOW}🔒 TESTING AUTHENTICATION${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: Authentication failure... "
status_code=$(curl -s -w '%{http_code}' -o "$TEMP_DIR/response.json" \
    -X GET "$BASE_URL/leads")

if [ "$status_code" = "401" ] || [ "$status_code" = "403" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ FAIL (Expected 401/403, got $status_code)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test invalid endpoint
echo ""
echo -e "${YELLOW}🚫 TESTING ERROR HANDLING${NC}"
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: 404 error handling... "
status_code=$(curl -s -w '%{http_code}' -o "$TEMP_DIR/response.json" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -X GET "$BASE_URL/non-existent-endpoint")

if [ "$status_code" = "404" ]; then
    echo -e "${GREEN}✅ PASS${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}❌ FAIL (Expected 404, got $status_code)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Cleanup
rm -rf "$TEMP_DIR"

# Final results
echo ""
echo -e "${BLUE}📊 SMOKE TEST RESULTS${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL SMOKE TESTS PASSED!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}💥 $FAILED_TESTS TESTS FAILED!${NC}"
    exit 1
fi
