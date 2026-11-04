"""Package-relative assets and process-scoped Windows identity."""

import ctypes
import logging
from pathlib import Path
import sys

from PySide6.QtGui import QIcon

APP_NAME = "RoboKin3D"
APP_USER_MODEL_ID = "ICONByte.RoboKin3D"
RESOURCE_DIR = Path(__file__).resolve().parent / "resources"


def application_icon():
    icon = QIcon(str(RESOURCE_DIR / "robokin3d.ico"))
    if icon.isNull():
        raise RuntimeError("RoboKin3D icon resource could not be loaded")
    return icon


def set_windows_identity():
    """Call before QApplication, without registry or system-wide changes."""
    if sys.platform != "win32":
        return False
    function = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
    function.argtypes = [ctypes.c_wchar_p]
    function.restype = ctypes.c_long
    result = function(APP_USER_MODEL_ID)
    if result != 0:
        logging.getLogger(__name__).warning("Windows AppUserModelID returned HRESULT %s", result)
    return result == 0
