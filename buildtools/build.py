import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "kiabom.py"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
EXE = DIST / "kiabom.exe"


def clean_build():
    """Remove previous PyInstaller build output."""

    for path in (BUILD, DIST):
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path)


def build_exe():
    """Build the executable with PyInstaller."""

    print("Running PyInstaller...")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(SOURCE),
            "--onefile",
            "--clean",
            "--add-data",
            f"{ROOT / 'LICENSE'};.",
            "--icon",
            str(ROOT / "images" / "kiabom-icon.ico"),
            "--name",
            "kiabom",
        ],
        cwd=ROOT,
        check=True,
    )


def verify_build():
    """Make sure PyInstaller produced the expected executable."""

    if not EXE.exists():
        raise RuntimeError(
            f"PyInstaller completed, but the executable was not found:\n{EXE}"
        )

    print(f"Built: {EXE}")


def main():
    clean_build()
    build_exe()
    verify_build()


if __name__ == "__main__":
    main()
