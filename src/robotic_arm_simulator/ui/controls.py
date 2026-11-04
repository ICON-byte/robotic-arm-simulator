"""Demonstration chooser and synchronized joint/target workflows."""

from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider,
                              QTabWidget, QVBoxLayout, QWidget)
from .inverse_controls import InverseControls
from ..core.presets import IK_PRESET_NAME, PRESET_NAMES


def label(text, role=None):
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(True)
    return widget


def angle_text(angle):
    value = 0.0 if abs(angle) < 0.0005 else angle
    return f"{value:.3f}".rstrip("0").rstrip(".")


class ControlSidebar(QWidget):
    angles_changed = Signal(tuple)
    reset_requested = Signal()
    preset_requested = Signal(str)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(270)
        self.setMaximumWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        layout.addWidget(label("Arm configuration", "section"))
        presets = QHBoxLayout()
        self.presets = QComboBox()
        self.presets.addItems(list(PRESET_NAMES))
        self.presets.setAccessibleName("Demonstration preset")
        self.presets.setToolTip("Choose a demonstration; Load applies a pose or prepares an IK target")
        presets.addWidget(self.presets, 1)
        self.load_preset_button = QPushButton("Load")
        self.load_preset_button.setAccessibleName("Load selected demonstration preset")
        self.load_preset_button.clicked.connect(lambda: self.preset_requested.emit(self.presets.currentText()))
        presets.addWidget(self.load_preset_button)
        layout.addLayout(presets)
        self.preset_hint = label("Pose · applies immediately", "muted")
        layout.addWidget(self.preset_hint)
        self.presets.currentTextChanged.connect(self._preset_changed)
        self._preset_changed(self.presets.currentText())
        self.modes = QTabWidget()
        layout.addWidget(self.modes)
        joint_page = QWidget()
        layout = QVBoxLayout(joint_page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(label("Adjust the joints to explore the arm's geometry.", "muted"))
        self.sliders = []
        self.angle_labels = []
        for joint, (title, (low, high)) in enumerate(zip(model.joint_names, model.joint_limits)):
            heading = QHBoxLayout()
            heading.addWidget(label(title, "pending"))
            value = label("", "accent")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            heading.addWidget(value)
            layout.addLayout(heading)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(low, high)
            slider.setAccessibleName(f"{title} angle in degrees")
            slider.setToolTip(f"{title}: {low}° to {high}°. Arrow keys change by 1°.")
            slider.valueChanged.connect(lambda value, index=joint: self._slider_changed(index, value))
            self.sliders.append(slider)
            self.angle_labels.append(value)
            layout.addWidget(slider)
            layout.addWidget(label(f"{low:+d}° to {high:+d}°", "muted"))
        self.reset_button = QPushButton("Reset arm")
        self.reset_button.setObjectName("resetArmButton")
        self.reset_button.setShortcut("Ctrl+R")
        self.reset_button.setToolTip("Reset arm (Ctrl+R): stop motion, restore 0°, 45°, −90°, and clear IK; keep the camera")
        self.reset_button.clicked.connect(lambda: self.reset_requested.emit())
        layout.addSpacing(8)
        layout.addWidget(label("Forward kinematics · Live", "accent"))
        layout.addWidget(label("Coordinates and matrix below the scene", "muted"))
        layout.addSpacing(4)
        layout.addStretch(1)
        layout.addWidget(label("Gold: endpoint · Coral: IK target", "muted"))
        self.modes.addTab(joint_page, "FK joints")
        self.ik = InverseControls(model)
        self.modes.addTab(self.ik, "IK target")
        self.set_angles(model.angles)

    def _slider_changed(self, joint, value):
        angles = list(self._angles)
        angles[joint] = value
        self.angles_changed.emit(tuple(angles))

    def _preset_changed(self, name):
        is_target = name == IK_PRESET_NAME
        self.preset_hint.setText("Target · calculate before moving" if is_target else "Pose · applies immediately")
        self.load_preset_button.setToolTip("Prepare a reachable IK target; keep the current pose" if is_target else "Apply this pose now and stop any active motion")

    def set_angles(self, angles):
        self._angles = tuple(angles)
        for slider, value_label, angle in zip(self.sliders, self.angle_labels, angles):
            with QSignalBlocker(slider):
                slider.setValue(round(angle))
            value_label.setText(f"{angle_text(angle)}°")
