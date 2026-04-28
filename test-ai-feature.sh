#!/bin/bash

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     AWS Idle Resource Finder - AI Feature Test           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper function
test_step() {
    echo -e "${YELLOW}[TEST]${NC} $1"
}

test_pass() {
    echo -e "${GREEN}  ✓ PASS${NC} $1"
    ((TESTS_PASSED++))
}

test_fail() {
    echo -e "${RED}  ✗ FAIL${NC} $1"
    ((TESTS_FAILED++))
}

# Test 1: Check if Ollama container is running
test_step "Checking if Ollama container is running..."
if docker ps | grep -q "aws-resource-finder-ollama"; then
    test_pass "Ollama container is running"
else
    test_fail "Ollama container is not running"
    echo "       Run: docker-compose up -d"
fi

# Test 2: Check if Ollama is accessible
test_step "Checking if Ollama API is accessible..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    test_pass "Ollama API is accessible on port 11434"
else
    test_fail "Ollama API is not accessible"
    echo "       Check: docker logs aws-resource-finder-ollama"
fi

# Test 3: Check if Llama model is pulled
test_step "Checking if Llama 3.2 model is available..."
if docker exec aws-resource-finder-ollama ollama list 2>/dev/null | grep -q "llama3.2"; then
    test_pass "Llama 3.2 model is available"
else
    test_fail "Llama 3.2 model is not available"
    echo "       Run: ./setup-ai.sh"
fi

# Test 4: Check if backend is running
test_step "Checking if backend is running..."
if docker ps | grep -q "aws-resource-finder-backend"; then
    test_pass "Backend container is running"
else
    test_fail "Backend container is not running"
    echo "       Run: docker-compose up -d"
fi

# Test 5: Check backend AI status endpoint
test_step "Checking backend AI status endpoint..."
if curl -s http://localhost:8000/ai/status > /dev/null 2>&1; then
    test_pass "Backend AI status endpoint is accessible"
    
    # Get the actual status
    AI_STATUS=$(curl -s http://localhost:8000/ai/status)
    echo "       Status: $AI_STATUS"
    
    if echo "$AI_STATUS" | grep -q '"available": true'; then
        test_pass "AI is marked as available"
    else
        test_fail "AI is not available according to backend"
    fi
else
    test_fail "Backend AI status endpoint is not accessible"
fi

# Test 6: Check if frontend is running
test_step "Checking if frontend is running..."
if docker ps | grep -q "aws-resource-finder-frontend"; then
    test_pass "Frontend container is running"
else
    test_fail "Frontend container is not running"
    echo "       Run: docker-compose up -d"
fi

# Test 7: Check frontend accessibility
test_step "Checking if frontend is accessible..."
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    test_pass "Frontend is accessible on port 3000"
else
    test_fail "Frontend is not accessible"
fi

# Test 8: Test AI inference (if model is available)
test_step "Testing AI inference capability..."
if docker exec aws-resource-finder-ollama ollama list 2>/dev/null | grep -q "llama3.2"; then
    # Try a simple test prompt
    TEST_RESPONSE=$(docker exec aws-resource-finder-ollama ollama run llama3.2:latest "Say 'AI is working' and nothing else" 2>/dev/null | head -1)
    if [ ! -z "$TEST_RESPONSE" ]; then
        test_pass "AI inference is working"
        echo "       Response: $TEST_RESPONSE"
    else
        test_fail "AI inference test failed"
    fi
else
    echo "       Skipped (model not available)"
fi

# Test 9: Check Docker volumes
test_step "Checking Docker volumes..."
if docker volume ls | grep -q "ollama-data"; then
    test_pass "Ollama data volume exists"
else
    test_fail "Ollama data volume not found"
fi

# Test 10: Check network connectivity
test_step "Checking network connectivity between services..."
if docker network ls | grep -q "aws_idle_resource_finder_app-network"; then
    test_pass "App network exists"
else
    test_fail "App network not found"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    Test Summary                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo -e "Tests Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests Failed: ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! AI feature is ready to use.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:3000"
    echo "  2. Enable 'AI Filtering' in Configuration"
    echo "  3. Run an analysis"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please fix the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Run: docker-compose up -d"
    echo "  - Run: ./setup-ai.sh"
    echo "  - Check: docker-compose logs"
    echo ""
    exit 1
fi
