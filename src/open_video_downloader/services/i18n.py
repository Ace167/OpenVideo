"""Internationalization (i18n) translation service for OpenVideo Downloader."""

from collections.abc import Callable

from open_video_downloader.core.constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

# Translation dictionaries for Dutch (nl) and English (en)
TRANSLATIONS: dict[str, dict[str, str]] = {
    "nl": {
        # Navigation
        "nav.downloads": "Downloaden",
        "nav.queue": "Wachtrij",
        "nav.history": "Geschiedenis",
        "nav.settings": "Instellingen",
        "nav.about": "Over",
        # Status Bar
        "status.ready": "Gereed",
        "status.ffmpeg_available": "FFmpeg: Beschikbaar",
        "status.ffmpeg_missing": "FFmpeg: Niet gedetecteerd",
        "status.theme": "Thema: {theme}",
        "status.page_opened": "Pagina geopend: {page}",
        "status.task_enqueued": "Download toegevoegd: {title}",
        "status.task_duplicate": "Taak is al actief in de wachtrij.",
        "status.task_completed": "✓ Download voltooid: {title}",
        "status.task_failed": "⚠ Download mislukt: {title}",
        "status.task_cancelled": "✕ Download geannuleerd: {title}",
        # Exit dialog
        "exit.title": "Actieve downloads annuleren?",
        "exit.prompt": (
            "Er zijn nog {count} actieve download(s) bezig. "
            "Weet u zeker dat u wilt afsluiten en deze downloads wilt annuleren?"
        ),
        "exit.cancelled_reason": "Geannuleerd wegens afsluiten van de applicatie.",
        # Download Page
        "download.header_title": "Download video of audio",
        "download.header_sub": (
            "Voer een weblink in om mediagegevens op te halen en downloads te starten."
        ),
        "download.input_placeholder": "Plak een video- of audio-URL (bijv. https://...)",
        "download.btn_paste": "Plakken",
        "download.btn_fetch": "Informatie ophalen",
        "download.btn_loading": "Laden...",
        "download.fetching_status": "Informatie en formaten ophalen via engine...",
        "download.err_empty_url": "Voer eerst een geldige URL in.",
        "download.err_invalid_url": "De opgegeven URL heeft geen geldige HTTP- of HTTPS-indeling.",
        "download.empty_title": "Geen media geladen",
        "download.empty_desc": (
            "Voer hierboven een geldige media-URL in en klik op 'Informatie ophalen'\n"
            "om resoluties, kwaliteiten en audio-opties te selecteren."
        ),
        "download.meta_duration": "Duur: {duration} • Bron: {extractor}",
        "download.meta_uploader": " • Maker: {uploader}",
        "download.format_label": "Beschikbare formaten & kwaliteit:",
        "download.dir_label": "Opslaan in:",
        "download.btn_browse": "Bladeren...",
        "download.browse_dialog": "Kies downloadmap",
        "download.btn_enqueue": "Download starten",
        "download.btn_go_to_queue": "Bekijk wachtrij →",
        "download.enqueue_success": "✓ Taak toegevoegd aan wachtrij!",
        "download.folder_create_error": "Doelmap kon niet worden aangemaakt: {err}",
        "download.ffmpeg_warning": (
            "⚠️ Let op: Dit formaat vereist FFmpeg om de gescheiden video- en audiostream "
            "samen te voegen. FFmpeg is niet gedetecteerd op uw systeem."
        ),
        "download.ffmpeg_fallback_note": (
            "💡 Zonder FFmpeg schakelt 'Beste kwaliteit' automatisch terug "
            "naar een enkele stream met beeld en geluid."
        ),
        # Queue Page
        "queue.header_title": "Wachtrij",
        "queue.header_sub": "Overzicht van actieve en wachtende downloadtaken.",
        "queue.btn_cancel_all": "Alle actieve annuleren",
        "queue.empty_title": "De downloadwachtrij is leeg",
        "queue.empty_sub": (
            "Er worden momenteel geen media gedownload.\n"
            "Taken die u toevoegt via het downloadscherm verschijnen hier direct "
            "met hun actieve voortgang."
        ),
        "queue.status.waiting": "In de wachtrij",
        "queue.status.downloading": "Downloaden...",
        "queue.status.processing": "Verwerken...",
        "queue.status.completed": "Voltooid",
        "queue.status.failed": "Mislukt",
        "queue.status.cancelled": "Geannuleerd",
        "queue.btn_cancel": "Annuleren",
        "queue.btn_retry": "Opnieuw proberen",
        "queue.stats_completed": "Voltooid ({size})",
        "queue.stats_failed": "Mislukt: {err}",
        "queue.stats_cancelled": "Geannuleerd door gebruiker",
        "queue.stats_processing": "Bezig met samenvoegen van audio en video...",
        "queue.stats_downloading": "{progress:.1f}% van {total} ({downloaded}) • {speed}",
        "queue.stats_waiting": "Wachten op beurt in de wachtrij...",
        "queue.item_format_info": "Formaat: {format} • Doel: {target}",
        # History Page
        "history.header_title": "Geschiedenis",
        "history.header_sub": "Lokaal opgeslagen geschiedenis van voltooide en verwerkte media.",
        "history.search_placeholder": "Zoeken op titel, bestandsnaam of URL...",
        "history.filter_all": "Alle statussen",
        "history.filter_completed": "Voltooid",
        "history.filter_failed": "Mislukt",
        "history.filter_cancelled": "Geannuleerd",
        "history.sort_newest": "Nieuwste eerst",
        "history.sort_oldest": "Oudste eerst",
        "history.sort_title": "Titel (A-Z)",
        "history.sort_size": "Bestandsgrootte",
        "history.btn_clear": "Geschiedenis wissen",
        "history.clear_confirm_title": "Geschiedenis wissen?",
        "history.clear_confirm_text": (
            "Weet u zeker dat u de volledige downloadgeschiedenis wilt wissen?\n\n"
            "De gedownloade mediabestanden op uw schijf blijven intact."
        ),
        "history.empty_title": "Nog geen geschiedenis",
        "history.empty_sub": (
            "Wanneer downloads zijn afgerond, worden de bron-URL, titel, bestandsgrootte\n"
            "en doelmap hier bewaard in de lokale database."
        ),
        "history.no_results_title": "Geen resultaten gevonden",
        "history.no_results_sub": (
            "Er zijn geen downloads gevonden die voldoen aan uw zoekterm of geselecteerde filters."
        ),
        "history.btn_reset_filters": "Filters wissen",
        "history.btn_open_file": "Bestand openen",
        "history.btn_open_folder": "Map openen",
        "history.btn_delete_item": "Verwijderen",
        "history.file_not_found_title": "Bestand niet gevonden",
        "history.file_not_found_msg": "Het bestand '{path}' bestaat niet meer op schijf.",
        "history.folder_not_found_title": "Map niet gevonden",
        "history.folder_not_found_msg": "De doelmap '{path}' kon niet worden gevonden.",
        "history.item_meta": "Formaat: {format} • Grootte: {size} • Bestand: {file}",
        "history.item_source": "Bron: {url}",
        # Settings Page
        "settings.header_title": "Instellingen",
        "settings.header_sub": (
            "Configureer downloadlocaties, interface-uiterlijk en diagnosevoorkeuren."
        ),
        "settings.sec_general": "Downloads",
        "settings.download_dir": "Standaard downloadmap:",
        "settings.concurrent_downloads": "Maximum aantal gelijktijdige downloads:",
        "settings.sec_appearance": "Interface & Weergave",
        "settings.theme": "Thema:",
        "settings.theme_system": "Systeemthema volgen",
        "settings.theme_dark": "Donker thema",
        "settings.theme_light": "Licht thema",
        "settings.language": "Interfacetaal:",
        "settings.notifications": "Bureaubladmeldingen tonen wanneer een download gereed is",
        "settings.sec_advanced": "Geavanceerd & Diagnose",
        "settings.log_level": "Logniveau:",
        "settings.btn_open_data_dir": "Open gebruikersdatamap",
        "settings.btn_open_logs_dir": "Open logmap",
        "settings.btn_save": "Instellingen opslaan",
        "settings.btn_reset": "Standaardwaarden herstellen",
        "settings.saved_success": "✓ Instellingen succesvol opgeslagen.",
        "settings.saved_error": "Fout bij opslaan van instellingen.",
        "settings.defaults_restored": "✓ Standaardwaarden hersteld.",
        # About Page
        "about.header_title": "OpenVideo Downloader",
        "about.header_sub": "Versie {version} • Open-Source Windows Media Manager",
        "about.sec_diagnostics": "Systeeminformatie & Diagnostiek",
        "about.lbl_app_version": "Applicatieversie:",
        "about.lbl_python": "Python runtime:",
        "about.lbl_pyside": "PySide6 / Qt runtime:",
        "about.lbl_ytdlp": "yt-dlp engine:",
        "about.lbl_sqlite": "SQLite database:",
        "about.lbl_ffmpeg": "FFmpeg status:",
        "about.lbl_data_dir": "Gebruikersdatamap:",
        "about.btn_copy_diag": "Diagnostiek kopiëren",
        "about.btn_open_data_dir": "Gebruikersdatamap openen",
        "about.copy_success": (
            "✓ Diagnostiek gekopieerd naar klembord (gevoelige data geredigeerd)."
        ),
        "about.sec_legal": "Licentie & Verantwoordelijkheid",
        "about.legal_text": (
            "OpenVideo Downloader is een onafhankelijke desktopapplicatie uitgebracht onder "
            "de MIT-licentie.\n\n"
            "Dit project is niet verbonden aan, goedgekeurd door of officieel gelieerd aan "
            "YouTube, Google of enige andere externe mediadienst. De gebruiker is zelf "
            "verantwoordelijk voor rechtmatig gebruik, toepasselijke auteursrechten en de "
            "gebruiksvoorwaarden van bezochte platforms."
        ),
        "about.ffmpeg_notice": (
            "💡 <b>Over FFmpeg & downloadkwaliteit:</b> Hoge resoluties (1080p, 4K) worden door "
            "platforms zoals YouTube gesplitst in losse video- en audiostreams. FFmpeg is nodig "
            "om deze samen te voegen. Zonder FFmpeg downloadt OpenVideo Downloader automatisch "
            "de hoogste beschikbare enkele stream (beeld en geluid gecombineerd) tot 720p.<br>"
            "<i>Optionele installatie:</i> Voer in PowerShell uit: "
            "<code>winget install Gyan.FFmpeg</code> "
            "of plaats <code>ffmpeg.exe</code> in de applicatiemap."
        ),
        "about.ffmpeg_available": "Beschikbaar ({binary})",
        "about.ffmpeg_missing": "Niet gedetecteerd (progressieve formaten beschikbaar)",
        "about.diag_title": "=== OpenVideo Downloader Diagnostiek ===",
        "about.diag_version": "Versie: v{version}",
        "about.diag_ffmpeg": "FFmpeg: {status}",
        "about.diag_datadir": "Datamap: {path}",
        "about.clipboard_unavailable": "Klembord niet beschikbaar.",
    },
    "en": {
        # Navigation
        "nav.downloads": "Downloads",
        "nav.queue": "Queue",
        "nav.history": "History",
        "nav.settings": "Settings",
        "nav.about": "About",
        # Status Bar
        "status.ready": "Ready",
        "status.ffmpeg_available": "FFmpeg: Available",
        "status.ffmpeg_missing": "FFmpeg: Not detected",
        "status.theme": "Theme: {theme}",
        "status.page_opened": "Page opened: {page}",
        "status.task_enqueued": "Download added: {title}",
        "status.task_duplicate": "Task is already active in the queue.",
        "status.task_completed": "✓ Download completed: {title}",
        "status.task_failed": "⚠ Download failed: {title}",
        "status.task_cancelled": "✕ Download cancelled: {title}",
        # Exit dialog
        "exit.title": "Cancel active downloads?",
        "exit.prompt": (
            "There are still {count} active download(s) running. "
            "Are you sure you want to exit and cancel these downloads?"
        ),
        "exit.cancelled_reason": "Cancelled due to application shutdown.",
        # Download Page
        "download.header_title": "Download video or audio",
        "download.header_sub": ("Enter a web link to fetch media information and start downloads."),
        "download.input_placeholder": "Paste a video or audio URL (e.g. https://...)",
        "download.btn_paste": "Paste",
        "download.btn_fetch": "Fetch Information",
        "download.btn_loading": "Loading...",
        "download.fetching_status": "Fetching media information and formats...",
        "download.err_empty_url": "Please enter a valid URL first.",
        "download.err_invalid_url": "The provided URL does not have a valid HTTP or HTTPS format.",
        "download.empty_title": "No media loaded",
        "download.empty_desc": (
            "Enter a valid media URL above and click 'Fetch Information'\n"
            "to select resolutions, qualities, and audio options."
        ),
        "download.meta_duration": "Duration: {duration} • Source: {extractor}",
        "download.meta_uploader": " • Uploader: {uploader}",
        "download.format_label": "Available formats & quality:",
        "download.dir_label": "Save to:",
        "download.btn_browse": "Browse...",
        "download.browse_dialog": "Select download folder",
        "download.btn_enqueue": "Start download",
        "download.btn_go_to_queue": "View Queue →",
        "download.enqueue_success": "✓ Task added to queue!",
        "download.folder_create_error": "Could not create destination folder: {err}",
        "download.ffmpeg_warning": (
            "⚠️ Notice: This format requires FFmpeg to merge separate video and audio streams. "
            "FFmpeg was not detected on your system."
        ),
        "download.ffmpeg_fallback_note": (
            "💡 Without FFmpeg, 'Best quality' automatically falls back "
            "to a single stream with audio and video."
        ),
        # Queue Page
        "queue.header_title": "Queue",
        "queue.header_sub": "Overview of active and pending download tasks.",
        "queue.btn_cancel_all": "Cancel All Active",
        "queue.empty_title": "The download queue is empty",
        "queue.empty_sub": (
            "No media is currently being downloaded.\n"
            "Tasks added from the download screen will appear here immediately "
            "with their live progress."
        ),
        "queue.status.waiting": "In queue",
        "queue.status.downloading": "Downloading...",
        "queue.status.processing": "Processing...",
        "queue.status.completed": "Completed",
        "queue.status.failed": "Failed",
        "queue.status.cancelled": "Cancelled",
        "queue.btn_cancel": "Cancel",
        "queue.btn_retry": "Retry",
        "queue.stats_completed": "Completed ({size})",
        "queue.stats_failed": "Failed: {err}",
        "queue.stats_cancelled": "Cancelled by user",
        "queue.stats_processing": "Merging audio and video streams...",
        "queue.stats_downloading": "{progress:.1f}% of {total} ({downloaded}) • {speed}",
        "queue.stats_waiting": "Waiting in queue...",
        "queue.item_format_info": "Format: {format} • Destination: {target}",
        # History Page
        "history.header_title": "History",
        "history.header_sub": "Locally stored history of completed and processed media.",
        "history.search_placeholder": "Search by title, filename or URL...",
        "history.filter_all": "All statuses",
        "history.filter_completed": "Completed",
        "history.filter_failed": "Failed",
        "history.filter_cancelled": "Cancelled",
        "history.sort_newest": "Newest first",
        "history.sort_oldest": "Oldest first",
        "history.sort_title": "Title (A-Z)",
        "history.sort_size": "File size",
        "history.btn_clear": "Clear History",
        "history.clear_confirm_title": "Clear History?",
        "history.clear_confirm_text": (
            "Are you sure you want to clear all download history?\n\n"
            "Downloaded media files on your drive will remain intact."
        ),
        "history.empty_title": "No history yet",
        "history.empty_sub": (
            "When downloads finish, the source URL, title, file size\n"
            "and destination folder will be saved here in the local database."
        ),
        "history.no_results_title": "No results found",
        "history.no_results_sub": (
            "No downloads found matching your search query or selected filters."
        ),
        "history.btn_reset_filters": "Clear filters",
        "history.btn_open_file": "Open File",
        "history.btn_open_folder": "Open Folder",
        "history.btn_delete_item": "Delete",
        "history.file_not_found_title": "File not found",
        "history.file_not_found_msg": "The file '{path}' no longer exists on disk.",
        "history.folder_not_found_title": "Folder not found",
        "history.folder_not_found_msg": "The destination folder '{path}' could not be found.",
        "history.item_meta": "Format: {format} • Size: {size} • File: {file}",
        "history.item_source": "Source: {url}",
        # Settings Page
        "settings.header_title": "Settings",
        "settings.header_sub": (
            "Configure download locations, interface appearance and diagnostic preferences."
        ),
        "settings.sec_general": "Downloads",
        "settings.download_dir": "Default download folder:",
        "settings.concurrent_downloads": "Maximum concurrent downloads:",
        "settings.sec_appearance": "Interface & Appearance",
        "settings.theme": "Theme:",
        "settings.theme_system": "Follow system theme",
        "settings.theme_dark": "Dark theme",
        "settings.theme_light": "Light theme",
        "settings.language": "Interface language:",
        "settings.notifications": "Show desktop notifications when a download finishes",
        "settings.sec_advanced": "Advanced & Diagnostics",
        "settings.log_level": "Log level:",
        "settings.btn_open_data_dir": "Open user data folder",
        "settings.btn_open_logs_dir": "Open logs folder",
        "settings.btn_save": "Save Settings",
        "settings.btn_reset": "Restore Defaults",
        "settings.saved_success": "✓ Settings saved successfully.",
        "settings.saved_error": "Error saving settings.",
        "settings.defaults_restored": "✓ Default settings restored.",
        # About Page
        "about.header_title": "OpenVideo Downloader",
        "about.header_sub": "Version {version} • Open-Source Windows Media Manager",
        "about.sec_diagnostics": "System Information & Diagnostics",
        "about.lbl_app_version": "Application version:",
        "about.lbl_python": "Python runtime:",
        "about.lbl_pyside": "PySide6 / Qt runtime:",
        "about.lbl_ytdlp": "yt-dlp engine:",
        "about.lbl_sqlite": "SQLite database:",
        "about.lbl_ffmpeg": "FFmpeg status:",
        "about.lbl_data_dir": "User data folder:",
        "about.btn_copy_diag": "Copy Diagnostics",
        "about.btn_open_data_dir": "Open user data folder",
        "about.copy_success": "✓ Diagnostics copied to clipboard (sensitive data redacted).",
        "about.sec_legal": "License & Disclaimer",
        "about.legal_text": (
            "OpenVideo Downloader is an independent desktop application released under "
            "the MIT License.\n\n"
            "This project is not affiliated with, endorsed by, or officially associated with "
            "YouTube, Google, or any other external media platform. The user is solely "
            "responsible for lawful use, applicable copyrights, and terms of service of "
            "visited platforms."
        ),
        "about.ffmpeg_notice": (
            "💡 <b>About FFmpeg & download quality:</b> High resolutions (1080p, 4K) are split "
            "by platforms like YouTube into separate video and audio streams. FFmpeg is required "
            "to merge them into a single file.<br>"
            "Without FFmpeg, OpenVideo Downloader automatically downloads the best available "
            "progressive stream (audio and video combined) up to 720p.<br>"
            "<i>Optional installation:</i> In PowerShell run: "
            "<code>winget install Gyan.FFmpeg</code> "
            "or place <code>ffmpeg.exe</code> in the application directory."
        ),
        "about.ffmpeg_available": "Available ({binary})",
        "about.ffmpeg_missing": "Not detected (progressive formats available)",
        "about.diag_title": "=== OpenVideo Downloader Diagnostics ===",
        "about.diag_version": "Version: v{version}",
        "about.diag_ffmpeg": "FFmpeg: {status}",
        "about.diag_datadir": "Data folder: {path}",
        "about.clipboard_unavailable": "Clipboard not available.",
    },
}

