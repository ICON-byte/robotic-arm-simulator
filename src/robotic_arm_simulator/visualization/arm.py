"""Reusable mechanical geometry positioned only by core model transforms."""

import pyvista as pv


class ArmVisual:
    def __init__(self, plotter, model):
        self.plotter = plotter
        self.actors = {}
        self.frames = {}
        geometry = model.geometry

        def add(name, mesh, color, frame=None, specular=0.35):
            actor = plotter.add_mesh(
                mesh, name=name, color=color, smooth_shading=True,
                ambient=0.25, diffuse=0.75, specular=specular, specular_power=32,
                split_sharp_edges=True, render=False,
            )
            self.actors[name] = actor
            if frame:
                self.frames[name] = frame

        def cylinder(center, radius, height, direction=(0, 0, 1)):
            return pv.Cylinder(center=center, direction=direction, radius=radius,
                               height=height, resolution=48)

        add("base_plate", cylinder((0, 0, 8), 60, 16), "#657788")
        add("base_bearing", cylinder((0, 0, 23), 41, 14), "#263b49")
        add("turntable", cylinder((0, 0, 35), 45, 10), "#59bdb0", "base")
        tower_height = geometry.shoulder_height - 40
        if tower_height > 0:
            add("pedestal", pv.Cube(center=(0, 0, 40 + tower_height / 2),
                                   x_length=40, y_length=40, z_length=tower_height),
                "#8fa4b5", "base")
        # An asymmetric face makes base yaw visible even when links are vertical.
        add("base_index", pv.Cube(center=(40, 0, 41), x_length=12, y_length=6, z_length=3),
            "#e2b77c", "base", specular=0.1)
        for name, length, frame in [("upper_arm", geometry.upper_arm_length, "shoulder"),
                                    ("forearm", geometry.forearm_length, "elbow")]:
            add(name, pv.Cube(center=(length / 2, 0, 0), x_length=length,
                             y_length=26, z_length=32), "#8fa4b5", frame)
            add(name + "_inlay", pv.Cube(center=(length / 2, -13.5, 0),
                                        x_length=length * 0.68, y_length=2, z_length=12),
                "#59bdb0", frame, specular=0.2)
        for joint in ("shoulder", "elbow"):
            add(joint + "_bearing", cylinder((0, 0, 0), 23, 52, (0, 1, 0)),
                "#263b49", joint)
            for side in (-1, 1):
                add(f"{joint}_cap_{side}", cylinder((0, side * 28, 0), 18, 5, (0, 1, 0)),
                    "#59bdb0", joint)
                add(f"{joint}_axle_{side}", cylinder((0, side * 31, 0), 6, 2, (0, 1, 0)),
                    "#d7e2e9", joint)
        # The collar stops at the mathematical endpoint; the gold marker is
        # centered exactly on it and never adds to either link length.
        add("tool_collar", cylinder((-10, 0, 0), 17, 20, (1, 0, 0)),
            "#263b49", "endpoint")
        add("endpoint", pv.Sphere(radius=9, theta_resolution=24, phi_resolution=24),
            "#e2b77c", "endpoint", specular=0.2)
        self.update(model)

    def update(self, model):
        transforms = model.transforms()
        for name, frame in self.frames.items():
            self.actors[name].user_matrix = transforms[frame]
