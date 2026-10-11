"""Sidebar navigation rail with modern icon and button controls."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from open_video_downloader import __version__
from open_video_downloader.core.constants import APP_NAME
from open_video_downloader.resources.icons import create_app_icon, create_symbol_icon
from open_video_downloader.services.i18n import tr


class NavigationRail(QFrame):
    """Vertical sidebar rail for top-level view switching."""

    page_selected = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navRail")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(8)

        # Header: App Icon and Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)

        app_icon_label = QLabel(self)
        app_icon_label.setPixmap(create_app_icon(34).pixmap(34, 34))
        header_layout.addWidget(app_icon_label)

        title_container = QVBoxLayout()
        title_container.setSpacing(1)

        title_label = QLabel(APP_NAME, self)
        title_label.setObjectName("navHeaderTitle")
        title_container.addWidget(title_label)

        sub_label = QLabel("Media Manager", self)
        sub_label.setObjectName("navHeaderSubtitle")
        title_container.addWidget(sub_label)

        header_layout.addLayout(title_container)
        layout.addLayout(header_layout)

        layout.addSpacing(18)

        # Navigation Buttons Group
        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._nav_items: list[tuple[str, str, int]] = [
            ("Downloaden", "download", 0),
            ("Wachtrij", "queue", 1),
            ("Geschiedenis", "history", 2),
            ("Instellingen", "settings", 3),
            ("Over", "about", 4),
        ]
        self._buttons: list[QPushButton] = []

        for title, symbol, index in self._nav_items:
            btn = QPushButton(f"  {title}", self)
            btn.setProperty("class", "navBtn")
            btn.setIcon(create_symbol_icon(symbol, 18))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            self._button_group.addButton(btn, index)
            self._buttons.append(btn)
            layout.addWidget(btn)

        # Connect button group clicks
        self._button_group.idClicked.connect(self._on_button_clicked)

        layout.addStretch()

        # Footer with version tag
        self._version_label = QLabel(f"v{__version__}", self)
        self._version_label.setObjectName("navHeaderSubtitle")
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._version_label)

        # Apply initial translations
        self.retranslate_ui()

        # Default selection: 0 (Downloaden)
        if self._buttons:
            self._buttons[0].setChecked(True)

    def retranslate_ui(self) -> None:
        """Update button labels and text to reflect active language."""
        titles = [
            tr("nav.downloads"),
            tr("nav.queue"),
            tr("nav.history"),
            tr("nav.settings"),
            tr("nav.about"),
        ]
        for btn, title in zip(self._buttons, titles, strict=False):
            btn.setText(f"  {title}")
        self._version_label.setText(f"v{__version__}")

    def _on_button_clicked(self, page_index: int) -> None:
        """Handle navigation item selection."""
        self.page_selected.emit(page_index)

    def set_current_index(self, index: int) -> None:
        """Programmatically switch active checked button."""
        btn = self._button_group.button(index)
        if btn:
            btn.setChecked(True)
