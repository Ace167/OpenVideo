"""Initial sanity and environment validation tests."""

import sqlite3

import PySide6
import yt_dlp

import open_video_downloader
from open_video_downloader import __version__


def test_package_metadata():
    """Verify package version is set and non-empty."""
    assert __version__ == "0.1.0"
    assert open_video_downloader.__version__ == "0.1.0"


def test_core_dependencies_available():
    """Verify primary dependencies are functional and provide version identifiers."""
    assert hasattr(PySide6, "__version__")
    assert hasattr(yt_dlp, "version")
    assert sqlite3.sqlite_version != ""
