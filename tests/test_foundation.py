"""Camera, renderer lifecycle, and production launch regression checks."""

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

    reset = window.findChild(QPushButton, "resetViewButton")
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


@pytest.mark.parametrize("joint,value", [(0, 90), (1, 0), (2, 0)])
def test_joint_controls_and_actor_transforms(app, window, joint, value):
    model = window.robot
    visual = window.viewport.arm
    actors = {name: actor.GetAddressAsString("") for name, actor in visual.actors.items()}
    before = model.transforms()
    camera = camera_state(window.viewport.plotter)
    slider = window.controls.sliders[joint]
    slider.setFocus()
    QTest.keyClick(slider, Qt.Key.Key_Right)
    assert model.angles[joint] == model.initial_angles[joint] + 1
    slider.setValue(value)
    app.processEvents()
    expected = list(model.initial_angles)
    expected[joint] = value
    assert model.angles == tuple(expected)
    assert window.controls.angle_labels[joint].text() == f"{value}°"
    transforms = model.transforms()
    for name, frame in visual.frames.items():
        np.testing.assert_allclose(visual.actors[name].user_matrix, transforms[frame])
    for name in ("base_plate", "base_bearing"):
        np.testing.assert_allclose(visual.actors[name].user_matrix, np.eye(4))
    assert actors == {name: actor.GetAddressAsString("") for name, actor in visual.actors.items()}
    # Local beam endpoints meet exact joint pivots, without renderer-side FK.
    upper_tip = visual.actors["upper_arm"].user_matrix @ [200, 0, 0, 1]
    forearm_tip = visual.actors["forearm"].user_matrix @ [150, 0, 0, 1]
    np.testing.assert_allclose(upper_tip[:3], transforms["elbow"][:3, 3], atol=1e-10)
    np.testing.assert_allclose(forearm_tip[:3], transforms["endpoint"][:3, 3], atol=1e-10)
    np.testing.assert_allclose(visual.actors["endpoint"].center, transforms["endpoint"][:3, 3], atol=1e-6)
    np.testing.assert_allclose(camera_state(window.viewport.plotter), camera)
    if joint == 2:
        np.testing.assert_allclose(transforms["shoulder"], before["shoulder"])
        np.testing.assert_allclose(transforms["elbow"][:3, 3], before["elbow"][:3, 3])
    capture_dir = os.environ.get("SIMULATOR_CAPTURE_DIR")
    if capture_dir:
        assert window.grab().save(os.path.join(capture_dir, f"joint-{joint}.png"))
    QTest.mouseClick(window.controls.reset_button, Qt.MouseButton.LeftButton)
    assert model.angles == model.initial_angles
    assert [slider.value() for slider in window.controls.sliders] == list(model.initial_angles)
    np.testing.assert_allclose(camera_state(window.viewport.plotter), camera)


def test_slider_limits_and_repeated_updates(app, window):
    actor_count = len(window.viewport.plotter.renderer.actors)
    for slider, (low, high) in zip(window.controls.sliders, window.robot.joint_limits):
        slider.setValue(high + 50)
        assert slider.value() == high
        slider.setValue(low - 50)
        assert slider.value() == low
    for value in range(-135, 136, 9):
        window.controls.sliders[2].setValue(value)
        app.processEvents()
    assert len(window.viewport.plotter.renderer.actors) == actor_count
    assert window.isVisible()
    QTest.mouseClick(window.controls.reset_button, Qt.MouseButton.LeftButton)
    assert window.robot.angles == window.robot.initial_angles


@pytest.mark.parametrize("angles,expected", [
    ((0, 0, 0), ("350.000", "0.000", "100.000")),
    ((90, 0, 0), ("0.000", "350.000", "100.000")),
    ((0, 45, -90), ("247.487", "0.000", "135.355")),
    ((0, -90, 0), ("0.000", "0.000", "-250.000")),
])
def test_live_fk_matrix_and_marker(app, window, angles, expected):
    panel = window.results
    for slider, angle in zip(window.controls.sliders, angles):
        slider.setValue(angle)
    app.processEvents()
    assert tuple(cell.text() for cell in panel.coordinate_labels) == expected
    assert panel.angles_label.text() == "Base {:.0f}°   ·   Shoulder {:.0f}°   ·   Elbow {:.0f}°".format(*angles)
    assert tuple(panel.matrix_labels[row][3].text() for row in range(3)) == expected
    displayed = np.array([[float(cell.text()) for cell in row] for row in panel.matrix_labels])
    np.testing.assert_allclose(displayed, panel.result.transform, atol=0.0005)
    np.testing.assert_allclose(window.viewport.arm.actors["endpoint"].center, panel.result.endpoint, atol=1e-6)
    np.testing.assert_allclose(window.viewport.arm.actors["endpoint"].user_matrix, panel.result.transform)
    QTest.mouseClick(window.controls.reset_button, Qt.MouseButton.LeftButton)
    assert tuple(cell.text() for cell in panel.coordinate_labels) == ("247.487", "0.000", "135.355")


