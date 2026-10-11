"""UI tests for Phase 4 history page, search/filter interactions, and SQLite integration."""

from pathlib import Path
from unittest.mock import patch

from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import QMessageBox

from open_video_downloader.core.models import (
    DownloadTask,
    FormatOption,
    TaskStatus,
)
from open_video_downloader.core.queue_manager import QueueManager
from open_video_downloader.database.manager import DatabaseManager
from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.ui.main_window import MainWindow
from open_video_downloader.ui.pages.history_page import HistoryItemCard, HistoryPage


def test_history_page_empty_state_and_controls_disabled(qtbot, tmp_path: Path) -> None:
    """Verify HistoryPage shows empty card and disables filter controls when DB has 0 items."""
    db_file = tmp_path / "empty.db"
    db_mgr = DatabaseManager(db_path=db_file)

    page = HistoryPage(database_manager=db_mgr)
    qtbot.addWidget(page)
    page.show()

    assert page.empty_card.isVisible()
    assert not page.no_results_card.isVisible()
    assert not page.scroll_area.isVisible()

    assert not page.search_input.isEnabled()
    assert not page.status_filter_combo.isEnabled()
    assert not page.sort_combo.isEnabled()
    assert not page.clear_btn.isEnabled()


def test_history_page_populates_cards_for_all_statuses(qtbot, tmp_path: Path) -> None:
    """Verify HistoryPage presents cards for completed, failed, and cancelled downloads."""
    db_file = tmp_path / "populated.db"
    db_mgr = DatabaseManager(db_path=db_file)

    t_comp = DownloadTask(
        task_id="t_comp",
        url="https://example.com/comp",
        title="Completed Video Clip",
        target_dir=str(tmp_path),
        final_filepath=str(tmp_path / "comp.mp4"),
        selected_format=FormatOption("137", "mp4", "1080p"),
        status=TaskStatus.COMPLETED,
        total_bytes=15000000,
    )
    t_fail = DownloadTask(
        task_id="t_fail",
        url="https://example.com/fail",
        title="Failed Video Clip",
        target_dir=str(tmp_path),
        status=TaskStatus.FAILED,
        error_message="HTTP Error 403: Forbidden",
    )
    t_canc = DownloadTask(
        task_id="t_canc",
        url="https://example.com/canc",
        title="Cancelled Download",
        target_dir=str(tmp_path),
        status=TaskStatus.CANCELLED,
    )

    db_mgr.save_task(t_comp)
    db_mgr.save_task(t_fail)
    db_mgr.save_task(t_canc)

    page = HistoryPage(database_manager=db_mgr)
    qtbot.addWidget(page)
    page.show()

    assert not page.empty_card.isVisible()
    assert not page.no_results_card.isVisible()
    assert page.scroll_area.isVisible()

    assert page.search_input.isEnabled()
    assert page.status_filter_combo.isEnabled()
    assert page.sort_combo.isEnabled()
    assert page.clear_btn.isEnabled()
    assert len(page._cards) == 3

    # Check that completed card shows open file button
    comp_card = next(c for c in page._cards if c.task_id == "t_comp")
    assert comp_card.status_badge.text() == "Voltooid"
    assert comp_card.open_file_btn.isVisible()

    # Check that failed card displays error banner
    fail_card = next(c for c in page._cards if c.task_id == "t_fail")
    assert fail_card.status_badge.text() == "Mislukt"
    assert not fail_card.open_file_btn.isVisible()
    assert hasattr(fail_card, "error_label")
    assert "403" in fail_card.error_label.text()


