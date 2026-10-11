"""Unit tests for core domain models, format options and status transitions."""

from open_video_downloader.core.models import (
    DownloadTask,
    FormatOption,
    MediaMetadata,
    TaskStatus,
    format_bytes,
    format_duration,
)


def test_task_status_transitions():
    """Verify enforced valid and invalid state transitions."""
    task = DownloadTask(
        url="https://example.com/video",
        title="Test Video",
        target_dir="C:/Downloads",
    )
    assert task.status == TaskStatus.WAITING

    # WAITING -> DOWNLOADING is valid
    assert task.set_status(TaskStatus.DOWNLOADING) is True
    assert task.status == TaskStatus.DOWNLOADING

    # DOWNLOADING -> WAITING is invalid
    assert task.set_status(TaskStatus.WAITING) is False
    assert task.status == TaskStatus.DOWNLOADING

    # DOWNLOADING -> PROCESSING is valid
    assert task.set_status(TaskStatus.PROCESSING) is True
    assert task.status == TaskStatus.PROCESSING

    # PROCESSING -> COMPLETED is valid
    assert task.set_status(TaskStatus.COMPLETED) is True
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None

    # COMPLETED is terminal (no transitions allowed)
    assert task.set_status(TaskStatus.WAITING) is False
    assert task.set_status(TaskStatus.DOWNLOADING) is False


def test_task_status_failed_retry():
    """Verify failed tasks can be transitioned back to WAITING for retry."""
    task = DownloadTask(
        url="https://example.com/video",
        title="Test Video",
        target_dir="C:/Downloads",
    )
    task.set_status(TaskStatus.DOWNLOADING)
    task.set_status(TaskStatus.FAILED)
    assert task.status == TaskStatus.FAILED

    # FAILED -> WAITING is valid for retry
    assert task.set_status(TaskStatus.WAITING) is True
    assert task.status == TaskStatus.WAITING


def test_format_helpers():
    """Verify byte and duration human-readable formatting."""
    assert format_bytes(None) == "onbekend"
    assert format_bytes(0) == "onbekend"
    assert format_bytes(512) == "512.0 B"
    assert format_bytes(1048576) == "1.0 MB"
    assert format_bytes(1073741824) == "1.0 GB"

    assert format_duration(None) == "--:--"
    assert format_duration(45) == "00:45"
    assert format_duration(125) == "02:05"
    assert format_duration(3665) == "01:01:05"


def test_format_option_serialization():
    """Verify FormatOption to_dict and from_dict roundtrip."""
    fmt = FormatOption(
        format_id="137+140",
        ext="mp4",
        resolution="1080p",
        filesize=45000000,
        is_video_only=False,
        requires_ffmpeg=True,
    )
    data = fmt.to_dict()
    restored = FormatOption.from_dict(data)

    assert restored.format_id == "137+140"
    assert restored.resolution == "1080p"
    assert restored.requires_ffmpeg is True
    assert "1080p" in restored.display_label
    assert "[Vereist FFmpeg]" in restored.display_label


def test_media_metadata_best_helpers():
    """Verify best_video_format and best_audio_format selection."""
    video_1080 = FormatOption(format_id="1", ext="mp4", resolution="1080p", is_audio_only=False)
    video_720 = FormatOption(format_id="2", ext="mp4", resolution="720p", is_audio_only=False)
    audio_m4a = FormatOption(format_id="3", ext="m4a", resolution="Audio", is_audio_only=True)

    meta = MediaMetadata(
        url="https://example.com/video",
        extractor="YouTube",
        id="123",
        title="Title",
        formats=[video_1080, video_720, audio_m4a],
    )

    assert meta.best_video_format == video_1080
    assert meta.best_audio_format == audio_m4a
