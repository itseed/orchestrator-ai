#!/bin/bash
# API Testing Script
# Tests the Orchestrator AI API endpoints

BASE_URL="http://localhost:8000"
API_URL="${BASE_URL}/api/v1"

echo "🧪 Testing Orchestrator AI API"
echo "================================"
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health")
echo "Response: $HEALTH_RESPONSE"
echo ""

# Test 2: API Health Check
echo "2. Testing API Health Check..."
API_HEALTH=$(curl -s "${API_URL}/health")
echo "Response: $API_HEALTH"
echo ""

# Test 3: Submit Task
echo "3. Submitting a test task..."
TASK_RESPONSE=$(curl -s -X POST "${API_URL}/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "simple",
    "input": {
      "message": "Hello from API test"
    }
  }')
echo "Response: $TASK_RESPONSE"
TASK_ID=$(echo $TASK_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('task_id', ''))" 2>/dev/null)
echo "Task ID: $TASK_ID"
echo ""

# Test 4: Get Task Status
if [ ! -z "$TASK_ID" ]; then
  echo "4. Getting task status..."
  sleep 2
  STATUS_RESPONSE=$(curl -s "${API_URL}/tasks/${TASK_ID}")
  echo "Response: $STATUS_RESPONSE"
  echo ""
  
  # Test 5: Get Task Result (if completed)
  echo "5. Getting task result..."
  sleep 2
  RESULT_RESPONSE=$(curl -s "${API_URL}/tasks/${TASK_ID}/result")
  echo "Response: $RESULT_RESPONSE"
  echo ""
fi

# Test 6: List Tasks
echo "6. Listing all tasks..."
LIST_RESPONSE=$(curl -s "${API_URL}/tasks?limit=5")
echo "Response: $LIST_RESPONSE"
echo ""

echo "✅ API Testing Complete!"

