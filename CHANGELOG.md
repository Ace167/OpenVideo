# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added
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
