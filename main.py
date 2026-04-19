"""
Root entrypoint for Render deployment.

Render runs:  uvicorn main:app --host 0.0.0.0 --port $PORT
from the repo root, so this file adds the backend package to sys.path
and re-exports `app` from the FastAPI backend.
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── Add backend directory to Python path ──────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent / "inspection" / "backend" / "bug1"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

# ── Import the FastAPI application ────────────────────────────────────────────
from main import app  # noqa: E402  (imported after sys.path patch)

__all__ = ["app"]
