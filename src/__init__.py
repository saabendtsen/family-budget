"""Family Budget App package metadata."""

import os
import subprocess
from pathlib import Path


def _get_git_version() -> str | None:
    """Get version from git tags or commit hash."""
    try:
        # Try to get the latest git tag
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).resolve().parent.parent,
        ).decode().strip()
        # Remove 'v' prefix if present (v1.0.0 -> 1.0.0)
        return tag.lstrip("v")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    try:
        # Fallback to short commit hash
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).resolve().parent.parent,
        ).decode().strip()
        return f"dev-{commit}"
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    return None


def _read_version() -> str:
    """Read version from environment, git, or VERSION file."""
    # 1. Check environment variable (highest priority)
    env_version = os.environ.get("APP_VERSION")
    if env_version:
        return env_version.strip()

    # 2. Try git-based version
    git_version = _get_git_version()
    if git_version:
        return git_version

    # 3. Fallback to VERSION file
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"


__version__ = _read_version()
