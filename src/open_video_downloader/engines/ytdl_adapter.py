"""Adapter for yt-dlp Python API with structured errors, format sorting and hooks."""

import re
import urllib.parse
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp
from yt_dlp.utils import DownloadCancelled, DownloadError, ExtractorError

from open_video_downloader.core.models import (
    FormatOption,
    MediaMetadata,
    format_duration,
)
from open_video_downloader.services.logger import get_logger

logger = get_logger("engines.ytdl_adapter")


class EngineError(Exception):
    """Base exception for all download engine failures."""


class InvalidUrlError(EngineError):
    """Raised when URL syntax is malformed or platform extractor is not supported."""


class MediaUnavailableError(EngineError):
    """Raised when media is deleted, private, geo-blocked or age-restricted."""


class NetworkTimeoutError(EngineError):
    """Raised when network connection drops, DNS fails or request times out."""


class DownloadCancelledError(EngineError):
    """Raised when a download operation was terminated by the user."""


def is_valid_url(url: str) -> bool:
    """Validate whether input is a syntactically plausible web media URL."""
    if not url or not isinstance(url, str):
        return False
    url_clean = url.strip()
    try:
        parsed = urllib.parse.urlparse(url_clean)
        return bool(parsed.scheme in ("http", "https") and parsed.netloc and "." in parsed.netloc)
    except Exception:
        return False


def _parse_formats(raw_formats: list[dict[str, Any]]) -> list[FormatOption]:
    """Parse, filter and sort raw yt-dlp format dictionaries into user-friendly options."""
    results: list[FormatOption] = []
    seen_resolutions: set[str] = set()

    # 1. Best Quality (Automatic)
    results.append(
        FormatOption(
            format_id="bestvideo+bestaudio/best",
            ext="mp4",
            resolution="Beste kwaliteit (automatisch)",
            requires_ffmpeg=True,
            note="Combineert de hoogste video- en audiostream",
        )
    )

    # Filter out storyboards / invalid formats
    valid_raw: list[dict[str, Any]] = []
    for f in raw_formats:
        fmt_id = str(f.get("format_id", ""))
        vcodec = str(f.get("vcodec", "none"))
        acodec = str(f.get("acodec", "none"))
        ext = str(f.get("ext", "")).lower()

        if ext in ("mhtml", "none") or "storyboard" in fmt_id or "sb" in fmt_id:
            continue
        if vcodec == "none" and acodec == "none":
            continue
        valid_raw.append(f)

    # Sort video formats by height descending
    video_raw = [f for f in valid_raw if f.get("vcodec") != "none"]
    video_raw.sort(key=lambda x: (x.get("height") or 0, x.get("tbr") or 0), reverse=True)

    for f in video_raw:
        height = f.get("height")
        if not height:
            continue
        res_str = f"{height}p"
        vcodec = str(f.get("vcodec", "none"))
        acodec = str(f.get("acodec", "none"))
        is_video_only = acodec == "none"
        ext = str(f.get("ext", "mp4"))
        filesize = f.get("filesize")
        filesize_approx = f.get("filesize_approx")

        # Dedup resolutions to present clean resolution choices to the user
        key = f"{res_str}_{ext}"
        if key in seen_resolutions:
            continue
        seen_resolutions.add(key)

        format_id = f"{f['format_id']}+bestaudio/best" if is_video_only else str(f["format_id"])
        requires_ffmpeg = is_video_only

        results.append(
            FormatOption(
                format_id=format_id,
                ext=ext,
                resolution=res_str,
                filesize=filesize,
                filesize_approx=filesize_approx,
                vcodec=vcodec,
                acodec=acodec,
                fps=f.get("fps"),
                tbr=f.get("tbr"),
                is_audio_only=False,
                is_video_only=is_video_only,
                requires_ffmpeg=requires_ffmpeg,
                note=f.get("format_note", ""),
            )
        )

    # 2. Audio-only options
    audio_raw = [f for f in valid_raw if f.get("vcodec") == "none" and f.get("acodec") != "none"]
    audio_raw.sort(key=lambda x: (x.get("abr") or 0, x.get("tbr") or 0), reverse=True)

    # Best audio shortcut
    results.append(
        FormatOption(
            format_id="bestaudio/best",
            ext="m4a",
            resolution="Audio",
            is_audio_only=True,
            requires_ffmpeg=False,
            note="Hoogste beschikbare geluidskwaliteit",
        )
    )

    seen_audio_exts: set[str] = set()
    for f in audio_raw:
        ext = str(f.get("ext", "m4a"))
        if ext in seen_audio_exts:
            continue
        seen_audio_exts.add(ext)

        results.append(
            FormatOption(
                format_id=str(f["format_id"]),
                ext=ext,
                resolution="Audio",
                filesize=f.get("filesize"),
                filesize_approx=f.get("filesize_approx"),
                vcodec="none",
                acodec=str(f.get("acodec", "none")),
                is_audio_only=True,
                requires_ffmpeg=False,
                note=f.get("format_note", ""),
            )
        )

    return results


