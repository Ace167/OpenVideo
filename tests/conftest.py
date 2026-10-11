"""Pytest shared test fixtures and environment configuration."""

import os

import pytest

# Ensure Qt runs offscreen in headless test runs when needed
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp_args():
    """Custom arguments passed to QApplication fixture if pytest-qt is used."""
    return ["-platform", "offscreen"]
