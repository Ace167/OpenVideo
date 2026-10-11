"""Unit tests for internationalization (i18n) translation and locale switching."""

import pytest

from open_video_downloader.core.models import FormatOption, TaskStatus
from open_video_downloader.services.i18n import (
    get_language,
    normalize_language_code,
    register_language_listener,
    set_language,
    tr,
    unregister_language_listener,
)


@pytest.fixture(autouse=True)
def reset_i18n_language() -> None:
    """Ensure tests run in clean Dutch state and reset afterwards."""
    set_language("nl")
    yield
    set_language("nl")


def test_normalize_language_code() -> None:
    """Test normalization of language names and codes."""
    assert normalize_language_code("en") == "en"
    assert normalize_language_code("EN") == "en"
    assert normalize_language_code("english") == "en"
    assert normalize_language_code("English") == "en"
    assert normalize_language_code("eng") == "en"

    assert normalize_language_code("nl") == "nl"
    assert normalize_language_code("NL") == "nl"
    assert normalize_language_code("dutch") == "nl"
    assert normalize_language_code("Dutch") == "nl"
    assert normalize_language_code("nld") == "nl"

    # Unsupported or arbitrary fallback to default
    assert normalize_language_code("de") == "nl"
    assert normalize_language_code("unknown_val") == "nl"


def test_set_and_get_language() -> None:
    """Test setting active language and listener triggers."""
    called: list[str] = []

    def on_change() -> None:
        called.append(get_language())

    register_language_listener(on_change)
    try:
        assert get_language() == "nl"
        set_language("en")
        assert get_language() == "en"
        assert called == ["en"]

        # Setting same language does not trigger listeners again
        set_language("en")
        assert len(called) == 1

        set_language("nl")
        assert get_language() == "nl"
        assert called == ["en", "nl"]
    finally:
        unregister_language_listener(on_change)


def test_translation_lookups() -> None:
    """Test tr() translation lookup and formatting in both Dutch and English."""
    set_language("nl")
    assert tr("nav.downloads") == "Downloaden"
    assert tr("nav.settings") == "Instellingen"
    assert tr("status.task_enqueued", title="Muziek") == "Download toegevoegd: Muziek"

    set_language("en")
    assert tr("nav.downloads") == "Downloads"
    assert tr("nav.settings") == "Settings"
    assert tr("status.task_enqueued", title="Music") == "Download added: Music"

    # Fallback to key or default for unknown key
    assert tr("non.existent.key") == "non.existent.key"
    assert tr("non.existent.key", default="Fallback") == "Fallback"


def test_task_status_localized_label() -> None:
    """Test TaskStatus.label property changes according to active language."""
    set_language("nl")
    assert TaskStatus.WAITING.label == "In wachtrij"
    assert TaskStatus.COMPLETED.label == "Voltooid"
    assert TaskStatus.DOWNLOADING.label == "Downloaden..."

    set_language("en")
    assert TaskStatus.WAITING.label == "In queue"
    assert TaskStatus.COMPLETED.label == "Completed"
    assert TaskStatus.DOWNLOADING.label == "Downloading..."


def test_format_option_localized_ffmpeg_tag() -> None:
    """Test FormatOption display label includes localized FFmpeg requirement."""
    fmt = FormatOption(
        format_id="137+140",
        ext="mp4",
        resolution="1080p",
        filesize=50000000,
        requires_ffmpeg=True,
    )

    set_language("nl")
    assert "[Vereist FFmpeg]" in fmt.display_label

    set_language("en")
    assert "[Requires FFmpeg]" in fmt.display_label
