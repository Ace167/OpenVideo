"""Download queue manager controlling task lifecycle, concurrency and worker threads."""

from PySide6.QtCore import QObject, Signal

from open_video_downloader.core.models import DownloadTask, TaskStatus
from open_video_downloader.engines.workers import DownloadWorker
from open_video_downloader.services.logger import get_logger

logger = get_logger("core.queue_manager")


class QueueManager(QObject):
    """Orchestrates scheduled download tasks and enforces concurrency limits."""

    task_added = Signal(object)  # DownloadTask
    task_updated = Signal(object)  # DownloadTask
    task_progress = Signal(str, float, str, str)  # (task_id, percent, speed_str, eta_str)
    task_status_changed = Signal(str, object)  # (task_id, TaskStatus)
    task_completed = Signal(str, str)  # (task_id, filepath)
    task_failed = Signal(str, str)  # (task_id, error_message)
    task_cancelled = Signal(str)  # (task_id)

    def __init__(self, max_concurrent: int = 3, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._max_concurrent = max(1, min(8, max_concurrent))
        self._tasks: dict[str, DownloadTask] = {}
        self._workers: dict[str, DownloadWorker] = {}

    @property
    def max_concurrent(self) -> int:
        """Maximum number of simultaneous active downloads."""
        return self._max_concurrent

    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        """Update maximum concurrency and trigger queue processing."""
        self._max_concurrent = max(1, min(8, value))
        self._process_queue()

    def get_task(self, task_id: str) -> DownloadTask | None:
        """Lookup task by identifier."""
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[DownloadTask]:
        """Return all managed tasks."""
        return list(self._tasks.values())

    def add_task(self, task: DownloadTask) -> bool:
        """Add new task to queue and attempt scheduling."""
        # Friendly duplicate check: if identical URL is currently downloading, reject duplicate
        for existing in self._tasks.values():
            if existing.url == task.url and existing.status in (
                TaskStatus.WAITING,
                TaskStatus.DOWNLOADING,
                TaskStatus.PROCESSING,
            ):
                logger.warning(
                    "Downloadtaak voor URL '%s' is reeds actief (taak %s).",
                    task.url,
                    existing.task_id,
                )
                return False

        self._tasks[task.task_id] = task
        self.task_added.emit(task)
        logger.info("Taak '%s' toegevoegd aan wachtrij (status: %s).", task.task_id, task.status)
        self._process_queue()
        return True

    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending or currently active download task."""
        task = self._tasks.get(task_id)
        if not task:
            return False

        # If worker is currently running, signal it
        worker = self._workers.get(task_id)
        if worker and worker.isRunning():
            logger.info("Annuleringssignaal verzonden naar actieve worker voor taak '%s'.", task_id)
            worker.cancel()
            return True

        # If still waiting in queue, transition directly
        if task.status == TaskStatus.WAITING:
            task.set_status(TaskStatus.CANCELLED)
            self.task_status_changed.emit(task_id, TaskStatus.CANCELLED)
            self.task_cancelled.emit(task_id)
            self._cleanup_worker(task_id)
            self._process_queue()
            return True

        return False

    def retry_task(self, task_id: str) -> bool:
        """Reset a failed or cancelled task to WAITING and re-queue."""
        task = self._tasks.get(task_id)
        if not task or task.status not in (TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False

        task.progress = 0.0
        task.downloaded_bytes = 0
        task.error_message = None
        task.set_status(TaskStatus.WAITING)
        self.task_status_changed.emit(task_id, TaskStatus.WAITING)
        logger.info("Taak '%s' gereset voor herhaling.", task_id)
        self._process_queue()
        return True

    def _process_queue(self) -> None:
        """Schedule pending tasks up to the concurrency limit."""
        active_count = sum(1 for w in self._workers.values() if w.isRunning())

        for task in self._tasks.values():
            if active_count >= self._max_concurrent:
                break

            if task.status == TaskStatus.WAITING and task.task_id not in self._workers:
                self._start_task(task)
                active_count += 1

    def _start_task(self, task: DownloadTask) -> None:
        """Create and start DownloadWorker for task."""
        task.set_status(TaskStatus.DOWNLOADING)
        worker = DownloadWorker(task)
        self._workers[task.task_id] = worker

        # Connect worker signals
        worker.progress_updated.connect(self._on_worker_progress)
        worker.status_changed.connect(self._on_worker_status)
        worker.task_completed.connect(self._on_worker_completed)
        worker.task_failed.connect(self._on_worker_failed)
        worker.task_cancelled.connect(self._on_worker_cancelled)

        worker.start()

    def _on_worker_progress(
        self, task_id: str, percent: float, speed_str: str, eta_str: str
    ) -> None:
        """Relay progress update from worker."""
        self.task_progress.emit(task_id, percent, speed_str, eta_str)

    def _on_worker_status(self, task_id: str, status: TaskStatus) -> None:
        """Relay status change from worker."""
        self.task_status_changed.emit(task_id, status)
        task = self._tasks.get(task_id)
        if task:
            self.task_updated.emit(task)

    def _on_worker_completed(self, task_id: str, filepath: str) -> None:
        """Handle task completion."""
        self.task_completed.emit(task_id, filepath)
        task = self._tasks.get(task_id)
        if task:
            self.task_updated.emit(task)
        self._cleanup_worker(task_id)
        self._process_queue()

    def _on_worker_failed(self, task_id: str, error_msg: str) -> None:
        """Handle task failure."""
        self.task_failed.emit(task_id, error_msg)
        task = self._tasks.get(task_id)
        if task:
            self.task_updated.emit(task)
        self._cleanup_worker(task_id)
        self._process_queue()

    def _on_worker_cancelled(self, task_id: str) -> None:
        """Handle task cancellation."""
        self.task_cancelled.emit(task_id)
        task = self._tasks.get(task_id)
        if task:
            self.task_updated.emit(task)
        self._cleanup_worker(task_id)
        self._process_queue()

    def _cleanup_worker(self, task_id: str) -> None:
        """Safely release worker instance reference."""
        if task_id in self._workers:
            del self._workers[task_id]

    def shutdown(self, timeout_ms: int = 2000) -> None:
        """Cancel and wait for all running workers on application shutdown."""
        logger.info("QueueManager afsluiten. Actieve workers worden beëindigd...")
        for worker in list(self._workers.values()):
            if worker.isRunning():
                worker.cancel()
                worker.wait(timeout_ms)
        self._workers.clear()
