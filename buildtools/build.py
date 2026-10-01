import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src" / "kiabom.py"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
EXE = DIST / "kiabom.exe"
STAGING = ROOT / "staging"
STAGING_DIST = STAGING / "dist"
STAGING_BUILD = STAGING / "build"
STAGING_EXE = STAGING_DIST / "kiabom.exe"

def clean_build():
    """Remove previous PyInstaller build output."""

    for path in (BUILD, DIST):
        if path.exists():
            print(f"Removing {path}...")
            shutil.rmtree(path)

def clean_staging():
    """Remove any leftover staging output."""

    if STAGING.exists():
        print(f"Removing {STAGING}...")
        shutil.rmtree(STAGING)


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
            "--distpath",
            str(STAGING_DIST),
            "--workpath",
            str(STAGING_BUILD),
            "--specpath",
            str(STAGING),
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

    if not STAGING_EXE.exists():
        raise RuntimeError(
            f"PyInstaller completed, but the executable was not found:\n{STAGING_EXE}"
        )

    try:
        result = subprocess.run(
            [str(STAGING_EXE), "--version"],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"The executable timed out running --version:\n{STAGING_EXE}")

    if result.returncode != 0:
        raise RuntimeError(
            f"The executable failed to run --version (exit code {result.returncode}):\n"
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
        
    print(f"Verified: {STAGING_EXE}")


def replace_old_build():
    """Replace the old build with the new one."""

    clean_build()

    shutil.move(str(STAGING_DIST), str(DIST))
    shutil.move(str(STAGING_BUILD), str(BUILD))

    print(f"Built: {DIST / 'kiabom.exe'}")

def main():
    try:
        build_exe()
        verify_build()
        replace_old_build()
    finally:
        clean_staging()

if __name__ == "__main__":
    main()
