"""Centralized application logging with sensitive data redaction and log rotation."""

import getpass
import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from open_video_downloader.core.paths import ensure_app_directories

_ROOT_LOGGER_NAME = "open_video_downloader"


class SensitiveDataFilter(logging.Filter):
    """Filter that intercepts log messages to redact private and sensitive information."""

    def __init__(self) -> None:
        super().__init__()
        # Redaction patterns
        self._patterns: list[tuple[re.Pattern[str], str]] = [
            # Authorization tokens / Bearer headers
            (
                re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{8,}", re.IGNORECASE),
                r"\1[REDACTED_TOKEN]",
            ),
            # API keys and secret query parameters
            (
                re.compile(
                    r"(?i)(api[_-]?key|token|auth|secret|password|passwd|pwd)=([^\s&]+)",
                    re.IGNORECASE,
                ),
                r"\1=[REDACTED]",
            ),
            # Cookies
            (re.compile(r"(?i)(cookie:\s*)[^\r\n;]+", re.IGNORECASE), r"\1[REDACTED_COOKIE]"),
        ]

        # Current username redaction in local Windows paths (C:\Users\<username>)
        try:
            current_user = getpass.getuser()
            if current_user and len(current_user) > 2:
                # Match path structures with username
                user_pattern = re.compile(
                    rf"([\\/][Uu]sers[\\/]){re.escape(current_user)}([\\/])",
                    re.IGNORECASE,
                )
                self._patterns.append((user_pattern, r"\1[USER]\2"))
        except Exception:
            pass

    def redact(self, text: str) -> str:
        """Sanitize a text string by replacing matches of sensitive patterns."""
        sanitized = text
        for pattern, replacement in self._patterns:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and sanitize the LogRecord in-place."""
        if isinstance(record.msg, str):
            record.msg = self.redact(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self.redact(str(v)) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self.redact(str(a)) if isinstance(a, str) else a for a in record.args
                )
        return True


def setup_logging(
    level: str = "INFO",
    custom_logs_dir: Path | None = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> logging.Logger:
    """Configure the root application logger with console and rotating file output.

    Thread-safe and idempotent: avoids adding duplicate handlers if called multiple times.
    """
    logger = logging.getLogger(_ROOT_LOGGER_NAME)
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    # If handlers already configured, simply update log level
    if logger.handlers:
        for handler in logger.handlers:
            handler.setLevel(numeric_level)
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] (%(threadName)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    redaction_filter = SensitiveDataFilter()

    # Console Handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(redaction_filter)
    logger.addHandler(console_handler)

    # Rotating File Handler
    try:
        if custom_logs_dir is None:
            _, logs_dir = ensure_app_directories()
        else:
            logs_dir = custom_logs_dir
            logs_dir.mkdir(parents=True, exist_ok=True)

        log_file = logs_dir / "openvideo.log"
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(redaction_filter)
        logger.addHandler(file_handler)
    except Exception as err:
        logger.warning(
            "Kon roterend logbestand niet initialiseren (%s). Logging alleen naar console.", err
        )

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger child under the application root logger."""
    if not name or name == _ROOT_LOGGER_NAME:
        return logging.getLogger(_ROOT_LOGGER_NAME)
    return logging.getLogger(f"{_ROOT_LOGGER_NAME}.{name}")
