"""Download queue management view with active task list and empty state."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader.resources.icons import create_symbol_icon


class QueuePage(QWidget):
    """View presenting active downloads, queue controls and task progress."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        # 1. Header
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        title_container.setSpacing(4)

        title = QLabel("Wachtrij", self)
        title.setProperty("class", "pageTitle")
        title_container.addWidget(title)

        subtitle = QLabel("Overzicht van actieve, gepauzeerde en wachtende downloads.", self)
        subtitle.setProperty("class", "pageSubtitle")
        title_container.addWidget(subtitle)
        header_layout.addLayout(title_container)

        header_layout.addStretch()

        # Action buttons
        self.resume_all_btn = QPushButton("Alles hervatten", self)
        self.resume_all_btn.setProperty("class", "btnSecondary")
        self.resume_all_btn.setEnabled(False)
        header_layout.addWidget(self.resume_all_btn)

        self.pause_all_btn = QPushButton("Alles pauzeren", self)
        self.pause_all_btn.setProperty("class", "btnSecondary")
        self.pause_all_btn.setEnabled(False)
        header_layout.addWidget(self.pause_all_btn)

        layout.addLayout(header_layout)

        # 2. Content Card: Empty State
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

        empty_title = QLabel("De downloadwachtrij is leeg", self)
        empty_title.setProperty("class", "emptyStateTitle")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)

        empty_desc = QLabel(
            "Er worden momenteel geen media gedownload.\n"
            "Toegevoegde taken verschijnen hier met hun actuele snelheid en voortgang (Fase 4).",
            self,
        )
        empty_desc.setProperty("class", "emptyStateText")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_desc)

        layout.addWidget(self.empty_card, stretch=1)