def test_copy_results_and_matrix_tab_layout(app, window):
    panel = window.results
    clipboard = QApplication.clipboard()
    original_clipboard = clipboard.text()
    try:
        for slider in window.controls.sliders:
            slider.setValue(0)
        QTest.mouseClick(panel.copy_button, Qt.MouseButton.LeftButton)
        text = clipboard.text()
        for line in ("Base: 0 deg", "Shoulder: 0 deg", "Elbow: 0 deg",
                     "X: 350.000 mm", "Y: 0.000 mm", "Z: 100.000 mm"):
            assert line in text
        assert "copied" in window.statusBar().currentMessage()
        QTest.mouseClick(window.controls.reset_button, Qt.MouseButton.LeftButton)
        QTest.mouseClick(panel.copy_button, Qt.MouseButton.LeftButton)
        assert "X: 247.487 mm" in clipboard.text()
        for width, height in [(960, 680), (1360, 900)]:
            window.resize(width, height)
            for tab in (0, 1):
                panel.tabs.setCurrentIndex(tab)
                app.processEvents()
                assert window.viewport.height() > 250
                if tab == 1:
                    for row in panel.matrix_labels:
                        for cell in row:
                            assert cell.isVisible()
                            assert cell.height() >= cell.fontMetrics().height()
                capture_dir = os.environ.get("SIMULATOR_CAPTURE_DIR")
                if capture_dir:
                    assert window.grab().save(os.path.join(capture_dir, f"results-{width}-tab{tab}.png"))
    finally:
        clipboard.setText(original_clipboard)


def test_readout_normalizes_rounded_negative_zero():
    from robotic_arm_simulator.ui.results import format_number
    assert format_number(-1e-10) == "0.000"
    assert format_number(-0.001) == "-0.001"


def set_ik_target(window, target):
    window.controls.modes.setCurrentIndex(1)
    for field, value in zip(window.controls.ik.inputs, target):
        field.setText(str(value))


def test_ik_calculate_apply_and_fractional_state(app, window):
    panel = window.controls.ik
    initial = window.robot.angles
    camera = camera_state(window.viewport.plotter)
    actor = window.viewport.target_actor
    set_ik_target(window, (250, 50, 150))
    assert window.robot.angles == initial
    QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
    assert window.robot.angles == initial
    assert panel.solution_list.count() == 2
    assert panel.solution_list.currentRow() == 0
    chosen = panel.result.solutions[0].angles
    assert any(abs(a - round(a)) > 0.001 for a in chosen)
    assert actor.visibility
    np.testing.assert_allclose(actor.position, (250, 50, 150))
    QTest.mouseClick(panel.apply_button, Qt.MouseButton.LeftButton)
    assert window.robot.angles == chosen
    np.testing.assert_allclose(window.results.result.endpoint, (250, 50, 150), atol=1e-6)
    np.testing.assert_allclose(window.viewport.arm.actors["endpoint"].center, actor.center, atol=1e-6)
    np.testing.assert_allclose(window.results.result.transform, window.robot.transforms()["endpoint"])
    assert "X: 250.000 mm" in window.results.clipboard_text()
    assert f"Base: {chosen[0]:g} deg" in window.results.clipboard_text()
    assert [slider.value() for slider in window.controls.sliders] == [round(a) for a in chosen]
    assert "Positioning error:" in panel.error_label.text()
    assert float(panel.error_label.text().split()[2]) <= 1e-6
    window.controls.modes.setCurrentIndex(0)
    assert window.robot.angles == chosen
    window.controls.sliders[0].setValue(20)
    assert window.robot.angles[1:] == chosen[1:], "Coarse sliders must not round other IK joints"
    np.testing.assert_allclose(camera_state(window.viewport.plotter), camera)
    window.controls.modes.setCurrentIndex(1)
    QTest.mouseClick(window.controls.reset_button, Qt.MouseButton.LeftButton)
    assert window.robot.angles == initial
    assert panel.result is None and not panel.apply_button.isEnabled()
    assert not actor.visibility


