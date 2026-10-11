"""Application bootstrap and lifecycle management."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget

from open_video_downloader import __version__


class MainWindow(QMainWindow):
    """Initial placeholder window for Phase 1 environment verification."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"OpenVideo Downloader v{__version__} (Phase 1 Initial)")
        self.resize(700, 450)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel(
            f"OpenVideo Downloader v{__version__}\n\n"
            "Fase 1: Architectuur & Basisstructuur geïnitialiseerd.\n"
            "Klaar voor Fase 2: UI Foundation & Thema's.",
            self,
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        self.setCentralWidget(central)


def create_application(argv: list[str] | None = None) -> QApplication:
    """Create and configure the Qt Application instance."""
    app = QApplication(argv or sys.argv)
    app.setApplicationName("OpenVideo Downloader")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("OpenVideo")
    return app
