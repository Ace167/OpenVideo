# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

src_dir = Path("src").resolve()

datas = [
    ("assets", "assets"),
    ("LICENSE", "."),
    ("THIRD_PARTY_NOTICES.md", "."),
]

hiddenimports = [
    "open_video_downloader",
    "open_video_downloader.main",
    "open_video_downloader.app",
    "open_video_downloader.core",
    "open_video_downloader.core.constants",
    "open_video_downloader.core.models",
    "open_video_downloader.core.paths",
    "open_video_downloader.core.queue_manager",
    "open_video_downloader.database",
    "open_video_downloader.database.manager",
    "open_video_downloader.engines",
    "open_video_downloader.engines.ffmpeg_probe",
    "open_video_downloader.engines.workers",
    "open_video_downloader.engines.ytdl_adapter",
    "open_video_downloader.resources",
    "open_video_downloader.resources.icons",
    "open_video_downloader.resources.theme",
    "open_video_downloader.services",
    "open_video_downloader.services.logger",
    "open_video_downloader.settings",
    "open_video_downloader.settings.manager",
    "open_video_downloader.ui",
    "open_video_downloader.ui.main_window",
    "open_video_downloader.ui.navigation",
    "open_video_downloader.ui.pages.download_page",
    "open_video_downloader.ui.pages.queue_page",
    "open_video_downloader.ui.pages.history_page",
    "open_video_downloader.ui.pages.settings_page",
    "open_video_downloader.ui.pages.about_page",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "sqlite3",
] + collect_submodules("yt_dlp")

a = Analysis(
    [str(src_dir / "open_video_downloader" / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "unittest",
        "pydoc",
        "pdb",
        "matplotlib",
        "scipy",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OpenVideoDownloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/app_icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="OpenVideoDownloader",
)
