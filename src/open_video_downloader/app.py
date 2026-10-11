"""Application bootstrap, lifecycle and main window initialization."""

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from open_video_downloader import __version__
from open_video_downloader.core.constants import APP_NAME, APP_ORGANIZATION
from open_video_downloader.core.paths import StorageError, ensure_app_directories
from open_video_downloader.resources.icons import create_app_icon
from open_video_downloader.services.logger import get_logger, setup_logging
from open_video_downloader.settings.manager import SettingsManager
from open_video_downloader.ui.main_window import MainWindow

logger = get_logger("app")


def create_application(argv: list[str] | None = None) -> QApplication:
    """Create and configure the Qt Application instance."""
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        app = QApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setWindowIcon(create_app_icon(64))
    return app


def run_app(argv: list[str] | None = None) -> int:
    """Bootstrap directories, logging, settings and launch the MainWindow."""
    app = create_application(argv)

    # 1. First-run user storage check
    try:
        data_dir, logs_dir = ensure_app_directories()
    except StorageError as err:
        logger.critical("Kritieke fout bij toegang tot gebruikersdatamap: %s", err)
        msg = (
            "OpenVideo Downloader kan niet starten omdat de gebruikersdatamap "
            f"niet toegankelijk of schrijfbaar is:\n\n{err}"
        )
        QMessageBox.critical(None, "Opslagfout bij opstarten", msg)
        return 1

    # 2. Centralized logging setup
    settings_manager = SettingsManager()
    initial_log_level = settings_manager.get().log_level
    setup_logging(level=initial_log_level, custom_logs_dir=logs_dir)

    logger.info("OpenVideo Downloader gestart (data_dir='%s').", data_dir)

    # 3. MainWindow initialization & display
    window = MainWindow(settings_manager)
    window.show()

    return app.exec()