_current_language: str = DEFAULT_LANGUAGE
_language_listeners: list[Callable[[], None]] = []


def normalize_language_code(code: str) -> str:
    """Normalize language identifiers like 'dutch' -> 'nl', 'english' -> 'en'."""
    clean = code.strip().lower()
    if clean in ("en", "english", "eng"):
        return "en"
    if clean in ("nl", "dutch", "nld"):
        return "nl"
    return DEFAULT_LANGUAGE


def get_language() -> str:
    """Return currently active language code ('nl' or 'en')."""
    return _current_language


def set_language(code: str) -> None:
    """Change the active language and notify registered UI observers."""
    global _current_language
    norm = normalize_language_code(code)
    if norm not in SUPPORTED_LANGUAGES:
        norm = DEFAULT_LANGUAGE

    changed = norm != _current_language
    _current_language = norm

    if changed:
        for callback in list(_language_listeners):
            try:
                callback()
            except Exception:
                pass


def tr(key: str, default: str | None = None, **kwargs: object) -> str:
    """Translate key into the currently active language with optional kwargs interpolation."""
    lang_dict = TRANSLATIONS.get(_current_language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = lang_dict.get(key)
    if text is None:
        # Fallback to default language dictionary
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, default or key)

    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text


def register_language_listener(callback: Callable[[], None]) -> None:
    """Register a UI component callback to trigger whenever the interface language changes."""
    if callback not in _language_listeners:
        _language_listeners.append(callback)


def unregister_language_listener(callback: Callable[[], None]) -> None:
    """Unregister a language change callback."""
    if callback in _language_listeners:
        _language_listeners.remove(callback)
