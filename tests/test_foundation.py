"""Integration checks against a real Qt/VTK window, without a robot model."""

import os
import subprocess
import sys
os.environ["QT_API"] = "pyside6"

import numpy as np
import pytest
from importlib.resources import files
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton
from robotic_arm_simulator.ui.main_window import MainWindow


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    application.setStyle("Fusion")
    application.setStyleSheet(files("robotic_arm_simulator.ui").joinpath("theme.qss").read_text())
    yield application


def drag(interactor, start, end, shift=False):
    interactor.SetEventInformation(*start, 0, int(shift))
    interactor.LeftButtonPressEvent()
    interactor.SetEventInformation(*end, 0, int(shift))
    interactor.MouseMoveEvent()
    interactor.LeftButtonReleaseEvent()


@pytest.fixture
def window(app):
    window = MainWindow()
    window.show()
    QTest.qWait(500)
    yield window
    window.close()
    app.processEvents()


def camera_state(plotter):
    return np.array([plotter.camera.position, plotter.camera.focal_point,
                     plotter.camera.up])


def test_real_viewport_navigation_resize_and_shutdown(app, window):
    plotter = window.viewport.plotter
    vtk_interactor = plotter.iren.interactor
    initial = camera_state(plotter)
    assert plotter.ren_win.GetSize()[0] > 0
    image = plotter.screenshot(return_img=True)
    assert image.std() > 5, "Viewport must render a nonblank scene"

    drag(vtk_interactor, (300, 250), (380, 300))
    assert not np.allclose(plotter.camera.position, initial[0]), "Rotation must change camera position"
    window.viewport.reset_camera()
    focal = np.array(plotter.camera.focal_point)
    drag(vtk_interactor, (300, 250), (360, 280), shift=True)
    assert not np.allclose(plotter.camera.focal_point, focal), "Pan must move camera focal point"
    window.viewport.reset_camera()
    distance = plotter.camera.distance
    vtk_interactor.MouseWheelForwardEvent()
    assert plotter.camera.distance < distance, "Wheel must zoom in"

    window.viewport.reset_camera()
    vtk_interactor.SetEventInformation(300, 250)
    vtk_interactor.RightButtonPressEvent()
    vtk_interactor.SetEventInformation(300, 310)
    vtk_interactor.MouseMoveEvent()
    vtk_interactor.RightButtonReleaseEvent()
    assert not np.isclose(plotter.camera.distance, distance), "Right drag must zoom"
    window.viewport.reset_camera()
    vtk_interactor.SetEventInformation(300, 250)
    vtk_interactor.MiddleButtonPressEvent()
    vtk_interactor.SetEventInformation(360, 280)
    vtk_interactor.MouseMoveEvent()
    vtk_interactor.MiddleButtonReleaseEvent()
    assert not np.allclose(plotter.camera.focal_point, initial[1]), "Middle drag must pan"

    reset = window.findChild(QPushButton)
    QTest.mouseClick(reset, Qt.MouseButton.LeftButton)
    assert np.allclose(camera_state(plotter), initial)
    reset.setFocus()
    for width, height in [(960, 680), (1360, 900)]:
        window.resize(width, height)
        app.processEvents()
        assert window.viewport.width() > 500
        assert window.viewport.height() > 250
        assert reset.isVisible()
        capture_dir = os.environ.get("SIMULATOR_CAPTURE_DIR")
        if capture_dir:
            os.makedirs(capture_dir, exist_ok=True)
            assert window.grab().save(os.path.join(capture_dir, f"workspace-{width}.png"))
    window.close()
    app.processEvents()
    assert not window.isVisible()
    assert plotter._closed


def test_application_entrypoint_launches_and_exits():
    # Exercise production initialization, adding only an automatic close timer.
    code = '''
from PySide6.QtCore import QTimer
import robotic_arm_simulator.__main__ as launcher
BaseApplication = launcher.QApplication
class TimedApplication(BaseApplication):
    def __init__(self, *args):
        super().__init__(*args)
        QTimer.singleShot(2000, self.closeAllWindows)
launcher.QApplication = TimedApplication
raise SystemExit(launcher.main())
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                            text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
