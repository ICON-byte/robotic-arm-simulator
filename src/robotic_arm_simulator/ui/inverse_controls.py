"""Explicit calculate/select/apply workflow for position-only analytical IK."""

from math import hypot, isfinite

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QFormLayout, QLabel, QLineEdit, QListWidget,
                              QListWidgetItem, QPushButton, QVBoxLayout, QWidget)

from ..core.inverse_kinematics import IKError, solve_inverse_kinematics


class InverseControls(QWidget):
    target_changed = Signal(object)
    apply_requested = Signal(tuple)
    move_requested = Signal(tuple)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.result = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(10)
        hint = QLabel("Enter a world-space target in millimetres.")
        hint.setWordWrap(True)
        hint.setProperty("role", "muted")
        layout.addWidget(hint)
        form = QFormLayout()
        self.inputs = []
        for axis, value in zip("XYZ", model.forward_kinematics().endpoint):
            field = QLineEdit(f"{value:.6f}")
            field.setAccessibleName(f"Target {axis} coordinate in millimetres")
            field.setPlaceholderText(f"{axis} in mm")
            field.textChanged.connect(self.invalidate)
            form.addRow(f"{axis} · mm", field)
            self.inputs.append(field)
        layout.addLayout(form)
        self.calculate_button = QPushButton("Calculate IK")
        self.calculate_button.clicked.connect(self.calculate)
        layout.addWidget(self.calculate_button)
        self.message = QLabel("Calculate to find valid solutions.")
        self.message.setWordWrap(True)
        self.message.setProperty("role", "muted")
        layout.addWidget(self.message)
        self.solution_list = QListWidget()
        self.solution_list.setAccessibleName("Valid inverse kinematics solutions")
        self.solution_list.setWordWrap(True)
        self.solution_list.setMinimumHeight(80)
        self.solution_list.setMaximumHeight(150)
        layout.addWidget(self.solution_list)
        self.apply_button = QPushButton("Apply instantly")
        self.apply_button.setToolTip("Cancel any motion and apply the selected IK pose immediately")
        self.apply_button.setEnabled(False)
        self.solution_list.currentRowChanged.connect(lambda row: self.apply_button.setEnabled(row >= 0))
        self.apply_button.clicked.connect(self.apply_solution)
        layout.addWidget(self.apply_button)
        self.move_button = QPushButton("Move to solution")
        self.move_button.setEnabled(False)
        self.move_button.setToolTip("Animate to the selected IK configuration at the chosen speed")
        self.solution_list.currentRowChanged.connect(lambda row: self.move_button.setEnabled(row >= 0))
        self.move_button.clicked.connect(self.move_solution)
        layout.addWidget(self.move_button)
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setProperty("role", "accent")
        layout.addWidget(self.error_label)
        layout.addStretch()

    def invalidate(self):
        self.result = None
        self.solution_list.clear()
        self.apply_button.setEnabled(False)
        self.move_button.setEnabled(False)
        self.error_label.clear()
        self.message.setText("Target changed. Calculate IK to refresh solutions.")
        self.target_changed.emit(None)

    def calculate(self):
        self.invalidate()
        try:
            try:
                target = tuple(float(field.text()) for field in self.inputs)
            except (ValueError, OverflowError) as exc:
                raise IKError("invalid_input", "Enter a finite number for X, Y, and Z.") from exc
            if not all(isfinite(value) for value in target):
                raise IKError("invalid_input", "X, Y, and Z must be finite numbers.")
            self.target_changed.emit(target)
            self.result = solve_inverse_kinematics(self.model, target)
        except IKError as exc:
            self.message.setText(f"{exc.code.replace('_', ' ').capitalize()}: {exc}")
            return
        for solution in self.result.solutions:
            b, s, e = solution.angles
            item = QListWidgetItem(f"{solution.branch}\nB {b:.2f}° · S {s:.2f}° · E {e:.2f}°")
            item.setToolTip("Base {:.10f}°\nShoulder {:.10f}°\nElbow {:.10f}°\nError {:.9f} mm".format(b, s, e, solution.error_mm))
            self.solution_list.addItem(item)
        self.solution_list.setCurrentRow(0)
        notes = " ".join(self.result.notes)
        self.message.setText(f"{len(self.result.solutions)} valid solution(s). Closest selected. {notes}".strip())
        self.update_pose_feedback()

    def apply_solution(self):
        row = self.solution_list.currentRow()
        if self.result is None or row < 0:
            return
        solution = self.result.solutions[row]
        self.apply_requested.emit(solution.angles)
        self.message.setText(f"Applied {solution.branch.lower()}.")
        self.update_pose_feedback()

    def update_pose_feedback(self):
        if self.result is not None:
            endpoint = self.model.forward_kinematics().endpoint
            error = hypot(*(float(a) - b for a, b in zip(endpoint, self.result.target)))
            self.error_label.setText(f"Positioning error: {error:.9f} mm")

    def move_solution(self):
        row = self.solution_list.currentRow()
        if self.result is None or row < 0:
            return
        self.move_requested.emit(self.result.solutions[row].angles)
