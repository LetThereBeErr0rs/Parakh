from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


def _load_app():
    app_path = Path(__file__).resolve().parent / "backend" / "bug1" / "main.py"
    app_dir = str(app_path.parent)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    spec = spec_from_file_location("bug1_main", app_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load app module from {app_path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    app_obj = getattr(module, "app", None)
    if app_obj is None:
        raise RuntimeError("Loaded module does not expose `app`.")
    return app_obj


app = _load_app()
