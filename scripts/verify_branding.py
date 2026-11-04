"""Developer-only visual/native icon inspection; never included in the bundle."""
import ctypes
import json
from pathlib import Path
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from robotic_arm_simulator.branding import application_icon, set_windows_identity
from robotic_arm_simulator.startup import StartupController

destination = Path(sys.argv[1]).resolve()
destination.mkdir(parents=True, exist_ok=True)
identity = set_windows_identity()
app = QApplication([])
app.setWindowIcon(application_icon())
from importlib.resources import files
app.setStyle("Fusion")
app.setStyleSheet(files("robotic_arm_simulator.ui").joinpath("theme.qss").read_text())
controller = StartupController(app)
controller.splash.show()
controller.splash.set_status("Loading 3D engine…")
controller.splash.grab().save(str(destination / "splash.png"))
report = {"windows_identity": identity, "device_pixel_ratio": controller.splash.devicePixelRatioF()}

def ready(window):
    assert not controller.splash.isVisible()
    window.grab().save(str(destination / "workspace.png"))
    if sys.platform == "win32":
        user32 = ctypes.windll.user32
        user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_ssize_t]
        user32.SendMessageW.restype = ctypes.c_void_p
        report["native_small_icon"] = bool(user32.SendMessageW(int(window.winId()), 0x7f, 0, 0))
        report["native_large_icon"] = bool(user32.SendMessageW(int(window.winId()), 0x7f, 1, 0))
        from PIL import ImageGrab
        frame = window.frameGeometry()
        ImageGrab.grab(bbox=(frame.left(), frame.top(), frame.right()+1,
                            frame.top()+30)).save(destination / "titlebar.png")
    report["main_window_icon"] = not window.windowIcon().isNull()
    report["splash_dismissed"] = not controller.splash.isVisible()
    (destination / "native-verification.json").write_text(json.dumps(report, indent=2))
    QTimer.singleShot(0, window.close)

controller.ready.connect(ready)
controller.start()
raise SystemExit(app.exec())