@pytest.mark.parametrize("target,expected", [
    ((500, 0, 100), "Unreachable"), ((100, 0, 100), "Joint limits"),
    (("bad", 0, 100), "Invalid input"), (("nan", 0, 100), "Invalid input"),
])
def test_ik_failures_leave_pose_unchanged(app, window, target, expected):
    before = window.robot.angles
    panel = window.controls.ik
    set_ik_target(window, target)
    QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
    assert expected in panel.message.text()
    assert window.robot.angles == before
    assert panel.result is None
    assert not panel.apply_button.isEnabled()


def test_ik_target_edit_invalidates_all_solutions(app, window):
    panel = window.controls.ik
    set_ik_target(window, (250, 0, 100))
    QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
    assert panel.solution_list.count() == 2
    panel.inputs[0].setText("251")
    assert panel.result is None
    assert panel.solution_list.count() == 0
    assert not panel.apply_button.isEnabled()
    assert not window.viewport.target_actor.visibility
    before = window.robot.angles
    panel.apply_solution()
    assert window.robot.angles == before


def test_ik_all_branches_selection_and_layout(app, window):
    panel = window.controls.ik
    set_ik_target(window, (-150, 0, 300))
    QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
    assert panel.solution_list.count() == 3
    for index in range(3):
        panel.solution_list.setCurrentRow(index)
        chosen = panel.result.solutions[index]
        QTest.mouseClick(panel.apply_button, Qt.MouseButton.LeftButton)
        assert window.robot.angles == chosen.angles
        np.testing.assert_allclose(window.results.result.endpoint, (-150, 0, 300), atol=1e-6)
    assert window.viewport.target_actor.visibility
    # Capture a representative fractional solution and a failure at both sizes.
    for width, height in [(960, 680), (1360, 900)]:
        window.resize(width, height)
        set_ik_target(window, (250, 50, 150))
        QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
        QTest.mouseClick(panel.apply_button, Qt.MouseButton.LeftButton)
        app.processEvents()
        assert window.viewport.height() > 250
        assert panel.apply_button.isVisible()
        capture_dir = os.environ.get("SIMULATOR_CAPTURE_DIR")
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"ik-{width}-success.png"))
        set_ik_target(window, (500, 0, 100))
        QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
        app.processEvents()
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"ik-{width}-error.png"))


def start_motion_to_ik(window, target=(250, 50, 150)):
    set_ik_target(window, target)
    panel = window.controls.ik
    QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
    chosen = panel.result.solutions[panel.solution_list.currentRow()].angles
    QTest.mouseClick(panel.move_button, Qt.MouseButton.LeftButton)
    return chosen


def test_motion_live_sync_pause_resume_and_completion(app, window):
    from robotic_arm_simulator.core.motion import MotionState, interpolate
    clock = [100.0]
    window.motion.clock = lambda: clock[0]
    initial = window.robot.angles
    actor_ids = {name: actor.GetAddressAsString("") for name, actor in window.viewport.arm.actors.items()}
    chosen = start_motion_to_ik(window)
    assert window.motion.state == MotionState.RUNNING
    assert window.motion_timer.isActive()
    assert window.robot.angles == initial
    assert not window.motion_controls.speed.isEnabled()
    duration = window.motion.duration
    clock[0] += duration*0.25
    window._motion_tick()
    np.testing.assert_allclose(window.robot.angles, interpolate(initial, chosen, 0.25))
    assert window.results.result.angles == window.robot.angles
    np.testing.assert_allclose(window.results.result.endpoint, window.viewport.arm.actors["endpoint"].center, atol=1e-6)
    np.testing.assert_allclose(window.results.result.transform, window.viewport.arm.actors["endpoint"].user_matrix)
    assert window.motion_controls.progress.value() == 25
    QTest.mouseClick(window.motion_controls.pause_button, Qt.MouseButton.LeftButton)
    assert window.motion.state == MotionState.PAUSED
    assert not window.motion_timer.isActive()
    paused_pose = window.robot.angles
    clock[0] += 100
    window._motion_tick()
    assert window.robot.angles == paused_pose
    assert window.motion_controls.pause_button.text() == "Resume"
    # Mode changes preserve active/paused motion and its target marker.
    window.controls.modes.setCurrentIndex(0)
    assert window.motion.state == MotionState.PAUSED
    assert window.viewport.target_actor.visibility
    QTest.mouseClick(window.motion_controls.pause_button, Qt.MouseButton.LeftButton)
    assert window.motion.state == MotionState.RUNNING
    assert window.motion_timer.isActive()
    clock[0] += duration*0.75 + 0.001
    window._motion_tick()
    assert window.robot.angles == chosen
    assert window.motion.state == MotionState.COMPLETED
    assert not window.motion_timer.isActive()
    assert window.motion_controls.progress.value() == 100
    assert "completed" in window.statusBar().currentMessage()
    assert "Motion completed" in window.controls.ik.message.text()
    assert float(window.controls.ik.error_label.text().split()[2]) <= 1e-6
    np.testing.assert_allclose(window.results.result.endpoint, (250, 50, 150), atol=1e-6)
    assert actor_ids == {name: actor.GetAddressAsString("") for name, actor in window.viewport.arm.actors.items()}


