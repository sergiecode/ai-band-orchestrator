"""
Plugin Client - Communication with ai-band-plugin (JUCE)

Handles communication with the JUCE audio plugin through various methods:
- File-based communication (folder monitoring)
- HTTP requests to plugin endpoints
- WebSocket messaging for real-time updates

Author: Sergie Code
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import httpx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)


class PluginFileHandler(FileSystemEventHandler):
    """Handle file system events for plugin communication"""
    
    def __init__(self, plugin_client):
        self.plugin_client = plugin_client
    
    def on_created(self, event):
        """Handle new file creation"""
        if not event.is_directory and event.src_path.endswith('.mid'):
            asyncio.create_task(
                self.plugin_client.notify_file_created(event.src_path)
            )


class PluginClient:
    """Client for communicating with ai-band-plugin"""
    
    def __init__(self, plugin_folder: Optional[str] = None):
        """
        Initialize plugin client
        
        Args:
            plugin_folder: Path to folder monitored by plugin
        """
        self.plugin_folder = Path(plugin_folder) if plugin_folder else Path(__file__).parent.parent / "generated_files"
        self.plugin_folder.mkdir(exist_ok=True)
        
        self.observer = None
        self.file_handler = None
        self.connected_plugins: Dict[str, Dict] = {}
        
        # HTTP client for plugin communication
        self.http_client = httpx.AsyncClient(timeout=10.0)
        
        logger.info(f"Plugin client initialized with folder: {self.plugin_folder}")
    
    async def start_monitoring(self):
        """Start monitoring plugin folder for file changes"""
        try:
            self.file_handler = PluginFileHandler(self)
            self.observer = Observer()
            self.observer.schedule(
                self.file_handler,
                str(self.plugin_folder),
                recursive=True
            )
            self.observer.start()
            logger.info("Started file monitoring for plugin communication")
        except Exception as e:
            logger.error(f"Failed to start file monitoring: {e}")
    
    async def stop_monitoring(self):
        """Stop file monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("Stopped file monitoring")
        
        await self.http_client.aclose()
    
    def register_plugin(self, plugin_id: str, plugin_info: Dict):
        """Register a plugin for communication"""
        self.connected_plugins[plugin_id] = {
            **plugin_info,
            "last_heartbeat": asyncio.get_event_loop().time(),
            "active": True
        }
        logger.info(f"Registered plugin: {plugin_id}")
    
    def unregister_plugin(self, plugin_id: str):
        """Unregister a plugin"""
        self.connected_plugins.pop(plugin_id, None)
        logger.info(f"Unregistered plugin: {plugin_id}")
    
    async def notify_file_created(self, file_path: str):
        """Notify about new file creation"""
        file_name = Path(file_path).name
        logger.info(f"New MIDI file created: {file_name}")
        
        # Notify all connected plugins about new file
        for plugin_id in self.connected_plugins:
            await self.send_file_notification(plugin_id, file_name)
    
    async def send_file_notification(self, plugin_id: str, filename: str):
        """Send file notification to specific plugin"""
        try:
            plugin_info = self.connected_plugins.get(plugin_id)
            if not plugin_info:
                logger.warning(f"Plugin {plugin_id} not found")
                return
            
            # Try HTTP notification first (if plugin has HTTP endpoint)
            endpoint = plugin_info.get("http_endpoint")
            if endpoint:
                await self._send_http_notification(endpoint, filename)
            
            # File-based notification (create notification file)
            await self._create_notification_file(plugin_id, filename)
            
        except Exception as e:
            logger.error(f"Failed to notify plugin {plugin_id}: {e}")
    
    async def _send_http_notification(self, endpoint: str, filename: str):
        """Send HTTP notification to plugin"""
        try:
            payload = {
                "type": "file_ready",
                "filename": filename,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            response = await self.http_client.post(f"{endpoint}/api/notify", json=payload)
            response.raise_for_status()
            
            logger.info(f"HTTP notification sent to {endpoint}")
            
        except httpx.RequestError as e:
            logger.warning(f"HTTP notification failed: {e}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP notification error {e.response.status_code}: {e}")
    
    async def _create_notification_file(self, plugin_id: str, filename: str):
        """Create notification file for plugin"""
        try:
            notification_file = self.plugin_folder / f"{plugin_id}_notification.txt"
            
            notification_data = f"{filename}\\n{asyncio.get_event_loop().time()}\\n"
            
            with open(notification_file, "a") as f:
                f.write(notification_data)
            
            logger.info(f"Notification file updated for plugin {plugin_id}")
            
        except Exception as e:
            logger.error(f"Failed to create notification file: {e}")
    
    async def send_transport_state(self, plugin_id: str, transport_data: Dict):
        """Send transport state to plugin"""
        try:
            plugin_info = self.connected_plugins.get(plugin_id)
            if not plugin_info:
                return
            
            endpoint = plugin_info.get("http_endpoint")
            if endpoint:
                response = await self.http_client.post(
                    f"{endpoint}/api/transport",
                    json=transport_data
                )
                response.raise_for_status()
                logger.info(f"Transport state sent to plugin {plugin_id}")
                
        except Exception as e:
            logger.error(f"Failed to send transport state to {plugin_id}: {e}")
    
    async def request_plugin_status(self, plugin_id: str) -> Optional[Dict]:
        """Request status from plugin"""
        try:
            plugin_info = self.connected_plugins.get(plugin_id)
            if not plugin_info:
                return None
            
            endpoint = plugin_info.get("http_endpoint")
            if not endpoint:
                return {"status": "no_http_endpoint"}
            
            response = await self.http_client.get(f"{endpoint}/api/status")
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get status from plugin {plugin_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def send_generation_command(self, plugin_id: str, generation_params: Dict):
        """Send generation command to plugin"""
        try:
            plugin_info = self.connected_plugins.get(plugin_id)
            if not plugin_info:
                return False
            
            endpoint = plugin_info.get("http_endpoint")
            if endpoint:
                response = await self.http_client.post(
                    f"{endpoint}/api/generate",
                    json=generation_params
                )
                response.raise_for_status()
                logger.info(f"Generation command sent to plugin {plugin_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send generation command to {plugin_id}: {e}")
            return False
    
    def get_active_plugins(self) -> List[str]:
        """Get list of active plugin IDs"""
        current_time = asyncio.get_event_loop().time()
        active_plugins = []
        
        for plugin_id, info in self.connected_plugins.items():
            # Check if plugin has sent heartbeat recently (within 30 seconds)
            if current_time - info.get("last_heartbeat", 0) < 30:
                active_plugins.append(plugin_id)
            else:
                # Mark as inactive
                info["active"] = False
        
        return active_plugins
    
    def update_plugin_heartbeat(self, plugin_id: str):
        """Update plugin heartbeat timestamp"""
        if plugin_id in self.connected_plugins:
            self.connected_plugins[plugin_id]["last_heartbeat"] = asyncio.get_event_loop().time()
            self.connected_plugins[plugin_id]["active"] = True
    
    async def broadcast_to_all_plugins(self, message: Dict):
        """Broadcast message to all active plugins"""
        active_plugins = self.get_active_plugins()
        
        for plugin_id in active_plugins:
            try:
                plugin_info = self.connected_plugins[plugin_id]
                endpoint = plugin_info.get("http_endpoint")
                
                if endpoint:
                    await self.http_client.post(
                        f"{endpoint}/api/broadcast",
                        json=message
                    )
                    
            except Exception as e:
                logger.error(f"Failed to broadcast to plugin {plugin_id}: {e}")
        
        logger.info(f"Broadcasted message to {len(active_plugins)} plugins")
    
    def get_plugin_folder(self) -> Path:
        """Get the plugin monitoring folder path"""
        return self.plugin_folder
    
    def set_plugin_folder(self, folder_path: str):
        """Set a new plugin monitoring folder"""
        old_folder = self.plugin_folder
        self.plugin_folder = Path(folder_path)
        self.plugin_folder.mkdir(exist_ok=True)
        
        logger.info(f"Plugin folder changed from {old_folder} to {self.plugin_folder}")
        
        # Restart monitoring with new folder
        if self.observer:
            asyncio.create_task(self._restart_monitoring())
    
    async def _restart_monitoring(self):
        """Restart file monitoring with new folder"""
        await self.stop_monitoring()
        await self.start_monitoring()
    
    def get_plugin_statistics(self) -> Dict:
        """Get statistics about connected plugins"""
        total_plugins = len(self.connected_plugins)
        active_plugins = len(self.get_active_plugins())
        
        return {
            "total_plugins": total_plugins,
            "active_plugins": active_plugins,
            "inactive_plugins": total_plugins - active_plugins,
            "plugin_folder": str(self.plugin_folder),
            "monitoring_active": self.observer is not None and self.observer.is_alive()
        }
