"""Explicit placeholders for controls implemented in later phases."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


def label(text, role=None):
    widget = QLabel(text)
    if role:
        widget.setProperty("role", role)
    widget.setWordWrap(True)
    return widget


class ControlSidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setMinimumWidth(270)
        self.setMaximumWidth(340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(label("Arm configuration", "section"))
        layout.addWidget(label("Joint controls become available when the robot model is added.", "muted"))
        for title, detail in [("Base", "Rotation about Z"), ("Shoulder", "Upper-arm elevation"), ("Elbow", "Forearm articulation")]:
            row = label(f"{title}\n{detail}", "placeholder")
            row.setMinimumHeight(58)
            layout.addWidget(row)
        layout.addSpacing(16)
        layout.addWidget(label("Kinematics", "section"))
        layout.addWidget(label("Forward kinematics", "pending"))
        layout.addWidget(label("Joint angles → endpoint position", "muted"))
        layout.addSpacing(4)
        layout.addWidget(label("Inverse kinematics", "pending"))
        layout.addWidget(label("Target position → joint angles", "muted"))
        layout.addStretch(1)
        layout.addWidget(label("Phase 1 · Application foundation", "accent"))
        layout.addWidget(label("Reference scene only. No arm or calculated coordinates yet.", "muted"))
