"""Unit tests for QueueManager concurrency, task scheduling and lifecycle control."""

from unittest.mock import MagicMock, patch

from open_video_downloader.core.models import DownloadTask, TaskStatus
from open_video_downloader.core.queue_manager import QueueManager


def test_queue_manager_add_and_duplicate():
    """Verify adding tasks and rejecting duplicate active URLs."""
    qm = QueueManager(max_concurrent=2)

    task1 = DownloadTask(
        task_id="t1", url="https://example.com/video1", title="V1", target_dir="C:/"
    )
    task2 = DownloadTask(
        task_id="t2", url="https://example.com/video1", title="V1 Duplicate", target_dir="C:/"
    )

    emitted: list[DownloadTask] = []
    qm.task_added.connect(lambda t: emitted.append(t))

    # Disable auto-starting workers for unit testing queue state
    with patch.object(qm, "_start_task"):
        assert qm.add_task(task1) is True
        assert len(emitted) == 1

        # Adding identical URL while active should be rejected
        assert qm.add_task(task2) is False
        assert len(emitted) == 1


def test_queue_manager_cancel_waiting_task():
    """Verify cancelling a WAITING task transitions status to CANCELLED."""
    qm = QueueManager(max_concurrent=1)
    task = DownloadTask(task_id="t1", url="https://example.com/video", title="V", target_dir="C:/")

    with patch.object(qm, "_start_task"):
        qm.add_task(task)
        assert task.status == TaskStatus.WAITING

        cancelled_ids: list[str] = []
        qm.task_cancelled.connect(lambda tid: cancelled_ids.append(tid))

        assert qm.cancel_task("t1") is True
        assert task.status == TaskStatus.CANCELLED
        assert cancelled_ids == ["t1"]


def test_queue_manager_retry_task():
    """Verify retrying a failed task resets status to WAITING and re-triggers scheduling."""
    qm = QueueManager(max_concurrent=1)
    task = DownloadTask(task_id="t1", url="https://example.com/video", title="V", target_dir="C:/")
    task.set_status(TaskStatus.DOWNLOADING)
    task.set_status(TaskStatus.FAILED)
    task.error_message = "Network error"

    qm._tasks["t1"] = task

    with patch.object(qm, "_process_queue") as mock_process:
        assert qm.retry_task("t1") is True
        assert task.status == TaskStatus.WAITING
        assert task.error_message is None
        mock_process.assert_called_once()


def test_queue_manager_concurrency_scheduling():
    """Verify _process_queue respects max_concurrent limit."""
    qm = QueueManager(max_concurrent=2)
    t1 = DownloadTask(task_id="t1", url="https://example.com/1", title="V1", target_dir="C:/")
    t2 = DownloadTask(task_id="t2", url="https://example.com/2", title="V2", target_dir="C:/")
    t3 = DownloadTask(task_id="t3", url="https://example.com/3", title="V3", target_dir="C:/")

    started_tasks: list[str] = []

    def fake_start(task: DownloadTask):
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = True
        qm._workers[task.task_id] = mock_worker
        started_tasks.append(task.task_id)

    with patch.object(qm, "_start_task", side_effect=fake_start):
        qm.add_task(t1)
        qm.add_task(t2)
        qm.add_task(t3)

        # Only first 2 tasks should be started due to max_concurrent=2
        assert started_tasks == ["t1", "t2"]
        assert qm.get_task("t3").status == TaskStatus.WAITING
