"""Comprehensive UI tests for responsive layouts across window sizes and DPI scales."""

from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QFont

from open_video_downloader.core.models import (
    DownloadTask,
    FormatOption,
    MediaMetadata,
    TaskStatus,
)
from open_video_downloader.core.queue_manager import QueueManager
from open_video_downloader.database.manager import DatabaseManager
from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.ui.main_window import MainWindow
from open_video_downloader.ui.pages.about_page import AboutPage
from open_video_downloader.ui.pages.download_page import DownloadPage
from open_video_downloader.ui.pages.history_page import HistoryPage
from open_video_downloader.ui.pages.queue_page import QueuePage
from open_video_downloader.ui.pages.settings_page import SettingsPage


def test_window_resizes_to_all_required_resolutions(qtbot, tmp_path: Path) -> None:
    """Verify MainWindow supports 800x600, 1024x700, 1280x800, and 1920x1080."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    db_mgr = DatabaseManager(db_path=tmp_path / "test.db")
    qm = QueueManager()

    window = MainWindow(settings_manager=settings_mgr, queue_manager=qm, database_manager=db_mgr)
    qtbot.addWidget(window)
    window.show()

    resolutions = [
        (800, 600),
        (1024, 700),
        (1280, 800),
        (1920, 1080),
    ]

    for width, height in resolutions:
        window.resize(width, height)
        qtbot.wait(20)
        assert window.width() == width
        assert window.height() == height

        # Verify all 5 pages can be navigated and displayed cleanly at this resolution
        for page_idx in range(5):
            window._switch_to_page(page_idx)
            assert window.stack.currentIndex() == page_idx
            current_page = window.stack.currentWidget()
            assert current_page.isVisible()


def test_navigation_rail_compact_mode_and_tooltips(qtbot, tmp_path: Path) -> None:
    """Verify NavigationRail enters compact mode on small screens and toggle button works."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    window = MainWindow(settings_manager=settings_mgr)
    qtbot.addWidget(window)
    window.show()

    # 1. At 1024 width, sidebar should be expanded (>= 920 breakpoint)
    window.resize(1024, 700)
    qtbot.wait(20)
    assert not window.nav_rail.is_compact
    assert window.nav_rail.width() == window.nav_rail.EXPANDED_WIDTH

    # 2. At 800 width, sidebar should automatically collapse to compact mode
    window.resize(800, 600)
    qtbot.wait(20)
    assert window.nav_rail.is_compact
    assert window.nav_rail.width() == window.nav_rail.COMPACT_WIDTH

    # Verify tooltips and accessibility names are present on buttons
    for btn in window.nav_rail._buttons:
        assert btn.toolTip() != ""
        assert btn.accessibleName() != ""
        assert btn.text() == ""  # Text hidden in compact mode

    # 3. Click toggle button to manually expand
    window.nav_rail.toggle_btn.click()
    assert not window.nav_rail.is_compact
    assert window.nav_rail.width() == window.nav_rail.EXPANDED_WIDTH
    for btn in window.nav_rail._buttons:
        assert btn.text().strip() != ""

    # 4. Click toggle button to manually collapse again
    window.nav_rail.toggle_btn.click()
    assert window.nav_rail.is_compact


