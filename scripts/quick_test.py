#!/usr/bin/env python3
"""
Quick API Test Script
Tests basic API functionality
"""

import sys
import json
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

def test_endpoint(url, method="GET", data=None):
    """Test an API endpoint"""
    try:
        req = Request(url, data=data.encode() if data else None, method=method)
        if data:
            req.add_header('Content-Type', 'application/json')
        
        with urlopen(req, timeout=5) as response:
            return {
                'status': response.getcode(),
                'data': json.loads(response.read().decode())
            }
    except HTTPError as e:
        return {
            'status': e.code,
            'error': str(e)
        }
    except URLError as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def main():
    print("🧪 Testing Orchestrator AI API")
    print("=" * 50)
    print()
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    result = test_endpoint(f"{BASE_URL}/health")
    if result.get('status') == 200:
        print(f"   ✅ Health: {result.get('data', {})}")
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        print("   💡 Make sure the server is running:")
        print("      uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload")
        return
    print()
    
    # Test 2: API Health
    print("2. Testing API Health...")
    result = test_endpoint(f"{API_URL}/health")
    if result.get('status') == 200:
        print(f"   ✅ API Health: {result.get('data', {})}")
    else:
        print(f"   ⚠️  API Health: {result.get('error', 'Not available')}")
    print()
    
    # Test 3: Submit Task
    print("3. Submitting a test task...")
    task_data = json.dumps({
        "type": "simple",
        "input": {
            "message": "Hello from Python test script"
        }
    })
    result = test_endpoint(f"{API_URL}/tasks", "POST", task_data)
    
    if result.get('status') == 201:
        task_id = result.get('data', {}).get('task_id')
        print(f"   ✅ Task submitted: {task_id}")
        print(f"   Response: {json.dumps(result.get('data', {}), indent=6)}")
        
        # Test 4: Get Task Status
        print()
        print("4. Getting task status...")
        time.sleep(2)  # Wait a bit for processing
        result = test_endpoint(f"{API_URL}/tasks/{task_id}")
        if result.get('status') == 200:
            status_data = result.get('data', {})
            print(f"   ✅ Status: {status_data.get('status', 'unknown')}")
            print(f"   Workflow ID: {status_data.get('workflow_id', 'N/A')}")
            
            # Test 5: Get Result if completed
            if status_data.get('status') == 'completed':
                print()
                print("5. Getting task result...")
                result = test_endpoint(f"{API_URL}/tasks/{task_id}/result")
                if result.get('status') == 200:
                    print(f"   ✅ Result: {json.dumps(result.get('data', {}), indent=6)}")
        else:
            print(f"   ⚠️  Status check failed: {result.get('error', 'Unknown')}")
    else:
        print(f"   ❌ Task submission failed: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 6: List Tasks
    print("6. Listing tasks...")
    result = test_endpoint(f"{API_URL}/tasks?limit=5")
    if result.get('status') == 200:
        tasks_data = result.get('data', {})
        task_count = tasks_data.get('total', 0)
        print(f"   ✅ Found {task_count} task(s)")
    else:
        print(f"   ⚠️  List tasks failed: {result.get('error', 'Unknown')}")
    print()
    
    print("=" * 50)
    print("✅ API Testing Complete!")
    print()
    print("📚 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

