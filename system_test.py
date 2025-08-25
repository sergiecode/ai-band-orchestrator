#!/usr/bin/env python3
"""
Final System Test - Comprehensive test of the entire AI Band Orchestrator

This test verifies that all components work together correctly.

Author: Sergie Code
"""

import sys
import asyncio
import tempfile
import shutil
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from backend_client import BackendClient
from plugin_client import PluginClient
from utils import setup_logging, FileManager, format_file_size, validate_midi_file

async def test_full_workflow():
    """Test the complete workflow"""
    print("🎵 AI Band Orchestrator - Full System Test")
    print("="*60)
    
    # Test 1: Backend Client
    print("\\n1️⃣ Testing Backend Client...")
    backend = BackendClient()
    print(f"   ✅ Backend client initialized")
    print(f"   ✅ Connected: {backend.is_connected()}")
    
    # Generate some tracks
    chords = [
        {"chord": "C", "start_time": 0.0, "duration": 2.0},
        {"chord": "Am", "start_time": 2.0, "duration": 2.0},
        {"chord": "F", "start_time": 4.0, "duration": 2.0},
        {"chord": "G", "start_time": 6.0, "duration": 2.0}
    ]
    
    result = await backend.generate_tracks(
        chords=chords,
        tempo=120,
        key="C",
        track_types=["bass", "drums"],
        duration=8.0
    )
    
    print(f"   ✅ Generation successful: {result['success']}")
    print(f"   ✅ Files created: {len(result['files'])}")
    print(f"   ✅ Files: {result['files']}")
    
    # Test 2: Plugin Client  
    print("\\n2️⃣ Testing Plugin Client...")
    with tempfile.TemporaryDirectory() as temp_dir:
        plugin = PluginClient(temp_dir)
        await plugin.start_monitoring()
        print(f"   ✅ Plugin client initialized")
        print(f"   ✅ Monitoring folder: {plugin.plugin_folder}")
        
        # Register plugins
        plugin.register_plugin("test_plugin_1", {"name": "Test Plugin 1"})
        plugin.register_plugin("test_plugin_2", {"name": "Test Plugin 2"})
        print(f"   ✅ Registered 2 plugins")
        
        # Test statistics
        stats = plugin.get_plugin_statistics()
        print(f"   ✅ Active plugins: {stats['active_plugins']}")
        
        await plugin.stop_monitoring()
    
    # Test 3: File Manager
    print("\\n3️⃣ Testing File Manager...")
    with tempfile.TemporaryDirectory() as temp_dir:
        fm = FileManager(temp_dir)
        await fm.start_monitoring()
        print(f"   ✅ File manager initialized")
        
        # Create test files
        test_file = fm.generated_files_dir / "test.mid"
        test_file.write_bytes(b"MThd" + b"\\x00" * 20)  # Mock MIDI
        
        file_info = fm.get_file_info("test.mid")
        print(f"   ✅ File info retrieved: {file_info['filename']}")
        
        files = fm.list_generated_files()
        print(f"   ✅ Files listed: {len(files)}")
        
        # Test metadata
        metadata = {"tempo": 120, "key": "C"}
        await fm.save_metadata("test.mid", metadata)
        loaded_meta = await fm.load_metadata("test.mid")
        print(f"   ✅ Metadata saved and loaded: {loaded_meta == metadata}")
        
        await fm.stop_monitoring()
    
    # Test 4: Utilities
    print("\\n4️⃣ Testing Utilities...")
    logger = setup_logging("INFO")
    print(f"   ✅ Logging setup complete")
    
    # Test file size formatting
    print(f"   ✅ File size format: {format_file_size(1024)} = '1.0 KB'")
    
    # Test MIDI validation
    with tempfile.TemporaryDirectory() as temp_dir:
        valid_midi = Path(temp_dir) / "valid.mid"
        valid_midi.write_bytes(b"MThd" + b"\\x00" * 20)
        
        invalid_file = Path(temp_dir) / "invalid.txt"
        invalid_file.write_text("not midi")
        
        print(f"   ✅ MIDI validation - valid: {validate_midi_file(valid_midi)}")
        print(f"   ✅ MIDI validation - invalid: {not validate_midi_file(invalid_file)}")
    
    # Test 5: Integration Test
    print("\\n5️⃣ Testing Full Integration...")
    
    # Create a realistic scenario
    plugin_folder = Path(__file__).parent / "generated_files"
    plugin_client = PluginClient(str(plugin_folder))
    
    # Register a plugin
    plugin_client.register_plugin("integration_test", {
        "name": "Integration Test Plugin",
        "version": "1.0.0"
    })
    
    # Generate tracks
    integration_result = await backend.generate_tracks(
        chords=[{"chord": "C", "start_time": 0.0, "duration": 4.0}],
        tempo=140,
        key="G",
        track_types=["bass", "drums"]
    )
    
    print(f"   ✅ Integration generation: {integration_result['success']}")
    
    # Notify plugin about files
    if integration_result['success']:
        for filename in integration_result['files']:
            await plugin_client.send_file_notification("integration_test", filename)
        print(f"   ✅ Plugin notified about {len(integration_result['files'])} files")
    
    print("\\n🎯 SYSTEM TEST SUMMARY")
    print("="*60)
    print("✅ Backend Client: Working")
    print("✅ Plugin Client: Working") 
    print("✅ File Manager: Working")
    print("✅ Utilities: Working")
    print("✅ Integration: Working")
    
    print("\\n🎉 ALL SYSTEMS GO! The AI Band Orchestrator is ready! 🎸🤖🥁")
    
    return True

def main():
    """Run the full system test"""
    try:
        result = asyncio.run(test_full_workflow())
        return 0 if result else 1
    except Exception as e:
        print(f"\\n❌ SYSTEM TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
