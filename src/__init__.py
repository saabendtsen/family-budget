"""Family Budget App package metadata."""

import os
from pathlib import Path


def _read_version() -> str:
    env_version = os.environ.get("APP_VERSION")
    if env_version:
        return env_version.strip()
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"


__version__ = _read_version()
