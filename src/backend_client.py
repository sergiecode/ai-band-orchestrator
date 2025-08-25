"""
Backend Client - Integration with ai-band-backend

Handles communication with the AI Band Backend for MIDI generation.
This module abstracts the backend interaction and provides async methods
for the orchestrator to generate tracks.

Author: Sergie Code
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add ai-band-backend to path
backend_path = Path(__file__).parent.parent.parent / "ai-band-backend" / "src"
if backend_path.exists():
    sys.path.append(str(backend_path))

try:
    from chord_detection import ChordDetector
    from midi_generator import MidiGenerator
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False
    ChordDetector = None
    MidiGenerator = None

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for communicating with ai-band-backend"""
    
    def __init__(self):
        self.chord_detector = None
        self.midi_generator = None
        self.output_dir = Path(__file__).parent.parent / "generated_files"
        self.output_dir.mkdir(exist_ok=True)
        
        global BACKEND_AVAILABLE
        if BACKEND_AVAILABLE:
            try:
                self.chord_detector = ChordDetector()
                self.midi_generator = MidiGenerator()
                logger.info("Backend client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize backend: {e}")
                BACKEND_AVAILABLE = False
        else:
            logger.warning("AI Band Backend not available - using mock mode")
    
    def is_connected(self) -> bool:
        """Check if backend is available"""
        return BACKEND_AVAILABLE and self.midi_generator is not None
    
    async def generate_tracks(
        self,
        chords: List[Dict[str, Any]],
        tempo: int = 120,
        key: str = "C",
        track_types: List[str] = None,
        duration: float = 32.0
    ) -> Dict[str, Any]:
        """
        Generate MIDI tracks using the backend
        
        Args:
            chords: List of chord dictionaries with chord, start_time, duration
            tempo: BPM for generation
            key: Musical key
            track_types: Types of tracks to generate (bass, drums, etc.)
            duration: Total duration in beats
            
        Returns:
            Dict with success, files, metadata, and error info
        """
        if track_types is None:
            track_types = ["bass", "drums"]
        
        try:
            if not self.is_connected():
                # Mock mode for development
                return await self._generate_mock_tracks(chords, tempo, key, track_types, duration)
            
            # Real backend generation
            return await self._generate_real_tracks(chords, tempo, key, track_types, duration)
            
        except Exception as e:
            logger.error(f"Track generation failed: {e}")
            return {
                "success": False,
                "files": [],
                "metadata": {},
                "error": str(e)
            }
    
    async def _generate_real_tracks(
        self,
        chords: List[Dict[str, Any]],
        tempo: int,
        key: str,
        track_types: List[str],
        duration: float
    ) -> Dict[str, Any]:
        """Generate tracks using real backend"""
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        def _sync_generate():
            generated_files = []
            metadata = {
                "tempo": tempo,
                "key": key,
                "duration": duration,
                "chord_count": len(chords)
            }
            
            # Generate each track type
            for track_type in track_types:
                try:
                    if track_type == "bass":
                        midi_data = self.midi_generator.generate_bass_track(
                            chords, tempo=tempo, key=key
                        )
                    elif track_type == "drums":
                        midi_data = self.midi_generator.generate_drum_track(
                            chords, tempo=tempo, duration=duration
                        )
                    else:
                        logger.warning(f"Unknown track type: {track_type}")
                        continue
                    
                    # Save file
                    filename = f"{track_type}_{tempo}bpm_{key}_{len(chords)}chords.mid"
                    file_path = self.output_dir / filename
                    midi_data.write(str(file_path))
                    
                    generated_files.append(filename)
                    logger.info(f"Generated {track_type} track: {filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to generate {track_type}: {e}")
            
            return generated_files, metadata
        
        generated_files, metadata = await loop.run_in_executor(None, _sync_generate)
        
        return {
            "success": len(generated_files) > 0,
            "files": generated_files,
            "metadata": metadata,
            "error": None
        }
    
    async def _generate_mock_tracks(
        self,
        chords: List[Dict[str, Any]],
        tempo: int,
        key: str,
        track_types: List[str],
        duration: float
    ) -> Dict[str, Any]:
        """Generate mock tracks for development/testing"""
        
        # Simulate generation delay
        await asyncio.sleep(0.5)
        
        generated_files = []
        metadata = {
            "tempo": tempo,
            "key": key,
            "duration": duration,
            "chord_count": len(chords),
            "mock_mode": True
        }
        
        # Create mock MIDI files
        for track_type in track_types:
            filename = f"mock_{track_type}_{tempo}bpm_{key}_{len(chords)}chords.mid"
            file_path = self.output_dir / filename
            
            # Create a minimal MIDI file for testing
            mock_content = self._create_mock_midi_content(track_type, tempo, duration)
            
            with open(file_path, "wb") as f:
                f.write(mock_content)
            
            generated_files.append(filename)
            logger.info(f"Generated mock {track_type} track: {filename}")
        
        return {
            "success": True,
            "files": generated_files,
            "metadata": metadata,
            "error": None
        }
    
    def _create_mock_midi_content(self, track_type: str, tempo: int, duration: float) -> bytes:
        """Create minimal MIDI file content for testing"""
        # This is a very basic MIDI file header + minimal data
        # In real implementation, you'd use pretty_midi to create proper files
        
        midi_header = bytes([
            # MIDI file header
            0x4D, 0x54, 0x68, 0x64,  # "MThd"
            0x00, 0x00, 0x00, 0x06,  # Header length
            0x00, 0x01,              # Format type 1
            0x00, 0x02,              # Number of tracks
            0x01, 0xE0,              # Ticks per quarter note (480)
        ])
        
        # Simple track with a few notes
        track_data = bytes([
            # Track header
            0x4D, 0x54, 0x72, 0x6B,  # "MTrk"
            0x00, 0x00, 0x00, 0x0B,  # Track length
            # Simple note on/off sequence
            0x00, 0x90, 0x3C, 0x64,  # Note on C4
            0x60, 0x80, 0x3C, 0x64,  # Note off C4
            0x00, 0xFF, 0x2F, 0x00   # End of track
        ])
        
        return midi_header + track_data
    
    async def analyze_chords(self, chords: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze chord progression for musical information"""
        if not self.is_connected():
            return {
                "key": "C",
                "tempo": 120,
                "analysis": "Mock analysis - backend not available"
            }
        
        try:
            loop = asyncio.get_event_loop()
            
            def _sync_analyze():
                tempo = self.chord_detector.detect_tempo(chords)
                key = self.chord_detector.detect_key(chords) 
                analysis = self.chord_detector.analyze_chord_progression(chords)
                return tempo, key, analysis
            
            tempo, key, analysis = await loop.run_in_executor(None, _sync_analyze)
            
            return {
                "tempo": tempo,
                "key": key,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Chord analysis failed: {e}")
            return {
                "key": "C",
                "tempo": 120,
                "analysis": f"Analysis failed: {e}"
            }
