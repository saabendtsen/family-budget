"""Unit tests for version functionality."""

import importlib
import os
import re
import subprocess
import sys
from unittest.mock import patch

import pytest


# Import the module for testing internal functions
import src as src_module


class TestVersionFunctions:
    """Tests for version reading functions."""

    def test_get_version_returns_string(self):
        """get_version() should return a string."""
        from src import __version__

        assert isinstance(__version__, str)

    def test_get_version_not_empty(self):
        """Version must not be empty."""
        from src import __version__

        assert __version__ != ""

    def test_get_version_format(self):
        """Version should match expected formats: X.Y.Z, dev-XXXXXX, or unknown."""
        from src import __version__

        # Valid patterns: semantic version, dev-hash, or unknown
        semver_pattern = r"^\d+\.\d+\.\d+$"
        dev_pattern = r"^dev-[a-f0-9]+$"
        unknown_pattern = r"^unknown$"

        is_valid = (
            re.match(semver_pattern, __version__)
            or re.match(dev_pattern, __version__)
            or re.match(unknown_pattern, __version__)
        )
        assert is_valid, f"Version '{__version__}' does not match expected format"

    def test_env_version_takes_priority(self):
        """APP_VERSION environment variable should take highest priority."""
        with patch.dict(os.environ, {"APP_VERSION": "99.88.77"}):
            result = src_module._read_version()
            assert result == "99.88.77"

    def test_env_version_strips_whitespace(self):
        """APP_VERSION should be stripped of whitespace."""
        with patch.dict(os.environ, {"APP_VERSION": "  1.2.3  \n"}):
            result = src_module._read_version()
            assert result == "1.2.3"

    def test_git_version_strips_v_prefix(self):
        """Git tags with 'v' prefix should have it removed."""
        # Mock git describe to return a v-prefixed tag
        with patch("src.subprocess.check_output") as mock_git:
            mock_git.return_value = b"v2.0.0\n"
            result = src_module._get_git_version()
            assert result == "2.0.0"

    def test_git_fallback_to_commit_hash(self):
        """Should fall back to commit hash if no tags exist."""
        def mock_check_output(cmd, **kwargs):
            if "describe" in cmd:
                raise subprocess.CalledProcessError(128, cmd)
            elif "rev-parse" in cmd:
                return b"abc1234\n"
            raise ValueError(f"Unexpected command: {cmd}")

        with patch("src.subprocess.check_output", side_effect=mock_check_output):
            result = src_module._get_git_version()
            assert result == "dev-abc1234"

    def test_git_version_returns_none_without_git(self):
        """Should return None if git is not available."""
        with patch("src.subprocess.check_output", side_effect=FileNotFoundError):
            result = src_module._get_git_version()
            assert result is None


class TestVersionIntegration:
    """Integration tests for version display."""

    def test_help_page_shows_version(self, authenticated_client):
        """Help page should display the current version."""
        from src import __version__

        response = authenticated_client.get("/budget/help")
        assert response.status_code == 200
        assert __version__ in response.text
