"""Unit tests for SQLite database manager, schema migrations and task persistence."""

import sqlite3
import time
from pathlib import Path
from unittest.mock import patch

from open_video_downloader.core.models import DownloadTask, FormatOption, TaskStatus
from open_video_downloader.database.manager import CURRENT_SCHEMA_VERSION, DatabaseManager


def test_database_initialization(tmp_path: Path) -> None:
    """Verify database file creation and schema_version initialization."""
    db_file = tmp_path / "test_openvideo.db"
    manager = DatabaseManager(db_path=db_file)

    assert db_file.exists()
    tasks = manager.list_tasks()
    assert tasks == []
    assert manager.total_history_count() == 0


def test_database_save_and_get_task(tmp_path: Path) -> None:
    """Verify storing and retrieving a DownloadTask with full format & filename details."""
    db_file = tmp_path / "test_openvideo.db"
    manager = DatabaseManager(db_path=db_file)

    fmt = FormatOption(
        format_id="137+140",
        ext="mp4",
        resolution="1080p",
        filesize=25000000,
    )
    task = DownloadTask(
        task_id="t123",
        url="https://example.com/video1",
        title="Test SQLite Video",
        target_dir="C:/Downloads",
        final_filepath="C:/Downloads/test_video.mp4",
        selected_format=fmt,
        total_bytes=25000000,
        status=TaskStatus.COMPLETED,
    )
    assert manager.save_task(task) is True

    retrieved = manager.get_task("t123")
    assert retrieved is not None
    assert retrieved.task_id == "t123"
    assert retrieved.title == "Test SQLite Video"
    assert retrieved.status == TaskStatus.COMPLETED
    assert retrieved.filename == "test_video.mp4"
    assert retrieved.selected_format is not None
    assert retrieved.selected_format.resolution == "1080p"
    assert retrieved.total_bytes == 25000000


def test_database_update_on_conflict(tmp_path: Path) -> None:
    """Verify updating existing task record on conflict does not create duplicates."""
    db_file = tmp_path / "test_openvideo.db"
    manager = DatabaseManager(db_path=db_file)

    task = DownloadTask(
        task_id="t456",
        url="https://example.com/video2",
        title="Original Title",
        target_dir="C:/Downloads",
        status=TaskStatus.DOWNLOADING,
    )
    manager.save_task(task)
    assert manager.total_history_count() == 1

    # Update state to completed
    task.set_status(TaskStatus.COMPLETED)
    task.final_filepath = "C:/Downloads/video.mp4"
    task.total_bytes = 10485760
    manager.save_task(task)

    # Should still only be 1 record in database
    assert manager.total_history_count() == 1
    updated = manager.get_task("t456")
    assert updated is not None
    assert updated.status == TaskStatus.COMPLETED
    assert updated.final_filepath == "C:/Downloads/video.mp4"
    assert updated.filename == "video.mp4"
    assert updated.total_bytes == 10485760


def test_database_delete_and_clear(tmp_path: Path) -> None:
    """Verify deleting single task and clearing all records."""
    db_file = tmp_path / "test_openvideo.db"
    manager = DatabaseManager(db_path=db_file)

    t1 = DownloadTask(task_id="t1", url="https://ex.com/1", title="V1", target_dir="C:/")
    t2 = DownloadTask(task_id="t2", url="https://ex.com/2", title="V2", target_dir="C:/")
    manager.save_task(t1)
    manager.save_task(t2)
    assert len(manager.list_tasks()) == 2

    assert manager.delete_task("t1") is True
    assert len(manager.list_tasks()) == 1
    assert manager.get_task("t1") is None

    assert manager.clear_all() is True
    assert len(manager.list_tasks()) == 0
    assert manager.total_history_count() == 0


def test_database_schema_v1_to_v2_migration(tmp_path: Path) -> None:
    """Verify seamless migration from schema v1 to v2 without data loss."""
    db_file = tmp_path / "v1_legacy.db"

    # 1. Manually create schema version 1 table
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE schema_version (version INTEGER PRIMARY KEY);")
    conn.execute("INSERT INTO schema_version (version) VALUES (1);")
    conn.execute(
        """
        CREATE TABLE downloads (
            task_id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            format_id TEXT,
            target_dir TEXT NOT NULL,
            final_filepath TEXT,
            total_bytes INTEGER,
            error_message TEXT,
            created_at REAL NOT NULL,
            completed_at REAL
        );
        """
    )
    conn.execute(
        """
        INSERT INTO downloads VALUES (
            'legacy_t1', 'https://example.com/v1', 'Legacy Video', 'completed',
            '137', 'C:/Downloads', 'C:/Downloads/legacy_video.mp4', 5000000,
            NULL, 1700000000.0, 1700000100.0
        );
        """
    )
    conn.commit()
    conn.close()

    # 2. Open via DatabaseManager (triggers automatic migration to v2)
    manager = DatabaseManager(db_path=db_file)
    assert CURRENT_SCHEMA_VERSION == 2

    # Check that schema version is now 2
    with manager._get_connection() as c:
        row = c.execute("SELECT version FROM schema_version;").fetchone()
        assert row["version"] == 2

    # Verify existing record was retained and filename was backfilled
    record = manager.get_task("legacy_t1")
    assert record is not None
    assert record.title == "Legacy Video"
    assert record.filename == "legacy_video.mp4"
    assert record.status == TaskStatus.COMPLETED


