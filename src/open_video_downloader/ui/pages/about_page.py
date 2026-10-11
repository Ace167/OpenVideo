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
    QVBoxLayout,
    QWidget,
)

from open_video_downloader import __version__
from open_video_downloader.core.constants import APP_NAME
from open_video_downloader.core.paths import get_app_data_dir
from open_video_downloader.engines.ffmpeg_probe import get_ffmpeg_path
from open_video_downloader.resources.icons import create_app_icon
from open_video_downloader.services.logger import SensitiveDataFilter


class AboutPage(QWidget):
    """View presenting application details, environment versions and diagnostic export."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._redaction_filter = SensitiveDataFilter()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        icon_label = QLabel(self)
        icon_label.setPixmap(create_app_icon(52).pixmap(52, 52))
        header_layout.addWidget(icon_label)

        title_container = QVBoxLayout()
        title_container.setSpacing(2)

        title = QLabel(APP_NAME, self)
        title.setProperty("class", "pageTitle")
        title_container.addWidget(title)

        subtitle = QLabel(f"Versie {__version__} • Open-Source Windows Media Manager", self)
        subtitle.setProperty("class", "pageSubtitle")
        title_container.addWidget(subtitle)

        header_layout.addLayout(title_container)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. System & Diagnostics Card
        diag_card = QFrame(self)
        diag_card.setProperty("class", "card")
        diag_layout = QVBoxLayout(diag_card)
        diag_layout.setSpacing(14)

        diag_header = QLabel("Systeeminformatie & Diagnostiek", self)
        diag_header.setProperty("class", "sectionHeader")
        diag_layout.addWidget(diag_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)

        # System info items
        ffmpeg_bin = get_ffmpeg_path()
        if ffmpeg_bin:
            self._ffmpeg_status = f"Beschikbaar ({Path(ffmpeg_bin).name})"
        else:
            self._ffmpeg_status = "Niet gedetecteerd (progressieve formaten beschikbaar)"
        self._data_dir = str(get_app_data_dir())

        info_rows = [
            ("Applicatieversie:", f"v{__version__}"),
            ("Python runtime:", sys.version.split()[0]),
            ("PySide6 / Qt runtime:", f"{PySide6.__version__} (Qt {QtCore.qVersion()})"),
            ("yt-dlp engine:", yt_dlp.version.__version__),
            ("SQLite database:", sqlite3.sqlite_version),
            ("FFmpeg status:", self._ffmpeg_status),
            ("Gebruikersdatamap:", self._data_dir),
        ]

        for idx, (label_txt, value_txt) in enumerate(info_rows):
            lbl = QLabel(label_txt, self)
            lbl.setStyleSheet("color: #64748b; font-weight: 500;")
            val = QLabel(value_txt, self)
            val.setStyleSheet("color: #1e293b; font-weight: 600;")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(lbl, idx, 0)
            grid.addWidget(val, idx, 1)

        diag_layout.addLayout(grid)

        # Informational note regarding FFmpeg and stream muxing
        ffmpeg_notice = QLabel(
            "💡 <b>Over FFmpeg & downloadkwaliteit:</b> Hoge resoluties (1080p, 4K) worden door "
            "platforms zoals YouTube gesplitst in losse video- en audiostreams. FFmpeg is nodig "
            "om deze samen te voegen. Zonder FFmpeg downloadt OpenVideo Downloader automatisch "
            "de hoogste beschikbare enkele stream (beeld en geluid gecombineerd) tot 720p.<br>"
            "<i>Optionele installatie:</i> Voer in PowerShell uit: "
            "<code>winget install Gyan.FFmpeg</code> "
            "of plaats <code>ffmpeg.exe</code> in de applicatiemap.",
            self,
        )
        ffmpeg_notice.setStyleSheet(
            "background-color: rgba(2, 132, 199, 0.08); "
            "border: 1px solid rgba(2, 132, 199, 0.25); "
            "border-radius: 6px; padding: 10px; font-size: 12px; color: #334155;"
        )
        ffmpeg_notice.setWordWrap(True)
        diag_layout.addWidget(ffmpeg_notice)

        # Copy and open buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.copy_btn = QPushButton("Diagnostiek kopiëren", self)
        self.copy_btn.setProperty("class", "btnPrimary")
        self.copy_btn.clicked.connect(self._copy_diagnostics)
        btn_row.addWidget(self.copy_btn)

        self.open_folder_btn = QPushButton("Gebruikersdatamap openen", self)
        self.open_folder_btn.setProperty("class", "btnSecondary")
        self.open_folder_btn.clicked.connect(self._open_data_folder)
        btn_row.addWidget(self.open_folder_btn)

        self.copy_feedback = QLabel("", self)
        self.copy_feedback.setStyleSheet("color: #16a34a; font-weight: 600; font-size: 12px;")
        btn_row.addWidget(self.copy_feedback)

        btn_row.addStretch()
        diag_layout.addLayout(btn_row)

        layout.addWidget(diag_card)

        # 3. Legal and Disclaimer Card
        legal_card = QFrame(self)
        legal_card.setProperty("class", "card")
        legal_layout = QVBoxLayout(legal_card)
        legal_layout.setSpacing(8)

        legal_header = QLabel("Licentie & Verantwoordelijkheid", self)
        legal_header.setProperty("class", "sectionHeader")
        legal_layout.addWidget(legal_header)

        disclaimer_text = QLabel(
            "OpenVideo Downloader is een onafhankelijke desktopapplicatie uitgebracht onder "
            "de MIT-licentie.\n\n"
            "Dit project is niet verbonden aan, goedgekeurd door of officieel gelieerd aan "
            "YouTube, Google of enige andere externe mediadienst. De gebruiker is zelf "
            "verantwoordelijk voor rechtmatig gebruik, toepasselijke auteursrechten en de "
            "gebruiksvoorwaarden van bezochte platforms.",
            self,
        )
        disclaimer_text.setWordWrap(True)
        disclaimer_text.setStyleSheet("color: #64748b; font-size: 12px; line-height: 1.4;")
        legal_layout.addWidget(disclaimer_text)

        layout.addWidget(legal_card)
        layout.addStretch()

    def get_diagnostic_report(self) -> str:
        """Construct sanitized markdown report of diagnostic details."""
        raw_report = (
            f"=== OpenVideo Downloader Diagnostiek ===\n"
            f"Versie: v{__version__}\n"
            f"Python: {sys.version.split()[0]}\n"
            f"PySide6: {PySide6.__version__}\n"
            f"Qt: {QtCore.qVersion()}\n"
            f"yt-dlp: {yt_dlp.version.__version__}\n"
            f"SQLite: {sqlite3.sqlite_version}\n"
            f"FFmpeg: {self._ffmpeg_status}\n"
            f"Datamap: {self._data_dir}\n"
        )
        # Apply privacy redaction on username and local paths
        return self._redaction_filter.redact(raw_report)

    def _copy_diagnostics(self) -> None:
        """Copy diagnostic details to the system clipboard with privacy redaction."""
        clipboard = QGuiApplication.clipboard()
        if clipboard:
            clipboard.setText(self.get_diagnostic_report())
            self.copy_feedback.setText(
                "✓ Diagnostiek gekopieerd naar klembord (gevoelige data geredigeerd)."
            )
        else:
            self.copy_feedback.setText("Klembord niet beschikbaar.")

    def _open_data_folder(self) -> None:
        """Open user data folder in Windows Explorer."""
        data_dir = get_app_data_dir()
        data_dir.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir)))
