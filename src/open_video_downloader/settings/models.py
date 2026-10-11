"""Data models and validation rules for user settings."""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from open_video_downloader.core.constants import (
    DEFAULT_LANGUAGE,
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_CONCURRENT,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DEFAULT_THEME,
    SUPPORTED_LANGUAGES,
    SUPPORTED_LOG_LEVELS,
    SUPPORTED_THEMES,
)
from open_video_downloader.core.paths import get_default_download_dir


@dataclass
class AppSettings:
    """Strongly typed application configuration settings."""

    download_dir: str
    theme: str = DEFAULT_THEME
    language: str = DEFAULT_LANGUAGE
    notifications_enabled: bool = DEFAULT_NOTIFICATIONS_ENABLED
    log_level: str = DEFAULT_LOG_LEVEL
    max_concurrent_downloads: int = DEFAULT_MAX_CONCURRENT

    def to_dict(self) -> dict[str, Any]:
        """Convert settings instance to dictionary for JSON persistence."""
        return asdict(self)

    @classmethod
    def create_default(cls) -> "AppSettings":
        """Instantiate settings with safe default values."""
        return cls(
            download_dir=str(get_default_download_dir()),
            theme=DEFAULT_THEME,
            language=DEFAULT_LANGUAGE,
            notifications_enabled=DEFAULT_NOTIFICATIONS_ENABLED,
            log_level=DEFAULT_LOG_LEVEL,
            max_concurrent_downloads=DEFAULT_MAX_CONCURRENT,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AppSettings":
        """Validate raw dictionary and construct AppSettings with safe fallbacks."""
        defaults = cls.create_default()
        if not isinstance(data, dict):
            return defaults

        # 1. Download directory validation
        download_dir_raw = data.get("download_dir")
        if isinstance(download_dir_raw, str) and download_dir_raw.strip():
            dir_path = Path(download_dir_raw.strip())
            # Accept if directory exists or if parent exists, else fallback
            if dir_path.is_dir() or dir_path.parent.is_dir():
                download_dir = str(dir_path)
            else:
                download_dir = defaults.download_dir
        else:
            download_dir = defaults.download_dir

        # 2. Theme validation
        theme_raw = str(data.get("theme", "")).lower()
        theme = theme_raw if theme_raw in SUPPORTED_THEMES else defaults.theme

        # 3. Language validation
        lang_raw = str(data.get("language", "")).lower()
        language = lang_raw if lang_raw in SUPPORTED_LANGUAGES else defaults.language

        # 4. Notifications validation
        notif_raw = data.get("notifications_enabled")
        notifications_enabled = (
            bool(notif_raw) if isinstance(notif_raw, bool) else defaults.notifications_enabled
        )

        # 5. Log level validation
        log_level_raw = str(data.get("log_level", "")).upper()
        log_level = log_level_raw if log_level_raw in SUPPORTED_LOG_LEVELS else defaults.log_level

        # 6. Max concurrent downloads validation (bounded 1 to 8)
        max_concurrent_raw = data.get("max_concurrent_downloads")
        if isinstance(max_concurrent_raw, int) and 1 <= max_concurrent_raw <= 8:
            max_concurrent = max_concurrent_raw
        else:
            max_concurrent = defaults.max_concurrent_downloads

        return cls(
            download_dir=download_dir,
            theme=theme,
            language=language,
            notifications_enabled=notifications_enabled,
            log_level=log_level,
            max_concurrent_downloads=max_concurrent,
        )
