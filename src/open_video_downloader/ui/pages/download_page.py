"""Download view allowing URL input, format probing, and queue submission."""

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt, QUrl, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader.core.models import DownloadTask, FormatOption, MediaMetadata
from open_video_downloader.engines.ffmpeg_probe import is_ffmpeg_available
from open_video_downloader.engines.workers import MetadataWorker
from open_video_downloader.engines.ytdl_adapter import is_valid_url
from open_video_downloader.resources.icons import create_symbol_icon
from open_video_downloader.services.i18n import tr
from open_video_downloader.services.logger import get_logger
from open_video_downloader.settings.manager import SettingsManager

logger = get_logger("ui.download_page")


class DownloadPage(QWidget):
    """Primary interface for probing video metadata and configuring format choices."""

    fetch_requested = Signal(str)
    task_created = Signal(object)  # DownloadTask
    navigate_to_queue = Signal()

    def __init__(self, settings_manager: SettingsManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings_mgr = settings_manager
        self._metadata_worker: MetadataWorker | None = None
        self._current_metadata: MediaMetadata | None = None
        self._net_manager = QNetworkAccessManager(self)
        self._net_manager.finished.connect(self._on_thumbnail_downloaded)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        self.title_label = QLabel(self)
        self.title_label.setProperty("class", "pageTitle")
        header_layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(self)
        self.subtitle_label.setProperty("class", "pageSubtitle")
        header_layout.addWidget(self.subtitle_label)
        layout.addLayout(header_layout)

        # 2. Input Card
        input_card = QFrame(self)
        input_card.setProperty("class", "card")
        card_layout = QVBoxLayout(input_card)
        card_layout.setSpacing(10)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.url_input = QLineEdit(self)
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self._on_fetch_clicked)
        input_row.addWidget(self.url_input, stretch=1)

        self.paste_btn = QPushButton(self)
        self.paste_btn.setProperty("class", "btnSecondary")
        self.paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.paste_btn.clicked.connect(self.url_input.paste)
        input_row.addWidget(self.paste_btn)

        self.fetch_btn = QPushButton(self)
        self.fetch_btn.setProperty("class", "btnPrimary")
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        input_row.addWidget(self.fetch_btn)

        card_layout.addLayout(input_row)

        # Status & Error Feedback
        self.status_msg = QLabel("", self)
        self.status_msg.setWordWrap(True)
        self.status_msg.setVisible(False)
        card_layout.addWidget(self.status_msg)

        layout.addWidget(input_card)

        # 3. Authentic Empty State Card (Visible when no metadata loaded)
        self.empty_card = QFrame(self)
        self.empty_card.setProperty("class", "card")
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(32, 44, 32, 44)
        empty_layout.setSpacing(12)

        icon_label = QLabel(self)
        icon_label.setPixmap(create_symbol_icon("download", 48, "#94a3b8").pixmap(48, 48))
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

        # 4. Metadata Details Card (Hidden until metadata fetched)
        self.meta_card = QFrame(self)
        self.meta_card.setProperty("class", "card")
        self.meta_card.setVisible(False)
        meta_layout = QVBoxLayout(self.meta_card)
        meta_layout.setSpacing(14)

        # Media summary header (Thumbnail + Info)
        media_header_layout = QHBoxLayout()
        media_header_layout.setSpacing(16)

        self.thumb_label = QLabel(self)
        self.thumb_label.setFixedSize(140, 80)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("background-color: #0f172a; border-radius: 6px;")
        self.thumb_label.setPixmap(create_symbol_icon("download", 32, "#64748b").pixmap(32, 32))
        media_header_layout.addWidget(self.thumb_label)

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(4)

        self.media_title_label = QLabel(self)
        self.media_title_label.setStyleSheet("font-size: 15px; font-weight: 700;")
        self.media_title_label.setWordWrap(True)
        info_vbox.addWidget(self.media_title_label)

        self.media_meta_label = QLabel(self)
        self.media_meta_label.setStyleSheet("color: #64748b; font-size: 12px;")
        info_vbox.addWidget(self.media_meta_label)
        info_vbox.addStretch()

        media_header_layout.addLayout(info_vbox, stretch=1)
        meta_layout.addLayout(media_header_layout)

        # Format selector row
        format_vbox = QVBoxLayout()
        format_vbox.setSpacing(6)
        self.fmt_label = QLabel(self)
        self.fmt_label.setStyleSheet("font-weight: 600;")
        format_vbox.addWidget(self.fmt_label)

        self.format_combo = QComboBox(self)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_vbox.addWidget(self.format_combo)

        # FFmpeg warning banner
        self.ffmpeg_warning = QLabel("", self)
        self.ffmpeg_warning.setStyleSheet(
            "background-color: #fef3c7; color: #92400e; padding: 6px 10px; "
            "border-radius: 4px; font-size: 12px; font-weight: 500;"
        )
        self.ffmpeg_warning.setWordWrap(True)
        self.ffmpeg_warning.setVisible(False)
        format_vbox.addWidget(self.ffmpeg_warning)

        meta_layout.addLayout(format_vbox)

        # Download directory row
        dir_vbox = QVBoxLayout()
        dir_vbox.setSpacing(6)
        self.dir_label = QLabel(self)
        self.dir_label.setStyleSheet("font-weight: 600;")
        dir_vbox.addWidget(self.dir_label)

        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)
        self.dest_dir_input = QLineEdit(self)
        self.dest_dir_input.setText(self._settings_mgr.get().download_dir)
        dir_row.addWidget(self.dest_dir_input, stretch=1)

        self.browse_dir_btn = QPushButton(self)
        self.browse_dir_btn.setProperty("class", "btnSecondary")
        self.browse_dir_btn.clicked.connect(self._on_browse_target_dir)
        dir_row.addWidget(self.browse_dir_btn)
        dir_vbox.addLayout(dir_row)

        meta_layout.addLayout(dir_vbox)

        # Action Buttons
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.enqueue_btn = QPushButton(self)
        self.enqueue_btn.setProperty("class", "btnPrimary")
        self.enqueue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.enqueue_btn.clicked.connect(self._on_enqueue_clicked)
        action_row.addWidget(self.enqueue_btn)

        self.go_to_queue_btn = QPushButton(self)
        self.go_to_queue_btn.setProperty("class", "btnSecondary")
        self.go_to_queue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.go_to_queue_btn.setVisible(False)
        self.go_to_queue_btn.clicked.connect(lambda: self.navigate_to_queue.emit())
        action_row.addWidget(self.go_to_queue_btn)

        self.enqueue_feedback = QLabel("", self)
        self.enqueue_feedback.setStyleSheet("color: #16a34a; font-weight: 600; font-size: 12px;")
        action_row.addWidget(self.enqueue_feedback)

        action_row.addStretch()
        meta_layout.addLayout(action_row)

        layout.addWidget(self.meta_card, stretch=1)

        # Apply initial translations
        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Update texts to active language."""
        self.title_label.setText(tr("nav.downloads"))
        self.subtitle_label.setText(tr("download.header_sub"))
        self.url_input.setPlaceholderText(tr("download.input_placeholder"))
        self.paste_btn.setText(tr("download.btn_paste"))

        if self.fetch_btn.isEnabled():
            self.fetch_btn.setText(tr("download.btn_fetch"))
        else:
            self.fetch_btn.setText(tr("download.btn_loading"))

        self.empty_title.setText(tr("download.empty_title"))
        self.empty_desc.setText(tr("download.empty_desc"))

        self.fmt_label.setText(tr("download.format_label"))
        self.dir_label.setText(tr("download.dir_label"))
        self.browse_dir_btn.setText(tr("download.btn_browse"))
        self.enqueue_btn.setText(tr("download.btn_enqueue"))
        self.go_to_queue_btn.setText(tr("download.btn_go_to_queue"))

        if self._current_metadata:
            meta = self._current_metadata
            meta_text = tr(
                "download.meta_duration",
                duration=meta.duration_str,
                extractor=meta.extractor,
            )
            if meta.uploader:
                meta_text += tr("download.meta_uploader", uploader=meta.uploader)
            self.media_meta_label.setText(meta_text)

            # Refresh format combo item display labels
            curr_idx = self.format_combo.currentIndex()
            self.format_combo.blockSignals(True)
            self.format_combo.clear()
            for idx, fmt in enumerate(meta.formats):
                self.format_combo.addItem(fmt.display_label, idx)
            if 0 <= curr_idx < self.format_combo.count():
                self.format_combo.setCurrentIndex(curr_idx)
            self.format_combo.blockSignals(False)
            self._on_format_changed(self.format_combo.currentIndex())

    def _on_fetch_clicked(self) -> None:
        """Validate input URL and initiate background metadata extraction."""
        url = self.url_input.text().strip()
        if not url:
            self._show_error(tr("download.err_empty_url"))
            return

        if not is_valid_url(url):
            self._show_error(tr("download.err_invalid_url"))
            return

        # Prepare UI for loading
        self.status_msg.setText(tr("download.fetching_status"))
        self.status_msg.setStyleSheet("color: #0284c7; font-size: 12px; font-weight: 500;")
        self.status_msg.setVisible(True)
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText(tr("download.btn_loading"))
        self.url_input.setEnabled(False)
        self.enqueue_feedback.setText("")
        self.go_to_queue_btn.setVisible(False)

        # Cancel any previous worker
        self._cancel_existing_worker()

        # Start background worker
        self._metadata_worker = MetadataWorker(url)
        self._metadata_worker.metadata_ready.connect(self._on_metadata_ready)
        self._metadata_worker.metadata_error.connect(self._on_metadata_error)
        self._metadata_worker.start()
        self.fetch_requested.emit(url)

    def _on_metadata_ready(self, metadata: MediaMetadata) -> None:
        """Populate format options and display media details upon worker success."""
        self._reset_fetch_button()
        self.status_msg.setVisible(False)
        self._current_metadata = metadata

        self.media_title_label.setText(metadata.title)
        meta_text = tr(
            "download.meta_duration",
            duration=metadata.duration_str,
            extractor=metadata.extractor,
        )
        if metadata.uploader:
            meta_text += tr("download.meta_uploader", uploader=metadata.uploader)
        self.media_meta_label.setText(meta_text)

        # Populate format choices
        self.format_combo.blockSignals(True)
        self.format_combo.clear()
        for idx, fmt in enumerate(metadata.formats):
            self.format_combo.addItem(fmt.display_label, idx)
        self.format_combo.blockSignals(False)

        # Fetch thumbnail if available
        if metadata.thumbnail_url:
            self._net_manager.get(QNetworkRequest(QUrl(metadata.thumbnail_url)))

        # Update FFmpeg warning for initial selection
        self._on_format_changed(self.format_combo.currentIndex())

        # Switch views
        self.empty_card.setVisible(False)
        self.meta_card.setVisible(True)
        logger.info("Metadata getoond voor '%s'.", metadata.title)

    def _on_metadata_error(self, user_msg: str, tech_msg: str) -> None:
        """Present failure message when metadata probe fails."""
        self._reset_fetch_button()
        self._show_error(user_msg)
        logger.warning("Fout bij metadata-opvraging: %s", tech_msg)

    def _reset_fetch_button(self) -> None:
        """Restore fetch controls after probe completes."""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText(tr("download.btn_fetch"))
        self.url_input.setEnabled(True)

    def _show_error(self, message: str) -> None:
        """Display error banner below input bar."""
        self.status_msg.setText(message)
        self.status_msg.setStyleSheet("color: #e11d48; font-size: 12px; font-weight: 500;")
        self.status_msg.setVisible(True)

    def _on_format_changed(self, index: int) -> None:
        """Inspect selected format and show FFmpeg warning banner if needed."""
        if not self._current_metadata or index < 0 or index >= len(self._current_metadata.formats):
            self.ffmpeg_warning.setVisible(False)
            return

        selected_fmt = self._current_metadata.formats[index]
        if selected_fmt.requires_ffmpeg and not is_ffmpeg_available():
            self.ffmpeg_warning.setText(tr("download.ffmpeg_warning"))
            self.ffmpeg_warning.setVisible(True)
        else:
            self.ffmpeg_warning.setVisible(False)

    def _on_thumbnail_downloaded(self, reply: QNetworkReply) -> None:
        """Render received thumbnail image into label."""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data: QByteArray = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                scaled = pixmap.scaled(
                    self.thumb_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.thumb_label.setPixmap(scaled)
        reply.deleteLater()

    def _on_browse_target_dir(self) -> None:
        """Open folder dialog to pick destination."""
        curr = self.dest_dir_input.text() or str(Path.home())
        selected = QFileDialog.getExistingDirectory(self, tr("download.browse_dialog"), curr)
        if selected:
            self.dest_dir_input.setText(selected)

    def _on_enqueue_clicked(self) -> None:
        """Create DownloadTask with selected options and emit creation signal."""
        if not self._current_metadata:
            return

        dest_dir = self.dest_dir_input.text().strip()
        if not dest_dir:
            dest_dir = self._settings_mgr.get().download_dir

        target_path = Path(dest_dir)
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except OSError as err:
            self._show_error(tr("download.folder_create_error", err=str(err)))
            return

        fmt_idx = self.format_combo.currentIndex()
        selected_fmt: FormatOption | None = None
        if 0 <= fmt_idx < len(self._current_metadata.formats):
            selected_fmt = self._current_metadata.formats[fmt_idx]

        task = DownloadTask(
            url=self._current_metadata.url,
            title=self._current_metadata.title,
            target_dir=str(target_path),
            selected_format=selected_fmt,
        )

        self.task_created.emit(task)
        self.enqueue_feedback.setText(tr("download.enqueue_success"))
        self.go_to_queue_btn.setVisible(True)
        logger.info("Nieuwe DownloadTask '%s' aangemaakt vanaf DownloadPage.", task.task_id)

    def _cancel_existing_worker(self) -> None:
        """Cancel and clean up any ongoing metadata extraction worker."""
        if self._metadata_worker and self._metadata_worker.isRunning():
            self._metadata_worker.cancel()
            self._metadata_worker.wait(1000)
            self._metadata_worker = None
