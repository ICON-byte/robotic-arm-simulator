"""Brand resources, real startup lifecycle, diagnostics and DPI regressions."""

import os
from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest

from robotic_arm_simulator.branding import RESOURCE_DIR


def test_original_icon_frames():
    with Image.open(RESOURCE_DIR / "robokin3d.png") as image:
        assert image.size == (512, 512)
    with Image.open(RESOURCE_DIR / "robokin3d.ico") as image:
        assert image.ico.sizes() == {(n, n) for n in (16, 24, 32, 48, 64, 128, 256)}


@pytest.mark.parametrize("scale", ["1", "1.5", "2"])
def test_splash_resources_and_high_dpi_from_other_directory(tmp_path, scale):
    code = '''
from PySide6.QtWidgets import QApplication
from robotic_arm_simulator.branding import application_icon, set_windows_identity
from robotic_arm_simulator.startup import StartupSplash
import sys
if sys.platform == "win32":
    assert set_windows_identity()
app = QApplication([])
app.setWindowIcon(application_icon())
splash = StartupSplash()
splash.show()
splash.set_status("Loading 3D engine…")
assert splash.isVisible()
assert splash.size().width() == 560 and splash.size().height() == 300
assert splash.progress.minimum() == splash.progress.maximum() == 0
assert not app.windowIcon().isNull()
assert splash.status.fontMetrics().horizontalAdvance(splash.status.text()) < splash.status.width()
splash.close()
app.processEvents()
assert not splash.isVisible()
'''
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path,
                            env={**os.environ, "QT_SCALE_FACTOR": scale},
                            capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("failure_stage", ["none", "import", "create", "finish"])
def test_startup_lifecycle_and_failure_diagnostics(tmp_path, failure_stage):
    code = '''
import logging
from pathlib import Path
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget, QMessageBox
from robotic_arm_simulator.startup import StartupController, configure_logging
app = QApplication([])
log = configure_logging()
controller = StartupController(app, log)
messages = []
def dialog(parent, title, text):
    assert not controller.splash.isVisible()
    assert "private diagnostic detail" not in text
    assert str(log) in text
    messages.append(text)
QMessageBox.critical = dialog
def fail(*args):
    raise RuntimeError("private diagnostic detail")
stage = sys.argv[1]
if stage == "import":
    import builtins
    original_import = builtins.__import__
    def importing(name, *args, **kwargs):
        if name == "ui.main_window":
            fail()
        return original_import(name, *args, **kwargs)
    builtins.__import__ = importing
else:
    import robotic_arm_simulator.ui.main_window as module
    module.MainWindow = fail if stage == "create" else QWidget
    if stage == "finish":
        controller.splash.finish = fail
def ready(window):
    assert not controller.splash.isVisible()
    assert window.isVisible()
    QTimer.singleShot(0, window.close)
controller.ready.connect(ready)
QTimer.singleShot(30000, lambda: app.exit(9))
controller.start()
result = app.exec()
assert result == (0 if stage == "none" else 1), result
assert not controller.splash.isVisible()
if controller.window is not None:
    assert not controller.window.isVisible()
logging.shutdown()
if stage != "none":
    assert len(messages) == 1
    assert "private diagnostic detail" in Path(log).read_text()
'''
    result = subprocess.run([sys.executable, "-c", code, failure_stage],
                            env={**os.environ, "ROBOKIN3D_LOG_DIR": str(tmp_path)},
                            capture_output=True, text=True, timeout=50)
    assert result.returncode == 0, result.stdout + result.stderr
