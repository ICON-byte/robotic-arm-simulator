"""Main workspace layout and viewport lifecycle."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QMainWindow, QPushButton,
                              QScrollArea, QSplitter, QVBoxLayout, QWidget)
from .controls import ControlSidebar, label
from .results import ResultsPanel
from .motion_controls import MotionControls
from ..core.motion import MotionEngine, MotionState
from ..core.presets import IK_PRESET_NAME, POSE_PRESETS, demonstration_target
from ..visualization.viewport import Viewport
from ..core.robot import RobotModel
from ..branding import APP_NAME, application_icon


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.robot = RobotModel()
        self.motion = MotionEngine(self.robot)
        self.motion_timer = QTimer(self)
        self.motion_timer.setInterval(20)
        self.motion_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.motion_timer.timeout.connect(self._motion_tick)
        self.setWindowTitle(f"{APP_NAME} — 3D Robotic Arm Kinematics Simulator")
        self.setWindowIcon(application_icon())
        self.resize(1360, 900)
        self.setMinimumSize(960, 680)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        header = QFrame()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 18, 24, 18)
        header_layout.addWidget(label(APP_NAME, "title"))
        header_layout.addStretch()
        self.mode_status = label("FK · Joint controls", "muted")
        self.mode_status.setAccessibleName("Current control mode")
        header_layout.addWidget(self.mode_status)
        layout.addWidget(header)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(285)
        scroll.setMaximumWidth(355)
        self.controls = ControlSidebar(self.robot)
        self.controls.modes.currentChanged.connect(
            lambda index: self.mode_status.setText("FK · Joint controls" if index == 0 else "IK · Target workflow"))
        self.controls.preset_requested.connect(self._load_preset)
        scroll.setWidget(self.controls)
        sidebar = QWidget()
        sidebar.setMinimumWidth(285)
        sidebar.setMaximumWidth(355)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(0)
        side_layout.addWidget(scroll, 1)
        self.motion_controls = MotionControls(self.controls.reset_button)
        self.motion_controls.pause_requested.connect(self._pause_resume_motion)
        self.motion_controls.stop_requested.connect(self._stop_motion)
        self.motion_controls.set_motion(self.motion)
        side_layout.addWidget(self.motion_controls)
        splitter.addWidget(sidebar)
        workspace = QWidget()
        area = QVBoxLayout(workspace)
        area.setContentsMargins(24, 20, 24, 20)
        area.setSpacing(12)
        toolbar = QHBoxLayout()
        toolbar.addWidget(label("Scene", "section"))
        scene_hint = label("Perspective · millimetres", "muted")
        scene_hint.setWordWrap(False)
        toolbar.addWidget(scene_hint)
        toolbar.addStretch()
        reset = QPushButton("Reset view")
        reset.setObjectName("resetViewButton")
        reset.setToolTip("Restore the initial camera position (Ctrl+Home)")
        reset.setShortcut("Ctrl+Home")
        toolbar.addWidget(reset)
        area.addLayout(toolbar)
        self.viewport = Viewport(self.robot)
        self.controls.ik.target_changed.connect(self._target_changed)
        self.controls.ik.apply_requested.connect(self._set_joint_angles)
        self.controls.ik.move_requested.connect(self._start_motion)
        self.controls.angles_changed.connect(self._set_joint_angles)
        self.controls.reset_requested.connect(self._reset_arm)
        reset.clicked.connect(self.viewport.reset_camera)
        area.addWidget(self.viewport, 1)
        area.addWidget(label("Left drag: rotate    ·    Wheel / right drag: zoom    ·    Middle drag / Shift + left drag: pan", "muted"))
        self.results = ResultsPanel(self.robot.forward_kinematics())
        self.results.copied.connect(lambda: self.statusBar().showMessage("Forward kinematics results copied to clipboard"))
        area.addWidget(self.results)
        splitter.addWidget(workspace)
        splitter.setStretchFactor(1, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        layout.addWidget(splitter, 1)
        self.statusBar().showMessage("Ready · 3-DOF arm loaded · Dimensions in millimetres")
        self.statusBar().setSizeGripEnabled(True)

    def _set_joint_angles(self, angles):
        self.motion.apply_instant(angles)
        self.motion_timer.stop()
        self._refresh_arm()
        self.motion_controls.set_motion(self.motion)
        if self.motion.state == MotionState.CANCELLED and self.controls.ik.result is not None:
            self.controls.ik.set_message("Motion cancelled by an immediate joint update.")

    def _load_preset(self, name):
        if name == IK_PRESET_NAME:
            self.controls.ik.set_target(demonstration_target(self.robot))
            self.controls.modes.setCurrentIndex(1)
            self.statusBar().showMessage("IK target prepared · Calculate IK, select a solution, then apply or animate")
        elif name == "Home position":
            self._reset_arm()
            self.controls.modes.setCurrentIndex(0)
            self.statusBar().showMessage("Home position loaded · Default pose restored")
        elif name in POSE_PRESETS:
            self._set_joint_angles(POSE_PRESETS[name])
            self.controls.ik.invalidate()
            self.controls.ik.set_message("Pose preset loaded. Calculate IK for the retained target.")
            self.controls.modes.setCurrentIndex(0)
            self.statusBar().showMessage(f"{name} loaded · Pose applied immediately")

    def _reset_arm(self):
        self.motion_timer.stop()
        self.motion.reset()
        self.controls.ik.invalidate()
        self.controls.ik.set_message("Arm reset. Calculate IK to refresh solutions.")
        self._refresh_arm()
        self.motion_controls.set_motion(self.motion)

    def _target_changed(self, target):
        if self.motion.active:
            self._stop_motion()
        self.viewport.set_target(target)

    def _start_motion(self, angles):
        try:
            self.motion.start(angles, self.motion_controls.speed.currentText())
        except ValueError:
            self.statusBar().showMessage("Cannot start motion · Calculate IK again and select a valid solution")
            return
        self._refresh_arm()
        if self.motion.state == MotionState.RUNNING:
            self.motion_timer.start()
            self.controls.ik.set_message("Moving to commanded pose.")
        else:
            self.motion_timer.stop()
        self._sync_motion_feedback()

    def _sync_motion_feedback(self):
        self.motion_controls.set_motion(self.motion)
        self.statusBar().showMessage(f"Motion {self.motion.state.value.lower()} · {int(100*self.motion.progress)}% · {self.motion.speed}")
        if self.motion.state == MotionState.COMPLETED:
            self.controls.ik.set_message("Motion completed. Final positioning error shown below.", "success")
        elif self.motion.state == MotionState.PAUSED and self.controls.ik.result is not None:
            self.controls.ik.set_message("Motion paused. Resume to continue or Stop to hold this pose.")
        elif self.motion.state == MotionState.RUNNING:
            self.controls.ik.set_message("Moving to commanded pose.")
        elif self.motion.state == MotionState.CANCELLED and self.controls.ik.result is not None:
            self.controls.ik.set_message("Motion cancelled. Arm held at its current pose.")

    def _motion_tick(self):
        self.motion.advance()
        if self.motion.state != MotionState.RUNNING:
            self.motion_timer.stop()
        self._refresh_arm()
        self._sync_motion_feedback()

    def _pause_resume_motion(self):
        if self.motion.state == MotionState.RUNNING:
            self.motion.pause()
            self.motion_timer.stop()
        elif self.motion.state == MotionState.PAUSED:
            self.motion.resume()
            self.motion_timer.start()
        self._refresh_arm()
        self._sync_motion_feedback()

    def _stop_motion(self):
        self.motion.stop()
        self.motion_timer.stop()
        self._refresh_arm()
        self._sync_motion_feedback()

    def _refresh_arm(self):
        self.controls.set_angles(self.robot.angles)
        self.viewport.update_arm(self.robot)
        self.results.set_result(self.robot.forward_kinematics())
        self.controls.ik.update_pose_feedback()
        self.statusBar().showMessage("Arm updated · Base {:.3f}° · Shoulder {:.3f}° · Elbow {:.3f}°".format(*self.robot.angles))

    def closeEvent(self, event):
        self.motion_timer.stop()
        self.motion.stop()
        self.viewport.shutdown()
        super().closeEvent(event)
