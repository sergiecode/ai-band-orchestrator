"""
Test Backend Client - Unit tests for backend integration

Author: Sergie Code
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from backend_client import BackendClient


@pytest.fixture
def backend_client():
    """Create a backend client for testing"""
    return BackendClient()


@pytest.mark.asyncio
async def test_backend_client_initialization(backend_client):
    """Test backend client initializes correctly"""
    assert backend_client is not None
    assert hasattr(backend_client, 'output_dir')
    assert backend_client.output_dir.exists()


@pytest.mark.asyncio
async def test_mock_track_generation(backend_client):
    """Test mock track generation when backend is not available"""
    chords = [
        {"chord": "C", "start_time": 0.0, "duration": 2.0},
        {"chord": "G", "start_time": 2.0, "duration": 2.0}
    ]
    
    result = await backend_client.generate_tracks(
        chords=chords,
        tempo=120,
        key="C",
        track_types=["bass", "drums"]
    )
    
    assert result["success"] == True
    assert len(result["files"]) == 2
    assert "bass" in result["files"][0] or "bass" in result["files"][1]
    assert "drums" in result["files"][0] or "drums" in result["files"][1]
    assert result["metadata"]["tempo"] == 120
    assert result["metadata"]["key"] == "C"


@pytest.mark.asyncio
async def test_chord_analysis(backend_client):
    """Test chord analysis functionality"""
    chords = [
        {"chord": "C", "start_time": 0.0, "duration": 2.0},
        {"chord": "Am", "start_time": 2.0, "duration": 2.0},
        {"chord": "F", "start_time": 4.0, "duration": 2.0},
        {"chord": "G", "start_time": 6.0, "duration": 2.0}
    ]
    
    result = await backend_client.analyze_chords(chords)
    
    assert "key" in result
    assert "tempo" in result
    assert "analysis" in result


@pytest.mark.asyncio
async def test_generation_error_handling(backend_client):
    """Test error handling in track generation"""
    # Test with invalid input
    result = await backend_client.generate_tracks(
        chords=[],  # Empty chord list
        tempo=120,
        key="C"
    )
    
    # Should still succeed with mock mode or handle gracefully
    assert "success" in result
    assert "files" in result
    assert "metadata" in result


def test_is_connected(backend_client):
    """Test connection status check"""
    # In test environment, backend likely not available
    # So this should return False
    connected = backend_client.is_connected()
    assert isinstance(connected, bool)


@pytest.mark.asyncio
async def test_file_creation(backend_client):
    """Test that generated files are actually created"""
    chords = [{"chord": "C", "start_time": 0.0, "duration": 4.0}]
    
    result = await backend_client.generate_tracks(
        chords=chords,
        tempo=120,
        track_types=["bass"]
    )
    
    if result["success"]:
        # Check that files exist
        for filename in result["files"]:
            file_path = backend_client.output_dir / filename
            assert file_path.exists()
            assert file_path.stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__])
