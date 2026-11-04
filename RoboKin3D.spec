# Build from the repository root: python -m PyInstaller --noconfirm RoboKin3D.spec
from pathlib import Path
import os

ROOT = Path(SPECPATH)
os.environ["QT_API"] = "pyside6"
PACKAGE = ROOT / "src" / "robotic_arm_simulator"
assets = [(str(PACKAGE / "ui" / "theme.qss"), "robotic_arm_simulator/ui")]
assets += [(str(PACKAGE / "resources" / name), "robotic_arm_simulator/resources")
           for name in ("robokin3d.png", "robokin3d.ico")]
a = Analysis([str(ROOT / "packaging" / "entrypoint.py")],
             pathex=[str(ROOT / "src")], binaries=[], datas=assets,
             hiddenimports=["vtkmodules.all", "vtkmodules.qt.QVTKRenderWindowInteractor",
                            "vtkmodules.util.numpy_support", "vtkmodules.numpy_interface.dataset_adapter"],
             hookspath=[], hooksconfig={"matplotlib": {"backends": ["Agg"]}},
             runtime_hooks=[], excludes=["PyQt5", "PyQt6", "PySide2", "pytest", "IPython"],
             noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="RoboKin3D",
          debug=False, strip=False, upx=False, console=False,
          icon=str(PACKAGE / "resources" / "robokin3d.ico"),
          version=str(ROOT / "packaging" / "version_info.txt"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="RoboKin3D")
