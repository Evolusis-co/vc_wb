"""
Startup script for VoiceCoach API - handles encoding issues on Windows
"""
import sys
import os

# Set UTF-8 encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Start uvicorn
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
