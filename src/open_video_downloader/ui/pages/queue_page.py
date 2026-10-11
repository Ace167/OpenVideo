"""Queue view displaying live download task cards, progress and controls."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader.core.models import DownloadTask, TaskStatus, format_bytes
from open_video_downloader.core.queue_manager import QueueManager
from open_video_downloader.resources.icons import create_symbol_icon
from open_video_downloader.services.i18n import get_language, tr
from open_video_downloader.services.logger import get_logger

logger = get_logger("ui.queue_page")


class TaskCardWidget(QFrame):
    """Visual card representing a single scheduled or active DownloadTask."""

    cancel_requested = Signal(str)  # task_id
    retry_requested = Signal(str)  # task_id

    def __init__(self, task: DownloadTask, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.task_id = task.task_id
        self._task = task
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # 1. Title & Status Badge Row
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.title_label = QLabel(task.title, self)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.title_label.setWordWrap(True)
        top_row.addWidget(self.title_label, stretch=1)

        self.status_badge = QLabel(task.status.label, self)
        self._update_badge_style(task.status)
        top_row.addWidget(self.status_badge)

        layout.addLayout(top_row)

        # 2. Metadata details row
        self.info_label = QLabel(self._build_info_text(task), self)
        self.info_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.info_label)

        # 3. Progress Bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(int(task.progress))
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # 4. Progress Stats & Actions Row
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.stats_label = QLabel(self._build_stats_text(task), self)
        self.stats_label.setStyleSheet("color: #475569; font-size: 12px; font-weight: 500;")
        bottom_row.addWidget(self.stats_label, stretch=1)

        # Cancel Button
        self.cancel_btn = QPushButton(tr("queue.btn_cancel"), self)
        self.cancel_btn.setProperty("class", "btnSecondary")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(lambda: self.cancel_requested.emit(self.task_id))
        bottom_row.addWidget(self.cancel_btn)

        # Retry Button
        self.retry_btn = QPushButton(tr("queue.btn_retry"), self)
        self.retry_btn.setProperty("class", "btnPrimary")
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.clicked.connect(lambda: self.retry_requested.emit(self.task_id))
        bottom_row.addWidget(self.retry_btn)

        # Open File / Folder Button
        self.open_file_btn = QPushButton(tr("history.btn_open_file"), self)
        self.open_file_btn.setProperty("class", "btnSecondary")
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self._on_open_file)
        bottom_row.addWidget(self.open_file_btn)

        layout.addLayout(bottom_row)

        self.update_task_state(task)

    def _build_info_text(self, task: DownloadTask) -> str:
        """Construct format and target location label."""
        default_fmt = "Standard" if get_language() == "en" else "Standaard"
        fmt_desc = task.selected_format.display_label if task.selected_format else default_fmt
        return tr("queue.item_format_info", format=fmt_desc, target=task.target_dir)

    def _build_stats_text(self, task: DownloadTask) -> str:
        """Construct progress stats or error string based on task status."""
        if task.status == TaskStatus.COMPLETED:
            size_str = format_bytes(task.total_bytes or task.downloaded_bytes)
            return tr("queue.stats_completed", size=size_str)
        if task.status == TaskStatus.FAILED:
            unknown_err = "Unknown error" if get_language() == "en" else "Onbekende fout"
            return tr("queue.stats_failed", err=task.error_message or unknown_err)
        if task.status == TaskStatus.CANCELLED:
            return tr("queue.stats_cancelled")
        if task.status == TaskStatus.PROCESSING:
            return tr("queue.stats_processing")
        if task.status == TaskStatus.DOWNLOADING:
            downloaded = format_bytes(task.downloaded_bytes)
            unknown_size = "unknown" if get_language() == "en" else "onbekend"
            total = format_bytes(task.total_bytes) if task.total_bytes else unknown_size
            speed = f"{format_bytes(task.speed_bytes_sec)}/s" if task.speed_bytes_sec else "-- KB/s"
            return tr(
                "queue.stats_downloading",
                progress=task.progress,
                total=total,
                downloaded=downloaded,
                speed=speed,
            )
        return tr("queue.stats_waiting")

    def _update_badge_style(self, status: TaskStatus) -> None:
        """Style status badge according to state."""
        self.status_badge.setText(status.label)
        badge_styles = {
            TaskStatus.WAITING: "background-color: #f1f5f9; color: #475569;",
            TaskStatus.DOWNLOADING: "background-color: #e0f2fe; color: #0369a1;",
            TaskStatus.PROCESSING: "background-color: #fef3c7; color: #92400e;",
            TaskStatus.COMPLETED: "background-color: #dcfce7; color: #15803d;",
            TaskStatus.FAILED: "background-color: #fee2e2; color: #b91c1c;",
            TaskStatus.CANCELLED: "background-color: #f1f5f9; color: #64748b;",
        }
        base_css = "padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;"
        self.status_badge.setStyleSheet(f"{base_css} {badge_styles.get(status, '')}")

    def update_task_state(self, task: DownloadTask) -> None:
        """Refresh visual progress and action button visibility."""
        self._task = task
        self.progress_bar.setValue(int(task.progress))
        self.stats_label.setText(self._build_stats_text(task))
        self.info_label.setText(self._build_info_text(task))
        self._update_badge_style(task.status)

        # Button visibility rules
        can_cancel = task.status in (
            TaskStatus.WAITING,
            TaskStatus.DOWNLOADING,
            TaskStatus.PROCESSING,
        )
        can_retry = task.status in (TaskStatus.FAILED, TaskStatus.CANCELLED)
        can_open = task.status == TaskStatus.COMPLETED and bool(task.final_filepath)

        self.cancel_btn.setVisible(can_cancel)
        self.retry_btn.setVisible(can_retry)
        self.open_file_btn.setVisible(can_open)

    def retranslate_ui(self) -> None:
        """Update texts in card to match active language."""
        self.cancel_btn.setText(tr("queue.btn_cancel"))
        self.retry_btn.setText(tr("queue.btn_retry"))
        self.open_file_btn.setText(tr("history.btn_open_file"))
        self.update_task_state(self._task)

    def _on_open_file(self) -> None:
        """Open completed file in default media player or Explorer."""
        if self._task.final_filepath and Path(self._task.final_filepath).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._task.final_filepath))
        elif Path(self._task.target_dir).exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._task.target_dir))


class QueuePage(QWidget):
    """View managing active downloads and task progression."""

    def __init__(self, queue_manager: QueueManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._queue_mgr = queue_manager
        self._card_widgets: dict[str, TaskCardWidget] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header Row
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        self.title_label = QLabel(self)
        self.title_label.setProperty("class", "pageTitle")
        title_container.addWidget(self.title_label)

        self.subtitle_label = QLabel(self)
        self.subtitle_label.setProperty("class", "pageSubtitle")
        title_container.addWidget(self.subtitle_label)
        header_layout.addLayout(title_container)

        header_layout.addStretch()

        self.cancel_all_btn = QPushButton(self)
        self.cancel_all_btn.setProperty("class", "btnSecondary")
        self.cancel_all_btn.clicked.connect(self._on_cancel_all)
        header_layout.addWidget(self.cancel_all_btn)

        layout.addLayout(header_layout)

        # 2. Authentic Empty State Card
        self.empty_card = QFrame(self)
        self.empty_card.setProperty("class", "card")
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(32, 48, 32, 48)
        empty_layout.setSpacing(12)

        icon_label = QLabel(self)
        icon_label.setPixmap(create_symbol_icon("queue", 48, "#94a3b8").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)

        self.empty_title = QLabel(self)
        self.empty_title.setProperty("class", "emptyStateTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_title)

        self.empty_desc = QLabel(self)
        self.empty_desc.setProperty("class", "emptyStateText")
        self.empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(self.empty_desc)

        layout.addWidget(self.empty_card, stretch=1)

        # 3. Scroll Area for Active Task Cards
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setVisible(False)

        self.cards_container = QWidget(self.scroll_area)
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        self.scroll_area.setWidget(self.cards_container)
        layout.addWidget(self.scroll_area, stretch=1)

        # Apply initial translations
        self.retranslate_ui()

        # Connect QueueManager signals
        self._queue_mgr.task_added.connect(self._on_task_added)
        self._queue_mgr.task_updated.connect(self._on_task_updated)
        self._queue_mgr.task_progress.connect(self._on_task_progress)

    def retranslate_ui(self) -> None:
        """Update view and child card texts to active language."""
        self.title_label.setText(tr("queue.header_title"))
        self.subtitle_label.setText(tr("queue.header_sub"))
        self.cancel_all_btn.setText(tr("queue.btn_cancel_all"))
        self.empty_title.setText(tr("queue.empty_title"))
        self.empty_desc.setText(tr("queue.empty_sub"))

        for card in self._card_widgets.values():
            card.retranslate_ui()

    def get_task(self, task_id: str) -> DownloadTask | None:
        """Lookup task in QueueManager."""
        return self._queue_mgr.get_task(task_id)

    def _on_task_added(self, task: DownloadTask) -> None:
        """Add new card widget for task."""
        card = TaskCardWidget(task, self)
        card.cancel_requested.connect(self._queue_mgr.cancel_task)
        card.retry_requested.connect(self._queue_mgr.retry_task)

        self._card_widgets[task.task_id] = card
        # Insert before stretch
        self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

        self._update_visibility()

    def _on_task_updated(self, task: DownloadTask) -> None:
        """Update card UI when task state changes."""
        card = self._card_widgets.get(task.task_id)
        if card:
            card.update_task_state(task)
        self._update_visibility()

    def _on_task_progress(self, task_id: str, percent: float, speed_str: str, eta_str: str) -> None:
        """Update card progress bar and stats dynamically."""
        card = self._card_widgets.get(task_id)
        task = self._queue_mgr.get_task(task_id)
        if card and task:
            card.update_task_state(task)

    def _on_cancel_all(self) -> None:
        """Cancel all managed tasks."""
        for task in self._queue_mgr.get_all_tasks():
            self._queue_mgr.cancel_task(task.task_id)

    def _update_visibility(self) -> None:
        """Toggle between empty card and scroll area."""
        has_cards = len(self._card_widgets) > 0
        self.empty_card.setVisible(not has_cards)
        self.scroll_area.setVisible(has_cards)
        self.cancel_all_btn.setEnabled(has_cards)
