"""Unit tests for storage paths and directory permissions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from open_video_downloader.core.paths import (
    StorageError,
    check_directory_writable,
    ensure_app_directories,
    get_app_data_dir,
    get_default_download_dir,
    get_logs_dir,
)


def test_get_app_data_dir_default():
    """Verify default app data directory is within standard local structure."""
    path = get_app_data_dir()
    assert isinstance(path, Path)
    assert "OpenVideoDownloader" in str(path) or "open_video_downloader" in str(path)


def test_get_app_data_dir_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    """Verify OPENVIDEO_DATA_DIR overrides the default data directory."""
    custom_dir = tmp_path / "custom_data"
    monkeypatch.setenv("OPENVIDEO_DATA_DIR", str(custom_dir))
    assert get_app_data_dir() == custom_dir


def test_get_logs_dir(tmp_path: Path):
    """Verify get_logs_dir appends 'logs' subfolder."""
    logs_dir = get_logs_dir(tmp_path)
    assert logs_dir == tmp_path / "logs"


def test_get_default_download_dir():
    """Verify default download directory returns an existing directory."""
    download_dir = get_default_download_dir()
    assert download_dir.exists()
    assert download_dir.is_dir()


def test_ensure_app_directories_success(tmp_path: Path):
    """Verify ensure_app_directories creates both data and logs directories."""
    target_data = tmp_path / "test_app_data"
    data_dir, logs_dir = ensure_app_directories(target_data)

    assert data_dir.is_dir()
    assert logs_dir.is_dir()
    assert logs_dir == data_dir / "logs"
    assert check_directory_writable(data_dir)
    assert check_directory_writable(logs_dir)


def test_ensure_app_directories_unwritable(tmp_path: Path):
    """Verify StorageError is raised when directory cannot be written to."""
    target_data = tmp_path / "unwritable_test"
    target_data.mkdir()

    # Simulate write failure by mocking check_directory_writable to return False
    with patch("open_video_downloader.core.paths.check_directory_writable", return_value=False):
        with pytest.raises(StorageError) as exc_info:
            ensure_app_directories(target_data)
        assert "Geen schrijfrechten" in str(exc_info.value)
