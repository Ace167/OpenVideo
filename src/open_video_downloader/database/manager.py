"""SQLite database persistence for download tasks and schema migrations."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from open_video_downloader.core.models import DownloadTask, TaskStatus
from open_video_downloader.core.paths import get_app_data_dir
from open_video_downloader.services.logger import get_logger

logger = get_logger("database.manager")

CURRENT_SCHEMA_VERSION = 1


class DatabaseManager:
    """Manages SQLite storage, table migrations and task record persistence."""

    def __init__(self, db_path: Path | None = None) -> None:
        if db_path is not None:
            self._db_path = db_path
        else:
            self._db_path = get_app_data_dir() / "openvideo.db"

        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @property
    def db_path(self) -> Path:
        """Path to SQLite database file."""
        return self._db_path

    @contextmanager
    def _get_connection(self) -> Iterator[sqlite3.Connection]:
        """Create a connection with WAL mode and foreign key constraints."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_database(self) -> None:
        """Run initial table creation and schema migrations."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                );
                """
            )
            row = conn.execute("SELECT version FROM schema_version LIMIT 1;").fetchone()
            current_ver = row["version"] if row else 0

            if current_ver < 1:
                logger.info("Migreren van database naar schema versie 1...")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS downloads (
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
                conn.execute("DELETE FROM schema_version;")
                conn.execute("INSERT INTO schema_version (version) VALUES (1);")
                conn.commit()

    def save_task(self, task: DownloadTask) -> bool:
        """Insert or update a DownloadTask record."""
        format_id = task.selected_format.format_id if task.selected_format else None
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO downloads (
                        task_id, url, title, status, format_id, target_dir,
                        final_filepath, total_bytes, error_message, created_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        status = excluded.status,
                        final_filepath = excluded.final_filepath,
                        total_bytes = excluded.total_bytes,
                        error_message = excluded.error_message,
                        completed_at = excluded.completed_at;
                    """,
                    (
                        task.task_id,
                        task.url,
                        task.title,
                        task.status.value,
                        format_id,
                        task.target_dir,
                        task.final_filepath,
                        task.total_bytes,
                        task.error_message,
                        task.created_at,
                        task.completed_at,
                    ),
                )
                conn.commit()
            return True
        except Exception as err:
            logger.error("Fout bij opslaan van taak '%s' in database: %s", task.task_id, err)
            return False

    def get_task(self, task_id: str) -> DownloadTask | None:
        """Retrieve task by id from database."""
        try:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM downloads WHERE task_id = ?;", (task_id,)
                ).fetchone()
                if row:
                    return self._row_to_task(row)
        except Exception as err:
            logger.error("Fout bij ophalen van taak '%s': %s", task_id, err)
        return None

    def list_tasks(self) -> list[DownloadTask]:
        """List all tasks sorted by creation date descending."""
        tasks: list[DownloadTask] = []
        try:
            with self._get_connection() as conn:
                rows = conn.execute("SELECT * FROM downloads ORDER BY created_at DESC;").fetchall()
                for r in rows:
                    tasks.append(self._row_to_task(r))
        except Exception as err:
            logger.error("Fout bij laden van takenlijst uit database: %s", err)
        return tasks

    def delete_task(self, task_id: str) -> bool:
        """Delete task record by id."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM downloads WHERE task_id = ?;", (task_id,))
                conn.commit()
            return True
        except Exception as err:
            logger.error("Fout bij verwijderen van taak '%s': %s", task_id, err)
            return False

    def clear_all(self) -> bool:
        """Remove all task records."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM downloads;")
                conn.commit()
            return True
        except Exception as err:
            logger.error("Fout bij wissen van downloadrecords: %s", err)
            return False

    def _row_to_task(self, row: sqlite3.Row) -> DownloadTask:
        """Map SQLite row to domain DownloadTask."""
        status_val = row["status"]
        try:
            status = TaskStatus(status_val)
        except ValueError:
            status = TaskStatus.FAILED

        return DownloadTask(
            task_id=row["task_id"],
            url=row["url"],
            title=row["title"],
            status=status,
            target_dir=row["target_dir"],
            final_filepath=row["final_filepath"],
            total_bytes=row["total_bytes"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )
