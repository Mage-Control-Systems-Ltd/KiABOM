import ast
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src" / "kiabom.py"
DIST = ROOT / "dist"
BUILD = ROOT / "build"
EXE = DIST / "kiabom.exe"
LICENSE = ROOT / "LICENSE"
ICON = ROOT / "images" / "kiabom-icon.ico"

def get_version():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "__version__"
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    return node.value.value

    raise RuntimeError("Could not find __version__")


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
            f"{LICENSE};.",
            "--icon",
            str(ICON),
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

def create_zip(version: str):
    """Create the versioned release ZIP."""

    zip_path = DIST / f"kiabom-{version}.zip"

    if zip_path.exists():
        zip_path.unlink()

    print(f"Creating {zip_path}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(EXE, "kiabom.exe")
        z.write(LICENSE, "LICENSE")

    return zip_path

def main():
    version = get_version()

    print(f"Building Kiabom {version}...")
    print()

    clean_build()
    build_exe()
    verify_build()

    zip_path = create_zip(version)

    print()
    print(f"Created release: {zip_path}")

if __name__ == "__main__":
    main()
