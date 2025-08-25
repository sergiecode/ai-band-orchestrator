#!/usr/bin/env python3
"""
AI Band Orchestrator - Startup Script

This script starts the AI Band Orchestrator server with proper configuration.

Author: Sergie Code
"""

import os
import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main entry point"""
    print("🎵 Starting AI Band Orchestrator...")
    print("Author: Sergie Code")
    print("- LinkedIn: https://www.linkedin.com/in/sergiecode/")
    print("- YouTube: https://www.youtube.com/@SergieCode")
    print("- GitHub: https://github.com/sergiecode")
    print()
    
    # Start the server using uvicorn directly
    try:
        import uvicorn
        
        # Start the server with the app import string
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
