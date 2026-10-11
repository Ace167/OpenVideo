"""Main window aggregating navigation rail, stacked page views, and status bar."""

import shutil

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QStackedWidget,
    QStatusBar,
    QWidget,
)

from open_video_downloader import __version__
from open_video_downloader.core.constants import (
    APP_NAME,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
)
from open_video_downloader.resources.icons import create_app_icon
from open_video_downloader.resources.themes import get_theme_stylesheet
from open_video_downloader.services.logger import get_logger
from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.settings.models import AppSettings
from open_video_downloader.ui.navigation import NavigationRail
from open_video_downloader.ui.pages.about_page import AboutPage
from open_video_downloader.ui.pages.download_page import DownloadPage
from open_video_downloader.ui.pages.history_page import HistoryPage
from open_video_downloader.ui.pages.queue_page import QueuePage
from open_video_downloader.ui.pages.settings_page import SettingsPage

logger = get_logger("ui.main_window")


class MainWindow(QMainWindow):
    """Primary application desktop window."""

    def __init__(
        self, settings_manager: SettingsManager | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._settings_mgr = settings_manager or SettingsManager()

        self.setWindowTitle(f"{APP_NAME} v{__version__}")
        self.setWindowIcon(create_app_icon(64))
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Central widget with horizontal split (NavigationRail + Content Pages)
        central_widget = QWidget(self)
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Navigation Rail
        self.nav_rail = NavigationRail(central_widget)
        root_layout.addWidget(self.nav_rail)

        # 2. Stacked Content Views
        self.stack = QStackedWidget(central_widget)

        self.download_page = DownloadPage(self.stack)
        self.queue_page = QueuePage(self.stack)
        self.history_page = HistoryPage(self.stack)
        self.settings_page = SettingsPage(self._settings_mgr, self.stack)
        self.about_page = AboutPage(self.stack)

        self.stack.addWidget(self.download_page)  # Index 0
        self.stack.addWidget(self.queue_page)  # Index 1
        self.stack.addWidget(self.history_page)  # Index 2
        self.stack.addWidget(self.settings_page)  # Index 3
        self.stack.addWidget(self.about_page)  # Index 4

        root_layout.addWidget(self.stack, stretch=1)
        self.setCentralWidget(central_widget)

        # Connect navigation
        self.nav_rail.page_selected.connect(self._on_page_selected)

        # 3. Status Bar
        self._setup_status_bar()

        # Connect live settings changes to theme updater
        self._settings_mgr.settings_changed.connect(self._on_settings_changed)

        # Apply initial theme
        self.apply_theme(self._settings_mgr.get().theme)
        logger.info("MainWindow geïnitialiseerd (versie v%s).", __version__)

    def _setup_status_bar(self) -> None:
        """Create and configure application status bar."""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)

        self.status_msg_label = QLabel("Gereed", self)
        status_bar.addWidget(self.status_msg_label, stretch=1)

        # FFmpeg presence indicator
        has_ffmpeg = bool(shutil.which("ffmpeg"))
        ffmpeg_txt = "FFmpeg: Beschikbaar" if has_ffmpeg else "FFmpeg: Niet gedetecteerd"
        ffmpeg_color = "#16a34a" if has_ffmpeg else "#d97706"
        self.ffmpeg_label = QLabel(ffmpeg_txt, self)
        self.ffmpeg_label.setStyleSheet(f"color: {ffmpeg_color}; font-weight: 500;")
        status_bar.addPermanentWidget(self.ffmpeg_label)

        # Theme indicator
        self.theme_label = QLabel(f"Thema: {self._settings_mgr.get().theme.capitalize()}", self)
        status_bar.addPermanentWidget(self.theme_label)

        # Version label
        version_badge = QLabel(f"v{__version__}", self)
        status_bar.addPermanentWidget(version_badge)

    def _on_page_selected(self, index: int) -> None:
        """Switch active view in the stacked widget."""
        self.stack.setCurrentIndex(index)
        page_names = ["Downloaden", "Wachtrij", "Geschiedenis", "Instellingen", "Over"]
        if 0 <= index < len(page_names):
            self.set_status_message(f"Pagina geopend: {page_names[index]}")

    def set_status_message(self, message: str) -> None:
        """Update transient status bar message."""
        self.status_msg_label.setText(message)

    def _on_settings_changed(self, settings: AppSettings) -> None:
        """Respond to dynamic settings updates."""
        self.apply_theme(settings.theme)
        self.theme_label.setText(f"Thema: {settings.theme.capitalize()}")

    def apply_theme(self, theme_name: str) -> None:
        """Apply Qt style sheet matching the selected theme."""
        stylesheet = get_theme_stylesheet(theme_name)
        self.setStyleSheet(stylesheet)
        logger.info("Thema '%s' toegepast op MainWindow.", theme_name)
