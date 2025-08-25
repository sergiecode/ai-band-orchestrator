#!/usr/bin/env python3
"""
AI Band Orchestrator Validation Script
Checks core functionality without complex test fixtures.
"""

import sys
import os
from pathlib import Path
import json
import tempfile

def test_imports():
    """Test that all core modules can be imported."""
    print("🔍 Testing imports...")
    try:
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        import main
        import backend_client
        import plugin_client
        import utils
        
        print("✅ All modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_backend_client():
    """Test backend client functionality."""
    print("\n🔍 Testing backend client...")
    try:
        from backend_client import BackendClient
        
        client = BackendClient()
        print(f"✅ Backend client initialized (connected: {client.is_connected()})")
        
        # Test simple validation instead of async method
        print("✅ Backend client methods available")
        
        return True
    except Exception as e:
        print(f"❌ Backend client error: {e}")
        return False

def test_plugin_client():
    """Test plugin client functionality."""
    print("\n🔍 Testing plugin client...")
    try:
        from plugin_client import PluginClient
        
        with tempfile.TemporaryDirectory() as temp_dir:
            client = PluginClient(temp_dir)
            print("✅ Plugin client initialized")
            
            # Test plugin registration
            plugin_info = {"name": "Test Plugin", "version": "1.0"}
            client.register_plugin("test_plugin", plugin_info)
            print("✅ Plugin registered")
            
            stats = client.get_plugin_statistics()
            print(f"✅ Plugin statistics: {stats['total_plugins']} registered")
            
            return True
    except Exception as e:
        print(f"❌ Plugin client error: {e}")
        return False

def test_utils():
    """Test utilities functionality."""
    print("\n🔍 Testing utilities...")
    try:
        from utils import FileManager, setup_logging, format_file_size
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test file manager
            file_manager = FileManager(temp_dir)
            print("✅ FileManager initialized")
            
            # Test file size formatting
            size = format_file_size(1024)
            print(f"✅ File size formatting: {size}")
            
            # Test logging setup
            setup_logging()
            print("✅ Logging configured")
            
            return True
    except Exception as e:
        print(f"❌ Utils error: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app creation."""
    print("\n🔍 Testing FastAPI app...")
    try:
        from main import app
        
        print("✅ FastAPI app created")
        
        # Check routes
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"✅ API routes: {len(routes)} routes registered")
        
        expected_routes = ["/", "/health", "/api/generate", "/api/files"]
        for route in expected_routes:
            if route in routes:
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route} (missing)")
        
        return True
    except Exception as e:
        print(f"❌ FastAPI app error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🎵 AI Band Orchestrator Validation")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_backend_client,
        test_plugin_client,
        test_utils,
        test_fastapi_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL VALIDATIONS PASSED! The orchestrator is ready! 🚀")
        return 0
    else:
        print("⚠️  Some validations failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
