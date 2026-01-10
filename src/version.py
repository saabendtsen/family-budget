"""Git-based version detection for Family Budget app.

Priority order:
1. APP_VERSION environment variable (for Docker/CI builds)
2. Git tag (e.g., v1.2.3 -> 1.2.3)
3. Git commit hash (dev-abc1234)
4. VERSION file
5. "unknown" fallback
"""

import os
import subprocess
from pathlib import Path


def get_version() -> str:
    """Get application version from git tags or fallback sources."""
    # 1. Check environment variable (highest priority, set by CI/Docker)
    env_version = os.environ.get("APP_VERSION")
    if env_version:
        return env_version.strip()

    # 2. Try git tag
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent,
        ).decode().strip()
        # Handle prefixed tags (e.g., "family-budget-v1.2.3" -> "1.2.3")
        if "-v" in tag:
            tag = tag.split("-v")[-1]
        # Remove 'v' prefix if present (v1.2.3 -> 1.2.3)
        return tag.lstrip("v")
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    # 3. Try git commit hash
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=Path(__file__).parent,
        ).decode().strip()
        return f"dev-{commit}"
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        pass

    # 4. Fall back to VERSION file
    version_file = Path(__file__).resolve().parent.parent / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        pass

    # 5. Final fallback
    return "unknown"
