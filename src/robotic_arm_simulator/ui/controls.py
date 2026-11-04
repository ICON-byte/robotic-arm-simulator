"""Joint controls with explicit placeholders for later kinematics modes."""

from PySide6.QtCore import Qt, Signal, QSignalBlocker
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QPushButton, QSlider,
                              QTabWidget, QVBoxLayout, QWidget)
from .inverse_controls import InverseControls


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

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(270)
        self.setMaximumWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(label("Arm configuration", "section"))
        self.modes = QTabWidget()
        layout.addWidget(self.modes)
        joint_page = QWidget()
        layout = QVBoxLayout(joint_page)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)
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
        self.reset_button.setToolTip("Restore base 0°, shoulder 45°, elbow −90°; keep the camera position")
        self.reset_button.clicked.connect(lambda: self.reset_requested.emit())
        layout.addSpacing(16)
        layout.addWidget(label("Forward kinematics · Live", "accent"))
        layout.addWidget(label("Coordinates and matrix below the scene", "muted"))
        layout.addSpacing(4)
        layout.addStretch(1)
        layout.addWidget(label("Gold: endpoint · Coral: IK target", "muted"))
        self.modes.addTab(joint_page, "Joint angles")
        self.ik = InverseControls(model)
        self.modes.addTab(self.ik, "IK target")
        self.set_angles(model.angles)

    def _slider_changed(self, joint, value):
        angles = list(self._angles)
        angles[joint] = value
        self.angles_changed.emit(tuple(angles))

    def set_angles(self, angles):
        self._angles = tuple(angles)
        for slider, value_label, angle in zip(self.sliders, self.angle_labels, angles):
            with QSignalBlocker(slider):
                slider.setValue(round(angle))
            value_label.setText(f"{angle_text(angle)}°")