@pytest.mark.parametrize("action", ["stop", "reset", "edit", "manual", "instant", "replace"])
def test_motion_interruption_workflows(app, window, action):
    from robotic_arm_simulator.core.motion import MotionState
    clock = [100.0]
    window.motion.clock = lambda: clock[0]
    start_motion_to_ik(window)
    clock[0] += window.motion.duration/2
    window._motion_tick()
    pose = window.robot.angles
    if action == "stop":
        QTest.mouseClick(window.motion_controls.stop_button, Qt.MouseButton.LeftButton)
        assert window.robot.angles == pose
    elif action == "reset":
        QTest.mouseClick(window.controls.reset_button, Qt.MouseButton.LeftButton)
        assert window.robot.angles == window.robot.initial_angles
        assert window.motion.state == MotionState.IDLE
        assert not window.viewport.target_actor.visibility
    elif action == "edit":
        window.controls.ik.inputs[0].setText("251")
        assert window.robot.angles == pose
        assert window.controls.ik.result is None
        assert not window.controls.ik.move_button.isEnabled()
        window.controls.ik.move_solution()
    elif action == "manual":
        window.controls.modes.setCurrentIndex(0)
        window.controls.sliders[0].setValue(20)
        assert window.robot.angles == (20, *pose[1:])
    elif action == "instant":
        panel = window.controls.ik
        target = panel.result.solutions[0].angles
        QTest.mouseClick(panel.apply_button, Qt.MouseButton.LeftButton)
        assert window.robot.angles == target
    else:
        panel = window.controls.ik
        panel.solution_list.setCurrentRow(1)
        target = panel.result.solutions[1].angles
        QTest.mouseClick(panel.move_button, Qt.MouseButton.LeftButton)
        assert window.motion.state == MotionState.RUNNING
        assert window.motion.start_angles == pose
        assert window.motion.target_angles == target
        assert window.motion.progress == 0
        return
    if action != "reset":
        assert window.motion.state == MotionState.CANCELLED
    assert not window.motion_timer.isActive()
    held = window.robot.angles
    clock[0] += 100
    window._motion_tick()
    assert window.robot.angles == held


def test_real_qtimer_moves_and_shutdown_is_clean(app, window):
    from robotic_arm_simulator.core.motion import MotionState
    before = window.robot.angles
    start_motion_to_ik(window)
    QTest.qWait(160)
    assert window.motion.state == MotionState.RUNNING
    assert 0 < window.motion.progress < 1
    assert window.robot.angles != before
    window.close()
    app.processEvents()
    assert not window.motion_timer.isActive()
    assert not window.motion.active
    assert window.viewport.plotter._closed


def test_motion_frames_and_controls_at_both_sizes(app, window):
    clock = [100.0]
    window.motion.clock = lambda: clock[0]
    capture_dir = os.environ.get("SIMULATOR_CAPTURE_DIR")
    for width, height in [(960, 680), (1360, 900)]:
        # The desktop may constrain large top-level windows; enforce this test
        # client size so evidence cannot silently describe a smaller surface.
        window.setMinimumSize(width, height)
        window.resize(width, height)
        app.processEvents()
        assert (window.width(), window.height()) == (width, height)
        window._reset_arm()
        start_motion_to_ik(window)
        started = clock[0]
        duration = window.motion.duration
        for progress in (0.25, 0.5, 0.75):
            clock[0] = started + duration*progress
            window._motion_tick()
            app.processEvents()
            assert window.viewport.height() > 250
            transport = window.motion_controls
            assert transport.pause_button.isVisible()
            assert transport.stop_button.isVisible()
            assert window.rect().contains(transport.mapTo(window, transport.rect().bottomRight()))
            if capture_dir:
                assert window.grab().save(os.path.join(capture_dir, f"motion-{width}-{int(progress*100)}.png"))
        QTest.mouseClick(window.motion_controls.pause_button, Qt.MouseButton.LeftButton)
        app.processEvents()
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"motion-{width}-paused.png"))


