"""Automated build script for OpenVideo Downloader on Windows."""

import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SPEC_FILE = ROOT_DIR / "open_video_downloader.spec"
DIST_DIR = ROOT_DIR / "dist" / "OpenVideoDownloader"
EXE_PATH = DIST_DIR / "OpenVideoDownloader.exe"


def main() -> int:
    """Execute PyInstaller build and verify the output binary."""
    print("=" * 60)
    print("OpenVideo Downloader - Windows Build Pipeline")
    print("=" * 60)

    start_time = time.time()

    # 1. Verify spec file exists
    if not SPEC_FILE.is_file():
        print(f"ERROR: Spec-bestand niet gevonden op: {SPEC_FILE}")
        return 1

    # 2. Verify or generate icon
    icon_file = ROOT_DIR / "assets" / "app_icon.ico"
    if not icon_file.is_file():
        print("WAARSCHUWING: assets/app_icon.ico niet gevonden. Icon wordt gegenereerd...")
        icon_file.parent.mkdir(parents=True, exist_ok=True)
        # Fallback generation handled by assets script

    print(f"Starten van PyInstaller met spec: {SPEC_FILE.name}")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_FILE),
    ]

    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    except subprocess.CalledProcessError as err:
        print(f"\nFOUT: PyInstaller build mislukt met code {err.returncode}!")
        return err.returncode

    # 3. Verify output
    if not EXE_PATH.is_file():
        print(f"\nFOUT: Verwacht uitvoerbestand niet gevonden op: {EXE_PATH}")
        return 1

    elapsed = time.time() - start_time
    exe_size_mb = EXE_PATH.stat().st_size / (1024 * 1024)

    # Calculate total dist size
    total_bytes = sum(f.stat().st_size for f in DIST_DIR.rglob("*") if f.is_file())
    total_size_mb = total_bytes / (1024 * 1024)

    print("\n" + "=" * 60)
    print("Build succesvol afgerond!")
    print(f"Locatie executable : {EXE_PATH}")
    print(f"Grootte .exe       : {exe_size_mb:.2f} MB")
    print(f"Totale mapgrootte  : {total_size_mb:.2f} MB")
    print(f"Bouwtijd           : {elapsed:.1f} seconden")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
