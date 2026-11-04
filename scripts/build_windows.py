"""Rebuild a tested, windowed Windows x64 portable distribution locally."""
import argparse
import json
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
from time import perf_counter
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-tests", action="store_true", help="Only after separately verifying this exact source")
    args = parser.parse_args()
    if sys.platform != "win32" or struct.calcsize("P") != 8 or sys.version_info[:2] != (3, 12):
        raise SystemExit("Build requires Windows x64 and Python 3.12.")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise SystemExit("Run with the project-local .venv/Scripts/python.exe.")
    subprocess.run([sys.executable, "-m", "pip", "check"], cwd=ROOT, check=True)
    if not args.skip_tests:
        subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT, check=True)
    started = perf_counter()
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "RoboKin3D.spec"], cwd=ROOT, check=True)
    elapsed = perf_counter()-started
    bundle = ROOT / "dist/RoboKin3D"
    for name in ("RoboKin3D.exe", "_internal/robotic_arm_simulator/resources/robokin3d.ico",
                 "_internal/robotic_arm_simulator/resources/robokin3d.png",
                 "_internal/robotic_arm_simulator/ui/theme.qss"):
        if not (bundle / name).is_file():
            raise SystemExit(f"Missing bundled resource: {name}")
    shutil.copyfile(ROOT / "packaging/README.txt", bundle / "README.txt")
    shutil.copyfile(ROOT / "USER_GUIDE.md", bundle / "USER_GUIDE.md")
    archive = ROOT / "dist/RoboKin3D-v1.0.0-Windows-x64.zip"
    paths = sorted(p for p in bundle.rglob("*") if p.is_file())
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as output:
        for path in paths:
            output.write(path, path.relative_to(bundle.parent))
    metrics = {"python": platform.python_version(), "build_seconds": round(elapsed, 2),
               "bundle_bytes": sum(p.stat().st_size for p in paths),
               "zip_bytes": archive.stat().st_size, "file_count": len(paths)}
    (ROOT / "build/build-metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    print(f"Portable ZIP: {archive}")


if __name__ == "__main__":
    main()
