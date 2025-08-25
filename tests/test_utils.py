"""
Test Utils - Utility functions tests

Tests logging setup, file management, configuration, and helper functions.

Author: Sergie Code
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
import sys
import time

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from utils import (
    setup_logging, FileManager, ConfigManager, 
    format_file_size, validate_midi_file, get_timestamp, sanitize_filename
)


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def file_manager(temp_directory):
    """Create a file manager for testing"""
    return FileManager(str(temp_directory))


def test_setup_logging():
    """Test logging setup"""
    logger = setup_logging("DEBUG")
    
    assert logger is not None
    assert logger.name == "ai-band-orchestrator"
    
    # Test logging
    logger.info("Test log message")
    
    # Check if log directory was created
    log_dir = Path(__file__).parent.parent / "logs"
    assert log_dir.exists()


def test_file_manager_initialization(temp_directory):
    """Test file manager initialization"""
    fm = FileManager(str(temp_directory))
    
    assert fm.base_path == temp_directory
    assert fm.generated_files_dir.exists()
    assert fm.logs_dir.exists()
    assert fm.monitoring_active is False


@pytest.mark.asyncio
async def test_file_manager_monitoring(file_manager):
    """Test file monitoring start/stop"""
    assert file_manager.monitoring_active is False
    
    await file_manager.start_monitoring()
    assert file_manager.monitoring_active is True
    
    await file_manager.stop_monitoring()
    assert file_manager.monitoring_active is False


def test_file_info_retrieval(file_manager):
    """Test file information retrieval"""
    # Create a test file
    test_file = file_manager.generated_files_dir / "test.mid"
    test_file.write_text("test midi content")
    
    file_info = file_manager.get_file_info("test.mid")
    
    assert file_info is not None
    assert file_info["filename"] == "test.mid"
    assert file_info["size"] > 0
    assert "created" in file_info
    assert "modified" in file_info


def test_file_info_nonexistent(file_manager):
    """Test file info for nonexistent file"""
    file_info = file_manager.get_file_info("nonexistent.mid")
    assert file_info is None


def test_list_generated_files(file_manager):
    """Test listing generated files"""
    # Create some test files
    for i in range(3):
        test_file = file_manager.generated_files_dir / f"test_{i}.mid"
        test_file.write_text(f"test midi content {i}")
        time.sleep(0.01)  # Small delay to ensure different timestamps
    
    files = file_manager.list_generated_files()
    
    assert len(files) == 3
    assert all("filename" in f for f in files)
    assert all("size" in f for f in files)
    assert all("age_seconds" in f for f in files)
    
    # Should be sorted by modification time (newest first)
    assert files[0]["modified"] >= files[1]["modified"]


def test_disk_usage(file_manager):
    """Test disk usage calculation"""
    # Create some test files
    for i in range(2):
        test_file = file_manager.generated_files_dir / f"usage_test_{i}.mid"
        test_file.write_bytes(b"0" * 1024)  # 1KB file
    
    usage = file_manager.get_disk_usage()
    
    assert "used_bytes" in usage
    assert "used_mb" in usage
    assert "available_bytes" in usage
    assert "available_mb" in usage
    assert "file_count" in usage
    assert usage["file_count"] >= 2


@pytest.mark.asyncio
async def test_metadata_save_load(file_manager):
    """Test metadata save and load"""
    metadata = {
        "tempo": 120,
        "key": "C",
        "tracks": ["bass", "drums"],
        "generated_at": "2025-08-25T10:30:00Z"
    }
    
    await file_manager.save_metadata("test_track.mid", metadata)
    
    loaded_metadata = await file_manager.load_metadata("test_track.mid")
    
    assert loaded_metadata == metadata


@pytest.mark.asyncio
async def test_metadata_nonexistent(file_manager):
    """Test loading metadata for nonexistent file"""
    metadata = await file_manager.load_metadata("nonexistent.mid")
    assert metadata is None


@pytest.mark.asyncio 
async def test_cleanup_old_files(file_manager):
    """Test cleanup of old files"""
    # Create some test files
    old_file = file_manager.generated_files_dir / "old.mid"
    new_file = file_manager.generated_files_dir / "new.mid"
    
    old_file.write_text("old content")
    new_file.write_text("new content")
    
    # Modify old file timestamp to make it appear old
    old_time = time.time() - (25 * 3600)  # 25 hours ago
    old_file.touch(times=(old_time, old_time))
    
    # Cleanup files older than 24 hours
    await file_manager.cleanup_old_files(max_age_hours=24)
    
    assert not old_file.exists()
    assert new_file.exists()


def test_config_manager_initialization():
    """Test configuration manager initialization"""
    cm = ConfigManager()
    
    assert cm.config is not None
    assert "server" in cm.config
    assert "backend" in cm.config
    assert "plugin" in cm.config


def test_config_manager_get_set():
    """Test configuration get/set operations"""
    cm = ConfigManager()
    
    # Test getting existing value
    port = cm.get("server.port", 8080)
    assert port == 8000  # Default value from config
    
    # Test setting value
    cm.set("server.debug", True)
    assert cm.get("server.debug") is True
    
    # Test getting nonexistent value with default
    value = cm.get("nonexistent.key", "default")
    assert value == "default"


def test_format_file_size():
    """Test file size formatting"""
    assert format_file_size(0) == "0 B"
    assert format_file_size(1024) == "1.0 KB"
    assert format_file_size(1024 * 1024) == "1.0 MB"
    assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


def test_validate_midi_file(temp_directory):
    """Test MIDI file validation"""
    # Create a valid MIDI file (with proper header)
    valid_midi = temp_directory / "valid.mid"
    valid_midi.write_bytes(b'MThd' + b'\\x00' * 20)  # MIDI header + some data
    
    # Create an invalid file
    invalid_file = temp_directory / "invalid.txt"
    invalid_file.write_text("not a midi file")
    
    # Create a file with wrong extension but valid content
    wrong_ext = temp_directory / "wrong.txt"
    wrong_ext.write_bytes(b'MThd' + b'\\x00' * 20)
    
    assert validate_midi_file(valid_midi) is True
    assert validate_midi_file(invalid_file) is False
    assert validate_midi_file(wrong_ext) is False
    assert validate_midi_file(temp_directory / "nonexistent.mid") is False


def test_get_timestamp():
    """Test timestamp generation"""
    timestamp = get_timestamp()
    
    assert isinstance(timestamp, str)
    assert "T" in timestamp  # ISO format should have T separator
    assert len(timestamp) > 10  # Should be a reasonable length


def test_sanitize_filename():
    """Test filename sanitization"""
    # Test with invalid characters
    dirty_name = 'test<>:"/\\|?*file.mid'
    clean_name = sanitize_filename(dirty_name)
    
    assert "<" not in clean_name
    assert ">" not in clean_name
    assert ":" not in clean_name
    assert '"' not in clean_name
    assert "/" not in clean_name
    assert "\\" not in clean_name
    assert "|" not in clean_name
    assert "?" not in clean_name
    assert "*" not in clean_name
    
    # Test with very long filename
    long_name = "a" * 300 + ".mid"
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) <= 255


def test_config_file_creation(temp_directory):
    """Test configuration file creation and loading"""
    config_file = temp_directory / "test_config.json"
    
    # Create config manager with custom file
    cm = ConfigManager(str(config_file))
    
    # Modify config and save
    cm.set("test.value", "test_data")
    cm.save_config()
    
    assert config_file.exists()
    
    # Load config in new manager
    cm2 = ConfigManager(str(config_file))
    assert cm2.get("test.value") == "test_data"


if __name__ == "__main__":
    print("Running utility tests...")
    pytest.main([__file__, "-v"])