def test_database_mark_interrupted_tasks(tmp_path: Path) -> None:
    """Verify startup recovery updates abandoned active tasks to failed status."""
    db_file = tmp_path / "recovery.db"
    manager = DatabaseManager(db_path=db_file)

    # Simulate tasks in progress when app crashed/killed
    t_wait = DownloadTask(task_id="t_wait", url="https://ex.com/w", title="W", target_dir="C:/")
    t_wait.status = TaskStatus.WAITING

    t_dl = DownloadTask(task_id="t_dl", url="https://ex.com/d", title="D", target_dir="C:/")
    t_dl.status = TaskStatus.DOWNLOADING

    t_done = DownloadTask(task_id="t_done", url="https://ex.com/c", title="C", target_dir="C:/")
    t_done.status = TaskStatus.COMPLETED

    manager.save_task(t_wait)
    manager.save_task(t_dl)
    manager.save_task(t_done)

    # Run cleanup of abandoned tasks
    recovered_count = manager.mark_interrupted_tasks()
    assert recovered_count == 2

    # Verify t_wait and t_dl were marked FAILED with explanation
    task_w = manager.get_task("t_wait")
    assert task_w is not None
    assert task_w.status == TaskStatus.FAILED
    assert "Onderbroken" in str(task_w.error_message)

    task_d = manager.get_task("t_dl")
    assert task_d is not None
    assert task_d.status == TaskStatus.FAILED
    assert "Onderbroken" in str(task_d.error_message)

    # Verify completed task remained COMPLETED
    task_c = manager.get_task("t_done")
    assert task_c is not None
    assert task_c.status == TaskStatus.COMPLETED


def test_database_query_history_search_and_filters(tmp_path: Path) -> None:
    """Verify query_history supports search across title/filename/url and status filters."""
    db_file = tmp_path / "search.db"
    manager = DatabaseManager(db_path=db_file)

    now = time.time()
    t1 = DownloadTask(
        task_id="t1",
        url="https://youtube.com/watch?v=nature123",
        title="Planet Earth Jungle",
        target_dir="C:/",
        final_filepath="C:/jungle.mp4",
        status=TaskStatus.COMPLETED,
        total_bytes=1000000,
        created_at=now - 300,
        completed_at=now - 200,
    )
    t2 = DownloadTask(
        task_id="t2",
        url="https://vimeo.com/science456",
        title="Physics Experiment",
        target_dir="C:/",
        final_filepath="C:/physics.mp4",
        status=TaskStatus.FAILED,
        error_message="HTTP 404 Not Found",
        total_bytes=0,
        created_at=now - 200,
        completed_at=now - 100,
    )
    t3 = DownloadTask(
        task_id="t3",
        url="https://archive.org/audio789",
        title="Old Radio Broadcast",
        target_dir="C:/",
        final_filepath="C:/radio.mp3",
        status=TaskStatus.CANCELLED,
        total_bytes=500000,
        created_at=now - 100,
        completed_at=now,
    )

    manager.save_task(t1)
    manager.save_task(t2)
    manager.save_task(t3)

    assert manager.total_history_count() == 3

    # 1. Search by title
    res_title = manager.query_history(search_query="Jungle")
    assert len(res_title) == 1
    assert res_title[0].task_id == "t1"

    # 2. Search by filename
    res_fname = manager.query_history(search_query="physics.mp4")
    assert len(res_fname) == 1
    assert res_fname[0].task_id == "t2"

    # 3. Search by URL substring
    res_url = manager.query_history(search_query="archive.org")
    assert len(res_url) == 1
    assert res_url[0].task_id == "t3"

    # 4. Status filter
    completed_only = manager.query_history(status_filter=TaskStatus.COMPLETED)
    assert len(completed_only) == 1
    assert completed_only[0].task_id == "t1"

    failed_only = manager.query_history(status_filter=TaskStatus.FAILED)
    assert len(failed_only) == 1
    assert failed_only[0].task_id == "t2"

    cancelled_only = manager.query_history(status_filter=TaskStatus.CANCELLED)
    assert len(cancelled_only) == 1
    assert cancelled_only[0].task_id == "t3"

    # 5. Combined search + filter
    no_match = manager.query_history(search_query="Jungle", status_filter=TaskStatus.FAILED)
    assert len(no_match) == 0

    # 6. Sorting
    by_date_desc = manager.query_history(sort_by="date_desc")
    assert [t.task_id for t in by_date_desc] == ["t3", "t2", "t1"]

    by_date_asc = manager.query_history(sort_by="date_asc")
    assert [t.task_id for t in by_date_asc] == ["t1", "t2", "t3"]

    by_title = manager.query_history(sort_by="title_asc")
    assert [t.task_id for t in by_title] == ["t3", "t2", "t1"]


def test_database_error_handling_graceful(tmp_path: Path) -> None:
    """Verify methods handle connection or query failures without raising unhandled exceptions."""
    db_file = tmp_path / "error_test.db"
    manager = DatabaseManager(db_path=db_file)

    task = DownloadTask(task_id="bad_t", url="https://ex.com", title="Title", target_dir="C:/")

    # Mock _get_connection to simulate database operational failure
    with patch.object(manager, "_get_connection", side_effect=sqlite3.OperationalError("Disk I/O")):
        assert manager.save_task(task) is False
        assert manager.get_task("bad_t") is None
        assert manager.list_tasks() == []
        assert manager.query_history() == []
        assert manager.count_history() == 0
        assert manager.total_history_count() == 0
        assert manager.delete_task("bad_t") is False
        assert manager.clear_all() is False
        assert manager.mark_interrupted_tasks() == 0
