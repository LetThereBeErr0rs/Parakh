"""
Root entrypoint for Render deployment.

Render runs:  gunicorn main:app  or  uvicorn main:app
from the repo root.  We load the backend FastAPI app by FILE PATH
(not by module name) to avoid circular imports — this file IS 'main',
so doing `from main import app` would import itself.
"""
from __future__ import annotations

import sys
import importlib.util
from pathlib import Path

# ── Resolve the backend main.py by absolute path ─────────────────────────────
_BACKEND_MAIN = (
    Path(__file__).resolve().parent
    / "inspection" / "backend" / "bug1" / "main.py"
)
_BACKEND_DIR = str(_BACKEND_MAIN.parent)

# Add backend dir to sys.path so relative imports inside the backend work
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

# ── Load the module by file path (avoids circular import via name) ────────────
_spec = importlib.util.spec_from_file_location("backend_main", _BACKEND_MAIN)
_module = importlib.util.module_from_spec(_spec)
sys.modules["backend_main"] = _module
_spec.loader.exec_module(_module)

# ── Re-export `app` so gunicorn/uvicorn can find it as  main:app ──────────────
app = _module.app
