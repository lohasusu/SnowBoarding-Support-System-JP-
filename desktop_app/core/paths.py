"""PyInstaller-aware path resolution.

When running from source: BASE_DIR = repo root (one level up from desktop_app/).
When packaged via PyInstaller: BASE_DIR = sys._MEIPASS (the temp unpack dir).

User-writable paths (config, output) always go under %APPDATA%/SnowTripDesktop/.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def base_dir() -> Path:
    """Read-only resource root.

    - Frozen: sys._MEIPASS (PyInstaller unpack dir)
    - Source: repo root (parent of desktop_app/)
    """
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS"))
    # desktop_app/core/paths.py → repo root
    return Path(__file__).resolve().parent.parent.parent


def user_data_dir() -> Path:
    """User-writable directory (config + logs)."""
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = Path(appdata) / "SnowTripDesktop"
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_output_dir() -> Path:
    """Where Excel outputs land by default."""
    home = Path(os.path.expanduser("~"))
    d = home / "SnowTrip_Output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return user_data_dir() / "config.json"


def log_path() -> Path:
    return user_data_dir() / "snowtrip.log"


def executable_path() -> Path:
    """Path to the running exe (frozen) or the python interpreter + script (source)."""
    if is_frozen():
        return Path(sys.executable)
    return Path(sys.executable)  # python.exe path; CLI uses `-m desktop_app.main` form
