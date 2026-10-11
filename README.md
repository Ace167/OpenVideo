# OpenVideo Downloader

OpenVideo Downloader is an open-source, desktop media download manager for Windows built with Python, PySide6 (Qt), and yt-dlp.

> **Disclaimer:** OpenVideo Downloader is an independent, community-driven project and is not affiliated with, endorsed by, or associated with YouTube, Google, or any other media hosting platform. Users are responsible for complying with applicable laws, copyright regulations, and the terms of service of the content platforms they access.

---

## Features (Roadmap)

- **Modern Windows 11 UI:** Native look-and-feel with dark and light theme support using PySide6.
- **Robust Media Extraction:** Powered by `yt-dlp` for accurate format probing and downloads.
- **Concurrent Download Queue:** Configurable parallelism, speed monitoring, progress tracking, and retry mechanisms.
- **Local Persistence:** SQLite database for download history and task state management.
- **Zero Cloud Dependence:** Works entirely locally with no external tracking or telemetry.

---

## Tech Stack

- **Language:** Python 3.12+ (tested with Python 3.14 / PySide6 6.12 ABI3)
- **GUI Framework:** PySide6 (Qt 6)
- **Download Engine:** yt-dlp
- **Media Processing:** FFmpeg / FFprobe
- **Database:** SQLite 3
- **Test Runner:** pytest & pytest-qt
- **Linter & Formatter:** Ruff

---

## Getting Started

### Prerequisites

- Windows 10 / 11 (x64)
- Python 3.12 or newer installed (`py` launcher available)
- FFmpeg on PATH (required for merging audio/video streams)

### Development Setup

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/<your-username>/open-video-downloader.git
   cd open-video-downloader
   ```

2. **Create a virtual environment:**
   ```powershell
   py -m venv .venv
   ```

3. **Activate the environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. **Install development dependencies and editable package:**
   ```powershell
   pip install -e ".[dev]"
   ```

5. **Run tests, type checks & code quality checks:**
   ```powershell
   pytest
   ruff check .
   ruff format --check .
   mypy src
   ```

6. **Launch the application:**
   ```powershell
   open-video-downloader
   # or:
   python -m open_video_downloader.main
   ```

---

## Project Structure

```text
src/open_video_downloader/
├── app.py              # Application lifecycle and window factory
├── main.py             # CLI entrypoint
├── core/               # Domain entities, queue management, signals
├── database/           # SQLite schema migrations and history storage
├── engines/            # yt-dlp and FFmpeg process adapters
├── resources/          # Icons, stylesheets, and visual assets
├── services/           # Diagnostic utilities, updater service
├── settings/           # Config persistence and validation
└── ui/                 # Qt widgets, pages, dialogs, and components
tests/
├── conftest.py         # Shared fixtures and offscreen Qt setup
├── unit/               # Domain, validation, and database unit tests
├── integration/        # yt-dlp adapter and engine integration tests
└── ui/                 # PySide6 widget and navigation tests
```

---

## License

This project is licensed under the [MIT License](LICENSE). Third-party components and their licenses are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
