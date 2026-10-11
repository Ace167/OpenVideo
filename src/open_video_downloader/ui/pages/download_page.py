"""Download view allowing URL input and format selection placeholder."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader.resources.icons import create_symbol_icon


class DownloadPage(QWidget):
    """Main view for probing media URLs and initiating downloads."""

    fetch_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Downloaden", self)
        title.setProperty("class", "pageTitle")
        header_layout.addWidget(title)

        subtitle = QLabel(
            "Voer een link in om beschikbare video- en audiokwaliteiten te bekijken.", self
        )
        subtitle.setProperty("class", "pageSubtitle")
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 2. URL Input Card
        input_card = QFrame(self)
        input_card.setProperty("class", "card")
        card_layout = QVBoxLayout(input_card)
        card_layout.setSpacing(12)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Plak een video- of afspeellijst-URL (bijv. https://...)")
        self.url_input.setClearButtonEnabled(True)
        self.url_input.returnPressed.connect(self._on_fetch_clicked)
        input_row.addWidget(self.url_input, stretch=1)

        self.paste_btn = QPushButton("Plakken", self)
        self.paste_btn.setProperty("class", "btnSecondary")
        self.paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.paste_btn.clicked.connect(self.url_input.paste)
        input_row.addWidget(self.paste_btn)

        self.fetch_btn = QPushButton("Informatie ophalen", self)
        self.fetch_btn.setProperty("class", "btnPrimary")
        self.fetch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fetch_btn.clicked.connect(self._on_fetch_clicked)
        input_row.addWidget(self.fetch_btn)

        card_layout.addLayout(input_row)

        # Message / feedback label
        self.status_msg = QLabel("", self)
        self.status_msg.setStyleSheet("color: #e11d48; font-size: 12px; font-weight: 500;")
        self.status_msg.setVisible(False)
        card_layout.addWidget(self.status_msg)

        layout.addWidget(input_card)

        # 3. Content Area: Authentic Empty State for Phase 2
        self.empty_card = QFrame(self)
        self.empty_card.setProperty("class", "card")
        empty_layout = QVBoxLayout(self.empty_card)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setContentsMargins(32, 48, 32, 48)
        empty_layout.setSpacing(12)

        icon_label = QLabel(self)
        icon_label.setPixmap(create_symbol_icon("download", 48, "#94a3b8").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(icon_label)

        empty_title = QLabel("Geen media geladen", self)
        empty_title.setProperty("class", "emptyStateTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel(
            "Voer hierboven een geldige media-URL in om videogegevens, thumbnails,\n"
            "beschikbare resoluties en audio-opties op te halen (actief in Fase 3).",
            self,
        )
        empty_desc.setProperty("class", "emptyStateText")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)

        layout.addWidget(self.empty_card, stretch=1)

    def _on_fetch_clicked(self) -> None:
        """Validate input and emit signal or prompt user."""
        url = self.url_input.text().strip()
        if not url:
            self.status_msg.setText(
                "Voer eerst een geldige URL in alvorens informatie op te halen."
            )
            self.status_msg.setStyleSheet("color: #e11d48; font-size: 12px; font-weight: 500;")
            self.status_msg.setVisible(True)
            return

        self.status_msg.setText(
            "URL gevalideerd. De downloadengine-adapter wordt geactiveerd in Fase 3."
        )
        self.status_msg.setStyleSheet("color: #0284c7; font-size: 12px; font-weight: 500;")
        self.status_msg.setVisible(True)
        self.fetch_requested.emit(url)
