"""Reference scene only; no robot geometry or kinematics in Phase 1."""

import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QVBoxLayout, QWidget


class Viewport(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)
        self.plotter.set_background("#151c24")
        self.plotter.enable_trackball_style()
        # A dimensional reference object makes camera movement easy to inspect.
        self.plotter.add_mesh(
            pv.Cube(center=(0, 0, 40), x_length=80, y_length=80, z_length=80),
            color="#59bdb0", show_edges=True, edge_color="#244f50",
            smooth_shading=False,
        )
        self.plotter.add_mesh(
            pv.Plane(center=(0, 0, 0), direction=(0, 0, 1),
                     i_size=800, j_size=800, i_resolution=16, j_resolution=16),
            style="wireframe", color="#35424e", line_width=1,
        )
        self.plotter.add_axes(xlabel="X", ylabel="Y", zlabel="Z", color="#aebdc9")
        self.plotter.add_text("REFERENCE OBJECT  /  80 mm", position="upper_left",
                              font_size=10, color="#aebdc9", font="arial")
        self.reset_camera()

    def reset_camera(self):
        self.plotter.camera_position = [(650, -750, 550), (0, 0, 0), (0, 0, 1)]
        self.plotter.camera.parallel_projection = False
        self.plotter.render()

    def shutdown(self):
        self.plotter.close()
