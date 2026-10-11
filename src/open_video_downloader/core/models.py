"""Core domain models: task statuses, format options, metadata and download tasks."""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from open_video_downloader.services.logger import get_logger

logger = get_logger("core.models")


class TaskStatus(str, Enum):
    """Lifecycle statuses for a download task."""

    WAITING = "waiting"
    FETCHING_METADATA = "fetching_metadata"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def label_nl(self) -> str:
        """User-friendly Dutch status label."""
        labels = {
            TaskStatus.WAITING: "In wachtrij",
            TaskStatus.FETCHING_METADATA: "Gegevens ophalen...",
            TaskStatus.DOWNLOADING: "Downloaden...",
            TaskStatus.PROCESSING: "Samenvoegen...",
            TaskStatus.COMPLETED: "Voltooid",
            TaskStatus.FAILED: "Mislukt",
            TaskStatus.CANCELLED: "Geannuleerd",
        }
        return labels.get(self, self.value)

    @property
    def label(self) -> str:
        """User-facing localized status label based on active language."""
        from open_video_downloader.services.i18n import get_language

        if get_language() == "en":
            labels_en = {
                TaskStatus.WAITING: "In queue",
                TaskStatus.FETCHING_METADATA: "Fetching info...",
                TaskStatus.DOWNLOADING: "Downloading...",
                TaskStatus.PROCESSING: "Processing...",
                TaskStatus.COMPLETED: "Completed",
                TaskStatus.FAILED: "Failed",
                TaskStatus.CANCELLED: "Cancelled",
            }
            return labels_en.get(self, self.value)
        return self.label_nl


VALID_STATUS_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.WAITING: {
        TaskStatus.FETCHING_METADATA,
        TaskStatus.DOWNLOADING,
        TaskStatus.CANCELLED,
    },
    TaskStatus.FETCHING_METADATA: {
        TaskStatus.WAITING,
        TaskStatus.DOWNLOADING,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.DOWNLOADING: {
        TaskStatus.PROCESSING,
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.PROCESSING: {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    },
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: {TaskStatus.WAITING},  # Retry allowed
    TaskStatus.CANCELLED: {TaskStatus.WAITING},  # Retry allowed
}


def format_bytes(num_bytes: int | float | None) -> str:
    """Format byte count into human-readable string (KB, MB, GB)."""
    if num_bytes is None or num_bytes <= 0:
        return "onbekend"
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0 or unit == "TB":
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def format_duration(seconds: int | None) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS."""
    if seconds is None or seconds < 0:
        return "--:--"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


@dataclass
class FormatOption:
    """Describes a specific video/audio format option provided by the extractor."""

    format_id: str
    ext: str
    resolution: str
    filesize: int | None = None
    filesize_approx: int | None = None
    vcodec: str = "none"
    acodec: str = "none"
    fps: float | None = None
    tbr: float | None = None
    is_audio_only: bool = False
    is_video_only: bool = False
    requires_ffmpeg: bool = False
    note: str = ""

    @property
    def display_label(self) -> str:
        """Formatted user-facing label for format selection dropdown."""
        from open_video_downloader.services.i18n import get_language

        size_bytes = self.filesize or self.filesize_approx
        size_str = f", ~{format_bytes(size_bytes)}" if size_bytes else ""
        if get_language() == "en":
            ffmpeg_tag = " [Requires FFmpeg]" if self.requires_ffmpeg else ""
        else:
            ffmpeg_tag = " [Vereist FFmpeg]" if self.requires_ffmpeg else ""

        if self.is_audio_only:
            codec_str = self.acodec if self.acodec != "none" else self.ext.upper()
            return f"Audio Only ({self.ext.upper()}, {codec_str}{size_str}){ffmpeg_tag}"

        res_str = self.resolution if self.resolution != "none" else "Video"
        return f"{res_str} ({self.ext.upper()}{size_str}){ffmpeg_tag}"

    def to_dict(self) -> dict[str, Any]:
        """Serialize FormatOption to dictionary."""
        return {
            "format_id": self.format_id,
            "ext": self.ext,
            "resolution": self.resolution,
            "filesize": self.filesize,
            "filesize_approx": self.filesize_approx,
            "vcodec": self.vcodec,
            "acodec": self.acodec,
            "fps": self.fps,
            "tbr": self.tbr,
            "is_audio_only": self.is_audio_only,
            "is_video_only": self.is_video_only,
            "requires_ffmpeg": self.requires_ffmpeg,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FormatOption":
        """Reconstruct FormatOption from dictionary."""
        return cls(
            format_id=str(data.get("format_id", "")),
            ext=str(data.get("ext", "mp4")),
            resolution=str(data.get("resolution", "")),
            filesize=data.get("filesize"),
            filesize_approx=data.get("filesize_approx"),
            vcodec=str(data.get("vcodec", "none")),
            acodec=str(data.get("acodec", "none")),
            fps=data.get("fps"),
            tbr=data.get("tbr"),
            is_audio_only=bool(data.get("is_audio_only", False)),
            is_video_only=bool(data.get("is_video_only", False)),
            requires_ffmpeg=bool(data.get("requires_ffmpeg", False)),
            note=str(data.get("note", "")),
        )


@dataclass
class MediaMetadata:
    """Parsed video/audio information returned from yt-dlp probing."""

    url: str
    extractor: str
    id: str
    title: str
    description: str = ""
    duration: int | None = None
    duration_str: str = ""
    thumbnail_url: str = ""
    uploader: str = ""
    view_count: int | None = None
    formats: list[FormatOption] = field(default_factory=list)

    @property
    def best_video_format(self) -> FormatOption | None:
        """Return highest resolution video format option."""
        video_formats = [f for f in self.formats if not f.is_audio_only]
        if not video_formats:
            return None
        # Sort by resolution / bitrate
        return video_formats[0]

    @property
    def best_audio_format(self) -> FormatOption | None:
        """Return highest quality audio-only format option."""
        audio_formats = [f for f in self.formats if f.is_audio_only]
        if not audio_formats:
            return None
        return audio_formats[0]


@dataclass
class DownloadTask:
    """Represents a scheduled, active or finished download task."""

    url: str
    title: str
    target_dir: str
    selected_format: FormatOption | None = None
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    final_filepath: str | None = None
    status: TaskStatus = TaskStatus.WAITING
    progress: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int | None = None
    speed_bytes_sec: float | None = None
    eta_seconds: int | None = None
    error_message: str | None = None
    created_at: float = field(default_factory=time.time)
    completed_at: float | None = None

    def can_transition_to(self, target: TaskStatus) -> bool:
        """Check whether status transition is valid."""
        allowed = VALID_STATUS_TRANSITIONS.get(self.status, set())
        return target in allowed

    def set_status(self, new_status: TaskStatus) -> bool:
        """Perform validated status transition."""
        if self.status == new_status:
            return True

        if not self.can_transition_to(new_status):
            logger.warning(
                "Ongeldige statusovergang van %s naar %s voor taak %s.",
                self.status.value,
                new_status.value,
                self.task_id,
            )
            return False

        self.status = new_status
        if new_status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            self.completed_at = time.time()
        return True

    @property
    def filename(self) -> str | None:
        """Return base filename derived from final_filepath if available."""
        if self.final_filepath:
            return Path(self.final_filepath).name
        return None
