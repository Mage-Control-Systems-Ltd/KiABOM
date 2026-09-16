import ast
import subprocess
import zipfile
from pathlib import Path


ROOT = Path(__file__).parent
SOURCE = ROOT / "src" / "kiabom.py"
DIST = ROOT / "dist"
EXE = DIST / "kiabom.exe"


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


version = get_version()
zip_path = DIST / f"kiabom-{version}.zip"

print(f"Building Kiabom {version}...")

subprocess.run(
    ["pyinstaller", "kiabom.spec", "--clean"],
    cwd=ROOT,
    check=True,
)

if zip_path.exists():
    zip_path.unlink()

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(EXE, "kiabom.exe")
    z.write(ROOT / "LICENSE", "LICENSE")

print(f"Created {zip_path}")
