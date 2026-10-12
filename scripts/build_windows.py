"""Automated build script for OpenVideo Downloader on Windows."""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SPEC_FILE = ROOT_DIR / "open_video_downloader.spec"
DIST_DIR = ROOT_DIR / "dist" / "OpenVideoDownloader"
EXE_PATH = DIST_DIR / "OpenVideoDownloader.exe"
ISS_FILE = ROOT_DIR / "installer" / "open_video_downloader.iss"
INSTALLER_DIR = ROOT_DIR / "dist" / "installer"


def find_iscc() -> Path | None:
    """Locate Inno Setup compiler executable (ISCC.exe)."""
    which_iscc = shutil.which("iscc")
    if which_iscc:
        return Path(which_iscc)

    candidates = [
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Inno Setup 6"
        / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LocalAppData", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def build_pyinstaller() -> int:
    """Execute PyInstaller build and verify the output binary."""
    # 1. Verify spec file exists
    if not SPEC_FILE.is_file():
        print(f"ERROR: Spec-bestand niet gevonden op: {SPEC_FILE}")
        return 1

    # 2. Verify icon
    icon_file = ROOT_DIR / "assets" / "app_icon.ico"
    if not icon_file.is_file():
        print("WAARSCHUWING: assets/app_icon.ico niet gevonden.")

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

    exe_size_mb = EXE_PATH.stat().st_size / (1024 * 1024)
    total_bytes = sum(f.stat().st_size for f in DIST_DIR.rglob("*") if f.is_file())
    total_size_mb = total_bytes / (1024 * 1024)

    print("\nPyInstaller build voltooid:")
    print(f"  Executable : {EXE_PATH}")
    print(f"  Grootte    : {exe_size_mb:.2f} MB")
    print(f"  Totale map : {total_size_mb:.2f} MB")
    return 0


def build_installer(iscc_path: Path) -> int:
    """Compile Inno Setup script into an installer executable."""
    print("\n" + "=" * 60)
    print("Inno Setup - Installer Creatie")
    print("=" * 60)
    print(f"Gebruik Inno Setup compiler: {iscc_path}")
    print(f"Script: {ISS_FILE}")

    cmd = [str(iscc_path), str(ISS_FILE)]
    try:
        subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
    except subprocess.CalledProcessError as err:
        print(f"\nFOUT: Inno Setup compilatie mislukt met code {err.returncode}!")
        return err.returncode

    installer_files = list(INSTALLER_DIR.glob("*.exe")) if INSTALLER_DIR.is_dir() else []
    if installer_files:
        latest = max(installer_files, key=lambda f: f.stat().st_mtime)
        size_mb = latest.stat().st_size / (1024 * 1024)
        print("\nInstaller succesvol gegenereerd:")
        print(f"  Locatie    : {latest}")
        print(f"  Bestand    : {latest.name}")
        print(f"  Grootte    : {size_mb:.2f} MB")
    return 0


def main() -> int:
    """Main build orchestrator."""
    parser = argparse.ArgumentParser(description="OpenVideo Downloader - Windows Build Pipeline")
    parser.add_argument(
        "--installer",
        action="store_true",
        help="Compile Inno Setup installer executable after build",
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Skip PyInstaller build and run installer creation only",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("OpenVideo Downloader - Windows Build Pipeline")
    print("=" * 60)

    start_time = time.time()

    if not args.skip_pyinstaller:
        ret = build_pyinstaller()
        if ret != 0:
            return ret

    if args.installer or args.skip_pyinstaller:
        iscc = find_iscc()
        if not iscc:
            print("\nFOUT: Inno Setup compiler (ISCC.exe) niet gevonden op het systeem!")
            print("Installeer Inno Setup 6 van: https://jrsoftware.org/isdl.php")
            return 1
        ret = build_installer(iscc)
        if ret != 0:
            return ret

    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"Totale pijplijntijd: {elapsed:.1f} seconden")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
