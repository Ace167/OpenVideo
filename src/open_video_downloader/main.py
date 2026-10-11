"""Entry point for OpenVideo Downloader."""

import sys

from open_video_downloader.app import run_app


def main() -> int:
    """Main execution entry point."""
    return run_app(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
