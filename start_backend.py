#!/usr/bin/env python3
"""
Backend service startup script
Starts the Flask API server with proper configuration
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

try:
    from BookLLM.src.api import app
    print("✅ Backend API loaded successfully")
    print("🚀 Starting Flask server on http://localhost:8000")
    print("📊 API endpoints available:")
    print("   - POST /generate - Generate book")
    print("   - GET /api/metrics - Get metrics")
    print("   - GET /api/agents - List agents")
    print("   - GET /health - Health check")
    print("   - GET /events/agent-status - Real-time status")
    print()
    app.run(host="0.0.0.0", port=8000, debug=True)
except ImportError as e:
    print(f"❌ Failed to import backend: {e}")
    print("💡 Make sure you've installed the dependencies: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Failed to start backend: {e}")
    sys.exit(1)