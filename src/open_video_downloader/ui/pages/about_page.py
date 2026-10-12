"""About and diagnostics view showing system versions, license and copy utility."""

import sqlite3
import sys
from pathlib import Path

import PySide6
import yt_dlp
from PySide6 import QtCore
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader import __version__
from open_video_downloader.core.constants import APP_NAME
from open_video_downloader.core.paths import get_app_data_dir
from open_video_downloader.engines.ffmpeg_probe import get_ffmpeg_path
from open_video_downloader.resources.icons import create_app_icon
from open_video_downloader.services.i18n import tr
from open_video_downloader.services.logger import SensitiveDataFilter


class AboutPage(QWidget):
    """View presenting application details, environment versions and diagnostic export."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._redaction_filter = SensitiveDataFilter()

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Smooth, responsive vertical scroll area
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget(self.scroll_area)
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel(self)
        icon_label.setPixmap(create_app_icon(44).pixmap(44, 44))
        header_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        title = QLabel(APP_NAME, self)
        title.setProperty("class", "pageTitle")
        title.setWordWrap(True)
        title_container.addWidget(title)

        self.subtitle_label = QLabel(self)
        self.subtitle_label.setProperty("class", "pageSubtitle")
        self.subtitle_label.setWordWrap(True)
        title_container.addWidget(self.subtitle_label)

        header_layout.addLayout(title_container, stretch=1)
        layout.addLayout(header_layout)

        # 2. System & Diagnostics Card
        diag_card = QFrame(self)
        diag_card.setProperty("class", "card")
        diag_layout = QVBoxLayout(diag_card)
        diag_layout.setSpacing(12)

        self.diag_header = QLabel(self)
        self.diag_header.setProperty("class", "sectionHeader")
        self.diag_header.setWordWrap(True)
        diag_layout.addWidget(self.diag_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        self._ffmpeg_bin = get_ffmpeg_path()
        self._data_dir = str(get_app_data_dir())

        # Create diagnostic rows
        self.lbl_app_ver = QLabel(self)
        self.val_app_ver = QLabel(f"v{__version__}", self)

        self.lbl_python = QLabel(self)
        self.val_python = QLabel(sys.version.split()[0], self)

        self.lbl_pyside = QLabel(self)
        self.val_pyside = QLabel(f"{PySide6.__version__} (Qt {QtCore.qVersion()})", self)

        self.lbl_ytdlp = QLabel(self)
        self.val_ytdlp = QLabel(yt_dlp.version.__version__, self)

        self.lbl_sqlite = QLabel(self)
        self.val_sqlite = QLabel(sqlite3.sqlite_version, self)

        self.lbl_ffmpeg = QLabel(self)
        self.val_ffmpeg = QLabel(self)

        self.lbl_datadir = QLabel(self)
        self.val_datadir = QLabel(self._data_dir, self)

        rows = [
            (self.lbl_app_ver, self.val_app_ver),
            (self.lbl_python, self.val_python),
            (self.lbl_pyside, self.val_pyside),
            (self.lbl_ytdlp, self.val_ytdlp),
            (self.lbl_sqlite, self.val_sqlite),
            (self.lbl_ffmpeg, self.val_ffmpeg),
            (self.lbl_datadir, self.val_datadir),
        ]

        for idx, (lbl, val) in enumerate(rows):
            lbl.setProperty("class", "diagLabel")
            lbl.setWordWrap(True)
            val.setProperty("class", "diagValue")
            val.setWordWrap(True)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            val.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            grid.addWidget(lbl, idx, 0, alignment=Qt.AlignmentFlag.AlignTop)
            grid.addWidget(val, idx, 1)

        diag_layout.addLayout(grid)

        # Informational note regarding FFmpeg and stream muxing
        self.ffmpeg_notice = QLabel(self)
        self.ffmpeg_notice.setProperty("class", "infoNotice")
        self.ffmpeg_notice.setWordWrap(True)
        diag_layout.addWidget(self.ffmpeg_notice)

        # Copy and open buttons container
        btn_box = QVBoxLayout()
        btn_box.setSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.copy_btn = QPushButton(self)
        self.copy_btn.setProperty("class", "btnPrimary")
        self.copy_btn.setAccessibleName("Copy diagnostic system report")
        self.copy_btn.clicked.connect(self._copy_diagnostics)
        btn_row.addWidget(self.copy_btn)

        self.open_folder_btn = QPushButton(self)
        self.open_folder_btn.setProperty("class", "btnSecondary")
        self.open_folder_btn.setAccessibleName("Open user data directory in Explorer")
        self.open_folder_btn.clicked.connect(self._open_data_folder)
        btn_row.addWidget(self.open_folder_btn)

        btn_row.addStretch()
        btn_box.addLayout(btn_row)

        self.copy_feedback = QLabel("", self)
        self.copy_feedback.setStyleSheet("color: #16a34a; font-weight: 600; font-size: 12px;")
        self.copy_feedback.setWordWrap(True)
        btn_box.addWidget(self.copy_feedback)

        diag_layout.addLayout(btn_box)
        layout.addWidget(diag_card)

        # 3. Legal and Disclaimer Card
        legal_card = QFrame(self)
        legal_card.setProperty("class", "card")
        legal_layout = QVBoxLayout(legal_card)
        legal_layout.setSpacing(8)

        self.legal_header = QLabel(self)
        self.legal_header.setProperty("class", "sectionHeader")
        self.legal_header.setWordWrap(True)
        legal_layout.addWidget(self.legal_header)

        self.disclaimer_text = QLabel(self)
        self.disclaimer_text.setProperty("class", "metaLabel")
        self.disclaimer_text.setWordWrap(True)
        legal_layout.addWidget(self.disclaimer_text)

        layout.addWidget(legal_card)
        layout.addStretch()

        self.scroll_area.setWidget(content_widget)
        root_layout.addWidget(self.scroll_area)

        # Apply initial translations
        self.retranslate_ui()

    def _get_ffmpeg_status_string(self) -> str:
        """Return localized FFmpeg status string."""
        if self._ffmpeg_bin:
            return tr("about.ffmpeg_available", binary=Path(self._ffmpeg_bin).name)
        return tr("about.ffmpeg_missing")

    def retranslate_ui(self) -> None:
        """Update texts to active language."""
        self.subtitle_label.setText(tr("about.header_sub", version=__version__))
        self.diag_header.setText(tr("about.sec_diagnostics"))

        self.lbl_app_ver.setText(tr("about.lbl_app_version"))
        self.lbl_python.setText(tr("about.lbl_python"))
        self.lbl_pyside.setText(tr("about.lbl_pyside"))
        self.lbl_ytdlp.setText(tr("about.lbl_ytdlp"))
        self.lbl_sqlite.setText(tr("about.lbl_sqlite"))
        self.lbl_ffmpeg.setText(tr("about.lbl_ffmpeg"))
        self.lbl_datadir.setText(tr("about.lbl_data_dir"))

        self.val_ffmpeg.setText(self._get_ffmpeg_status_string())

        self.ffmpeg_notice.setText(tr("about.ffmpeg_notice"))
        self.copy_btn.setText(tr("about.btn_copy_diag"))
        self.open_folder_btn.setText(tr("about.btn_open_data_dir"))

        self.legal_header.setText(tr("about.sec_legal"))
        self.disclaimer_text.setText(tr("about.legal_text"))

    def get_diagnostic_report(self) -> str:
        """Construct sanitized markdown report of diagnostic details."""
        raw_report = (
            f"{tr('about.diag_title')}\n"
            f"{tr('about.diag_version', version=__version__)}\n"
            f"Python: {sys.version.split()[0]}\n"
            f"PySide6: {PySide6.__version__}\n"
            f"Qt: {QtCore.qVersion()}\n"
            f"yt-dlp: {yt_dlp.version.__version__}\n"
            f"SQLite: {sqlite3.sqlite_version}\n"
            f"{tr('about.diag_ffmpeg', status=self._get_ffmpeg_status_string())}\n"
            f"{tr('about.diag_datadir', path=self._data_dir)}\n"
        )
        return self._redaction_filter.redact(raw_report)

    def _copy_diagnostics(self) -> None:
        """Copy diagnostic details to the system clipboard with privacy redaction."""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.get_diagnostic_report())
            self.copy_feedback.setText(tr("about.copy_success"))
        else:
            self.copy_feedback.setText(tr("about.clipboard_unavailable"))

    def _open_data_folder(self) -> None:
        """Open user data folder in Windows Explorer."""
        data_dir = get_app_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir)))
