#!/usr/bin/env python3
"""
Frontend service startup script
Starts the React development server
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    frontend_dir = Path(__file__).resolve().parent / "frontend"
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        sys.exit(1)
    
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        result = subprocess.run(["npm", "install"], cwd=frontend_dir)
        if result.returncode != 0:
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    print("✅ Frontend dependencies ready")
    print("🚀 Starting React development server on http://localhost:3000")
    print("🔗 Make sure backend is running on http://localhost:8000")
    print()
    
    try:
        subprocess.run(["npm", "start"], cwd=frontend_dir)
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()