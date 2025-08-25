"""
Utilities - Helper functions for AI Band Orchestrator

Provides logging setup, file management, and other utility functions
for the orchestrator service.

Author: Sergie Code
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import structlog


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup structured logging for the application"""
    
    # Create logs directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Setup standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "orchestrator.log"),
        ]
    )
    
    logger = logging.getLogger("ai-band-orchestrator")
    logger.info("Logging system initialized")
    
    return logger


class FileManager:
    """Manages file operations and monitoring for the orchestrator"""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.generated_files_dir = self.base_path / "generated_files"
        self.logs_dir = self.base_path / "logs"
        self.monitoring_active = False
        
        # Create directories
        self.generated_files_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
    
    async def start_monitoring(self):
        """Start file system monitoring"""
        self.monitoring_active = True
        self.logger.info("File monitoring started")
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    async def stop_monitoring(self):
        """Stop file system monitoring"""
        self.monitoring_active = False
        self.logger.info("File monitoring stopped")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old files"""
        while self.monitoring_active:
            try:
                await self.cleanup_old_files()
                await asyncio.sleep(3600)  # Run every hour
            except Exception as e:
                self.logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up files older than specified hours"""
        current_time = datetime.now().timestamp()
        max_age_seconds = max_age_hours * 3600
        
        cleaned_count = 0
        
        for file_path in self.generated_files_dir.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        cleaned_count += 1
                        self.logger.info(f"Cleaned up old file: {file_path.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to clean up {file_path.name}: {e}")
        
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old files")
    
    def get_file_info(self, filename: str) -> Optional[Dict]:
        """Get information about a file"""
        file_path = self.generated_files_dir / filename
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        return {
            "filename": filename,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "path": str(file_path)
        }
    
    def list_generated_files(self) -> List[Dict]:
        """List all generated MIDI files with metadata"""
        files = []
        
        for file_path in self.generated_files_dir.glob("*.mid"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "modified": stat.st_mtime,
                    "age_seconds": datetime.now().timestamp() - stat.st_mtime
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files
    
    def get_disk_usage(self) -> Dict:
        """Get disk usage information"""
        try:
            # Get directory size
            total_size = sum(
                f.stat().st_size 
                for f in self.generated_files_dir.rglob('*') 
                if f.is_file()
            )
            
            # Get available space - Windows and Unix compatibility
            if os.name == 'nt':  # Windows
                import shutil
                total, used, free = shutil.disk_usage(str(self.generated_files_dir))
                available_space = free
            else:  # Unix/Linux
                stat = os.statvfs(str(self.generated_files_dir))
                available_space = stat.f_bavail * stat.f_frsize
            
            return {
                "used_bytes": total_size,
                "used_mb": round(total_size / (1024 * 1024), 2),
                "available_bytes": available_space,
                "available_mb": round(available_space / (1024 * 1024), 2),
                "file_count": len(list(self.generated_files_dir.glob("*.mid")))
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {e}")
            return {
                "used_bytes": 0,
                "used_mb": 0,
                "available_bytes": 0,
                "available_mb": 0,
                "file_count": 0,
                "error": str(e)
            }
    
    async def save_metadata(self, filename: str, metadata: Dict):
        """Save metadata for a generated file"""
        metadata_file = self.generated_files_dir / f"{filename}.meta.json"
        
        try:
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Saved metadata for {filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save metadata for {filename}: {e}")
    
    async def load_metadata(self, filename: str) -> Optional[Dict]:
        """Load metadata for a file"""
        metadata_file = self.generated_files_dir / f"{filename}.meta.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load metadata for {filename}: {e}")
            return None


class ConfigManager:
    """Manages configuration for the orchestrator"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = Path(config_file) if config_file else Path(__file__).parent.parent / "config.json"
        self.config = self._load_default_config()
        self._load_config()
    
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8000,
                "reload": True
            },
            "backend": {
                "path": "../ai-band-backend/src",
                "timeout": 30
            },
            "plugin": {
                "folder": "./generated_files",
                "cleanup_hours": 24,
                "max_files": 1000
            },
            "logging": {
                "level": "INFO",
                "file": "./logs/orchestrator.log"
            },
            "websocket": {
                "heartbeat_interval": 30,
                "connection_timeout": 60
            }
        }
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    loaded_config = json.load(f)
                    
                # Merge with defaults
                self._deep_update(self.config, loaded_config)
                
            except Exception as e:
                logging.error(f"Failed to load config from {self.config_file}: {e}")
    
    def _deep_update(self, base_dict: Dict, update_dict: Dict):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config: {e}")
    
    def get(self, key_path: str, default=None):
        """Get configuration value by dot-separated path"""
        keys = key_path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value):
        """Set configuration value by dot-separated path"""
        keys = key_path.split(".")
        config_section = self.config
        
        for key in keys[:-1]:
            if key not in config_section:
                config_section[key] = {}
            config_section = config_section[key]
        
        config_section[keys[-1]] = value


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"


def validate_midi_file(file_path: Path) -> bool:
    """Validate if a file is a proper MIDI file"""
    try:
        if not file_path.exists() or file_path.suffix.lower() not in ['.mid', '.midi']:
            return False
        
        # Check MIDI header
        with open(file_path, 'rb') as f:
            header = f.read(4)
            return header == b'MThd'
            
    except Exception:
        return False


def get_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename
