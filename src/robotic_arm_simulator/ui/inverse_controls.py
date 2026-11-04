"""Explicit calculate/select/apply workflow for position-only analytical IK."""

from math import hypot, isfinite

from PySide6.QtCore import Signal, QSignalBlocker
from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
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
        layout.setSpacing(6)
        hint = QLabel("Enter XYZ, calculate, then select and apply a solution.")
        hint.setWordWrap(True)
        hint.setProperty("role", "muted")
        layout.addWidget(hint)
        form = QFormLayout()
        self.inputs = []
        for axis, value in zip("XYZ", model.forward_kinematics().endpoint):
            field = QLineEdit(f"{value:.6f}")
            field.setAccessibleName(f"Target {axis} coordinate in millimetres")
            field.setAccessibleDescription("Finite number in millimetres; use a decimal point. Enter calculates IK without moving.")
            field.setToolTip("Finite world coordinate in mm; decimal/scientific notation. Enter calculates without moving.")
            field.setPlaceholderText(f"{axis} in mm")
            field.textChanged.connect(lambda _text, edit=field: self._edited(edit))
            field.returnPressed.connect(self.calculate)
            caption = QLabel(f"&{axis} · mm")
            caption.setBuddy(field)
            form.addRow(caption, field)
            self.inputs.append(field)
        layout.addLayout(form)
        self.calculate_button = QPushButton("Calculate IK")
        self.calculate_button.setToolTip("Find valid joint configurations without moving the robot (Enter in a target field)")
        self.calculate_button.clicked.connect(self.calculate)
        layout.addWidget(self.calculate_button)
        self.message = QLabel("Calculate to find valid solutions.")
        self.message.setWordWrap(True)
        self.message.setProperty("role", "muted")
        layout.addWidget(self.message)
        self.solution_list = QListWidget()
        self.solution_list.setAccessibleName("Valid inverse kinematics solutions")
        self.solution_list.setWordWrap(True)
        self.solution_list.setMinimumHeight(68)
        self.solution_list.setMaximumHeight(100)
        self.solution_list.setToolTip("Choose a valid solution with the arrow keys; B/S/E mean base/shoulder/elbow")
        layout.addWidget(self.solution_list)
        self.selection_label = QLabel("No solution selected")
        self.selection_label.setProperty("role", "muted")
        layout.addWidget(self.selection_label)
        actions = QHBoxLayout()
        self.apply_button = QPushButton("Apply now")
        self.apply_button.setToolTip("Cancel any motion and apply the selected IK pose immediately")
        self.apply_button.setEnabled(False)
        self.solution_list.currentRowChanged.connect(lambda row: self.apply_button.setEnabled(row >= 0))
        self.apply_button.clicked.connect(self.apply_solution)
        actions.addWidget(self.apply_button)
        self.move_button = QPushButton("Animate")
        self.move_button.setEnabled(False)
        self.move_button.setToolTip("Animate to the selected IK configuration at the chosen speed")
        self.solution_list.currentRowChanged.connect(lambda row: self.move_button.setEnabled(row >= 0))
        self.solution_list.currentRowChanged.connect(self._selection_changed)
        self.move_button.clicked.connect(self.move_solution)
        actions.addWidget(self.move_button)
        layout.addLayout(actions)
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setProperty("role", "accent")
        layout.addWidget(self.error_label)
        layout.addStretch()
        order = [*self.inputs, self.calculate_button, self.solution_list, self.apply_button, self.move_button]
        for first, second in zip(order, order[1:]):
            self.setTabOrder(first, second)

    def set_message(self, text, kind="info"):
        role = {"info": "muted", "success": "accent", "error": "error"}[kind]
        if self.message.property("role") != role:
            self.message.setProperty("role", role)
            self.message.style().unpolish(self.message)
            self.message.style().polish(self.message)
        self.message.setText(text)

    def _selection_changed(self, row):
        if self.result is None or row < 0:
            self.selection_label.setText("No solution selected")
            self.selection_label.setToolTip("")
        else:
            self.selection_label.setText(f"Selected solution {row+1} of {len(self.result.solutions)}")
            self.selection_label.setToolTip(self.result.solutions[row].branch)

    @staticmethod
    def _mark_invalid(field, invalid):
        field.setProperty("invalid", invalid)
        field.style().unpolish(field)
        field.style().polish(field)

    def _edited(self, field):
        self._mark_invalid(field, False)
        self.invalidate()

    def set_target(self, target):
        values = tuple(float(value) for value in target)
        if len(values) != 3 or not all(isfinite(value) for value in values):
            raise ValueError("Target must contain three finite coordinates.")
        self.invalidate()
        for field, value in zip(self.inputs, values):
            with QSignalBlocker(field):
                field.setText(f"{value:.9f}")
            self._mark_invalid(field, False)
        self.set_message("Target prepared. Calculate IK, then choose Apply now or Animate.")

    def invalidate(self):
        self.result = None
        self.solution_list.clear()
        self.apply_button.setEnabled(False)
        self.move_button.setEnabled(False)
        self.error_label.clear()
        self.set_message("Target changed. Calculate IK to refresh solutions.")
        self.target_changed.emit(None)

    def calculate(self):
        self.invalidate()
        target = []
        invalid = []
        for axis, field in zip("XYZ", self.inputs):
            try:
                value = float(field.text())
                valid = isfinite(value)
            except (ValueError, OverflowError):
                value, valid = 0.0, False
            self._mark_invalid(field, not valid)
            if not valid:
                invalid.append((axis, field))
            target.append(value)
        if invalid:
            axes = ", ".join(axis for axis, _ in invalid)
            self.set_message(f"Invalid input: enter a finite number for {axes}. Use a decimal point.", "error")
            invalid[0][1].setFocus()
            return
        try:
            target = tuple(target)
            self.target_changed.emit(target)
            self.result = solve_inverse_kinematics(self.model, target)
        except IKError as exc:
            recovery = " Try a closer target." if exc.code == "unreachable" else " Try a different height or distance."
            self.set_message(f"{exc.code.replace('_', ' ').capitalize()}: {exc}{recovery}", "error")
            return
        for solution in self.result.solutions:
            b, s, e = solution.angles
            item = QListWidgetItem(f"{solution.branch}\nB {b:.2f}° · S {s:.2f}° · E {e:.2f}°")
            item.setToolTip("Base {:.10f}°\nShoulder {:.10f}°\nElbow {:.10f}°\nError {:.9f} mm".format(b, s, e, solution.error_mm))
            self.solution_list.addItem(item)
        self.solution_list.setCurrentRow(0)
        notes = " ".join(self.result.notes)
        self.set_message(f"{len(self.result.solutions)} valid solution(s). Closest selected. {notes}".strip(), "success")
        self.solution_list.setFocus()
        self.update_pose_feedback()

    def apply_solution(self):
        row = self.solution_list.currentRow()
        if self.result is None or row < 0:
            return
        solution = self.result.solutions[row]
        self.apply_requested.emit(solution.angles)
        self.set_message(f"Applied {solution.branch.lower()}.", "success")
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
