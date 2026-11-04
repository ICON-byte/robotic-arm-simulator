"""Interactive arm scene with reusable geometry and camera controls."""

import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QVBoxLayout, QWidget
from .arm import ArmVisual


class Viewport(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)
        self.plotter.set_background("#151c24")
        self.plotter.enable_trackball_style()
        self.arm = ArmVisual(self.plotter, model)
        # Reusable wire marker distinguishes the requested target from the gold
        # mathematical endpoint. Its center is set only from parsed coordinates.
        self.target_actor = self.plotter.add_mesh(
            pv.Cube(x_length=30, y_length=30, z_length=30),
            color="#f59a87", style="wireframe", line_width=2,
            lighting=False, render=False, name="ik_target")
        self.target_actor.visibility = False
        self.plotter.add_mesh(
            pv.Plane(center=(0, 0, 0), direction=(0, 0, 1),
                     i_size=800, j_size=800, i_resolution=16, j_resolution=16),
            style="wireframe", color="#35424e", line_width=1,
        )
        self.plotter.add_axes(xlabel="X", ylabel="Y", zlabel="Z", color="#aebdc9")
        self.plotter.add_text("Z UP  /  50 mm GRID", position="upper_left",
                              font_size=10, color="#aebdc9", font="arial")
        self.reset_camera()

    def reset_camera(self):
        self.plotter.camera_position = [(650, -850, 580), (60, 0, 120), (0, 0, 1)]
        self.plotter.camera.parallel_projection = False
        self.plotter.render()

    def update_arm(self, model):
        self.arm.update(model)
        self.plotter.render()

    def set_target(self, target):
        self.target_actor.visibility = target is not None
        if target is not None:
            self.target_actor.position = target
        self.plotter.render()

    def shutdown(self):
        self.plotter.close()
