"""Filesystem path helpers and user data directory validation."""

import os
import sys
from pathlib import Path


class StorageError(OSError):
    """Raised when an application storage directory cannot be accessed or written to."""


def get_app_data_dir() -> Path:
    """Return the base path for local user data storage.

    Supports override via OPENVIDEO_DATA_DIR environment variable for testing.
    On Windows defaults to %LOCALAPPDATA%/OpenVideoDownloader.
    """
    override = os.environ.get("OPENVIDEO_DATA_DIR")
    if override:
        return Path(override)

    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / "OpenVideoDownloader"
        return Path.home() / "AppData" / "Local" / "OpenVideoDownloader"

    # Unix-like fallback
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "open_video_downloader"
    return Path.home() / ".local" / "share" / "open_video_downloader"


def get_logs_dir(data_dir: Path | None = None) -> Path:
    """Return the directory path dedicated to log files."""
    base = data_dir or get_app_data_dir()
    return base / "logs"


def get_default_download_dir() -> Path:
    """Return the user's default Downloads directory with fallback to home."""
    downloads = Path.home() / "Downloads"
    if downloads.is_dir():
        return downloads
    return Path.home()


def check_directory_writable(directory: Path) -> bool:
    """Test whether a directory exists and can be written to by writing a canary file."""
    if not directory.exists() or not directory.is_dir():
        return False

    canary = directory / ".write_test_canary.tmp"
    try:
        with canary.open("w", encoding="utf-8") as f:
            f.write("canary")
        if canary.exists():
            canary.unlink()
        return True
    except OSError:
        return False


def ensure_app_directories(custom_data_dir: Path | None = None) -> tuple[Path, Path]:
    """Ensure that the application data directory and logs directory exist and are writable.

    Returns (data_dir, logs_dir).
    Raises StorageError if creation or write access fails.
    """
    data_dir = custom_data_dir or get_app_data_dir()
    logs_dir = get_logs_dir(data_dir)

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise StorageError(f"Kon gebruikersdatamap niet aanmaken op '{data_dir}': {err}") from err

    if not check_directory_writable(data_dir):
        raise StorageError(f"Geen schrijfrechten in gebruikersdatamap: '{data_dir}'")

    if not check_directory_writable(logs_dir):
        raise StorageError(f"Geen schrijfrechten in logsmap: '{logs_dir}'")

    return data_dir, logs_dir
