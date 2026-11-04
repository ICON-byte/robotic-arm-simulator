"""Always-visible motion transport shared by both sidebar modes."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel,
                              QProgressBar, QPushButton, QVBoxLayout)

from ..core.motion import MotionState, SPEEDS


class MotionControls(QFrame):
    pause_requested = Signal()
    stop_requested = Signal()

    def __init__(self, reset_button, parent=None):
        super().__init__(parent)
        self.setObjectName("motionControls")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        top = QHBoxLayout()
        top.addWidget(QLabel("Speed"))
        self.speed = QComboBox()
        self.speed.addItems(list(SPEEDS))
        self.speed.setCurrentText("Normal")
        self.speed.setAccessibleName("Motion speed for the next move")
        self.speed.setToolTip("Slow 45°/s · Normal 90°/s · Fast 180°/s peak; minimum duration 1 s. Fixed during a move.")
        top.addWidget(self.speed)
        self.status = QLabel("Idle · 0%")
        self.status.setProperty("role", "accent")
        top.addWidget(self.status, 1)
        layout.addLayout(top)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setAccessibleName("Motion progress percentage")
        layout.addWidget(self.progress)
        buttons = QHBoxLayout()
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(lambda: self.pause_requested.emit())
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(lambda: self.stop_requested.emit())
        self.stop_button.setToolTip("Cancel and hold the current interpolated pose")
        buttons.addWidget(self.pause_button)
        buttons.addWidget(self.stop_button)
        buttons.addWidget(reset_button)
        layout.addLayout(buttons)

    def set_motion(self, motion):
        percent = int(100*motion.progress)
        self.status.setText(f"{motion.state.value} · {percent}%")
        self.progress.setValue(percent)
        self.pause_button.setText("Resume" if motion.state == MotionState.PAUSED else "Pause")
        self.pause_button.setEnabled(motion.active)
        self.stop_button.setEnabled(motion.active)
        self.speed.setEnabled(not motion.active)