def test_history_page_search_and_filter_interactions(qtbot, tmp_path: Path) -> None:
    """Verify searching and status filtering updates rendered cards and no-results view."""
    db_file = tmp_path / "search_ui.db"
    db_mgr = DatabaseManager(db_path=db_file)

    t1 = DownloadTask(
        task_id="t1",
        url="https://youtube.com/ocean",
        title="Deep Blue Ocean",
        target_dir=str(tmp_path),
        final_filepath=str(tmp_path / "ocean.mp4"),
        status=TaskStatus.COMPLETED,
    )
    t2 = DownloadTask(
        task_id="t2",
        url="https://vimeo.com/mountain",
        title="Snow Mountain",
        target_dir=str(tmp_path),
        final_filepath=str(tmp_path / "mountain.mp4"),
        status=TaskStatus.FAILED,
        error_message="Network Timeout",
    )
    db_mgr.save_task(t1)
    db_mgr.save_task(t2)

    page = HistoryPage(database_manager=db_mgr)
    qtbot.addWidget(page)
    page.show()

    # 1. Search by title "Ocean"
    page.search_input.setText("Ocean")
    assert len(page._cards) == 1
    assert page._cards[0].task_id == "t1"

    # 2. Search for non-matching query
    page.search_input.setText("Galaxy Nonexistent")
    assert len(page._cards) == 0
    assert page.no_results_card.isVisible()
    assert not page.scroll_area.isVisible()

    # 3. Reset filters button resets view
    page.reset_filters_btn.click()
    assert page.search_input.text() == ""
    assert not page.no_results_card.isVisible()
    assert len(page._cards) == 2

    # 4. Filter by status "Mislukt"
    idx = page.status_filter_combo.findData(TaskStatus.FAILED)
    page.status_filter_combo.setCurrentIndex(idx)
    assert len(page._cards) == 1
    assert page._cards[0].task_id == "t2"


def test_history_page_delete_single_and_clear_all(qtbot, tmp_path: Path) -> None:
    """Verify deleting a single history item and clearing all history."""
    db_file = tmp_path / "delete.db"
    db_mgr = DatabaseManager(db_path=db_file)

    t1 = DownloadTask(task_id="t1", url="https://ex.com/1", title="V1", target_dir="C:/")
    t2 = DownloadTask(task_id="t2", url="https://ex.com/2", title="V2", target_dir="C:/")
    db_mgr.save_task(t1)
    db_mgr.save_task(t2)

    page = HistoryPage(database_manager=db_mgr)
    qtbot.addWidget(page)
    page.show()
    assert len(page._cards) == 2

    # 1. Delete single item
    card1 = next(c for c in page._cards if c.task_id == "t1")
    card1.delete_btn.click()
    assert len(page._cards) == 1
    assert db_mgr.get_task("t1") is None
    assert db_mgr.get_task("t2") is not None

    # 2. Clear all history with user prompt
    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
        page.clear_btn.click()

    assert db_mgr.total_history_count() == 0
    assert page.empty_card.isVisible()
    assert not page.scroll_area.isVisible()


def test_history_card_open_file_and_folder_safety(qtbot, tmp_path: Path) -> None:
    """Verify file/folder actions only trigger URL when path exists, prompting user safely."""
    real_file = tmp_path / "actual_video.mp4"
    real_file.write_text("dummy video content", encoding="utf-8")

    task = DownloadTask(
        task_id="t_real",
        url="https://example.com/v",
        title="Video With Real File",
        target_dir=str(tmp_path),
        final_filepath=str(real_file),
        status=TaskStatus.COMPLETED,
    )

    card = HistoryItemCard(task)
    qtbot.addWidget(card)

    # 1. When file exists, QDesktopServices.openUrl is invoked
    with patch.object(QDesktopServices, "openUrl") as mock_open:
        card._on_open_file()
        mock_open.assert_called_once()

    with patch.object(QDesktopServices, "openUrl") as mock_open_folder:
        card._on_open_folder()
        mock_open_folder.assert_called_once()

    # 2. When file has been deleted from disk, informational message is displayed safely
    real_file.unlink()
    with patch.object(QMessageBox, "information") as mock_info:
        card._on_open_file()
        mock_info.assert_called_once()
        assert "Bestand niet gevonden" in mock_info.call_args[0][1]


