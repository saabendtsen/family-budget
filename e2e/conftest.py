"""Pytest fixtures for E2E tests with Playwright."""

import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def temp_db_path():
    """Create a temporary database for E2E tests."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture(scope="session")
def app_server(temp_db_path):
    """Start the FastAPI server for E2E tests.

    Uses a temporary database to ensure test isolation.
    """
    import os

    # Set environment to use temp database
    env = os.environ.copy()
    env["BUDGET_DB_PATH"] = str(temp_db_path)

    # Start server on random available port
    import socket
    with socket.socket() as s:
        s.bind(('', 0))
        port = s.getsockname()[1]

    project_root = Path(__file__).parent.parent
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=project_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start
    time.sleep(2)

    # Check server is running
    if proc.poll() is not None:
        stdout, stderr = proc.communicate()
        raise RuntimeError(f"Server failed to start: {stderr.decode()}")

    yield f"http://127.0.0.1:{port}"

    # Cleanup
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def base_url(app_server):
    """Provide base URL to tests."""
    return app_server


@pytest.fixture
def authenticated_page(page, base_url, request):
    """Page with a logged-in user session.

    Creates a unique test user per test and logs in before returning the page.
    """
    import uuid

    # Create unique username for this test
    unique_id = str(uuid.uuid4())[:8]
    username = f"e2euser_{unique_id}"

    # Register new user
    page.goto(f"{base_url}/budget/register")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', "testpass123")
    page.fill('input[name="password_confirm"]', "testpass123")
    page.click('button[type="submit"]')

    # Should redirect to dashboard after registration
    page.wait_for_url(f"{base_url}/budget/")

    return page
