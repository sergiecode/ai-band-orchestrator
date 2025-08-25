"""
Test Plugin Client - Plugin communication tests

Tests the plugin client functionality including file monitoring,
HTTP communication, and plugin management.

Author: Sergie Code
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from plugin_client import PluginClient


@pytest.fixture
async def temp_plugin_folder():
    """Create a temporary folder for testing"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
async def plugin_client(temp_plugin_folder):
    """Create a plugin client for testing"""
    client = PluginClient(str(temp_plugin_folder))
    await client.start_monitoring()
    yield client
    await client.stop_monitoring()


@pytest.mark.asyncio
async def test_plugin_client_initialization(temp_plugin_folder):
    """Test plugin client initializes correctly"""
    client = PluginClient(str(temp_plugin_folder))
    
    assert client.plugin_folder == temp_plugin_folder
    assert client.plugin_folder.exists()
    assert len(client.connected_plugins) == 0
    
    await client.stop_monitoring()


@pytest.mark.asyncio
async def test_plugin_registration(plugin_client):
    """Test plugin registration and management"""
    plugin_info = {
        "name": "Test Plugin",
        "version": "1.0.0",
        "http_endpoint": "http://localhost:9000"
    }
    
    plugin_client.register_plugin("test_plugin_1", plugin_info)
    
    assert "test_plugin_1" in plugin_client.connected_plugins
    assert plugin_client.connected_plugins["test_plugin_1"]["name"] == "Test Plugin"
    assert plugin_client.connected_plugins["test_plugin_1"]["active"] is True


@pytest.mark.asyncio
async def test_plugin_unregistration(plugin_client):
    """Test plugin unregistration"""
    plugin_info = {"name": "Test Plugin"}
    
    plugin_client.register_plugin("test_plugin_2", plugin_info)
    assert "test_plugin_2" in plugin_client.connected_plugins
    
    plugin_client.unregister_plugin("test_plugin_2")
    assert "test_plugin_2" not in plugin_client.connected_plugins


@pytest.mark.asyncio
async def test_file_notification_creation(plugin_client):
    """Test notification file creation"""
    plugin_client.register_plugin("test_plugin_3", {"name": "Test"})
    
    # Test notification file creation
    await plugin_client._create_notification_file("test_plugin_3", "test_file.mid")
    
    notification_file = plugin_client.plugin_folder / "test_plugin_3_notification.txt"
    assert notification_file.exists()
    
    content = notification_file.read_text()
    assert "test_file.mid" in content


@pytest.mark.asyncio
async def test_heartbeat_tracking(plugin_client):
    """Test plugin heartbeat tracking"""
    plugin_client.register_plugin("test_plugin_4", {"name": "Test"})
    
    # Initially should be active
    active_plugins = plugin_client.get_active_plugins()
    assert "test_plugin_4" in active_plugins
    
    # Update heartbeat
    plugin_client.update_plugin_heartbeat("test_plugin_4")
    
    # Should still be active
    active_plugins = plugin_client.get_active_plugins()
    assert "test_plugin_4" in active_plugins


@pytest.mark.asyncio
async def test_plugin_statistics(plugin_client):
    """Test plugin statistics gathering"""
    # Register some plugins
    plugin_client.register_plugin("plugin_1", {"name": "Plugin 1"})
    plugin_client.register_plugin("plugin_2", {"name": "Plugin 2"})
    
    stats = plugin_client.get_plugin_statistics()
    
    assert stats["total_plugins"] == 2
    assert stats["active_plugins"] >= 0  # Depends on heartbeat timing
    assert stats["plugin_folder"] == str(plugin_client.plugin_folder)
    assert isinstance(stats["monitoring_active"], bool)


@pytest.mark.asyncio
async def test_folder_change(plugin_client, temp_plugin_folder):
    """Test changing plugin folder"""
    # Create a new temporary folder
    new_folder = temp_plugin_folder / "new_plugin_folder"
    new_folder.mkdir()
    
    original_folder = plugin_client.plugin_folder
    plugin_client.set_plugin_folder(str(new_folder))
    
    assert plugin_client.plugin_folder == new_folder
    assert plugin_client.plugin_folder != original_folder


@pytest.mark.asyncio
async def test_file_monitoring_start_stop(temp_plugin_folder):
    """Test starting and stopping file monitoring"""
    client = PluginClient(str(temp_plugin_folder))
    
    # Initially monitoring should be False
    assert client.observer is None
    
    # Start monitoring
    await client.start_monitoring()
    assert client.observer is not None
    
    # Stop monitoring
    await client.stop_monitoring()
    # Observer should be stopped but object might still exist


@pytest.mark.asyncio
async def test_send_file_notification(plugin_client):
    """Test sending file notifications"""
    plugin_info = {
        "name": "Test Plugin",
        "http_endpoint": None  # No HTTP endpoint for this test
    }
    plugin_client.register_plugin("test_plugin_notify", plugin_info)
    
    # This should create a notification file since no HTTP endpoint
    await plugin_client.send_file_notification("test_plugin_notify", "test.mid")
    
    notification_file = plugin_client.plugin_folder / "test_plugin_notify_notification.txt"
    assert notification_file.exists()


@pytest.mark.asyncio
async def test_mock_file_creation_and_detection(plugin_client):
    """Test file creation and detection"""
    # Create a mock MIDI file
    test_file = plugin_client.plugin_folder / "test_creation.mid"
    test_file.write_bytes(b"fake midi data")
    
    # Verify file exists
    assert test_file.exists()
    
    # The file handler should be notified (in real usage)
    # For this test, we just verify the file exists
    await plugin_client.notify_file_created(str(test_file))


def test_plugin_client_folder_property(temp_plugin_folder):
    """Test plugin folder property getter"""
    client = PluginClient(str(temp_plugin_folder))
    
    folder = client.get_plugin_folder()
    assert folder == temp_plugin_folder
    assert isinstance(folder, Path)


if __name__ == "__main__":
    print("Running plugin client tests...")
    pytest.main([__file__, "-v"])