def test_main_window_queue_to_history_lifecycle(qtbot, tmp_path: Path) -> None:
    """Verify task lifecycle events automatically update and refresh HistoryPage in MainWindow."""
    settings_mgr = SettingsManager(config_path=tmp_path / "settings.json")
    qm = QueueManager(max_concurrent=2)
    db_mgr = DatabaseManager(db_path=tmp_path / "mw_history.db")

    window = MainWindow(
        settings_manager=settings_mgr,
        queue_manager=qm,
        database_manager=db_mgr,
    )
    qtbot.addWidget(window)
    window.show()

    # 1. Simulate task completed event
    t_comp = DownloadTask(
        task_id="t_live_comp",
        url="https://example.com/live",
        title="Live Streamed Document",
        target_dir=str(tmp_path),
        final_filepath=str(tmp_path / "live.mp4"),
        status=TaskStatus.COMPLETED,
    )
    qm._tasks["t_live_comp"] = t_comp
    qm.task_completed.emit("t_live_comp", str(tmp_path / "live.mp4"))

    # Verify task was saved in DB and rendered in history page
    assert db_mgr.get_task("t_live_comp") is not None
    assert len(window.history_page._cards) == 1
    assert window.history_page._cards[0].title_label.text() == "Live Streamed Document"

    # 2. Simulate task cancellation event
    t_canc = DownloadTask(
        task_id="t_live_canc",
        url="https://example.com/canc",
        title="Cancelled Transfer",
        target_dir=str(tmp_path),
        status=TaskStatus.CANCELLED,
    )
    qm._tasks["t_live_canc"] = t_canc
    qm.task_cancelled.emit("t_live_canc")

    assert db_mgr.get_task("t_live_canc") is not None
    assert db_mgr.get_task("t_live_canc").status == TaskStatus.CANCELLED
    assert len(window.history_page._cards) == 2

    qm._tasks.clear()


def test_main_window_close_event_persists_active_cancelled_tasks(qtbot, tmp_path: Path) -> None:
    """Verify active tasks are saved as cancelled in DB when user confirms exit."""
    settings_mgr = SettingsManager(config_path=tmp_path / "settings.json")
    qm = QueueManager(max_concurrent=2)
    db_mgr = DatabaseManager(db_path=tmp_path / "close_test.db")

    window = MainWindow(
        settings_manager=settings_mgr,
        queue_manager=qm,
        database_manager=db_mgr,
    )
    qtbot.addWidget(window)
    window.show()

    active_task = DownloadTask(
        task_id="act_1",
        url="https://example.com/active",
        title="Active Clip On Exit",
        target_dir=str(tmp_path),
        status=TaskStatus.DOWNLOADING,
    )
    qm._tasks["act_1"] = active_task

    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
        close_evt = QCloseEvent()
        window.closeEvent(close_evt)
        assert close_evt.isAccepted()

    # Verify task was marked cancelled and saved to DB
    saved = db_mgr.get_task("act_1")
    assert saved is not None
    assert saved.status == TaskStatus.CANCELLED
    assert "Geannuleerd wegens afsluiten" in str(saved.error_message)

    qm._tasks.clear()


def test_application_relaunch_marks_abandoned_tasks_interrupted(tmp_path: Path) -> None:
    """Verify new database session on relaunch marks any unclosed active tasks as failed."""
    db_file = tmp_path / "relaunch.db"

    # Session 1: app unexpectedly terminates leaving tasks active
    mgr1 = DatabaseManager(db_path=db_file)
    t = DownloadTask(
        task_id="abandoned_t",
        url="https://example.com/abandoned",
        title="Abandoned In Flight",
        target_dir=str(tmp_path),
        status=TaskStatus.DOWNLOADING,
    )
    mgr1.save_task(t)

    # Session 2: application restarts and initializes new DatabaseManager
    mgr2 = DatabaseManager(db_path=db_file)
    recovered = mgr2.get_task("abandoned_t")
    assert recovered is not None
    assert recovered.status == TaskStatus.FAILED
    assert "Onderbroken" in str(recovered.error_message)
