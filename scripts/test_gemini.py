#!/usr/bin/env python3
"""
Test Google Gemini Integration
Tests specialized agents with Gemini API
"""

import sys
import json
import asyncio
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
        
        with urlopen(req, timeout=30) as response:
            return {
                'status': response.getcode(),
                'data': json.loads(response.read().decode())
            }
    except HTTPError as e:
        try:
            error_data = json.loads(e.read().decode())
            return {
                'status': e.code,
                'error': error_data.get('detail', str(e))
            }
        except:
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
    print("🧪 Testing Google Gemini Integration")
    print("=" * 60)
    print()
    
    # Test 1: Health Check
    print("1. Testing Health Check...")
    result = test_endpoint(f"{BASE_URL}/health")
    if result.get('status') == 200:
        print(f"   ✅ Server is running")
        print(f"   Response: {json.dumps(result.get('data', {}), indent=6)}")
    else:
        print(f"   ❌ Server not available: {result.get('error', 'Unknown error')}")
        print("   💡 Make sure the server is running:")
        print("      ./scripts/dev_start.sh")
        return
    print()
    
    # Test 2: Code Generation with Gemini
    print("2. Testing Code Generation Agent (with Gemini)...")
    print("   Submitting code generation task...")
    task_data = json.dumps({
        "type": "code_generation",
        "input": {
            "file_path": "test_output.py",
            "description": "Create a simple function that calculates factorial of a number",
            "language": "python",
            "write_to_file": False
        }
    })
    result = test_endpoint(f"{API_URL}/tasks", "POST", task_data)
    
    if result.get('status') == 201:
        task_id = result.get('data', {}).get('task_id')
        print(f"   ✅ Task submitted: {task_id}")
        
        # Wait for completion
        print("   ⏳ Waiting for task completion...")
        import time
        for i in range(30):  # Wait up to 30 seconds
            time.sleep(2)
            status_result = test_endpoint(f"{API_URL}/tasks/{task_id}")
            if status_result.get('status') == 200:
                status_data = status_result.get('data', {})
                status = status_data.get('status', 'unknown')
                print(f"   Status: {status}")
                
                if status == 'completed':
                    # Get result
                    result_response = test_endpoint(f"{API_URL}/tasks/{task_id}/result")
                    if result_response.get('status') == 200:
                        result_data = result_response.get('data', {})
                        print(f"   ✅ Task completed!")
                        print(f"   Result preview:")
                        result_content = result_data.get('result', {})
                        if isinstance(result_content, dict):
                            code = result_content.get('code', '')
                            if code:
                                # Show first 200 chars
                                preview = code[:200] + "..." if len(code) > 200 else code
                                print(f"   {preview}")
                        break
                elif status == 'failed':
                    print(f"   ❌ Task failed")
                    break
        else:
            print("   ⏳ Task still processing (timeout)")
    else:
        print(f"   ❌ Task submission failed: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 3: Research Agent with Gemini
    print("3. Testing Research Agent (with Gemini)...")
    print("   Submitting research task...")
    research_data = json.dumps({
        "type": "research",
        "input": {
            "query": "What is Python async/await?",
            "sources": ["web"],
            "max_results": 3,
            "include_citations": True
        }
    })
    result = test_endpoint(f"{API_URL}/tasks", "POST", research_data)
    
    if result.get('status') == 201:
        task_id = result.get('data', {}).get('task_id')
        print(f"   ✅ Task submitted: {task_id}")
        print("   ⏳ Waiting for completion...")
        import time
        for i in range(30):
            time.sleep(2)
            status_result = test_endpoint(f"{API_URL}/tasks/{task_id}")
            if status_result.get('status') == 200:
                status_data = status_result.get('data', {})
                if status_data.get('status') == 'completed':
                    result_response = test_endpoint(f"{API_URL}/tasks/{task_id}/result")
                    if result_response.get('status') == 200:
                        result_data = result_response.get('data', {})
                        print(f"   ✅ Research completed!")
                        summary = result_data.get('result', {}).get('summary', '')
                        if summary:
                            preview = summary[:300] + "..." if len(summary) > 300 else summary
                            print(f"   Summary preview: {preview}")
                    break
                elif status_data.get('status') == 'failed':
                    print(f"   ❌ Research failed")
                    break
    else:
        print(f"   ❌ Task submission failed: {result.get('error', 'Unknown error')}")
    print()
    
    # Test 4: Analysis Agent with Gemini
    print("4. Testing Analysis Agent (with Gemini)...")
    print("   Submitting analysis task...")
    analysis_data = json.dumps({
        "type": "analysis",
        "input": {
            "data": {
                "sales": [100, 150, 200, 180, 220, 250, 230],
                "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"]
            },
            "analysis_type": "trend",
            "insights": True,
            "visualization": False
        }
    })
    result = test_endpoint(f"{API_URL}/tasks", "POST", analysis_data)
    
    if result.get('status') == 201:
        task_id = result.get('data', {}).get('task_id')
        print(f"   ✅ Task submitted: {task_id}")
        print("   ⏳ Waiting for completion...")
        import time
        for i in range(30):
            time.sleep(2)
            status_result = test_endpoint(f"{API_URL}/tasks/{task_id}")
            if status_result.get('status') == 200:
                status_data = status_result.get('data', {})
                if status_data.get('status') == 'completed':
                    result_response = test_endpoint(f"{API_URL}/tasks/{task_id}/result")
                    if result_response.get('status') == 200:
                        result_data = result_response.get('data', {})
                        print(f"   ✅ Analysis completed!")
                        insights = result_data.get('result', {}).get('insights', [])
                        if insights:
                            print(f"   Insights:")
                            for insight in insights[:3]:
                                print(f"   - {insight}")
                    break
                elif status_data.get('status') == 'failed':
                    print(f"   ❌ Analysis failed")
                    break
    else:
        print(f"   ❌ Task submission failed: {result.get('error', 'Unknown error')}")
    print()
    
    print("=" * 60)
    print("✅ Gemini Integration Testing Complete!")
    print()
    print("📚 Check API documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()

