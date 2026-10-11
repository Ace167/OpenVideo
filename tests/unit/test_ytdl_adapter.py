"""Unit tests for the yt-dlp adapter layer, error mapping and format parsing."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from yt_dlp.utils import DownloadCancelled, DownloadError

from open_video_downloader.engines.ytdl_adapter import (
    DownloadCancelledError,
    MediaUnavailableError,
    NetworkTimeoutError,
    execute_download,
    extract_metadata,
    is_valid_url,
)


def test_is_valid_url():
    """Verify URL validation recognizes valid HTTP/HTTPS URLs and rejects invalid syntax."""
    assert is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert is_valid_url("http://vimeo.com/123456") is True
    assert is_valid_url("https://archive.org/details/test_video") is True

    # Invalid URLs
    assert is_valid_url("") is False
    assert is_valid_url("ftp://example.com/video.mp4") is False
    assert is_valid_url("not a url") is False
    assert is_valid_url("http://") is False
    assert is_valid_url("https://localhost") is False


@patch("yt_dlp.YoutubeDL")
def test_extract_metadata_success(mock_ydl_class: MagicMock):
    """Verify extract_metadata parses raw yt-dlp dictionary into structured MediaMetadata."""
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    mock_ydl.extract_info.return_value = {
        "id": "abc12345",
        "title": "Sample Educational Video",
        "description": "A demo video description",
        "duration": 185,
        "extractor": "MockPlatform",
        "thumbnail": "https://example.com/thumb.jpg",
        "uploader": "Test Channel",
        "view_count": 5000,
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "height": 1080,
                "vcodec": "avc1",
                "acodec": "none",
                "filesize": 40000000,
            },
            {
                "format_id": "18",
                "ext": "mp4",
                "height": 360,
                "vcodec": "avc1",
                "acodec": "mp4a",
                "filesize": 15000000,
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "vcodec": "none",
                "acodec": "mp4a",
                "filesize": 5000000,
            },
        ],
    }

    metadata = extract_metadata("https://example.com/watch?v=abc12345")

    assert metadata.id == "abc12345"
    assert metadata.title == "Sample Educational Video"
    assert metadata.duration == 185
    assert metadata.duration_str == "03:05"
    assert metadata.thumbnail_url == "https://example.com/thumb.jpg"
    assert len(metadata.formats) >= 3

    # Check that best quality automatic option was injected
    assert metadata.formats[0].format_id == "bestvideo+bestaudio/best"
    # Check separate video stream marked as requiring FFmpeg
    fmt_1080 = next(f for f in metadata.formats if f.resolution == "1080p")
    assert fmt_1080.requires_ffmpeg is True


@patch("yt_dlp.YoutubeDL")
def test_extract_metadata_unavailable_video(mock_ydl_class: MagicMock):
    """Verify private or removed video errors map to MediaUnavailableError."""
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = DownloadError("Private video. Sign in to view.")

    with pytest.raises(MediaUnavailableError) as exc_info:
        extract_metadata("https://example.com/private_video")
    assert "niet beschikbaar" in str(exc_info.value)


@patch("yt_dlp.YoutubeDL")
def test_extract_metadata_network_timeout(mock_ydl_class: MagicMock):
    """Verify network drop or timeout maps to NetworkTimeoutError."""
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = DownloadError("Connection timed out (getaddrinfo failed)")

    with pytest.raises(NetworkTimeoutError) as exc_info:
        extract_metadata("https://example.com/timeout_video")
    assert "getimed-out" in str(exc_info.value)


def test_extract_metadata_cancellation():
    """Verify extract_metadata aborts early when cancel_check returns True."""
    with pytest.raises(DownloadCancelledError):
        extract_metadata("https://example.com/video", cancel_check=lambda: True)


@patch("yt_dlp.YoutubeDL")
def test_execute_download_success(mock_ydl_class: MagicMock, tmp_path: Path):
    """Verify execute_download triggers yt-dlp with progress hooks and returns path."""
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl

    expected_file = tmp_path / "Test Video [123].mp4"
    expected_file.write_text("dummy media content", encoding="utf-8")

    mock_ydl.extract_info.return_value = {"id": "123", "title": "Test Video"}
    mock_ydl.prepare_filename.return_value = str(expected_file)

    progress_events: list[dict] = []
    result_path = execute_download(
        url="https://example.com/video",
        target_dir=tmp_path,
        format_id="best",
        progress_callback=lambda d: progress_events.append(d),
    )

    assert result_path == expected_file
    assert result_path.exists()
    mock_ydl.extract_info.assert_called_once_with("https://example.com/video", download=True)


@patch("yt_dlp.YoutubeDL")
def test_execute_download_cancellation(mock_ydl_class: MagicMock, tmp_path: Path):
    """Verify user cancellation during download raises DownloadCancelledError."""
    mock_ydl = MagicMock()
    mock_ydl_class.return_value.__enter__.return_value = mock_ydl
    mock_ydl.extract_info.side_effect = DownloadCancelled("Geannuleerd")

    with pytest.raises(DownloadCancelledError):
        execute_download(
            url="https://example.com/video",
            target_dir=tmp_path,
            format_id="best",
            progress_callback=lambda d: None,
            cancel_check=lambda: True,
        )
