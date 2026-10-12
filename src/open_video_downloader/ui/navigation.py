"""Sidebar navigation rail with modern icon and button controls supporting compact mode."""

from PySide6.QtCore import QSize, Qt, Signal
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
    """Vertical sidebar rail for top-level view switching with adaptive compact mode."""

    page_selected = Signal(int)
    compact_toggled = Signal(bool)

    EXPANDED_WIDTH = 224
    COMPACT_WIDTH = 68

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("navRail")
        self._is_compact = False
        self._titles: list[str] = []

        self.setFixedWidth(self.EXPANDED_WIDTH)

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 16, 12, 14)
        self._main_layout.setSpacing(8)

        # Header: App Icon, Title and Collapse Toggle
        self._header_layout = QHBoxLayout()
        self._header_layout.setSpacing(8)

        self._app_icon_label = QLabel(self)
        self._app_icon_label.setPixmap(create_app_icon(32).pixmap(32, 32))
        self._app_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header_layout.addWidget(self._app_icon_label)

        self._title_container = QWidget(self)
        title_box = QVBoxLayout(self._title_container)
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(1)

        self._title_label = QLabel(APP_NAME, self._title_container)
        self._title_label.setObjectName("navHeaderTitle")
        title_box.addWidget(self._title_label)

        self._sub_label = QLabel("Media Manager", self._title_container)
        self._sub_label.setObjectName("navHeaderSubtitle")
        title_box.addWidget(self._sub_label)

        self._header_layout.addWidget(self._title_container, stretch=1)

        # Sidebar Collapse / Expand Toggle Button
        self.toggle_btn = QPushButton(self)
        self.toggle_btn.setObjectName("navToggleBtn")
        self.toggle_btn.setFixedSize(28, 28)
        self.toggle_btn.setIcon(create_symbol_icon("menu", 16))
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.setAccessibleName("Toggle navigation sidebar")
        self.toggle_btn.clicked.connect(self.toggle_compact_mode)
        self._header_layout.addWidget(self.toggle_btn)

        self._main_layout.addLayout(self._header_layout)
        self._main_layout.addSpacing(14)

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
            btn.setIconSize(QSize(18, 18))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(title)
            btn.setAccessibleName(title)

            self._button_group.addButton(btn, index)
            self._buttons.append(btn)
            self._main_layout.addWidget(btn)

        # Connect button group clicks
        self._button_group.idClicked.connect(self._on_button_clicked)

        self._main_layout.addStretch()

        # Footer with version tag
        self._version_label = QLabel(f"v{__version__}", self)
        self._version_label.setObjectName("navHeaderSubtitle")
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._main_layout.addWidget(self._version_label)

        # Apply initial translations
        self.retranslate_ui()

        # Default selection: 0 (Downloaden)
        if self._buttons:
            self._buttons[0].setChecked(True)

    @property
    def is_compact(self) -> bool:
        """Return whether navigation rail is in compact mode."""
        return self._is_compact

    def toggle_compact_mode(self) -> None:
        """Toggle between expanded and compact navigation rail states."""
        self.set_compact_mode(not self._is_compact)

    def set_compact_mode(self, compact: bool) -> None:
        """Set compact mode state, updating sidebar width and button presentations."""
        if compact == self._is_compact:
            return

        self._is_compact = compact

        if self._is_compact:
            self.setFixedWidth(self.COMPACT_WIDTH)
            self._main_layout.setContentsMargins(6, 16, 6, 12)
            self._title_container.setVisible(False)
            self._version_label.setVisible(False)
            for btn, title in zip(self._buttons, self._titles, strict=False):
                btn.setText("")
                btn.setProperty("class", "navBtnCompact")
                btn.setToolTip(title)
                btn.setIconSize(QSize(20, 20))
                btn.style().unpolish(btn)
                btn.style().polish(btn)
        else:
            self.setFixedWidth(self.EXPANDED_WIDTH)
            self._main_layout.setContentsMargins(12, 16, 12, 14)
            self._title_container.setVisible(True)
            self._version_label.setVisible(True)
            for btn, title in zip(self._buttons, self._titles, strict=False):
                btn.setText(f"  {title}")
                btn.setProperty("class", "navBtn")
                btn.setToolTip(title)
                btn.setIconSize(QSize(18, 18))
                btn.style().unpolish(btn)
                btn.style().polish(btn)

        self.compact_toggled.emit(self._is_compact)

    def retranslate_ui(self) -> None:
        """Update button labels and text to reflect active language."""
        self._titles = [
            tr("nav.downloads"),
            tr("nav.queue"),
            tr("nav.history"),
            tr("nav.settings"),
            tr("nav.about"),
        ]
        for btn, title in zip(self._buttons, self._titles, strict=False):
            btn.setToolTip(title)
            btn.setAccessibleName(title)
            if self._is_compact:
                btn.setText("")
            else:
                btn.setText(f"  {title}")

        self._version_label.setText(f"v{__version__}")
        self.toggle_btn.setToolTip(tr("nav.toggle_sidebar"))

    def _on_button_clicked(self, page_index: int) -> None:
        """Handle navigation item selection."""
        self.page_selected.emit(page_index)

    def set_current_index(self, index: int) -> None:
        """Programmatically switch active checked button."""
        btn = self._button_group.button(index)
        if btn:
            btn.setChecked(True)
