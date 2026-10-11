# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added
- Phase 5 release readiness, Windows installer and GitHub publication:
  - PyInstaller one-folder specification (`open_video_downloader.spec`) bundling PySide6, yt-dlp, and assets with windowed execution (`--noconsole`) and custom Windows icon.
  - Inno Setup 6 installer script (`installer/open_video_downloader.iss`) producing `OpenVideoDownloader-Setup-v0.1.0.exe` with Dutch/English wizards, Start Menu shortcuts, and safe uninstaller preserving user data and downloads.
  - Automated local build script (`scripts/build_windows.py`) and headless frozen binary smoke test (`scripts/smoke_test_binary.py`).
  - GitHub Actions CI workflow (`.github/workflows/ci.yml`) running full linting, type checks, tests, Windows build, and artifact uploads.
  - GitHub Actions Release workflow (`.github/workflows/release.yml`) automating release assets, portable ZIP generation, and SHA256 checksums.
  - GitHub community assets: issue templates (`bug_report.md`, `feature_request.md`), pull request template (`pull_request_template.md`), and release guide (`docs/RELEASE_GUIDE.md`).
  - Module entry point (`open_video_downloader/__main__.py`) enabling `python -m open_video_downloader`.
  - About view and status bar integration with unified FFmpeg probe and educational guidance card.
  - Packaging and metadata unit tests (72 passing tests across the repository).
- Phase 4 download history, SQLite persistence and end-to-end flow completion:
  - SQLite schema migration to version 2 adding dedicated `filename` and `format_resolution` columns with automatic backfilling.
  - Startup recovery routine (`mark_interrupted_tasks`) transitioning abandoned in-flight downloads to `FAILED` with clear interruption explanations.
  - FFmpeg probe enhancement supporting portable application and `bin/` directories alongside system `PATH`.
  - Automatic graceful fallback for "Beste kwaliteit (automatisch)" to single progressive stream (`best[ext=mp4]/best`) when FFmpeg is not installed, preventing download crashes.
  - User-friendly Dutch error translation for missing FFmpeg when separate DASH audio/video stream merging is requested without FFmpeg installed.
  - Comprehensive history querying API (`query_history`, `count_history`, `total_history_count`) with parameterized multi-attribute search (title, filename, URL), status filtering, and sorting.
  - Full-featured `HistoryPage` interface with real-time card list, authentic empty state, no-results state with filter reset, and individual/batch deletion.
  - Safe file and destination directory opening verifying filesystem existence prior to launching default desktop tools.
  - Real-time `MainWindow` synchronization connecting completion, failure, and cancellation signals directly to SQLite and UI history cards.
  - Modal confirmation exit handler saving in-flight active downloads as cancelled in SQLite prior to application termination.
  - Expanded unit and UI test suite (68 passing tests across the repository).
- Phase 3 download engine and queue management foundation:
  - yt-dlp adapter with typed domain errors, robust progress hooks, and metadata extraction.
  - Asynchronous background workers (`MetadataWorker`, `DownloadWorker`) keeping GUI responsive.
  - FFmpeg probe utility for detecting installation and post-processing stream muxing needs.
  - Thread-safe `QueueManager` controlling concurrency, validated status transitions, cancellations and retries.
  - SQLite database persistence (`DatabaseManager`) with schema migrations and task history storage.
  - Interactive `DownloadPage` format selection, thumbnail previewing, and folder destination picking.
  - Real-time `QueuePage` cards featuring live progress, transfer speeds, ETA and task action buttons.
  - `MainWindow` lifecycle orchestration and modal confirmation protection on window exit during active downloads.
  - Comprehensive unit and UI test suite additions (53 tests passing across the project).
- Phase 2 desktop interface foundation with modern Windows 11 styling.
- Navigation rail with Downloaden, Wachtrij, Geschiedenis, Instellingen, and Over pages.
- Dynamic theme switching supporting System, Dark, and Light themes.
- Persistent settings management with JSON storage in user data directory and atomic disk writes.
- Centralized rotating logger with sensitive data redaction filter (tokens, cookies, passwords, usernames).
- First-run check validating write permissions in the local user data directory.
- Clear, authentic empty states on all views without misleading mock data.
- System diagnostics report generation with clipboard copy and user privacy redaction.
- Strict type annotations validated with Mypy (`disallow_untyped_defs = true`).
- Comprehensive unit and UI test suite covering navigation, settings, paths, logger and themes.
- Project architectural scaffolding and repository structure (Phase 1).
