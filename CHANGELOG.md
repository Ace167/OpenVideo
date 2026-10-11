# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added
- Phase 4 download history, SQLite persistence and end-to-end flow completion:
  - SQLite schema migration to version 2 adding dedicated `filename` and `format_resolution` columns with automatic backfilling.
  - Startup recovery routine (`mark_interrupted_tasks`) transitioning abandoned in-flight downloads to `FAILED` with clear interruption explanations.
  - Comprehensive history querying API (`query_history`, `count_history`, `total_history_count`) with parameterized multi-attribute search (title, filename, URL), status filtering, and sorting.
  - Full-featured `HistoryPage` interface with real-time card list, authentic empty state, no-results state with filter reset, and individual/batch deletion.
  - Safe file and destination directory opening verifying filesystem existence prior to launching default desktop tools.
  - Real-time `MainWindow` synchronization connecting completion, failure, and cancellation signals directly to SQLite and UI history cards.
  - Modal confirmation exit handler saving in-flight active downloads as cancelled in SQLite prior to application termination.
  - Expanded unit and UI test suite (65 passing tests across the repository).
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