def test_download_page_responsiveness_and_scroll_area(qtbot, tmp_path: Path) -> None:
    """Verify DownloadPage contents remain within bounds and reachable via scroll area."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    page = DownloadPage(settings_manager=settings_mgr)
    qtbot.addWidget(page)
    page.resize(600, 500)
    page.show()

    assert hasattr(page, "scroll_area")
    assert page.scroll_area.isVisible()

    # Load large metadata with long title and many formats
    meta = MediaMetadata(
        url="https://youtube.com/watch?v=very_long_sample_identifier_to_test_responsiveness",
        extractor="YouTube HD",
        id="vid_resp",
        title=(
            "Extraordinarily Long Video Title To Test Word Wrapping And "
            "Layout Integrity Across Small Screen Resolutions 2026"
        ),
        duration=7200,
        duration_str="02:00:00",
        formats=[
            FormatOption(
                "137+140",
                "mp4",
                "1080p Full HD (Combined Video+Audio, ~1.2 GB)",
                requires_ffmpeg=True,
            ),
            FormatOption("136+140", "mp4", "720p HD (~500 MB)", requires_ffmpeg=True),
            FormatOption("18", "mp4", "360p Standard (~180 MB)", requires_ffmpeg=False),
        ],
        uploader="International Documentary Film Network Official Channel",
    )
    page._on_metadata_ready(meta)

    # Primary buttons and controls must remain visible and accessible
    assert page.meta_card.isVisible()
    assert page.enqueue_btn.isVisible()
    assert page.format_combo.isVisible()
    assert page.dest_dir_input.isVisible()

    # Simulate enqueue click
    created_tasks: list[DownloadTask] = []
    page.task_created.connect(lambda t: created_tasks.append(t))
    page.enqueue_btn.click()
    assert len(created_tasks) == 1
    assert page.enqueue_feedback.isVisible()
    assert "✓" in page.enqueue_feedback.text()
    assert page.go_to_queue_btn.isVisible()


def test_queue_page_task_card_long_strings_wrapping(qtbot) -> None:
    """Verify QueuePage cards wrap long titles and stats without breaking bounds."""
    qm = QueueManager(max_concurrent=2)
    page = QueuePage(qm)
    qtbot.addWidget(page)
    page.resize(600, 500)
    page.show()

    long_title = "A" * 120
    task_downloading = DownloadTask(
        task_id="resp_t1",
        url="https://example.com/long_task",
        title=long_title,
        target_dir="C:/Users/TestUser/AppData/Local/OpenVideoDownloader/Downloads/Subfolder",
        status=TaskStatus.DOWNLOADING,
        progress=45.0,
        downloaded_bytes=45000000,
        total_bytes=100000000,
        speed_bytes_sec=3500000,
    )
    task_failed = DownloadTask(
        task_id="resp_t2",
        url="https://example.com/failed",
        title="Failed Transfer With Extremely Long Detailed Error Traceback Message For Testing",
        target_dir="C:/Downloads",
        status=TaskStatus.FAILED,
        error_message=(
            "HTTP Error 403 Forbidden: Cloudflare anti-bot challenged access "
            "token expired during stream muxing"
        ),
    )

    with patch.object(qm, "_start_task"):
        qm.add_task(task_downloading)
        qm.add_task(task_failed)

    assert len(page._card_widgets) == 2
    card1 = page._card_widgets["resp_t1"]
    assert not card1.cancel_btn.isHidden()
    assert not card1.stats_label.isHidden()

    card2 = page._card_widgets["resp_t2"]
    assert not card2.retry_btn.isHidden()
    assert "403" in card2.stats_label.text()


def test_history_page_long_urls_and_responsiveness(qtbot, tmp_path: Path) -> None:
    """Verify HistoryPage handles long unbroken URLs and small controls cleanly."""
    db_file = tmp_path / "hist_resp.db"
    db_mgr = DatabaseManager(db_path=db_file)

    very_long_url = "https://example.com/watch?v=abcd1234efgh5678" + "&param=" * 15 + "end"
    t = DownloadTask(
        task_id="hist_long",
        url=very_long_url,
        title="History Record With Massive URL",
        target_dir=str(tmp_path),
        final_filepath=str(tmp_path / "sample.mp4"),
        status=TaskStatus.COMPLETED,
        total_bytes=25000000,
    )
    db_mgr.save_task(t)

    page = HistoryPage(database_manager=db_mgr)
    qtbot.addWidget(page)
    page.resize(600, 500)
    page.show()

    assert len(page._cards) == 1
    card = page._cards[0]
    assert card.url_label.wordWrap()
    assert card.open_file_btn.isVisible()
    assert card.open_folder_btn.isVisible()
    assert card.delete_btn.isVisible()

    # Search & filters function properly at small width
    page.search_input.setText("History")
    assert len(page._cards) == 1
    page.search_input.setText("Nonexistent")
    assert page.no_results_card.isVisible()


def test_settings_page_scroll_area_and_accessibility(qtbot, tmp_path: Path) -> None:
    """Verify SettingsPage has scroll area, accessible inputs, and persists properly."""
    settings_mgr = SettingsManager(config_path=tmp_path / "settings.json")
    page = SettingsPage(settings_manager=settings_mgr)
    qtbot.addWidget(page)
    page.resize(600, 500)
    page.show()

    assert hasattr(page, "scroll_area")
    assert page.scroll_area.isVisible()

    # Change settings
    page.concurrency_spin.setValue(4)
    page.save_btn.click()
    assert settings_mgr.get().max_concurrent_downloads == 4
    assert page.status_label.isVisible()

    # Verify input accessibility names
    assert page.download_dir_input.accessibleName() != ""
    assert page.concurrency_spin.accessibleName() != ""
    assert page.theme_combo.accessibleName() != ""
    assert page.lang_combo.accessibleName() != ""
    assert page.save_btn.accessibleName() != ""


def test_about_page_scroll_area_and_report_copy(qtbot) -> None:
    """Verify AboutPage works within scroll area and copies diagnostic details."""
    page = AboutPage()
    qtbot.addWidget(page)
    page.resize(600, 500)
    page.show()

    assert hasattr(page, "scroll_area")
    assert page.scroll_area.isVisible()
    assert page.val_datadir.wordWrap()

    page.copy_btn.click()
    assert "✓" in page.copy_feedback.text()


def test_dpi_simulated_font_scaling(qtbot, tmp_path: Path) -> None:
    """Verify window and layouts accommodate large system font scaling (125%, 150%)."""
    settings_mgr = SettingsManager(config_path=tmp_path / "settings.json")
    window = MainWindow(settings_manager=settings_mgr)
    qtbot.addWidget(window)

    # Test with 14pt font (simulating 140% scaling)
    large_font = QFont("Segoe UI", 14)
    window.setFont(large_font)
    window.resize(800, 600)
    window.show()

    for idx in range(5):
        window._switch_to_page(idx)
        page = window.stack.currentWidget()
        assert page.isVisible()
        # Verify min size hint is within reasonable bounds
        msh = page.minimumSizeHint()
        assert msh.width() <= 800 or hasattr(page, "scroll_area")


def test_status_bar_responsiveness_on_resize(qtbot, tmp_path: Path) -> None:
    """Verify status bar permanent indicators adapt cleanly when window shrinks."""
    settings_mgr = SettingsManager(config_path=tmp_path / "settings.json")
    window = MainWindow(settings_manager=settings_mgr)
    qtbot.addWidget(window)
    window.show()

    # At 1280px width: full labels
    window.resize(1280, 800)
    qtbot.wait(20)
    assert window.theme_label.isVisible()
    assert "FFmpeg:" in window.ffmpeg_label.text()

    # At 800px width: compact labels
    window.resize(800, 600)
    qtbot.wait(20)
    assert "FFmpeg" in window.ffmpeg_label.text()
