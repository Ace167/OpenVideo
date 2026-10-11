"""Unit tests for logger setup, log rotation and sensitive data redaction."""

import getpass
from pathlib import Path

from open_video_downloader.services.logger import (
    SensitiveDataFilter,
    get_logger,
    setup_logging,
)


def test_sensitive_data_filter_tokens():
    """Verify bearer tokens and API keys in strings are redacted."""
    filter_obj = SensitiveDataFilter()

    # Bearer token
    msg = "Sending request with header Authorization: Bearer abcdef1234567890xyz"
    redacted = filter_obj.redact(msg)
    assert "[REDACTED_TOKEN]" in redacted
    assert "abcdef1234567890xyz" not in redacted

    # Query params
    url_msg = (
        "Fetching media from https://video.cdn.com/play?token=secret123&api_key=priv987&res=1080"
    )
    redacted_url = filter_obj.redact(url_msg)
    assert "token=[REDACTED]" in redacted_url
    assert "api_key=[REDACTED]" in redacted_url
    assert "secret123" not in redacted_url
    assert "priv987" not in redacted_url
    assert "res=1080" in redacted_url


def test_sensitive_data_filter_cookies():
    """Verify cookie headers are redacted."""
    filter_obj = SensitiveDataFilter()
    msg = "Setting cookie header: Cookie: session_id=123456789; auth=token_value"
    redacted = filter_obj.redact(msg)
    assert "Cookie: [REDACTED_COOKIE]" in redacted
    assert "session_id=123456789" not in redacted


def test_sensitive_data_filter_username_in_paths():
    """Verify local user name in Windows/POSIX paths is redacted."""
    current_user = getpass.getuser()
    if not current_user:
        return

    filter_obj = SensitiveDataFilter()
    path_msg = f"Writing temporary file to C:\\Users\\{current_user}\\AppData\\Local\\temp.tmp"
    redacted = filter_obj.redact(path_msg)
    assert f"\\Users\\{current_user}\\" not in redacted
    assert "\\Users\\[USER]\\" in redacted


def test_logger_setup_and_record_filtering(tmp_path: Path):
    """Verify setup_logging writes to file and applies sensitive data filter to log records."""
    logs_dir = tmp_path / "logs"
    setup_logging(level="DEBUG", custom_logs_dir=logs_dir)

    test_logger = get_logger("test_module")
    test_logger.info("Connecting with token=super_secret_token_123 to host")

    log_file = logs_dir / "openvideo.log"
    assert log_file.exists()

    content = log_file.read_text(encoding="utf-8")
    assert "token=[REDACTED]" in content
    assert "super_secret_token_123" not in content
