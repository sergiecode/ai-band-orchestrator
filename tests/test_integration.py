"""
Integration Tests - Test the complete orchestrator workflow

Author: Sergie Code
"""

import pytest
import httpx
import asyncio
import json
from pathlib import Path


@pytest.mark.asyncio
async def test_server_health():
    """Test if server responds to health check"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert data["status"] == "healthy"
            
        except httpx.ConnectError:
            pytest.skip("Server not running - start with 'python src/main.py'")


@pytest.mark.asyncio 
async def test_generation_api():
    """Test the generation API endpoint"""
    async with httpx.AsyncClient() as client:
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
                "plugin_id": "test_plugin"
            }
            
            response = await client.post(
                "http://localhost:8000/api/generate",
                json=payload,
                timeout=30.0
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "files" in data
            assert len(data["files"]) > 0
            
        except httpx.ConnectError:
            pytest.skip("Server not running")


@pytest.mark.asyncio
async def test_file_listing():
    """Test file listing API"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/files")
            assert response.status_code == 200
            
            data = response.json()
            assert "files" in data
            assert isinstance(data["files"], list)
            
        except httpx.ConnectError:
            pytest.skip("Server not running")


def test_project_structure():
    """Test that project structure is correct"""
    base_path = Path(__file__).parent.parent
    
    # Check main directories exist
    assert (base_path / "src").exists()
    assert (base_path / "generated_files").exists()
    assert (base_path / "logs").exists()
    assert (base_path / "tests").exists()
    
    # Check main files exist
    assert (base_path / "src" / "main.py").exists()
    assert (base_path / "src" / "backend_client.py").exists()
    assert (base_path / "src" / "plugin_client.py").exists()
    assert (base_path / "src" / "utils.py").exists()
    assert (base_path / "requirements.txt").exists()
    assert (base_path / "README.md").exists()


def test_requirements_file():
    """Test that requirements.txt contains necessary packages"""
    requirements_path = Path(__file__).parent.parent / "requirements.txt"
    assert requirements_path.exists()
    
    content = requirements_path.read_text()
    
    # Check for essential packages
    assert "fastapi" in content
    assert "uvicorn" in content
    assert "websockets" in content
    assert "pretty_midi" in content
    assert "mido" in content


if __name__ == "__main__":
    print("Running integration tests...")
    print("Make sure to start the server first: python src/main.py")
    pytest.main([__file__, "-v"])
