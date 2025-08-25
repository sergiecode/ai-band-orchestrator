# 🔧 AI Band Integration Fixes - Instructions for Other Agents

## 📋 Summary
The ai-band-orchestrator has been tested and integrated with ai-band-backend and ai-band-plugin. Several cross-platform and integration issues were identified and resolved. This document provides specific fixes needed in each component.

## 🎯 ai-band-backend Fixes Needed

### Issue: Import Path Dependencies
**Location**: If using the backend directly in other projects

**Current Working Setup**:
```python
# In orchestrator backend_client.py - THIS WORKS
backend_path = Path(__file__).parent.parent.parent / "ai-band-backend" / "src"
if backend_path.exists():
    sys.path.append(str(backend_path))
```

**Recommended Fix for ai-band-backend**:
Add to `src/__init__.py`:
```python
# src/__init__.py
"""
AI Band Backend - MIDI Generation System
"""

from .chord_detection import ChordDetector
from .midi_generator import MidiGenerator

__all__ = ['ChordDetector', 'MidiGenerator']
__version__ = '1.0.0'
```

### Issue: Package Dependencies
**Problem**: pretty_midi deprecation warnings

**Fix for requirements.txt**:
```
# Update when available - current version works but shows warnings
pretty_midi>=0.2.9,<1.0.0
setuptools<81  # Temporary fix for pkg_resources warnings
```

## 🎸 ai-band-plugin Fixes Needed

### Issue: Plugin Not Compiled
**Status**: Source code exists but no binary artifacts

**Required Actions**:
1. **Build Configuration** - Add to CMakeLists.txt:
```cmake
# Ensure proper output directory
set_target_properties(${PROJECT_NAME} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib"
)

# Copy plugin to standard VST3 location on build
if(WIN32)
    add_custom_command(TARGET ${PROJECT_NAME} POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
        $<TARGET_FILE:${PROJECT_NAME}>
        "$ENV{ProgramFiles}/Common Files/VST3/"
    )
endif()
```

2. **Communication Protocol** - Ensure plugin implements:
```cpp
// In PluginProcessor.h - Add these endpoints
class PluginProcessor {
    // HTTP server for orchestrator communication
    void startHttpServer(int port = 9000);
    
    // File monitoring callback
    void onMidiFileReceived(const String& filePath);
    
    // Registration with orchestrator
    void registerWithOrchestrator(const String& orchestratorUrl);
};
```

3. **Network Client** - In NetworkClient.cpp:
```cpp
void NetworkClient::registerPlugin() {
    // POST to http://localhost:8000/api/plugins/register
    json registration = {
        {"name", "AI Band Plugin"},
        {"version", "1.0.0"},
        {"http_endpoint", "http://localhost:9000"},
        {"capabilities", {"midi_playback", "real_time_sync"}}
    };
    // Send registration request
}
```

### Issue: File Monitoring Integration
**Expected Behavior**: Plugin should watch for notification files

**Implementation Needed**:
```cpp
// In MidiManager.cpp
void MidiManager::watchNotificationFile() {
    // Monitor: ./generated_files/integration_test_notification.txt
    // Format: filename1.mid,filename2.mid
    // Action: Load and play MIDI files listed
}
```

## 🌐 Cross-Platform Compatibility Fixes

### For Windows Development:
**Issue**: Path and encoding problems

**Fixes Applied in Orchestrator** (use in other components):
```python
# Encoding handling
import subprocess
result = subprocess.run(
    cmd,
    encoding='utf-8',
    errors='replace'  # Handle Windows encoding issues
)

# Disk usage (Windows compatible)
if os.name == 'nt':
    import shutil
    total, used, free = shutil.disk_usage(path)
else:
    stat = os.statvfs(path)
    free = stat.f_bavail * stat.f_frsize

# File timestamp operations
import os
os.utime(file_path, (access_time, modification_time))
```

## 🔄 API Compatibility Updates

### Pydantic v2 Migration
**Issue**: Deprecated .dict() method

**Fix for all FastAPI endpoints**:
```python
# OLD (deprecated):
data = model.dict()

# NEW (correct):
data = model.model_dump()
```

### Response Models
**Ensure consistency across all APIs**:
```python
from pydantic import BaseModel
from typing import List, Optional

class PluginInfo(BaseModel):
    name: str
    version: str
    http_endpoint: Optional[str] = None
    capabilities: List[str] = []

class GenerationResult(BaseModel):
    success: bool
    files: List[str]
    plugin_id: str
    timestamp: float
```

## 🧪 Testing Framework Updates

### For pytest-asyncio compatibility:
```python
# In conftest.py (add to each project):
import pytest

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### For Windows testing:
```python
# Add to test utilities
import tempfile
import platform

def create_temp_dir():
    """Cross-platform temporary directory creation"""
    if platform.system() == 'Windows':
        # Use Windows-safe temp directory
        return tempfile.mkdtemp(prefix='aiband_')
    else:
        return tempfile.mkdtemp()
```

## 📁 File Structure Recommendations

### Project Layout (ensure consistency):
```
ai-band-{component}/
├── src/                 # Source code
├── tests/               # Test files
├── config/              # Configuration files
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
├── CMakeLists.txt       # C++ build config (for plugin)
└── README.md           # Component documentation
```

### Configuration Files
**Standardize config.json across all components**:
```json
{
  "component_name": "ai-band-{component}",
  "version": "1.0.0",
  "orchestrator": {
    "host": "localhost",
    "port": 8000,
    "endpoints": {
      "register": "/api/plugins/register",
      "heartbeat": "/api/plugins/heartbeat"
    }
  },
  "communication": {
    "timeout": 30,
    "retry_attempts": 3
  }
}
```

## 🚀 Deployment Checklist

### Before integrating changes:
- [ ] Update all .dict() calls to .model_dump()
- [ ] Add Windows compatibility checks
- [ ] Implement proper error handling
- [ ] Add component registration logic
- [ ] Test cross-platform functionality
- [ ] Update API documentation

### Integration verification:
```bash
# Run this in each component directory
python -m pytest tests/ -v

# For orchestrator integration:
cd ai-band-orchestrator
python system_test.py
```

## 🔗 Communication Protocol

### Standard Message Format:
```json
{
  "timestamp": 1693008000,
  "source": "ai-band-orchestrator",
  "target": "ai-band-plugin",
  "type": "file_notification",
  "data": {
    "files": ["bass_120bpm_C.mid"],
    "action": "play"
  }
}
```

### Plugin Registration:
```json
{
  "plugin_id": "unique_plugin_id",
  "name": "AI Band Plugin",
  "version": "1.0.0",
  "capabilities": ["midi_playback", "real_time_sync"],
  "endpoints": {
    "health": "http://localhost:9000/health",
    "control": "http://localhost:9000/control"
  }
}
```

This guide ensures all three components work seamlessly together. Apply these fixes to resolve integration issues and enable full end-to-end functionality.
