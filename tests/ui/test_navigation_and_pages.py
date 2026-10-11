"""UI tests covering navigation, theme switching, settings interaction and empty states."""

from pathlib import Path

from open_video_downloader import __version__
from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.settings.models import AppSettings
from open_video_downloader.ui.main_window import MainWindow


def test_main_window_navigation_and_pages(qtbot, tmp_path: Path):
    """Verify MainWindow initializes, displays 5 pages and switches views correctly."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)

    window = MainWindow(settings_mgr)
    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert window.stack.count() == 5
    assert window.stack.currentIndex() == 0

    # Switch to QueuePage (index 1)
    window.nav_rail._button_group.button(1).click()
    assert window.stack.currentIndex() == 1
    assert "Wachtrij" in window.status_msg_label.text()

    # Switch to HistoryPage (index 2)
    window.nav_rail._button_group.button(2).click()
    assert window.stack.currentIndex() == 2
    assert "Geschiedenis" in window.status_msg_label.text()

    # Switch to SettingsPage (index 3)
    window.nav_rail._button_group.button(3).click()
    assert window.stack.currentIndex() == 3
    assert "Instellingen" in window.status_msg_label.text()

    # Switch to AboutPage (index 4)
    window.nav_rail._button_group.button(4).click()
    assert window.stack.currentIndex() == 4
    assert "Over" in window.status_msg_label.text()

    # Switch back to DownloadPage (index 0)
    window.nav_rail._button_group.button(0).click()
    assert window.stack.currentIndex() == 0


def test_main_window_theme_switching(qtbot, tmp_path: Path):
    """Verify applying dark, light, and system themes dynamically updates styling."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)

    window = MainWindow(settings_mgr)
    qtbot.addWidget(window)

    # 1. Dark theme
    window.apply_theme("dark")
    assert "#18181b" in window.styleSheet()

    # 2. Light theme
    window.apply_theme("light")
    assert "#f8f9fa" in window.styleSheet()

    # 3. System theme
    window.apply_theme("system")
    assert len(window.styleSheet()) > 100


def test_download_page_validation(qtbot, tmp_path: Path):
    """Verify DownloadPage prompts validation message for empty URL and emits signal."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    window = MainWindow(settings_mgr)
    qtbot.addWidget(window)
    window.show()

    page = window.download_page

    # Empty click
    page.url_input.setText("")
    page._on_fetch_clicked()
    assert page.status_msg.isVisible()
    assert "Voer eerst een geldige URL in" in page.status_msg.text()

    # Valid URL click
    emitted_urls: list[str] = []
    page.fetch_requested.connect(lambda u: emitted_urls.append(u))

    page.url_input.setText("https://example.com/video")
    page._on_fetch_clicked()
    assert len(emitted_urls) == 1
    assert emitted_urls[0] == "https://example.com/video"


def test_settings_page_save_and_reset(qtbot, tmp_path: Path):
    """Verify changing settings in SettingsPage persists through SettingsManager."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    window = MainWindow(settings_mgr)
    qtbot.addWidget(window)

    page = window.settings_page

    # Change concurrency to 5 and theme to light
    page.concurrency_spin.setValue(5)
    theme_idx = page.theme_combo.findData("light")
    page.theme_combo.setCurrentIndex(theme_idx)

    # Save
    page.save_btn.click()
    assert settings_mgr.get().max_concurrent_downloads == 5
    assert settings_mgr.get().theme == "light"
    assert "✓ Instellingen succesvol opgeslagen." in page.status_label.text()

    # Reset to defaults
    page.reset_btn.click()
    defaults = AppSettings.create_default()
    assert settings_mgr.get().max_concurrent_downloads == defaults.max_concurrent_downloads
    assert settings_mgr.get().theme == defaults.theme
    assert "✓ Standaardwaarden hersteld." in page.status_label.text()


def test_about_page_diagnostics_report(qtbot, tmp_path: Path):
    """Verify AboutPage generates complete diagnostic report and copies to clipboard."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    window = MainWindow(settings_mgr)
    qtbot.addWidget(window)

    page = window.about_page
    report = page.get_diagnostic_report()

    assert f"v{__version__}" in report
    assert "Python:" in report
    assert "PySide6:" in report
    assert "SQLite:" in report
    assert "yt-dlp:" in report

    # Click copy diagnostics button
    page.copy_btn.click()
    assert "✓ Diagnostiek gekopieerd" in page.copy_feedback.text()
