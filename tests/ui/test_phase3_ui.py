"""UI tests for Phase 3 download views, format selection and queue interactions."""

from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMessageBox

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
from open_video_downloader.ui.pages.download_page import DownloadPage
from open_video_downloader.ui.pages.queue_page import QueuePage


def test_download_page_metadata_flow(qtbot, tmp_path: Path):
    """Verify DownloadPage updates controls when metadata arrives or errors occur."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)

    page = DownloadPage(settings_mgr)
    qtbot.addWidget(page)
    page.show()

    assert page.empty_card.isVisible()
    assert not page.meta_card.isVisible()

    # 1. Simulate metadata arrival
    fmt_1080 = FormatOption(
        format_id="137+140",
        ext="mp4",
        resolution="1080p",
        requires_ffmpeg=True,
    )
    fmt_audio = FormatOption(
        format_id="140",
        ext="m4a",
        resolution="Audio",
        is_audio_only=True,
        requires_ffmpeg=False,
    )
    meta = MediaMetadata(
        url="https://example.com/video",
        extractor="TestHost",
        id="vid1",
        title="Super Nature Documentary",
        duration=120,
        duration_str="02:00",
        formats=[fmt_1080, fmt_audio],
    )

    page._on_metadata_ready(meta)

    assert not page.empty_card.isVisible()
    assert page.meta_card.isVisible()
    assert page.media_title_label.text() == "Super Nature Documentary"
    assert page.format_combo.count() == 2

    # 2. Simulate task creation click
    created_tasks: list[DownloadTask] = []
    page.task_created.connect(lambda t: created_tasks.append(t))

    page.enqueue_btn.click()
    assert len(created_tasks) == 1
    assert created_tasks[0].title == "Super Nature Documentary"
    assert "✓ Taak toegevoegd aan wachtrij" in page.enqueue_feedback.text()
    assert page.go_to_queue_btn.isVisible()


def test_download_page_error_handling(qtbot, tmp_path: Path):
    """Verify DownloadPage presents clear error when metadata worker fails."""
    settings_file = tmp_path / "settings.json"
    settings_mgr = SettingsManager(config_path=settings_file)
    page = DownloadPage(settings_mgr)
    qtbot.addWidget(page)
    page.show()

    page._on_metadata_error("Video is verwijderd of privé.", "HTTP 404")
    assert page.status_msg.isVisible()
    assert "Video is verwijderd of privé" in page.status_msg.text()
    assert page.fetch_btn.isEnabled()


def test_queue_page_task_card_lifecycle(qtbot):
    """Verify QueuePage transitions from empty state to populated task cards."""
    qm = QueueManager(max_concurrent=1)
    page = QueuePage(qm)
    qtbot.addWidget(page)
    page.show()

    assert page.empty_card.isVisible()
    assert not page.scroll_area.isVisible()

    # Add task
    task = DownloadTask(
        task_id="task_abc",
        url="https://example.com/item",
        title="Downloading Nature Clips",
        target_dir="C:/Downloads",
        selected_format=FormatOption("best", "mp4", "1080p"),
    )

    with patch.object(qm, "_start_task"):
        qm.add_task(task)

    assert not page.empty_card.isVisible()
    assert page.scroll_area.isVisible()
    assert "task_abc" in page._card_widgets

    card = page._card_widgets["task_abc"]
    assert card.title_label.text() == "Downloading Nature Clips"

    # Simulate progress
    task.set_status(TaskStatus.DOWNLOADING)
    task.downloaded_bytes = 5000000
    task.total_bytes = 10000000
    task.speed_bytes_sec = 2500000
    task.progress = 50.0

    qm.task_progress.emit("task_abc", 50.0, "2.5 MB/s", "Resterend: 00:02")
    assert card.progress_bar.value() == 50


def test_main_window_close_event_prompt(qtbot, tmp_path: Path):
    """Verify MainWindow prompts confirmation before closing if downloads are active."""
    settings_mgr = SettingsManager(config_path=tmp_path / "settings.json")
    qm = QueueManager(max_concurrent=2)
    db_mgr = DatabaseManager(db_path=tmp_path / "db.sqlite")

    window = MainWindow(
        settings_manager=settings_mgr,
        queue_manager=qm,
        database_manager=db_mgr,
    )
    qtbot.addWidget(window)
    window.show()

    # 1. Close when no active tasks: should accept immediately
    close_evt = QCloseEvent()
    window.closeEvent(close_evt)
    assert close_evt.isAccepted()

    # 2. Add an active downloading task
    active_task = DownloadTask(
        task_id="active_t",
        url="https://example.com/active",
        title="Active Clip",
        target_dir="C:/",
        status=TaskStatus.DOWNLOADING,
    )
    qm._tasks["active_t"] = active_task

    # When user rejects prompt, event is ignored
    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
        close_evt2 = QCloseEvent()
        window.closeEvent(close_evt2)
        assert not close_evt2.isAccepted()

    # When user accepts prompt, event is accepted and shutdown called
    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
        with patch.object(qm, "shutdown") as mock_shutdown:
            close_evt3 = QCloseEvent()
            window.closeEvent(close_evt3)
            assert close_evt3.isAccepted()
            mock_shutdown.assert_called_once()

    qm._tasks.clear()
