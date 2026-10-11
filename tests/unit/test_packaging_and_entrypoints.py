"""Unit tests verifying package entrypoints, metadata, spec file and build assets."""

from pathlib import Path
from unittest.mock import patch

import tomllib

from open_video_downloader import __version__
from open_video_downloader.main import main


def test_version_consistency():
    """Verify pyproject.toml version matches package __version__."""
    root_dir = Path(__file__).resolve().parents[2]
    pyproject_path = root_dir / "pyproject.toml"
    assert pyproject_path.is_file()

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    project_version = data["project"]["version"]
    assert project_version == __version__


def test_main_entrypoint_invocation():
    """Verify main() entrypoint executes and delegates to run_app."""
    with patch("open_video_downloader.main.run_app", return_value=0) as mock_run:
        exit_code = main()
        assert exit_code == 0
        mock_run.assert_called_once()


def test_main_module_import():
    """Verify open_video_downloader.__main__ is importable."""
    import open_video_downloader.__main__ as main_mod

    assert hasattr(main_mod, "main")


def test_packaging_assets_presence():
    """Verify icon and build script assets are present and valid."""
    root_dir = Path(__file__).resolve().parents[2]

    ico_path = root_dir / "assets" / "app_icon.ico"
    png_path = root_dir / "assets" / "app_icon.png"
    spec_path = root_dir / "open_video_downloader.spec"
    iss_path = root_dir / "installer" / "open_video_downloader.iss"

    assert ico_path.is_file(), "assets/app_icon.ico must exist for Windows packaging"
    assert png_path.is_file(), "assets/app_icon.png must exist for documentation"
    assert spec_path.is_file(), "open_video_downloader.spec must exist for PyInstaller"
    assert iss_path.is_file(), "installer/open_video_downloader.iss must exist for Inno Setup"

    # Verify installer script references the current version
    iss_content = iss_path.read_text(encoding="utf-8")
    assert f'#define MyAppVersion "{__version__}"' in iss_content
