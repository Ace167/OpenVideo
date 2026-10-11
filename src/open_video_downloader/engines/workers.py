"""Asynchronous background worker threads for metadata probing and downloads."""

import threading
import time
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread, Signal

from open_video_downloader.core.models import (
    DownloadTask,
    MediaMetadata,
    TaskStatus,
    format_bytes,
    format_duration,
)
from open_video_downloader.engines.ytdl_adapter import (
    DownloadCancelledError,
    EngineError,
    InvalidUrlError,
    MediaUnavailableError,
    NetworkTimeoutError,
    execute_download,
    extract_metadata,
)
from open_video_downloader.services.logger import get_logger

logger = get_logger("engines.workers")


class MetadataWorker(QThread):
    """Background worker fetching media metadata outside the GUI thread."""

    metadata_ready = Signal(object)  # MediaMetadata
    metadata_error = Signal(str, str)  # (user_message, tech_details)

    def __init__(self, url: str) -> None:
        super().__init__()
        self._url = url
        self._cancel_event = threading.Event()

    def cancel(self) -> None:
        """Signal worker to cancel extraction."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check whether cancel was requested."""
        return self._cancel_event.is_set()

    def run(self) -> None:
        """Execute extraction in thread."""
        logger.info("MetadataWorker gestart voor '%s'.", self._url)
        try:
            metadata: MediaMetadata = extract_metadata(self._url, cancel_check=self.is_cancelled)
            if self.is_cancelled():
                logger.info("MetadataWorker geannuleerd alvorens gereed.")
                return
            self.metadata_ready.emit(metadata)
        except InvalidUrlError as err:
            self.metadata_error.emit(
                "De ingevoerde URL is ongeldig of wordt niet ondersteund door de engine.",
                str(err),
            )
        except MediaUnavailableError as err:
            self.metadata_error.emit(
                "De opgevraagde video is niet beschikbaar (privé, verwijderd of afgeschermd).",
                str(err),
            )
        except NetworkTimeoutError as err:
            self.metadata_error.emit(
                "De netwerkverbinding is verlopen of kon de host niet bereiken.",
                str(err),
            )
        except DownloadCancelledError as err:
            logger.info("MetadataWorker beëindigd na annulering: %s", err)
        except EngineError as err:
            self.metadata_error.emit(
                f"Fout tijdens het ophalen van informatie: {err}",
                str(err),
            )
        except Exception as err:
            logger.error("Onverwachte fout in MetadataWorker: %s", err)
            self.metadata_error.emit("Onverwachte interne fout bij metadata-extractie.", str(err))


class DownloadWorker(QThread):
    """Background worker executing the media download process."""

    progress_updated = Signal(str, float, str, str)  # (task_id, percent, speed_str, eta_str)
    status_changed = Signal(str, object)  # (task_id, TaskStatus)
    task_completed = Signal(str, str)  # (task_id, filepath)
    task_failed = Signal(str, str)  # (task_id, error_message)
    task_cancelled = Signal(str)  # (task_id)

    def __init__(self, task: DownloadTask) -> None:
        super().__init__()
        self.task = task
        self._cancel_event = threading.Event()
        self._last_progress_time = 0.0

    def cancel(self) -> None:
        """Signal worker to cancel download."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check whether cancel was requested."""
        return self._cancel_event.is_set()

    def _progress_hook(self, d: dict[str, Any]) -> None:
        """Process yt-dlp progress hook dictionary and emit rate-limited signals."""
        now = time.time()
        status_raw = d.get("status")

        if status_raw == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            speed = d.get("speed")
            eta = d.get("eta")

            percent = 0.0
            if total and total > 0:
                percent = min(100.0, (downloaded / total) * 100.0)

            speed_str = f"{format_bytes(speed)}/s" if speed else "-- KB/s"
            eta_str = f"Resterend: {format_duration(eta)}" if eta else "Resterend: --:--"

            self.task.downloaded_bytes = downloaded
            self.task.total_bytes = total
            self.task.speed_bytes_sec = speed
            self.task.eta_seconds = eta
            self.task.progress = percent

            # Limit progress updates to ~10 per second to keep Qt event loop responsive
            if now - self._last_progress_time > 0.1:
                self._last_progress_time = now
                self.progress_updated.emit(self.task.task_id, percent, speed_str, eta_str)

        elif status_raw == "postprocessing":
            if self.task.set_status(TaskStatus.PROCESSING):
                self.status_changed.emit(self.task.task_id, TaskStatus.PROCESSING)
                self.progress_updated.emit(
                    self.task.task_id, 100.0, "Samenvoegen...", "Afronden..."
                )

    def run(self) -> None:
        """Execute download in background thread."""
        logger.info("DownloadWorker gestart voor taak '%s' (%s).", self.task.task_id, self.task.url)

        if not self.task.set_status(TaskStatus.DOWNLOADING):
            self.task_failed.emit(self.task.task_id, "Ongeldige statusovergang naar DOWNLOADING.")
            return
        self.status_changed.emit(self.task.task_id, TaskStatus.DOWNLOADING)

        format_id = (
            self.task.selected_format.format_id
            if self.task.selected_format
            else "bestvideo+bestaudio/best"
        )
        target_dir = Path(self.task.target_dir)

        try:
            final_path = execute_download(
                url=self.task.url,
                target_dir=target_dir,
                format_id=format_id,
                progress_callback=self._progress_hook,
                cancel_check=self.is_cancelled,
            )

            if final_path.exists() and final_path.is_file():
                try:
                    size = final_path.stat().st_size
                    if size > 0:
                        self.task.total_bytes = size
                        self.task.downloaded_bytes = size
                except OSError:
                    pass

            self.task.final_filepath = str(final_path)
            self.task.progress = 100.0
            self.task.set_status(TaskStatus.COMPLETED)
            self.status_changed.emit(self.task.task_id, TaskStatus.COMPLETED)
            self.task_completed.emit(self.task.task_id, str(final_path))
            logger.info("Taak '%s' succesvol afgerond: '%s'.", self.task.task_id, final_path)

        except DownloadCancelledError:
            self.task.set_status(TaskStatus.CANCELLED)
            self.status_changed.emit(self.task.task_id, TaskStatus.CANCELLED)
            self.task_cancelled.emit(self.task.task_id)
            logger.info("Taak '%s' geannuleerd.", self.task.task_id)

        except Exception as err:
            err_msg = str(err)
            self.task.error_message = err_msg
            self.task.set_status(TaskStatus.FAILED)
            self.status_changed.emit(self.task.task_id, TaskStatus.FAILED)
            self.task_failed.emit(self.task.task_id, err_msg)
            logger.warning("Taak '%s' mislukt: %s", self.task.task_id, err_msg)
