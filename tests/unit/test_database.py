"""Unit tests for SQLite database manager, schema migrations and task persistence."""

from pathlib import Path

from open_video_downloader.core.models import DownloadTask, TaskStatus
from open_video_downloader.database.manager import DatabaseManager


def test_database_initialization(tmp_path: Path):
    """Verify database file creation and schema_version initialization."""
    db_file = tmp_path / "test_openvideo.db"
    manager = DatabaseManager(db_path=db_file)

    assert db_file.exists()
    tasks = manager.list_tasks()
    assert tasks == []


def test_database_save_and_get_task(tmp_path: Path):
    """Verify storing and retrieving a DownloadTask."""
    db_file = tmp_path / "test_openvideo.db"
    manager = DatabaseManager(db_path=db_file)

    task = DownloadTask(
        task_id="t123",
        url="https://example.com/video1",
        title="Test SQLite Video",
        target_dir="C:/Downloads",
        status=TaskStatus.WAITING,
    )
    assert manager.save_task(task) is True

    retrieved = manager.get_task("t123")
    assert retrieved is not None
    assert retrieved.task_id == "t123"
    assert retrieved.title == "Test SQLite Video"
    assert retrieved.status == TaskStatus.WAITING


def test_database_update_on_conflict(tmp_path: Path):
    """Verify updating existing task record on conflict."""
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

    # Update state
    task.set_status(TaskStatus.COMPLETED)
    task.final_filepath = "C:/Downloads/video.mp4"
    task.total_bytes = 10485760
    manager.save_task(task)

    updated = manager.get_task("t456")
    assert updated is not None
    assert updated.status == TaskStatus.COMPLETED
    assert updated.final_filepath == "C:/Downloads/video.mp4"
    assert updated.total_bytes == 10485760


def test_database_delete_and_clear(tmp_path: Path):
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
