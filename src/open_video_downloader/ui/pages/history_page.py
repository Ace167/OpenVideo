"""Download history view with search, status filtering, date sorting and SQLite persistence."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader.core.models import DownloadTask, TaskStatus, format_bytes
from open_video_downloader.database.manager import DatabaseManager
from open_video_downloader.resources.icons import create_symbol_icon
from open_video_downloader.services.i18n import get_language, tr
from open_video_downloader.services.logger import get_logger

logger = get_logger("ui.history_page")


class HistoryItemCard(QFrame):
    """Card widget presenting a single historical download record."""

    delete_requested = Signal(str)  # task_id

    def __init__(self, task: DownloadTask, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.task_id = task.task_id
        self._task = task
        self.setProperty("class", "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # 1. Header: Title, Status Badge, Timestamp
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.title_label = QLabel(task.title, self)
        self.title_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        self.title_label.setWordWrap(True)
        top_row.addWidget(self.title_label, stretch=1)

        self.status_badge = QLabel(task.status.label, self)
        self._update_badge_style(task.status)
        top_row.addWidget(self.status_badge)

        timestamp_val = task.completed_at or task.created_at
        date_str = datetime.fromtimestamp(timestamp_val).strftime("%d-%m-%Y %H:%M")
        self.date_label = QLabel(date_str, self)
        self.date_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 500;")
        top_row.addWidget(self.date_label)

        layout.addLayout(top_row)

        # 2. File and Format Details
        details_row = QHBoxLayout()
        details_row.setSpacing(14)

        self.meta_label = QLabel(self._build_meta_text(task), self)
        self.meta_label.setStyleSheet("color: #475569; font-size: 12px;")
        self.meta_label.setWordWrap(True)
        details_row.addWidget(self.meta_label, stretch=1)
        layout.addLayout(details_row)

        # 3. URL Info
        self.url_label = QLabel(self._build_url_text(task), self)
        self.url_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.url_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.url_label)

        # 4. Error Message Banner if Failed
        if task.status == TaskStatus.FAILED and task.error_message:
            self.error_label = QLabel(f"⚠️ {task.error_message}", self)
            self.error_label.setStyleSheet(
                "color: #b91c1c; background-color: #fef2f2; border: 1px solid #fee2e2; "
                "border-radius: 4px; padding: 4px 8px; font-size: 11px;"
            )
            self.error_label.setWordWrap(True)
            layout.addWidget(self.error_label)

        # 5. Actions Row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)

        # Open File Button
        self.open_file_btn = QPushButton(tr("history.btn_open_file"), self)
        self.open_file_btn.setProperty("class", "btnSecondary")
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self._on_open_file)
        has_file = bool(task.status == TaskStatus.COMPLETED and task.final_filepath)
        self.open_file_btn.setVisible(has_file)
        actions_row.addWidget(self.open_file_btn)

        # Open Folder Button
        self.open_folder_btn = QPushButton(tr("history.btn_open_folder"), self)
        self.open_folder_btn.setProperty("class", "btnSecondary")
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self._on_open_folder)
        actions_row.addWidget(self.open_folder_btn)

        actions_row.addStretch()

        # Delete Entry Button
        self.delete_btn = QPushButton(tr("history.btn_delete_item"), self)
        self.delete_btn.setProperty("class", "btnSecondary")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_id))
        actions_row.addWidget(self.delete_btn)

        layout.addLayout(actions_row)

    def _build_meta_text(self, task: DownloadTask) -> str:
        """Construct localized metadata summary string."""
        default_fmt = "Standard" if get_language() == "en" else "Standaard"
        fmt_desc = task.selected_format.display_label if task.selected_format else default_fmt
        unknown_size = "unknown" if get_language() == "en" else "onbekend"
        size_str = format_bytes(task.total_bytes) if task.total_bytes else unknown_size
        fname = task.filename or (Path(task.final_filepath).name if task.final_filepath else "—")
        return tr("history.item_meta", format=fmt_desc, size=size_str, file=fname)

    def _build_url_text(self, task: DownloadTask) -> str:
        """Construct localized URL source label."""
        return tr("history.item_source", url=task.url)

    def _update_badge_style(self, status: TaskStatus) -> None:
        """Apply status badge pill styling."""
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

    def retranslate_ui(self) -> None:
        """Update card buttons and labels to match active language."""
        self.open_file_btn.setText(tr("history.btn_open_file"))
        self.open_folder_btn.setText(tr("history.btn_open_folder"))
        self.delete_btn.setText(tr("history.btn_delete_item"))
        self.status_badge.setText(self._task.status.label)
        self.meta_label.setText(self._build_meta_text(self._task))
        self.url_label.setText(self._build_url_text(self._task))

    def _on_open_file(self) -> None:
        """Open completed media file in default system player."""
        if not self._task.final_filepath:
            return

        file_path = Path(self._task.final_filepath)
        if file_path.is_file():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path)))
        else:
            QMessageBox.information(
                self,
                tr("history.file_not_found_title"),
                tr("history.file_not_found_msg", path=str(file_path)),
            )

    def _on_open_folder(self) -> None:
        """Open destination folder in File Explorer."""
        folder_path = (
            Path(self._task.final_filepath).parent
            if self._task.final_filepath
            else Path(self._task.target_dir)
        )
        if folder_path.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder_path)))
        else:
            QMessageBox.information(
                self,
                tr("history.folder_not_found_title"),
                tr("history.folder_not_found_msg", path=str(folder_path)),
            )


class HistoryPage(QWidget):
    """View presenting download history with search, filtering, sorting and SQLite storage."""

    def __init__(
        self, database_manager: DatabaseManager | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._db_mgr = database_manager or DatabaseManager()
        self._cards: list[HistoryItemCard] = []

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

        self.clear_btn = QPushButton(self)
        self.clear_btn.setProperty("class", "btnSecondary")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._on_clear_all_clicked)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # 2. Filter & Search Controls Bar
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        # Search Input
        self.search_input = QLineEdit(self)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.setEnabled(False)
        self.search_input.textChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self.search_input, stretch=2)

        # Status Filter Combobox
        self.status_filter_combo = QComboBox(self)
        self.status_filter_combo.addItem(tr("history.filter_all"), userData=None)
        self.status_filter_combo.addItem(
            tr("history.filter_completed"), userData=TaskStatus.COMPLETED
        )
        self.status_filter_combo.addItem(tr("history.filter_failed"), userData=TaskStatus.FAILED)
        self.status_filter_combo.addItem(
            tr("history.filter_cancelled"), userData=TaskStatus.CANCELLED
        )
        self.status_filter_combo.setEnabled(False)
        self.status_filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self.status_filter_combo)

        # Sorting Combobox
        self.sort_combo = QComboBox(self)
        self.sort_combo.addItem(tr("history.sort_newest"), userData="date_desc")
        self.sort_combo.addItem(tr("history.sort_oldest"), userData="date_asc")
        self.sort_combo.addItem(tr("history.sort_title"), userData="title_asc")
        self.sort_combo.addItem(tr("history.sort_size"), userData="size_desc")
        self.sort_combo.setEnabled(False)
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        controls_layout.addWidget(self.sort_combo)

        layout.addLayout(controls_layout)

        # 3. Authentic Empty State Card (0 total items in DB)
        self.empty_card = QFrame(self)
        self.empty_card.setProperty("class", "card")
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(32, 48, 32, 48)
        empty_layout.setSpacing(12)

        icon_label = QLabel(self)
        icon_label.setPixmap(create_symbol_icon("history", 48, "#94a3b8").pixmap(48, 48))
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

        # 4. No Results Card (DB has items, but search/filter yielded 0)
        self.no_results_card = QFrame(self)
        self.no_results_card.setProperty("class", "card")
        no_res_layout = QVBoxLayout(self.no_results_card)
        no_res_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_layout.setContentsMargins(32, 48, 32, 48)
        no_res_layout.setSpacing(12)

        no_res_icon = QLabel(self)
        no_res_icon.setPixmap(create_symbol_icon("history", 48, "#94a3b8").pixmap(48, 48))
        no_res_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_layout.addWidget(no_res_icon)

        self.no_res_title = QLabel(self)
        self.no_res_title.setProperty("class", "emptyStateTitle")
        self.no_res_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_layout.addWidget(self.no_res_title)

        self.no_res_desc = QLabel(self)
        self.no_res_desc.setProperty("class", "emptyStateText")
        self.no_res_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        no_res_layout.addWidget(self.no_res_desc)

        self.reset_filters_btn = QPushButton(self)
        self.reset_filters_btn.setProperty("class", "btnSecondary")
        self.reset_filters_btn.setFixedWidth(140)
        self.reset_filters_btn.clicked.connect(self._on_reset_filters_clicked)
        no_res_layout.addWidget(self.reset_filters_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.no_results_card.setVisible(False)
        layout.addWidget(self.no_results_card, stretch=1)

        # 5. Scroll Area for History Cards
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

        # Initial load
        self.refresh_history()

    def retranslate_ui(self) -> None:
        """Update texts and filter labels to active language."""
        self.title_label.setText(tr("history.header_title"))
        self.subtitle_label.setText(tr("history.header_sub"))
        self.clear_btn.setText(tr("history.btn_clear"))
        self.search_input.setPlaceholderText(tr("history.search_placeholder"))

        # Update status filter combobox items preserving userData
        status_labels = [
            tr("history.filter_all"),
            tr("history.filter_completed"),
            tr("history.filter_failed"),
            tr("history.filter_cancelled"),
        ]
        for i, text in enumerate(status_labels):
            if i < self.status_filter_combo.count():
                self.status_filter_combo.setItemText(i, text)

        # Update sort combobox items preserving userData
        sort_labels = [
            tr("history.sort_newest"),
            tr("history.sort_oldest"),
            tr("history.sort_title"),
            tr("history.sort_size"),
        ]
        for i, text in enumerate(sort_labels):
            if i < self.sort_combo.count():
                self.sort_combo.setItemText(i, text)

        self.empty_title.setText(tr("history.empty_title"))
        self.empty_desc.setText(tr("history.empty_sub"))
        self.no_res_title.setText(tr("history.no_results_title"))
        self.no_res_desc.setText(tr("history.no_results_sub"))
        self.reset_filters_btn.setText(tr("history.btn_reset_filters"))

        for card in self._cards:
            card.retranslate_ui()

    def refresh_history(self) -> None:
        """Fetch and render history items matching active filter criteria."""
        total_count = self._db_mgr.total_history_count()

        if total_count == 0:
            self._clear_rendered_cards()
            self.empty_card.setVisible(True)
            self.no_results_card.setVisible(False)
            self.scroll_area.setVisible(False)
            self.clear_btn.setEnabled(False)
            self.search_input.setEnabled(False)
            self.status_filter_combo.setEnabled(False)
            self.sort_combo.setEnabled(False)
            return

        # Enable search and filter controls when history exists
        self.clear_btn.setEnabled(True)
        self.search_input.setEnabled(True)
        self.status_filter_combo.setEnabled(True)
        self.sort_combo.setEnabled(True)
        self.empty_card.setVisible(False)

        search_text = self.search_input.text().strip()
        status_filter: TaskStatus | None = self.status_filter_combo.currentData()
        sort_by: str = self.sort_combo.currentData() or "date_desc"

        tasks = self._db_mgr.query_history(
            search_query=search_text,
            status_filter=status_filter,
            sort_by=sort_by,
        )

        if not tasks:
            self._clear_rendered_cards()
            self.no_results_card.setVisible(True)
            self.scroll_area.setVisible(False)
            return

        self.no_results_card.setVisible(False)
        self.scroll_area.setVisible(True)
        self._render_cards(tasks)

    def _render_cards(self, tasks: list[DownloadTask]) -> None:
        """Re-render card widgets for tasks list."""
        self._clear_rendered_cards()

        for task in tasks:
            card = HistoryItemCard(task, self.cards_container)
            card.delete_requested.connect(self._on_delete_item)
            self._cards.append(card)
            # Insert before trailing stretch
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _clear_rendered_cards(self) -> None:
        """Remove and delete all existing card widgets."""
        for card in self._cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

    def _on_filter_changed(self) -> None:
        """Slot invoked when search term, status filter or sort choice changes."""
        self.refresh_history()

    def _on_reset_filters_clicked(self) -> None:
        """Clear search input and reset filter combo to All."""
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)

        self.status_filter_combo.blockSignals(True)
        self.status_filter_combo.setCurrentIndex(0)
        self.status_filter_combo.blockSignals(False)

        self.sort_combo.blockSignals(True)
        self.sort_combo.setCurrentIndex(0)
        self.sort_combo.blockSignals(False)

        self.refresh_history()

    def _on_delete_item(self, task_id: str) -> None:
        """Remove record from SQLite and refresh view."""
        self._db_mgr.delete_task(task_id)
        self.refresh_history()

    def _on_clear_all_clicked(self) -> None:
        """Confirm with user and remove all records from database."""
        reply = QMessageBox.question(
            self,
            tr("history.clear_confirm_title"),
            tr("history.clear_confirm_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._db_mgr.clear_all()
            self.refresh_history()
            logger.info("Volledige downloadgeschiedenis gewist door gebruiker.")
