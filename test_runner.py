#!/usr/bin/env python3
"""
AI Band Orchestrator - Test Runner

Comprehensive test suite for the AI Band Orchestrator.
Runs all tests and provides detailed reporting.

Author: Sergie Code
"""

import sys
import subprocess
from pathlib import Path
import time

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} - PASSED ({duration:.2f}s)")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print(f"❌ {description} - FAILED ({duration:.2f}s)")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            if result.stdout:
                print("Output:")
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def main():
    """Run all tests"""
    print("🎵 AI Band Orchestrator - Test Suite")
    print("Author: Sergie Code")
    print("=" * 60)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")
    
    # Python executable
    python_exe = "C:/Users/SnS_D/AppData/Local/Programs/Python/Python312/python.exe"
    
    # Test commands
    tests = [
        # Basic import tests
        (f'"{python_exe}" -c "import sys; sys.path.append(\'src\'); import backend_client; print(\'✅ Backend client imports\')"',
         "Backend Client Import Test"),
        
        (f'"{python_exe}" -c "import sys; sys.path.append(\'src\'); import plugin_client; print(\'✅ Plugin client imports\')"',
         "Plugin Client Import Test"),
        
        (f'"{python_exe}" -c "import sys; sys.path.append(\'src\'); import utils; print(\'✅ Utils imports\')"',
         "Utils Import Test"),
        
        (f'"{python_exe}" -c "import sys; sys.path.append(\'src\'); import main; print(\'✅ Main module imports\')"',
         "Main Module Import Test"),
        
        # Unit tests
        (f'"{python_exe}" -m pytest tests/test_backend_client.py -v',
         "Backend Client Unit Tests"),
        
        (f'"{python_exe}" -m pytest tests/test_plugin_client.py -v',
         "Plugin Client Unit Tests"),
        
        (f'"{python_exe}" -m pytest tests/test_utils.py -v',
         "Utils Unit Tests"),
        
        (f'"{python_exe}" -m pytest tests/test_main_api.py -v',
         "FastAPI Endpoint Tests"),
        
        # Integration tests
        (f'"{python_exe}" -m pytest tests/test_integration.py -v',
         "Integration Tests"),
        
        # Code quality checks
        (f'"{python_exe}" -c "import src.main; print(\'✅ FastAPI app creates successfully\')"',
         "FastAPI App Creation Test"),
    ]
    
    # Run tests
    passed = 0
    failed = 0
    
    for cmd, description in tests:
        if run_command(cmd, description):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total:  {passed + failed}")
    
    if failed == 0:
        print("\\n🎉 ALL TESTS PASSED! The orchestrator is ready to rock! 🎸")
        return 0
    else:
        print(f"\\n⚠️  {failed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
