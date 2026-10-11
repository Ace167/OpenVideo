"""Persistent settings manager with atomic disk writes and Qt signals."""

import json
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from open_video_downloader.core.paths import get_app_data_dir
from open_video_downloader.services.logger import get_logger
from open_video_downloader.settings.models import AppSettings

logger = get_logger("settings")


class SettingsManager(QObject):
    """Manages reading, writing, and notifying changes to user configuration settings."""

    # Signal emitted whenever settings are saved/updated with the new AppSettings instance
    settings_changed = Signal(object)

    def __init__(self, config_path: Path | None = None) -> None:
        super().__init__()
        if config_path is not None:
            self._config_path = config_path
        else:
            self._config_path = get_app_data_dir() / "settings.json"

        self._current_settings: AppSettings = self.load_settings()

    @property
    def config_path(self) -> Path:
        """Return the target settings file path."""
        return self._config_path

    def get(self) -> AppSettings:
        """Return current in-memory settings."""
        return self._current_settings

    def load_settings(self) -> AppSettings:
        """Load settings from JSON file with safe fallbacks if missing or corrupted."""
        if not self._config_path.exists():
            logger.info(
                "Geen bestaand configuratiebestand op '%s'. Standaardwaarden worden gebruikt.",
                self._config_path,
            )
            settings = AppSettings.create_default()
            self._current_settings = settings
            return settings

        try:
            with self._config_path.open("r", encoding="utf-8") as f:
                raw_data = json.load(f)
            settings = AppSettings.from_dict(raw_data)
            logger.info("Instellingen succesvol geladen vanaf '%s'.", self._config_path)
        except Exception as err:
            logger.warning(
                "Fout bij lezen van instellingen '%s' (%s). Terugval op veilige standaardwaarden.",
                self._config_path,
                err,
            )
            settings = AppSettings.create_default()

        self._current_settings = settings
        return settings

    def save_settings(self, settings: AppSettings) -> bool:
        """Save settings to disk using an atomic temporary write pattern."""
        try:
            # Ensure parent directory exists
            parent_dir = self._config_path.parent
            parent_dir.mkdir(parents=True, exist_ok=True)

            temp_path = parent_dir / f"{self._config_path.name}.tmp"
            with temp_path.open("w", encoding="utf-8") as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)

            # Atomic replace on Windows / POSIX
            temp_path.replace(self._config_path)

            self._current_settings = settings
            logger.info("Instellingen succesvol opgeslagen naar '%s'.", self._config_path)
            self.settings_changed.emit(settings)
            return True
        except Exception as err:
            logger.error("Fout bij opslaan van instellingen naar '%s': %s", self._config_path, err)
            return False

    def update(self, **kwargs: object) -> bool:
        """Update specific settings attributes and persist changes."""
        current_dict = self._current_settings.to_dict()
        current_dict.update(kwargs)
        new_settings = AppSettings.from_dict(current_dict)
        return self.save_settings(new_settings)
