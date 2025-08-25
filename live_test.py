#!/usr/bin/env python3
"""
Live API Test - Test the running orchestrator server

Tests the actual running server to ensure it works correctly.

Author: Sergie Code
"""

import requests
import json
import time

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Backend Connected: {data.get('backend_connected')}")
            print(f"  Active Plugins: {data.get('active_plugins')}")
            return True
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return False

def test_root():
    """Test root endpoint"""
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"Root Endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Service: {data.get('service')}")
            print(f"  Author: {data.get('author')}")
            return True
    except Exception as e:
        print(f"Root Endpoint Failed: {e}")
        return False

def test_generation():
    """Test generation endpoint"""
    try:
        payload = {
            "chord_progression": {
                "chords": [
                    {"chord": "C", "start_time": 0.0, "duration": 2.0},
                    {"chord": "G", "start_time": 2.0, "duration": 2.0}
                ],
                "tempo": 120,
                "key": "C",
                "duration": 4.0
            },
            "track_types": ["bass"],
            "plugin_id": "test_plugin_live"
        }
        
        response = requests.post(
            "http://localhost:8000/api/generate", 
            json=payload, 
            timeout=10
        )
        
        print(f"Generation Endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Success: {data.get('success')}")
            print(f"  Files Generated: {data.get('files')}")
            print(f"  Metadata: {data.get('metadata')}")
            return True
        else:
            print(f"  Error: {response.text}")
            return False
    except Exception as e:
        print(f"Generation Failed: {e}")
        return False

def test_files_list():
    """Test file listing"""
    try:
        response = requests.get("http://localhost:8000/api/files", timeout=5)
        print(f"Files List: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Files Count: {len(data.get('files', []))}")
            return True
    except Exception as e:
        print(f"Files List Failed: {e}")
        return False

def main():
    """Run live API tests"""
    print("🎵 AI Band Orchestrator - Live API Tests")
    print("=" * 50)
    
    # Wait a bit for server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Files List", test_files_list),
        ("Generation Test", test_generation),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\\n🧪 {test_name}")
        print("-" * 30)
        if test_func():
            print(f"✅ {test_name} PASSED")
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
            failed += 1
    
    print(f"\\n{'='*50}")
    print("🎯 LIVE TEST SUMMARY")
    print(f"{'='*50}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\\n🎉 ALL LIVE TESTS PASSED! Server is working perfectly! 🎸")
    else:
        print(f"\\n⚠️  {failed} test(s) failed.")

if __name__ == "__main__":
    main()