def extract_metadata(url: str, cancel_check: Callable[[], bool] | None = None) -> MediaMetadata:
    """Extract media metadata using yt-dlp Python API with structured error handling."""
    if not is_valid_url(url):
        raise InvalidUrlError(f"Ongeldige of niet-ondersteunde URL: '{url}'")

    ydl_opts: dict[str, Any] = {
        "extract_flat": False,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 15,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if cancel_check and cancel_check():
                raise DownloadCancelledError("Extractie geannuleerd.")

            info = ydl.extract_info(url, download=False)
            if not info:
                raise MediaUnavailableError("Geen media-informatie ontvangen van de bron.")

            # Resolve if playlist or multiple entries
            if info.get("entries"):
                entries = list(info["entries"])
                if entries:
                    info = entries[0]

            duration = info.get("duration")
            raw_formats = info.get("formats", [])
            parsed_formats = _parse_formats(raw_formats)

            metadata = MediaMetadata(
                url=url,
                extractor=info.get("extractor", "Generic"),
                id=str(info.get("id", "")),
                title=str(info.get("title", "Naamloos")).strip(),
                description=str(info.get("description", "")).strip(),
                duration=duration,
                duration_str=format_duration(duration),
                thumbnail_url=str(info.get("thumbnail", "")),
                uploader=str(info.get("uploader", "")),
                view_count=info.get("view_count"),
                formats=parsed_formats,
            )
            logger.info(
                "Metadata succesvol opgehaald voor '%s' (ID: %s).", metadata.title, metadata.id
            )
            return metadata

    except DownloadCancelledError:
        raise
    except DownloadError as err:
        err_msg = str(err)
        logger.warning("yt-dlp DownloadError: %s", err_msg)
        if any(
            term in err_msg.lower()
            for term in ["private", "unavailable", "sign in", "confirm your age"]
        ):
            raise MediaUnavailableError(
                "De video is niet beschikbaar (privé, verwijderd of leeftijdsbeperkt)."
            ) from err
        if any(
            term in err_msg.lower()
            for term in ["timeout", "timed out", "getaddrinfo", "nameresolutionerror"]
        ):
            raise NetworkTimeoutError("Verbinding met de host is mislukt of getimed-out.") from err
        if "is not a valid url" in err_msg.lower() or "unsupported url" in err_msg.lower():
            raise InvalidUrlError(
                "Deze URL wordt niet ondersteund door de downloadengine."
            ) from err
        raise EngineError(f"Fout bij ophalen van media-informatie: {err_msg}") from err
    except ExtractorError as err:
        logger.warning("yt-dlp ExtractorError: %s", err)
        raise EngineError(f"Extractor-fout bij verwerken van media: {err}") from err
    except Exception as err:
        logger.error("Onverwachte fout tijdens extractie van '%s': %s", url, err)
        raise EngineError(f"Onverwachte systeemfout tijdens verwerking: {err}") from err


def execute_download(
    url: str,
    target_dir: Path,
    format_id: str,
    progress_callback: Callable[[dict[str, Any]], None],
    cancel_check: Callable[[], bool] | None = None,
) -> Path:
    """Download video/audio to target directory using yt-dlp with progress hook."""
    target_dir.mkdir(parents=True, exist_ok=True)

    # Safe filename template (limiting title to 100 chars to avoid Windows 260-char path limits)
    outtmpl = str(target_dir / "%(title).100B [%(id)s].%(ext)s")

    def internal_hook(d: dict[str, Any]) -> None:
        if cancel_check and cancel_check():
            raise DownloadCancelled("Download geannuleerd door gebruiker.")
        progress_callback(d)

    ydl_opts: dict[str, Any] = {
        "outtmpl": outtmpl,
        "format": format_id,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "continuedl": True,
        "socket_timeout": 20,
        "progress_hooks": [internal_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise MediaUnavailableError("Download voltooid maar geen media-info geretourneerd.")

            # Determine the generated file path
            filename = ydl.prepare_filename(info)
            final_path = Path(filename)
            # In case postprocessors merged into another extension (e.g. mkv -> mp4)
            if not final_path.exists():
                stem = final_path.stem
                parent = final_path.parent
                candidates = list(parent.glob(f"{re.escape(stem)}.*"))
                if candidates:
                    final_path = candidates[0]

            logger.info("Download succesvol afgerond: '%s'.", final_path)
            return final_path

    except DownloadCancelled as err:
        logger.info("Download van '%s' is geannuleerd door gebruiker.", url)
        raise DownloadCancelledError("Download is geannuleerd door gebruiker.") from err
    except DownloadError as err:
        err_msg = str(err)
        logger.warning("yt-dlp downloadfout voor '%s': %s", url, err_msg)
        if any(term in err_msg.lower() for term in ["timeout", "timed out", "connection reset"]):
            raise NetworkTimeoutError("Verbinding verbroken tijdens downloaden.") from err
        raise EngineError(f"Fout tijdens het downloaden: {err_msg}") from err
    except Exception as err:
        logger.error("Onverwachte downloadfout voor '%s': %s", url, err)
        raise EngineError(f"Onverwachte systeemfout tijdens download: {err}") from err
