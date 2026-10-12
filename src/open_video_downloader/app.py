"""Application bootstrap, lifecycle and main window initialization."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
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
    """Create and configure the Qt Application instance with crisp DPI scaling."""
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance()
    if not isinstance(app, QApplication):
        app = QApplication(argv or sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_ORGANIZATION)
    app.setWindowIcon(create_app_icon(64))
    app.setFont(QFont("Segoe UI", 10))
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

    # 3. Internationalization (i18n) setup
    from open_video_downloader.services.i18n import normalize_language_code, set_language
    from open_video_downloader.settings.models import AppSettings

    raw_args = argv if argv is not None else sys.argv
    cli_lang: str | None = None
    for idx, arg in enumerate(raw_args):
        if arg in ("--lang", "--language") and idx + 1 < len(raw_args):
            cli_lang = raw_args[idx + 1]
            break

    if cli_lang:
        norm_lang = normalize_language_code(cli_lang)
        set_language(norm_lang)
        current = settings_manager.get()
        if current.language != norm_lang:
            updated_settings = AppSettings(
                download_dir=current.download_dir,
                theme=current.theme,
                language=norm_lang,
                notifications_enabled=current.notifications_enabled,
                log_level=current.log_level,
                max_concurrent_downloads=current.max_concurrent_downloads,
            )
            settings_manager.save_settings(updated_settings)
    else:
        set_language(settings_manager.get().language)

    logger.info(
        "OpenVideo Downloader gestart (data_dir='%s', language='%s').",
        data_dir,
        settings_manager.get().language,
    )

    # 3. Database and Queue initialization
    from open_video_downloader.core.queue_manager import QueueManager
    from open_video_downloader.database.manager import DatabaseManager

    db_manager = DatabaseManager(data_dir / "openvideo.db")
    queue_manager = QueueManager(max_concurrent=settings_manager.get().max_concurrent_downloads)

    # 4. MainWindow initialization & display
    window = MainWindow(
        settings_manager=settings_manager,
        queue_manager=queue_manager,
        database_manager=db_manager,
    )
    window.show()

    return app.exec()
