"""Smoke test to verify that the built frozen executable launches successfully."""

import os
import subprocess
import sys
import time
from pathlib import Path

EXE_PATH = (
    Path(__file__).resolve().parent.parent
    / "dist"
    / "OpenVideoDownloader"
    / "OpenVideoDownloader.exe"
)


def main() -> int:
    """Launch frozen executable with offscreen platform and verify it runs without crashing."""
    if not EXE_PATH.is_file():
        print(f"FAIL: Executable niet gevonden op {EXE_PATH}")
        return 1

    print(f"Testing frozen executable: {EXE_PATH}")

    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    smoke_dir = Path(__file__).resolve().parent.parent / ".pytest_temp" / "smoke_data"
    env["OPENVIDEO_DATA_DIR"] = str(smoke_dir)

    proc = subprocess.Popen([str(EXE_PATH)], env=env)
    time.sleep(3.0)

    poll_result = proc.poll()
    if poll_result is not None and poll_result != 0:
        print(f"FAIL: Executable crashte bij opstarten met exit code {poll_result}")
        return 1

    # Terminate running app
    proc.terminate()
    try:
        proc.wait(timeout=3.0)
    except subprocess.TimeoutExpired:
        proc.kill()

    print("PASS: Frozen OpenVideoDownloader.exe startte succesvol zonder fouten!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
