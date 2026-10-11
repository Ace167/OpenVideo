"""SQLite database persistence for download tasks and schema migrations."""

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from open_video_downloader.core.models import DownloadTask, FormatOption, TaskStatus
from open_video_downloader.core.paths import get_app_data_dir
from open_video_downloader.services.logger import get_logger

logger = get_logger("database.manager")

CURRENT_SCHEMA_VERSION = 2


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
        """Create a connection with WAL mode, foreign keys, and busy timeout."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=3000;")
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
                logger.info("Aanmaken van database met schema versie 1...")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS downloads (
                        task_id TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        title TEXT NOT NULL,
                        status TEXT NOT NULL,
                        format_id TEXT,
                        format_resolution TEXT,
                        filename TEXT,
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
                current_ver = 1

            if current_ver < 2:
                logger.info("Migreren van database van schema versie %d naar 2...", current_ver)
                table_info = conn.execute("PRAGMA table_info(downloads);").fetchall()
                columns = [c["name"] for c in table_info]
                if "filename" not in columns:
                    conn.execute("ALTER TABLE downloads ADD COLUMN filename TEXT;")
                if "format_resolution" not in columns:
                    conn.execute("ALTER TABLE downloads ADD COLUMN format_resolution TEXT;")

                # Backfill filename from final_filepath where available
                rows = conn.execute(
                    "SELECT task_id, final_filepath FROM downloads "
                    "WHERE final_filepath IS NOT NULL AND filename IS NULL;"
                ).fetchall()
                for r in rows:
                    if r["final_filepath"]:
                        name = Path(r["final_filepath"]).name
                        conn.execute(
                            "UPDATE downloads SET filename = ? WHERE task_id = ?;",
                            (name, r["task_id"]),
                        )

                conn.execute("DELETE FROM schema_version;")
                conn.execute("INSERT INTO schema_version (version) VALUES (2);")
                conn.commit()

        # Clean up any tasks left in active state from an unclean previous session
        self.mark_interrupted_tasks()

    def mark_interrupted_tasks(self) -> int:
        """Mark any tasks left in active state from an unexpected shutdown as interrupted."""
        try:
            with self._get_connection() as conn:
                interrupt_msg = (
                    "Onderbroken: download werd onderbroken doordat de applicatie werd afgesloten."
                )
                cur = conn.execute(
                    """
                    UPDATE downloads
                    SET status = ?,
                        error_message = ?,
                        completed_at = ?
                    WHERE status IN (?, ?, ?, ?);
                    """,
                    (
                        TaskStatus.FAILED.value,
                        interrupt_msg,
                        time.time(),
                        TaskStatus.WAITING.value,
                        TaskStatus.FETCHING_METADATA.value,
                        TaskStatus.DOWNLOADING.value,
                        TaskStatus.PROCESSING.value,
                    ),
                )
                affected = cur.rowcount
                conn.commit()
                if affected > 0:
                    logger.info(
                        "%d achtergebleven actieve taak/taken gemarkeerd als onderbroken.",
                        affected,
                    )
                return affected
        except Exception as err:
            logger.error("Fout bij opruimen van achtergebleven actieve taken: %s", err)
            return 0

    def save_task(self, task: DownloadTask) -> bool:
        """Insert or update a DownloadTask record in SQLite."""
        format_id = task.selected_format.format_id if task.selected_format else None
        format_res = task.selected_format.resolution if task.selected_format else None
        fname = Path(task.final_filepath).name if task.final_filepath else None
        filename = task.filename or fname

        total_bytes = task.total_bytes
        if (total_bytes is None or total_bytes <= 0) and task.final_filepath:
            try:
                p = Path(task.final_filepath)
                if p.is_file():
                    total_bytes = p.stat().st_size
            except OSError:
                pass

        completed_at = task.completed_at
        if completed_at is None and task.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ):
            completed_at = time.time()

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO downloads (
                        task_id, url, title, status, format_id, format_resolution, filename,
                        target_dir, final_filepath, total_bytes, error_message,
                        created_at, completed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(task_id) DO UPDATE SET
                        status = excluded.status,
                        final_filepath = excluded.final_filepath,
                        filename = excluded.filename,
                        format_id = excluded.format_id,
                        format_resolution = excluded.format_resolution,
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
                        format_res,
                        filename,
                        task.target_dir,
                        task.final_filepath,
                        total_bytes,
                        task.error_message,
                        task.created_at,
                        completed_at,
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

    def total_history_count(self) -> int:
        """Return total number of records stored in history database."""
        try:
            with self._get_connection() as conn:
                row = conn.execute("SELECT COUNT(*) AS cnt FROM downloads;").fetchone()
                return int(row["cnt"]) if row else 0
        except Exception as err:
            logger.error("Fout bij tellen van records in database: %s", err)
            return 0

    def count_history(
        self,
        search_query: str | None = None,
        status_filter: TaskStatus | str | None = None,
    ) -> int:
        """Count records matching search criteria and optional status filter."""
        clauses: list[str] = []
        params: list[Any] = []

        if status_filter is not None:
            val = (
                status_filter.value if isinstance(status_filter, TaskStatus) else str(status_filter)
            )
            clauses.append("status = ?")
            params.append(val)

        if search_query and search_query.strip():
            clean = f"%{search_query.strip()}%"
            clauses.append("(title LIKE ? OR filename LIKE ? OR url LIKE ?)")
            params.extend([clean, clean, clean])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT COUNT(*) AS cnt FROM downloads {where_sql};"

        try:
            with self._get_connection() as conn:
                row = conn.execute(sql, tuple(params)).fetchone()
                return int(row["cnt"]) if row else 0
        except Exception as err:
            logger.error("Fout bij tellen van geschiedenis met filters: %s", err)
            return 0

    def query_history(
        self,
        search_query: str | None = None,
        status_filter: TaskStatus | str | None = None,
        sort_by: str = "date_desc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[DownloadTask]:
        """Query historical download tasks with optional filtering and sorting."""
        clauses: list[str] = []
        params: list[Any] = []

        if status_filter is not None:
            val = (
                status_filter.value if isinstance(status_filter, TaskStatus) else str(status_filter)
            )
            clauses.append("status = ?")
            params.append(val)

        if search_query and search_query.strip():
            clean = f"%{search_query.strip()}%"
            clauses.append("(title LIKE ? OR filename LIKE ? OR url LIKE ?)")
            params.extend([clean, clean, clean])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        sort_map = {
            "date_desc": "COALESCE(completed_at, created_at) DESC",
            "date_asc": "COALESCE(completed_at, created_at) ASC",
            "title_asc": "title COLLATE NOCASE ASC",
            "size_desc": "COALESCE(total_bytes, 0) DESC",
        }
        order_sql = sort_map.get(sort_by, "COALESCE(completed_at, created_at) DESC")

        sql = f"""
            SELECT * FROM downloads
            {where_sql}
            ORDER BY {order_sql}
            LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])

        tasks: list[DownloadTask] = []
        try:
            with self._get_connection() as conn:
                rows = conn.execute(sql, tuple(params)).fetchall()
                for r in rows:
                    tasks.append(self._row_to_task(r))
        except Exception as err:
            logger.error("Fout bij uitvoeren van geschiedenisquery: %s", err)
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

        keys = row.keys()
        format_id = row["format_id"] if "format_id" in keys else None
        format_res = row["format_resolution"] if "format_resolution" in keys else None

        selected_fmt: FormatOption | None = None
        if format_id or format_res:
            ext = "mp4"
            if row["final_filepath"]:
                ext = Path(row["final_filepath"]).suffix.lstrip(".") or "mp4"
            selected_fmt = FormatOption(
                format_id=format_id or "best",
                ext=ext,
                resolution=format_res or "",
            )

        return DownloadTask(
            task_id=row["task_id"],
            url=row["url"],
            title=row["title"],
            status=status,
            target_dir=row["target_dir"],
            final_filepath=row["final_filepath"],
            selected_format=selected_fmt,
            total_bytes=row["total_bytes"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            completed_at=row["completed_at"],
        )
