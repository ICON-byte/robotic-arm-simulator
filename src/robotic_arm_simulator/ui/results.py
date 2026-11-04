"""Live FK readout and local clipboard export, independent of the renderer."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                              QPushButton, QTabWidget, QVBoxLayout, QWidget)
from .controls import angle_text, label


def format_number(value):
    """Three decimals, with rounded negative zero displayed as zero."""
    return f"{0.0 if abs(value) < 0.0005 else value:.3f}"


class ResultsPanel(QFrame):
    copied = Signal()

    def __init__(self, result, parent=None):
        super().__init__(parent)
        self.setObjectName("results")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        header = QHBoxLayout()
        header.addWidget(label("Forward kinematics", "section"))
        header.addStretch()
        self.copy_button = QPushButton("Copy results")
        self.copy_button.setObjectName("copyResultsButton")
        self.copy_button.setShortcut("Ctrl+Shift+C")
        self.copy_button.setToolTip("Copy joint angles, endpoint coordinates, and matrix (Ctrl+Shift+C)")
        self.copy_button.clicked.connect(self.copy_results)
        header.addWidget(self.copy_button)
        layout.addLayout(header)
        self.tabs = QTabWidget()
        self.tabs.setMaximumHeight(136)
        coordinates = QWidget()
        grid = QGridLayout(coordinates)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setVerticalSpacing(4)
        self.coordinate_labels = []
        for column, axis in enumerate("XYZ"):
            grid.addWidget(label(f"{axis} · mm", "muted"), 0, column)
            value = label("", "coordinate")
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setAccessibleName(f"End-effector {axis} coordinate in millimetres")
            grid.addWidget(value, 1, column)
            grid.setColumnStretch(column, 1)
            self.coordinate_labels.append(value)
        self.angles_label = label("", "muted")
        grid.addWidget(self.angles_label, 2, 0, 1, 3)
        self.tabs.addTab(coordinates, "Coordinates")
        matrix_page = QWidget()
        matrix_layout = QVBoxLayout(matrix_page)
        matrix_layout.setContentsMargins(8, 4, 8, 4)
        matrix_layout.setSpacing(2)
        matrix_layout.addWidget(label("Tool → world · translation column in mm", "muted"))
        matrix_grid = QGridLayout()
        matrix_grid.setSpacing(2)
        self.matrix_labels = []
        for row in range(4):
            cells = []
            for column in range(4):
                cell = label("", "matrix")
                cell.setWordWrap(False)
                cell.setAlignment(Qt.AlignmentFlag.AlignRight)
                cell.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                cell.setAccessibleName(f"Tool-to-world matrix row {row + 1}, column {column + 1}")
                matrix_grid.addWidget(cell, row, column)
                matrix_grid.setColumnStretch(column, 1)
                cells.append(cell)
            self.matrix_labels.append(cells)
        matrix_layout.addLayout(matrix_grid)
        self.tabs.addTab(matrix_page, "4 × 4 matrix")
        layout.addWidget(self.tabs)
        self.set_result(result)

    def set_result(self, result):
        self.result = result
        for value_label, value in zip(self.coordinate_labels, result.endpoint):
            value_label.setText(format_number(value))
        self.angles_label.setText("Base {}°   ·   Shoulder {}°   ·   Elbow {}°".format(*(angle_text(a) for a in result.angles)))
        for cells, values in zip(self.matrix_labels, result.transform):
            for cell, value in zip(cells, values):
                cell.setText(format_number(value))

    def clipboard_text(self):
        result = self.result
        angles = "\n".join(f"{name}: {angle:g} deg" for name, angle in zip(("Base", "Shoulder", "Elbow"), result.angles))
        coordinates = "\n".join(f"{axis}: {format_number(value)} mm" for axis, value in zip("XYZ", result.endpoint))
        matrix = "\n".join("  ".join(format_number(value) for value in row) for row in result.transform)
        return (f"Forward kinematics — 3-DOF robotic arm\n\nJoint angles\n{angles}\n\n"
                f"End-effector position (world frame)\n{coordinates}\n\n"
                f"Tool-to-world homogeneous transform (translation in mm)\n{matrix}")

    def copy_results(self):
        QApplication.clipboard().setText(self.clipboard_text())
        self.copied.emit()
