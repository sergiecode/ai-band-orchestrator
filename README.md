# AI Band Orchestrator

A Python coordination server that bridges the AI Band Backend (MIDI generation) and AI Band Plugin (JUCE audio plugin). This orchestrator enables real-time AI-powered music accompaniment generation in Digital Audio Workstations (DAWs).

## 🎯 Project Purpose

The AI Band Orchestrator serves as the central coordination hub for the AI Band ecosystem:

- **Receives requests** from the JUCE plugin or external clients
- **Calls ai-band-backend** to generate bass and drum MIDI tracks
- **Delivers generated MIDI** to the plugin for real-time playback
- **Manages file sharing** and real-time synchronization
- **Supports multiple plugins** connecting simultaneously

## 🏗️ How It Works

```
Guitar Input → Plugin → Orchestrator → Backend → MIDI Generation
     ↓            ↓         ↓           ↓         ↓
  DAW Audio ←   Plugin  ←  WebSocket ←  Server  ←  MIDI Files
```

### Workflow:
1. **Plugin captures** chord progressions from guitar/MIDI input
2. **Orchestrator receives** generation requests via REST API or WebSocket
3. **Backend processes** chord data and generates bass/drum MIDI tracks
4. **Orchestrator delivers** MIDI files to plugin's monitored folder
5. **Plugin loads and plays** generated tracks synchronized with DAW transport

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ai-band-backend project (for MIDI generation)
- ai-band-plugin project (for DAW integration)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/sergiecode/ai-band-orchestrator.git
cd ai-band-orchestrator
```

2. **Create virtual environment:**
```bash
python -m venv venv

# Windows
venv\\Scripts\\activate

# macOS/Linux  
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure paths:**
   - Ensure `ai-band-backend` is in the parent directory
   - Update paths in `src/backend_client.py` if needed

### Running the Orchestrator

```bash
# Start the server
cd src
python main.py

# Or with custom configuration
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start on `http://localhost:8000`

## 📡 API Endpoints

### REST API

#### Health Check
```bash
GET /health
# Returns server status and connection info
```

#### Generate Tracks
```bash
POST /api/generate
Content-Type: application/json

{
  "chord_progression": {
    "chords": [
      {"chord": "C", "start_time": 0.0, "duration": 2.0},
      {"chord": "Am", "start_time": 2.0, "duration": 2.0},
      {"chord": "F", "start_time": 4.0, "duration": 2.0},
      {"chord": "G", "start_time": 6.0, "duration": 2.0}
    ],
    "tempo": 120,
    "key": "C",
    "duration": 8.0
  },
  "track_types": ["bass", "drums"],
  "plugin_id": "my-plugin"
}
```

#### File Management
```bash
GET /api/files              # List generated files
GET /api/files/{filename}   # Download specific file
DELETE /api/files/{filename} # Delete file
```

### WebSocket Communication

Connect to: `ws://localhost:8000/ws/{plugin_id}`

#### Message Types:
```javascript
// Transport synchronization
{
  "type": "transport_sync",
  "data": {
    "is_playing": true,
    "current_beat": 16.5,
    "tempo": 120.0
  }
}

// File notification
{
  "type": "files_ready", 
  "data": {
    "files": ["bass_120bpm_C_4chords.mid", "drums_120bpm_C_4chords.mid"]
  }
}

// Real-time generation request
{
  "type": "generation_request",
  "data": {
    "chord_progression": {...},
    "track_types": ["bass"]
  }
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Server configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Backend integration
BACKEND_PATH=../ai-band-backend/src
BACKEND_TIMEOUT=30

# File management
GENERATED_FILES_DIR=./generated_files
CLEANUP_HOURS=24
MAX_FILES=1000
```

### Configuration File
Create `config.json` in the project root:
```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "reload": true
  },
  "backend": {
    "path": "../ai-band-backend/src",
    "timeout": 30
  },
  "plugin": {
    "folder": "./generated_files",
    "cleanup_hours": 24,
    "max_files": 1000
  }
}
```

