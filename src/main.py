"""
AI Band Orchestrator - Main Server Application

This is the central coordination server for the AI Band ecosystem.
It acts as a bridge between the ai-band-backend (MIDI generation) 
and ai-band-plugin (JUCE audio plugin).

Author: Sergie Code
- LinkedIn: https://www.linkedin.com/in/sergiecode/
- YouTube: https://www.youtube.com/@SergieCode  
- GitHub: https://github.com/sergiecode
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add ai-band-backend to path for integration
backend_path = Path(__file__).parent.parent.parent / "ai-band-backend" / "src"
if backend_path.exists():
    sys.path.append(str(backend_path))

# Import local modules
try:
    from .backend_client import BackendClient
    from .plugin_client import PluginClient
    from .utils import setup_logging, FileManager
except ImportError:
    # Fallback for direct execution
    from backend_client import BackendClient
    from plugin_client import PluginClient
    from utils import setup_logging, FileManager

# Setup logging
logger = setup_logging()

# Global instances
backend_client: Optional[BackendClient] = None
plugin_client: Optional[PluginClient] = None
file_manager: Optional[FileManager] = None
connected_plugins: Dict[str, WebSocket] = {}


# Pydantic models for API
class ChordData(BaseModel):
    chord: str
    start_time: float
    duration: float

class ChordProgression(BaseModel):
    chords: List[ChordData]  # [{"chord": "C", "start_time": 0.0, "duration": 2.0}]
    tempo: int = 120
    key: str = "C"
    duration: float = 32.0


class GenerationRequest(BaseModel):
    chord_progression: ChordProgression
    track_types: List[str] = ["bass", "drums"]
    plugin_id: str = "default"


class GenerationResponse(BaseModel):
    success: bool
    files: List[str]
    metadata: Dict
    message: str = ""


class TransportState(BaseModel):
    is_playing: bool
    current_beat: float
    tempo: float
    timestamp: str


class WebSocketMessage(BaseModel):
    type: str
    data: Dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global backend_client, plugin_client, file_manager
    
    logger.info("Starting AI Band Orchestrator...")
    
    # Initialize components
    backend_client = BackendClient()
    plugin_client = PluginClient()
    file_manager = FileManager()
    
    # Start file monitoring
    await file_manager.start_monitoring()
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI Band Orchestrator...")
    if file_manager:
        await file_manager.stop_monitoring()


# Create FastAPI app
app = FastAPI(
    title="AI Band Orchestrator",
    description="Coordination server for AI-powered music accompaniment generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving generated MIDI
generated_files_path = Path(__file__).parent.parent / "generated_files"
generated_files_path.mkdir(exist_ok=True)
app.mount("/files", StaticFiles(directory=str(generated_files_path)), name="files")


# API Routes
@app.get("/")
async def root():
    """Health check and basic info"""
    return {
        "service": "AI Band Orchestrator",
        "status": "running",
        "version": "1.0.0",
        "author": "Sergie Code",
        "connected_plugins": len(connected_plugins)
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "backend_connected": backend_client.is_connected() if backend_client else False,
        "active_plugins": len(connected_plugins),
        "generated_files": len(list(generated_files_path.glob("*.mid")))
    }


@app.post("/api/generate", response_model=GenerationResponse)
async def generate_accompaniment(request: GenerationRequest):
    """Generate MIDI accompaniment tracks"""
    try:
        logger.info(f"Generation request from plugin {request.plugin_id}")
        
        if not backend_client:
            raise HTTPException(status_code=503, detail="Backend client not available")
        
        # Convert Pydantic models to dictionaries for backend
        chords_data = [chord.model_dump() for chord in request.chord_progression.chords]
        
        # Generate tracks using backend
        result = await backend_client.generate_tracks(
            chords=chords_data,
            tempo=request.chord_progression.tempo,
            key=request.chord_progression.key,
            track_types=request.track_types,
            duration=request.chord_progression.duration
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Notify connected plugin
        if request.plugin_id in connected_plugins:
            await notify_plugin_new_files(request.plugin_id, result["files"])
        
        return GenerationResponse(
            success=True,
            files=result["files"],
            metadata=result["metadata"],
            message="Tracks generated successfully"
        )
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files")
async def list_generated_files():
    """List all generated MIDI files"""
    files = []
    for midi_file in generated_files_path.glob("*.mid"):
        stat = midi_file.stat()
        files.append({
            "filename": midi_file.name,
            "size": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime
        })
    return {"files": files}


@app.get("/api/files/{filename}")
async def download_file(filename: str):
    """Download a specific MIDI file"""
    file_path = generated_files_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="audio/midi"
    )


@app.delete("/api/files/{filename}")
async def delete_file(filename: str):
    """Delete a generated MIDI file"""
    file_path = generated_files_path / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        file_path.unlink()
        return {"message": f"File {filename} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {e}")


@app.post("/api/transport/sync")
async def sync_transport(state: TransportState):
    """Sync transport state with all connected plugins"""
    message = WebSocketMessage(
        type="transport_sync",
        data=state.model_dump()
    )
    
    # Broadcast to all connected plugins
    disconnected = []
    for plugin_id, websocket in connected_plugins.items():
        try:
            await websocket.send_text(message.json())
        except Exception:
            disconnected.append(plugin_id)
    
    # Clean up disconnected plugins
    for plugin_id in disconnected:
        connected_plugins.pop(plugin_id, None)
    
    return {"synced_plugins": len(connected_plugins)}


# WebSocket endpoint for real-time communication
@app.websocket("/ws/{plugin_id}")
async def websocket_endpoint(websocket: WebSocket, plugin_id: str):
    """WebSocket connection for plugin communication"""
    await websocket.accept()
    connected_plugins[plugin_id] = websocket
    
    logger.info(f"Plugin {plugin_id} connected via WebSocket")
    
    try:
        # Send initial connection confirmation
        await websocket.send_text(WebSocketMessage(
            type="connection_confirmed",
            data={"plugin_id": plugin_id, "status": "connected"}
        ).json())
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            message = WebSocketMessage.parse_raw(data)
            
            # Handle different message types
            await handle_websocket_message(plugin_id, message)
            
    except WebSocketDisconnect:
        logger.info(f"Plugin {plugin_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for plugin {plugin_id}: {e}")
    finally:
        connected_plugins.pop(plugin_id, None)


async def handle_websocket_message(plugin_id: str, message: WebSocketMessage):
    """Handle incoming WebSocket messages from plugins"""
    try:
        if message.type == "transport_update":
            # Handle transport position updates
            await sync_transport_state(plugin_id, message.data)
        
        elif message.type == "generation_request":
            # Handle real-time generation requests
            await handle_realtime_generation(plugin_id, message.data)
        
        elif message.type == "heartbeat":
            # Respond to heartbeat
            websocket = connected_plugins.get(plugin_id)
            if websocket:
                await websocket.send_text(WebSocketMessage(
                    type="heartbeat_response",
                    data={"timestamp": message.data.get("timestamp")}
                ).json())
        
        else:
            logger.warning(f"Unknown message type: {message.type}")
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")


async def notify_plugin_new_files(plugin_id: str, files: List[str]):
    """Notify a specific plugin about new files"""
    websocket = connected_plugins.get(plugin_id)
    if websocket:
        try:
            message = WebSocketMessage(
                type="files_ready",
                data={"files": files}
            )
            await websocket.send_text(message.json())
        except Exception as e:
            logger.error(f"Error notifying plugin {plugin_id}: {e}")


async def sync_transport_state(plugin_id: str, transport_data: Dict):
    """Handle transport state synchronization"""
    # This could trigger content generation based on playback position
    logger.info(f"Transport update from {plugin_id}: {transport_data}")


async def handle_realtime_generation(plugin_id: str, generation_data: Dict):
    """Handle real-time generation requests"""
    # Convert to GenerationRequest and process
    try:
        request = GenerationRequest(**generation_data)
        result = await generate_accompaniment(request)
        
        # Send result back to requesting plugin
        websocket = connected_plugins.get(plugin_id)
        if websocket:
            await websocket.send_text(WebSocketMessage(
                type="generation_complete",
                data=result.model_dump()
            ).json())
            
    except Exception as e:
        logger.error(f"Real-time generation error: {e}")


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