def test_repeated_demo_presets_and_ik_preparation(app, window):
    from robotic_arm_simulator.core.presets import IK_PRESET_NAME, POSE_PRESETS, demonstration_target
    camera = camera_state(window.viewport.plotter)
    for _ in range(2):
        for name, expected in POSE_PRESETS.items():
            window.controls.presets.setCurrentText(name)
            QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
            assert window.robot.angles == expected
            assert window.results.result.angles == expected
            assert window.controls.ik.result is None
        pose = window.robot.angles
        window.controls.presets.setCurrentText(IK_PRESET_NAME)
        assert "Target" in window.controls.preset_hint.text()
        QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
        assert window.robot.angles == pose
        assert window.controls.modes.currentIndex() == 1
        assert "IK" in window.mode_status.text()
        panel = window.controls.ik
        assert panel.result is None and not panel.move_button.isEnabled()
        np.testing.assert_allclose([float(field.text()) for field in panel.inputs], demonstration_target(window.robot), atol=1e-8)
        QTest.mouseClick(panel.calculate_button, Qt.MouseButton.LeftButton)
        assert panel.solution_list.count() >= 2
        assert "Selected solution 1" in panel.selection_label.text()
        panel.solution_list.setCurrentRow(1)
        assert "Selected solution 2" in panel.selection_label.text()
    np.testing.assert_allclose(camera_state(window.viewport.plotter), camera)


@pytest.mark.parametrize("preset", ["Home position", "Fully extended", "Raised arm", "Elbow bend", "IK demonstration"])
def test_preset_during_motion_stops_old_timer(app, window, preset):
    from robotic_arm_simulator.core.motion import MotionState
    clock = [100.0]
    window.motion.clock = lambda: clock[0]
    start_motion_to_ik(window)
    clock[0] += window.motion.duration/2
    window._motion_tick()
    current = window.robot.angles
    window.controls.presets.setCurrentText(preset)
    QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
    assert not window.motion.active
    assert not window.motion_timer.isActive()
    if preset == "IK demonstration":
        assert window.robot.angles == current
        assert window.motion.state == MotionState.CANCELLED
    elif preset == "Home position":
        assert window.motion.state == MotionState.IDLE
        assert window.robot.angles == window.robot.initial_angles


def test_invalid_fields_and_keyboard_navigation(app, window):
    panel = window.controls.ik
    set_ik_target(window, ("bad", "nan", "inf"))
    window.activateWindow()
    panel.inputs[0].setFocus()
    QTest.keyClick(panel.inputs[0], Qt.Key.Key_Tab)
    assert QApplication.focusWidget() is panel.inputs[1]
    QTest.keyClick(panel.inputs[1], Qt.Key.Key_Tab)
    assert QApplication.focusWidget() is panel.inputs[2]
    QTest.keyClick(panel.inputs[2], Qt.Key.Key_Return)
    assert "X, Y, Z" in panel.message.text()
    assert panel.message.property("role") == "error"
    assert QApplication.focusWidget() is panel.inputs[0]
    assert all(field.property("invalid") for field in panel.inputs)
    panel.inputs[0].setText("250")
    assert not panel.inputs[0].property("invalid")
    set_ik_target(window, (250, 0, 100))
    QTest.keyClick(panel.inputs[2], Qt.Key.Key_Return)
    assert panel.result is not None
    assert panel.message.property("role") == "accent"
    assert not any(field.property("invalid") for field in panel.inputs)


