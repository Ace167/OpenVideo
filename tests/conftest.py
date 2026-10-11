"""Pytest shared test fixtures and environment configuration."""

import os
import sys

import pytest

# Ensure Qt runs offscreen in headless test runs
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# On Windows in sandboxed test environments, Python 3.14 os.mkdir mode=0o700 strips DACL
# permissions when pytest/tempfile creates temp dirs. Normalizing mkdir preserves permissions.
if sys.platform == "win32":
    _original_mkdir = os.mkdir

    def _safe_mkdir(path, mode=0o777, *args, **kwargs):  # type: ignore[no-untyped-def]
        return _original_mkdir(path, *args, **kwargs)

    os.mkdir = _safe_mkdir  # type: ignore[assignment]


@pytest.fixture(scope="session")
def qapp_args() -> list[str]:
    """Custom arguments passed to QApplication fixture if pytest-qt is used."""
    return ["-platform", "offscreen"]
