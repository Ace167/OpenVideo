"""Probing and detection of FFmpeg and FFprobe binary availability."""

import shutil
import subprocess

from open_video_downloader.services.logger import get_logger

logger = get_logger("engines.ffmpeg_probe")


def get_ffmpeg_path() -> str | None:
    """Return absolute path to ffmpeg executable if found on system PATH."""
    return shutil.which("ffmpeg")


def get_ffprobe_path() -> str | None:
    """Return absolute path to ffprobe executable if found on system PATH."""
    return shutil.which("ffprobe")


def is_ffmpeg_available() -> bool:
    """Return True if ffmpeg executable is present on PATH."""
    return get_ffmpeg_path() is not None


def is_ffprobe_available() -> bool:
    """Return True if ffprobe executable is present on PATH."""
    return get_ffprobe_path() is not None


def get_ffmpeg_version() -> str | None:
    """Execute ffmpeg -version and parse the first output line."""
    ffmpeg_path = get_ffmpeg_path()
    if not ffmpeg_path:
        return None

    try:
        proc = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout:
            first_line = proc.stdout.splitlines()[0].strip()
            return first_line
    except Exception as err:
        logger.warning("Fout bij aanroepen van ffmpeg -version: %s", err)

    return None
