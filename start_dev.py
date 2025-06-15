#!/usr/bin/env python3
"""
Development server startup script
Starts both backend and frontend servers simultaneously
"""

import os
import subprocess
import sys
import time
import signal
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent
    
    print("🚀 Starting LimAuto Development Environment")
    print("=" * 50)
    
    # Start backend server
    print("📡 Starting backend server...")
    backend_process = subprocess.Popen([
        sys.executable, str(project_root / "start_backend.py")
    ])
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Start frontend server
    print("🎨 Starting frontend server...")
    frontend_process = subprocess.Popen([
        sys.executable, str(project_root / "start_frontend.py")
    ])
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("👋 Development environment stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("\n✅ Development environment is running!")
        print(f"📡 Backend API: http://localhost:8000")
        print(f"🎨 Frontend UI: http://localhost:3000")
        print(f"📊 Health Check: http://localhost:8000/health")
        print("\nPress Ctrl+C to stop both servers")
        
        # Wait for processes
        backend_process.wait()
        frontend_process.wait()
        
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()