def test_repeated_workflows_reuse_scene_and_cancel_old_motion(app, window):
    clock = [100.0]
    window.motion.clock = lambda: clock[0]
    ids = {name: actor.GetAddressAsString("") for name, actor in window.viewport.arm.actors.items()}
    count = len(window.viewport.plotter.renderer.actors)
    for index in range(12):
        window._reset_arm()
        window.controls.modes.setCurrentIndex(0)
        for value in (0, 90, -90, 180, -180, 20):
            window.controls.sliders[0].setValue(value)
        for target in ((1e-12, 0, 450), (350, 0, 100), (250, 0, 100)):
            set_ik_target(window, target)
            window.controls.ik.calculate()
            assert window.controls.ik.result is not None
            window.controls.ik.calculate()
            assert window.controls.ik.solution_list.count() >= 1
        window.controls.ik.move_solution()
        duration = window.motion.duration
        clock[0] += duration/2
        window._motion_tick()
        if index % 2:
            window._pause_resume_motion()
            pose = window.robot.angles
            clock[0] += 5
            window._pause_resume_motion()
            assert window.robot.angles == pose
        window._stop_motion()
        held = window.robot.angles
        window._pause_resume_motion()  # Cancelled motion cannot be resumed.
        assert window.robot.angles == held
        window.controls.ik.move_solution()
        clock[0] += window.motion.duration + 0.01
        window._motion_tick()
        assert "X: 250.000 mm" in window.results.clipboard_text()
        np.testing.assert_allclose(window.results.result.endpoint, (250, 0, 100), atol=1e-6)
    assert count == len(window.viewport.plotter.renderer.actors)
    assert ids == {name: actor.GetAddressAsString("") for name, actor in window.viewport.arm.actors.items()}


def test_demo_layout_and_camera_from_multiple_angles(app, window):
    from robotic_arm_simulator.core.presets import POSE_PRESETS
    capture_dir = os.environ.get("SIMULATOR_CAPTURE_DIR")
    for width, height in [(960, 680), (1100, 760), (1360, 900)]:
        window.setMinimumSize(width, height)
        window.resize(width, height)
        app.processEvents()
        assert (window.width(), window.height()) == (width, height)
        for name in ("Fully extended", "Raised arm", "Elbow bend"):
            window.controls.presets.setCurrentText(name)
            QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
            app.processEvents()
            assert window.viewport.width() > 500 and window.viewport.height() > 250
            if capture_dir:
                slug = name.lower().replace(" ", "-")
                assert window.grab().save(os.path.join(capture_dir, f"demo-{width}-{slug}.png"))
        window.controls.presets.setCurrentText("IK demonstration")
        QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
        panel = window.controls.ik
        panel.calculate()
        panel.apply_solution()
        window.results.tabs.setCurrentIndex(1)
        app.processEvents()
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"demo-{width}-ik-matrix.png"))
        scroll = window.controls.parentWidget().parentWidget()
        scroll.ensureWidgetVisible(panel.move_button)
        app.processEvents()
        assert scroll.viewport().rect().contains(panel.move_button.mapTo(scroll.viewport(), panel.move_button.rect().bottomRight()))
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"demo-{width}-ik-actions.png"))
        set_ik_target(window, ("bad", 0, 100))
        panel.calculate()
        app.processEvents()
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"demo-{width}-invalid.png"))
    window.controls.presets.setCurrentText("Elbow bend")
    QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
    for index, position in enumerate(([(600, 650, 500), (80, 0, 120), (0, 0, 1)],
                                     [(-650, -700, 500), (80, 0, 120), (0, 0, 1)])):
        window.viewport.plotter.camera_position = position
        window.viewport.plotter.render()
        if capture_dir:
            assert window.grab().save(os.path.join(capture_dir, f"view-angle-{index}.png"))
    window.viewport.reset_camera()
    expected = camera_state(window.viewport.plotter)
    vtk_interactor = window.viewport.plotter.iren.interactor
    for _ in range(20):
        drag(vtk_interactor, (300, 250), (360, 300))
        vtk_interactor.MouseWheelForwardEvent()
    window.viewport.reset_camera()
    np.testing.assert_allclose(camera_state(window.viewport.plotter), expected)


def test_startup_failure_shows_recovery_without_exception_details():
    code = '''
import robotic_arm_simulator.__main__ as launcher
import robotic_arm_simulator.ui.main_window as window_module
def fail():
    raise RuntimeError("internal exception detail")
def message(parent, title, body):
    assert "internal exception detail" not in body
    assert "graphics driver" in body and "dependencies" in body
window_module.MainWindow = fail
launcher.QMessageBox.critical = message
assert launcher.main() == 1
'''
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr


def test_copy_and_reset_shortcuts(app, window):
    window.activateWindow()
    window.controls.presets.setCurrentText("Fully extended")
    QTest.mouseClick(window.controls.load_preset_button, Qt.MouseButton.LeftButton)
    clipboard = QApplication.clipboard()
    previous = clipboard.text()
    try:
        QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)
        QTest.qWait(150)
        assert "X: 350.000 mm" in clipboard.text()
        QTest.keyClick(window, Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier)
        QTest.qWait(150)
        assert window.robot.angles == window.robot.initial_angles
    finally:
        clipboard.setText(previous)
