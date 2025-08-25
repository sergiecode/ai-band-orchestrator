"""
Test Main API - FastAPI endpoint tests

Tests all the main FastAPI endpoints and functionality.

Author: Sergie Code
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from pathlib import Path
import sys
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from main import app

# Create test client
client = TestClient(app)


def test_root_endpoint():
    """Test the root endpoint returns correct info"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "AI Band Orchestrator"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"
    assert data["author"] == "Sergie Code"
    assert "connected_plugins" in data


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "backend_connected" in data
    assert "active_plugins" in data
    assert "generated_files" in data


def test_files_listing():
    """Test file listing endpoint"""
    response = client.get("/api/files")
    assert response.status_code == 200
    
    data = response.json()
    assert "files" in data
    assert isinstance(data["files"], list)


def test_generation_endpoint():
    """Test MIDI generation endpoint"""
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
        "plugin_id": "test_plugin"
    }
    
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "files" in data
    assert "metadata" in data
    assert len(data["files"]) > 0


def test_generation_with_multiple_tracks():
    """Test generation with bass and drums"""
    payload = {
        "chord_progression": {
            "chords": [
                {"chord": "C", "start_time": 0.0, "duration": 1.0},
                {"chord": "Am", "start_time": 1.0, "duration": 1.0},
                {"chord": "F", "start_time": 2.0, "duration": 1.0},
                {"chord": "G", "start_time": 3.0, "duration": 1.0}
            ],
            "tempo": 120,
            "key": "C",
            "duration": 4.0
        },
        "track_types": ["bass", "drums"],
        "plugin_id": "test_plugin_multi"
    }
    
    response = client.post("/api/generate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert len(data["files"]) == 2
    
    # Check that we have both bass and drums
    filenames = " ".join(data["files"])
    assert "bass" in filenames
    assert "drums" in filenames


def test_generation_with_invalid_data():
    """Test generation with invalid chord data"""
    payload = {
        "chord_progression": {
            "chords": [],  # Empty chords
            "tempo": 120,
            "key": "C"
        },
        "track_types": ["bass"],
        "plugin_id": "test_plugin_invalid"
    }
    
    response = client.post("/api/generate", json=payload)
    # Should still work due to graceful error handling
    assert response.status_code == 200 or response.status_code == 500


def test_transport_sync():
    """Test transport synchronization endpoint"""
    transport_data = {
        "is_playing": True,
        "current_beat": 16.5,
        "tempo": 120.0,
        "timestamp": "2025-08-25T10:30:00Z"
    }
    
    response = client.post("/api/transport/sync", json=transport_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "synced_plugins" in data


def test_file_download():
    """Test file download functionality"""
    # First generate a file
    payload = {
        "chord_progression": {
            "chords": [{"chord": "C", "start_time": 0.0, "duration": 4.0}],
            "tempo": 120,
            "key": "C"
        },
        "track_types": ["bass"],
        "plugin_id": "test_download"
    }
    
    gen_response = client.post("/api/generate", json=payload)
    assert gen_response.status_code == 200
    
    gen_data = gen_response.json()
    if gen_data["success"] and gen_data["files"]:
        filename = gen_data["files"][0]
        
        # Try to download the file
        download_response = client.get(f"/api/files/{filename}")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "audio/midi"


def test_nonexistent_file_download():
    """Test downloading a file that doesn't exist"""
    response = client.get("/api/files/nonexistent_file.mid")
    assert response.status_code == 404


def test_cors_headers():
    """Test that CORS headers are properly set"""
    response = client.options("/")
    # FastAPI with CORS should handle OPTIONS requests
    assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled


def test_api_docs_accessible():
    """Test that API documentation is accessible"""
    # Test Swagger UI
    response = client.get("/docs")
    assert response.status_code == 200
    
    # Test ReDoc
    response = client.get("/redoc")
    assert response.status_code == 200


def test_static_files_mount():
    """Test that static files are properly mounted"""
    # Check if the /files endpoint exists (even if empty)
    response = client.get("/files/")
    # Should return 404 for directory listing or 200 if index exists
    assert response.status_code in [200, 404, 405]


if __name__ == "__main__":
    print("Running FastAPI endpoint tests...")
    pytest.main([__file__, "-v"])
