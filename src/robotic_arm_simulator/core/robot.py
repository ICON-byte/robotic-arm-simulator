"""Three-joint arm geometry, in millimetres and user-facing degrees.

Column-vector transforms use a right-handed world frame: X forward, Y left,
Z up. Positive shoulder elevation raises local X toward Z (rotation about -Y).
The elbow angle is relative to the upper arm, with zero meaning straight.
"""

from dataclasses import dataclass
from math import cos, isfinite, radians, sin

import numpy as np

JOINT_NAMES = ("Base", "Shoulder", "Elbow")
JOINT_LIMITS = ((-180, 180), (-90, 90), (-135, 135))
INITIAL_ANGLES = (0.0, 45.0, -90.0)


@dataclass(frozen=True)
class ForwardKinematicsResult:
    """Snapshot in world coordinates; positions/translation use millimetres.

    transform maps tool-frame column vectors to world. Tool +X follows the
    forearm, +Y is the yawed hinge axis, and +Z completes the right-handed frame.
    Arrays are independent copies, so modifying a result cannot change the arm.
    """

    angles: tuple[float, float, float]
    shoulder: np.ndarray
    elbow: np.ndarray
    endpoint: np.ndarray
    transform: np.ndarray


@dataclass(frozen=True)
class RobotGeometry:
    shoulder_height: float = 100.0
    upper_arm_length: float = 200.0
    forearm_length: float = 150.0

    def __post_init__(self):
        for value in (self.shoulder_height, self.upper_arm_length, self.forearm_length):
            if not isfinite(value) or value <= 0:
                raise ValueError("Robot dimensions must be finite and positive.")


def _translation(x=0.0, y=0.0, z=0.0):
    matrix = np.eye(4)
    matrix[:3, 3] = (x, y, z)
    return matrix


def _elevation(degrees):
    angle = radians(degrees)
    c, s = cos(angle), sin(angle)
    return np.array([[c, 0, -s, 0], [0, 1, 0, 0],
                     [s, 0, c, 0], [0, 0, 0, 1]], dtype=float)


class RobotModel:
    """Single source of truth for the arm; no rendering or Qt dependencies."""

    joint_names = JOINT_NAMES
    joint_limits = JOINT_LIMITS
    initial_angles = INITIAL_ANGLES

    def __init__(self, geometry=None):
        self.geometry = geometry or RobotGeometry()
        self._angles = INITIAL_ANGLES

    @property
    def angles(self):
        return self._angles

    @staticmethod
    def validate_angles(angles):
        """Validate without changing state; shared by direct and animated moves."""
        values = tuple(float(value) for value in angles)
        if len(values) != 3:
            raise ValueError("Exactly three joint angles are required.")
        for name, value, (low, high) in zip(JOINT_NAMES, values, JOINT_LIMITS):
            if not isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be between {low}° and {high}°.")
        return values

    def set_angles(self, angles):
        self._angles = self.validate_angles(angles)

    def reset(self):
        self._angles = INITIAL_ANGLES

    def transforms(self):
        """Return independent local-to-world matrices for each component frame."""
        base_angle, shoulder_angle, elbow_angle = self._angles
        c, s = cos(radians(base_angle)), sin(radians(base_angle))
        base = np.array([[c, -s, 0, 0], [s, c, 0, 0],
                         [0, 0, 1, 0], [0, 0, 0, 1]], dtype=float)
        shoulder = base @ _translation(z=self.geometry.shoulder_height) @ _elevation(shoulder_angle)
        elbow = shoulder @ _translation(x=self.geometry.upper_arm_length) @ _elevation(elbow_angle)
        endpoint = elbow @ _translation(x=self.geometry.forearm_length)
        return {"base": base, "shoulder": shoulder, "elbow": elbow, "endpoint": endpoint}

    def joint_positions(self):
        """World positions of the base, shoulder, elbow, and mathematical endpoint."""
        return {name: matrix[:3, 3].copy() for name, matrix in self.transforms().items()}

    def forward_kinematics(self):
        """Reuse the same transformation chain that positions the rendered arm."""
        frames = self.transforms()
        return ForwardKinematicsResult(
            angles=self.angles,
            shoulder=frames["shoulder"][:3, 3].copy(),
            elbow=frames["elbow"][:3, 3].copy(),
            endpoint=frames["endpoint"][:3, 3].copy(),
            transform=frames["endpoint"].copy(),
        )
