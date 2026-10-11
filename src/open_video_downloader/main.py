"""Entry point for OpenVideo Downloader."""

import sys

from open_video_downloader.app import MainWindow, create_application


def main() -> int:
    """Main execution entry point."""
    app = create_application(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
