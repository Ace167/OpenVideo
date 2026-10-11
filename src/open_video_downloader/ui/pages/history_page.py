"""Download history view with search bar and empty state."""

from PySide6.QtCore import Qt
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


class HistoryPage(QWidget):
    """View displaying historical completed and failed download tasks from SQLite."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header & Controls
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title = QLabel("Geschiedenis", self)
        title.setProperty("class", "pageTitle")
        title_container.addWidget(title)

        subtitle = QLabel("Lokaal opgeslagen geschiedenis van voltooide en verwerkte media.", self)
        subtitle.setProperty("class", "pageSubtitle")
        title_container.addWidget(subtitle)
        header_layout.addLayout(title_container)

        header_layout.addStretch()

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Zoeken in geschiedenis...")
        self.search_input.setFixedWidth(220)
        self.search_input.setEnabled(False)
        header_layout.addWidget(self.search_input)

        self.clear_btn = QPushButton("Geschiedenis wissen", self)
        self.clear_btn.setProperty("class", "btnSecondary")
        self.clear_btn.setEnabled(False)
        header_layout.addWidget(self.clear_btn)

        layout.addLayout(header_layout)

        # 2. Content Card: Empty State
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

        empty_title = QLabel("Nog geen geschiedenis", self)
        empty_title.setProperty("class", "emptyStateTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel(
            "Wanneer downloads zijn afgerond, worden de bron-URL, titel, bestandsgrootte\n"
            "en doelmap hier bewaard in de lokale database (Fase 4).",
            self,
        )
        empty_desc.setProperty("class", "emptyStateText")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)

        layout.addWidget(self.empty_card, stretch=1)
