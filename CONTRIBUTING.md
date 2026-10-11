# Contributing to OpenVideo Downloader

Thank you for your interest in contributing to OpenVideo Downloader!

## Code of Conduct

Please be respectful, constructive, and collaborative in all communications.

## Development Workflow

1. Fork and clone the repository.
2. Set up the local virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```
3. Create a descriptive feature branch:
   ```powershell
   git checkout -b feature/your-feature-name
   ```
4. Adhere to code quality standards:
   - Run `ruff check .` and `ruff format .` before committing.
   - Write tests for new functionality under `tests/`.
   - Ensure all tests pass: `pytest`.
5. Submit a pull request with a clear description of changes.

## Architectural Guidelines

- **No heavy work on the Qt UI thread:** Network calls, metadata probing, and downloads must run via background workers (`QThread` / `QRunnable`).
- **Controlled adapters:** Access `yt-dlp` exclusively through dedicated engine adapters, never via unvalidated shell string concatenation.
- **Privacy first:** Never collect telemetry or transmit private information. Redact sensitive user data in logs.
