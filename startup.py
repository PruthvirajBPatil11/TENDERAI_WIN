#!/usr/bin/env python
"""
Minimal startup wrapper for debugging import errors.
"""
import sys
import os

# Set environment variables
os.environ.setdefault("PORT", "10000")
port = os.environ.get("PORT", "10000")

print(f"Starting on port: {port}", file=sys.stderr)
print(f"Python version: {sys.version}", file=sys.stderr)
print(f"Working directory: {os.getcwd()}", file=sys.stderr)

# Test imports step by step
print("Testing imports...", file=sys.stderr)

try:
    print("  Importing fastapi...", file=sys.stderr, flush=True)
    from fastapi import FastAPI
    print("    ✓ fastapi imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"    ✗ fastapi import failed: {e}", file=sys.stderr, flush=True)
    sys.exit(1)

try:
    print("  Importing backend.config...", file=sys.stderr, flush=True)
    from backend.config import settings
    print("    ✓ backend.config imported", file=sys.stderr, flush=True)
    print(f"    Settings: groq_api_key={'***' if settings.groq_api_key else 'NOT SET'}", file=sys.stderr, flush=True)
except Exception as e:
    print(f"    ✗ backend.config failed: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)

try:
    print("  Importing backend.main...", file=sys.stderr, flush=True)
    from backend.main import app
    print("    ✓ backend.main imported", file=sys.stderr, flush=True)
except Exception as e:
    print(f"    ✗ backend.main failed: {e}", file=sys.stderr, flush=True)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("All imports successful, starting uvicorn...", file=sys.stderr, flush=True)

# Start uvicorn
import uvicorn
uvicorn.run(
    "backend.main:app",
    host="0.0.0.0",
    port=int(port),
    reload=False,
    log_level="info"
)