## 🧪 Testing

### Test the API
```bash
# Test generation endpoint
curl -X POST http://localhost:8000/api/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "chord_progression": {
      "chords": [{"chord": "C", "start_time": 0, "duration": 4}],
      "tempo": 120
    },
    "track_types": ["bass"]
  }'
```

### Test with Plugin
1. Start the orchestrator server
2. Load the ai-band-plugin in your DAW
3. Configure the plugin to connect to `http://localhost:8000`
4. Play guitar chords or MIDI input
5. Verify generated accompaniment playback

## 📁 Project Structure

```
ai-band-orchestrator/
├── src/
│   ├── main.py              # FastAPI server and endpoints
│   ├── backend_client.py    # Integration with ai-band-backend
│   ├── plugin_client.py     # Communication with JUCE plugin
│   └── utils.py             # Logging, file management, utilities
├── generated_files/         # Generated MIDI files directory
├── logs/                    # Application logs
├── tests/                   # Unit and integration tests
├── requirements.txt         # Python dependencies
├── config.json             # Configuration file (optional)
└── README.md               # This file
```

## 🔗 Integration with Other Projects

### ai-band-backend Integration
The orchestrator imports and uses the backend directly:
```python
from chord_detection import ChordDetector
from midi_generator import MidiGenerator

# Generate tracks
detector = ChordDetector()
generator = MidiGenerator()
bass_midi = generator.generate_bass_track(chords, tempo=120)
```

### ai-band-plugin Integration
Communication via:
- **File sharing**: Plugin monitors `generated_files/` folder
- **HTTP endpoints**: Plugin sends requests to orchestrator API
- **WebSocket**: Real-time bidirectional communication

## 🚀 Development

### Adding New Features

#### New Instrument Types
1. Add track type to `backend_client.py` generation logic
2. Update API models in `main.py`
3. Test with updated chord progressions

#### Advanced Scheduling
1. Extend `utils.py` with scheduling utilities
2. Add background tasks in `main.py`
3. Implement in `plugin_client.py`

#### Multiple Plugin Support
1. Enhance plugin registration in `plugin_client.py`
2. Add plugin management endpoints
3. Implement plugin-specific file handling

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### Development Mode
```bash
# Start with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Enable debug logging
export LOG_LEVEL=DEBUG
python src/main.py
```

## 📚 API Documentation

When the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes and add tests
4. Commit: `git commit -am 'Add new feature'`
5. Push: `git push origin feature/new-feature`
6. Create a Pull Request

## 👨‍💻 Author

**Sergie Code** - Software Engineer & Programming Educator

- 📸 Instagram: https://www.instagram.com/sergiecode

- 🧑🏼‍💻 LinkedIn: https://www.linkedin.com/in/sergiecode/

- 📽️Youtube: https://www.youtube.com/@SergieCode

- 😺 Github: https://github.com/sergiecode

- 👤 Facebook: https://www.facebook.com/sergiecodeok

- 🎞️ Tiktok: https://www.tiktok.com/@sergiecode

- 🕊️Twitter: https://twitter.com/sergiecode

- 🧵Threads: https://www.threads.net/@sergiecode

*Creating AI tools for musicians through programming education.*

## 🎵 Related Projects

- **[ai-band-backend](https://github.com/sergiecode/ai-band-backend)** - Core AI engine for MIDI generation
- **[ai-band-plugin](https://github.com/sergiecode/ai-band-plugin)** - JUCE audio plugin for DAW integration

## 🔮 Future Enhancements

- **Real-time chord detection** from audio input
- **Machine learning models** for style adaptation
- **Cloud deployment** support
- **Advanced synchronization** features
- **Multi-user collaboration** capabilities
- **Extended instrument support** (piano, guitar, etc.)

---

**Ready to create AI-powered music? Start the orchestrator and let the AI band play! 🎸🤖🥁**

