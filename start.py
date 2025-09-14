#!/usr/bin/env python3
"""
Startup script for the EEG Tutor backend.
This handles imports properly for both local and deployed environments.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the FastAPI app
from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
