"""Basic UI initialization and window presentation test."""

from open_video_downloader.app import MainWindow


def test_main_window_creation(qtbot):
    """Verify MainWindow can be instantiated and shown in the Qt event loop."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.isVisible()
    assert "OpenVideo Downloader" in window.windowTitle()
