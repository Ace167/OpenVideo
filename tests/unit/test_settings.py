"""Unit tests for settings data model, validation and persistent SettingsManager."""

from pathlib import Path

from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.settings.models import AppSettings


def test_app_settings_create_default():
    """Verify default settings instantiation has sensible values."""
    settings = AppSettings.create_default()
    assert Path(settings.download_dir).exists()
    assert settings.theme == "system"
    assert settings.language == "nl"
    assert settings.notifications_enabled is True
    assert settings.log_level == "INFO"
    assert settings.max_concurrent_downloads == 3


def test_app_settings_from_dict_valid(tmp_path: Path):
    """Verify construct from valid dictionary preserves values."""
    custom_dir = str(tmp_path)
    data = {
        "download_dir": custom_dir,
        "theme": "dark",
        "language": "en",
        "notifications_enabled": False,
        "log_level": "DEBUG",
        "max_concurrent_downloads": 5,
    }
    settings = AppSettings.from_dict(data)
    assert settings.download_dir == custom_dir
    assert settings.theme == "dark"
    assert settings.language == "en"
    assert settings.notifications_enabled is False
    assert settings.log_level == "DEBUG"
    assert settings.max_concurrent_downloads == 5


def test_app_settings_from_dict_invalid_fallbacks(tmp_path: Path):
    """Verify invalid or corrupted field values safely fallback to defaults."""
    bad_data = {
        "download_dir": "Z:\\NonExistent_Invalid_Folder_12345\\sub",
        "theme": "neon-glow-invalid",
        "language": "esperanto",
        "notifications_enabled": "not_a_bool",
        "log_level": "VERBOSE_SUPER",
        "max_concurrent_downloads": 999,  # out of bound (max 8)
    }
    settings = AppSettings.from_dict(bad_data)
    defaults = AppSettings.create_default()

    assert settings.download_dir == defaults.download_dir
    assert settings.theme == defaults.theme
    assert settings.language == defaults.language
    assert settings.notifications_enabled == defaults.notifications_enabled
    assert settings.log_level == defaults.log_level
    assert settings.max_concurrent_downloads == defaults.max_concurrent_downloads


def test_settings_manager_load_missing_file(tmp_path: Path):
    """Verify loading from non-existent file returns default settings without error."""
    config_file = tmp_path / "non_existent_settings.json"
    manager = SettingsManager(config_path=config_file)
    settings = manager.get()
    assert settings.theme == "system"
    assert not config_file.exists()


def test_settings_manager_save_and_load(tmp_path: Path):
    """Verify saving settings persists to disk and can be reloaded."""
    config_file = tmp_path / "settings.json"
    manager = SettingsManager(config_path=config_file)

    new_settings = AppSettings(
        download_dir=str(tmp_path),
        theme="light",
        language="en",
        notifications_enabled=False,
        log_level="WARNING",
        max_concurrent_downloads=2,
    )
    assert manager.save_settings(new_settings) is True
    assert config_file.exists()

    # Re-read with a fresh manager instance
    fresh_manager = SettingsManager(config_path=config_file)
    loaded = fresh_manager.get()
    assert loaded.theme == "light"
    assert loaded.language == "en"
    assert loaded.notifications_enabled is False
    assert loaded.log_level == "WARNING"
    assert loaded.max_concurrent_downloads == 2


def test_settings_manager_signal_emission(tmp_path: Path):
    """Verify settings_changed signal is emitted when save_settings is called."""
    config_file = tmp_path / "settings.json"
    manager = SettingsManager(config_path=config_file)

    emitted: list[AppSettings] = []
    manager.settings_changed.connect(lambda s: emitted.append(s))

    manager.update(theme="dark", max_concurrent_downloads=4)

    assert len(emitted) == 1
    assert emitted[0].theme == "dark"
    assert emitted[0].max_concurrent_downloads == 4


def test_settings_manager_corrupted_json_recovery(tmp_path: Path):
    """Verify corrupted JSON file does not crash the manager and falls back safely."""
    config_file = tmp_path / "corrupted_settings.json"
    with config_file.open("w", encoding="utf-8") as f:
        f.write("{ invalid json content ::: 12345")

    manager = SettingsManager(config_path=config_file)
    settings = manager.get()
    assert settings.theme == "system"
