"""Tests for version detection module."""

import os
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from src.version import get_version


class TestGetVersion:
    """Tests for get_version() function."""

    def test_returns_string(self):
        """get_version() should return a string."""
        version = get_version()
        assert isinstance(version, str)

    def test_not_empty(self):
        """Version should not be empty."""
        version = get_version()
        assert len(version) > 0

    def test_env_variable_takes_priority(self):
        """APP_VERSION environment variable should take priority."""
        with patch.dict(os.environ, {"APP_VERSION": "2.0.0"}):
            assert get_version() == "2.0.0"

    def test_env_variable_strips_whitespace(self):
        """APP_VERSION should be stripped of whitespace."""
        with patch.dict(os.environ, {"APP_VERSION": "  2.0.0  \n"}):
            assert get_version() == "2.0.0"

    def test_git_tag_removes_v_prefix(self):
        """Git tag version should have 'v' prefix removed."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove APP_VERSION from env
            os.environ.pop("APP_VERSION", None)

            mock_output = MagicMock(return_value=b"v1.2.3\n")
            with patch("subprocess.check_output", mock_output):
                version = get_version()
                assert version == "1.2.3"

    def test_git_tag_handles_prefixed_tags(self):
        """Git tag version should handle prefixed tags like 'family-budget-v1.2.3'."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("APP_VERSION", None)

            mock_output = MagicMock(return_value=b"family-budget-v1.2.3\n")
            with patch("subprocess.check_output", mock_output):
                version = get_version()
                assert version == "1.2.3"

    def test_falls_back_to_commit_hash(self):
        """Should fall back to commit hash if no tags."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("APP_VERSION", None)

            def mock_git_command(cmd, **kwargs):
                if "--tags" in cmd:
                    raise subprocess.CalledProcessError(1, cmd)
                return b"abc1234\n"

            with patch("subprocess.check_output", mock_git_command):
                version = get_version()
                assert version == "dev-abc1234"

    def test_falls_back_to_unknown_without_git(self):
        """Should return 'unknown' if git not available and no VERSION file."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("APP_VERSION", None)

            with patch("subprocess.check_output", side_effect=FileNotFoundError()):
                with patch("pathlib.Path.read_text", side_effect=OSError()):
                    version = get_version()
                    assert version == "unknown"

    def test_version_format_semver_or_dev(self):
        """Version should match semver (X.Y.Z) or dev-XXXXXX format."""
        import re

        version = get_version()
        # Match semver (1.0.0) or dev-hash (dev-abc1234) or unknown
        pattern = r"^(\d+\.\d+\.\d+|dev-[a-f0-9]+|unknown)$"
        assert re.match(pattern, version), f"Version '{version}' doesn't match expected format"


class TestVersionIntegration:
    """Integration tests for version in the app."""

    def test_package_version_is_set(self):
        """__version__ should be set in package."""
        from src import __version__
        assert __version__ is not None
        assert len(__version__) > 0

    def test_help_page_shows_version(self, authenticated_client):
        """Help page should display current version."""
        response = authenticated_client.get("/budget/help")
        assert response.status_code == 200
        # Version should be visible on help page
        assert "Version" in response.text or "version" in response.text
