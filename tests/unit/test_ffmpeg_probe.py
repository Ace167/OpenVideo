"""Unit tests for FFmpeg detection and version inspection."""

from unittest.mock import MagicMock, patch

from open_video_downloader.engines.ffmpeg_probe import (
    get_ffmpeg_version,
    is_ffmpeg_available,
    is_ffprobe_available,
)


@patch("shutil.which")
def test_ffmpeg_available(mock_which: MagicMock):
    """Verify is_ffmpeg_available reflects shutil.which results."""
    mock_which.return_value = "C:\\tools\\ffmpeg.exe"
    assert is_ffmpeg_available() is True

    mock_which.return_value = None
    assert is_ffmpeg_available() is False


@patch("shutil.which")
def test_ffprobe_available(mock_which: MagicMock):
    """Verify is_ffprobe_available reflects shutil.which results."""
    mock_which.return_value = "C:\\tools\\ffprobe.exe"
    assert is_ffprobe_available() is True

    mock_which.return_value = None
    assert is_ffprobe_available() is False


@patch("shutil.which", return_value="C:\\tools\\ffmpeg.exe")
@patch("subprocess.run")
def test_get_ffmpeg_version_success(mock_run: MagicMock, mock_which: MagicMock):
    """Verify parsing first line of ffmpeg -version."""
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = "ffmpeg version 7.0.1-full_build Copyright (c) 2000-2024\nbuilt with gcc"
    mock_run.return_value = mock_proc

    version_str = get_ffmpeg_version()
    assert version_str == "ffmpeg version 7.0.1-full_build Copyright (c) 2000-2024"


@patch("shutil.which", return_value=None)
def test_get_ffmpeg_version_missing(mock_which: MagicMock):
    """Verify missing ffmpeg returns None."""
    assert get_ffmpeg_version() is None
