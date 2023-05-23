"""conftest file."""

import io
import logging
import tempfile
from pathlib import Path

import pytest

from mse_home.log import LOGGER as LOG
from mse_home.log import setup_logging


@pytest.fixture(scope="session")
def cmd_log() -> io.StringIO:
    """Initialize the log capturing."""
    cmd_log_str = io.StringIO()
    ch = logging.StreamHandler(cmd_log_str)
    ch.setLevel(logging.DEBUG)
    setup_logging()
    LOG.addHandler(ch)
    yield cmd_log_str


@pytest.fixture(scope="session")
def workspace() -> Path:
    """Create a workspace for the test session."""
    return Path(tempfile.mkdtemp())


def capture_logs(f: io.StringIO) -> str:
    """Get the logs stacked until now."""
    log_contents = f.getvalue()
    f.truncate(0)
    return log_contents
