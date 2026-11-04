"""Analytical, position-only IK for the established bounded yaw/pitch/pitch arm."""

from dataclasses import dataclass
from math import acos, atan2, cos, degrees, hypot, isfinite, pi, sin, sqrt

from .robot import RobotModel

POSITION_TOLERANCE_MM = 1e-6
AXIS_TOLERANCE_MM = 1e-9
ANGLE_TOLERANCE_DEG = 1e-7


class IKError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class IKSolution:
    angles: tuple[float, float, float]
    branch: str
    error_mm: float
    distance_degrees: float


@dataclass(frozen=True)
class IKResult:
    target: tuple[float, float, float]
    solutions: tuple[IKSolution, ...]
    notes: tuple[str, ...]


def joint_distance(angles, current):
    """Bounded-joint Euclidean distance; never wrap through a mechanical stop."""
    return sqrt(sum((a - b) ** 2 for a, b in zip(angles, current)))


def _equivalent(a, b):
    return all(abs((x - y + 180) % 360 - 180) < ANGLE_TOLERANCE_DEG for x, y in zip(a, b))


def _normalize(angle):
    # Rounding removes arithmetic noise at exact limits, not invalid angles.
    return round((degrees(angle) + 180) % 360 - 180, 10)


def solve_inverse_kinematics(model, target):
    """Return all discrete valid branches, nearest first, without changing model.

    Axis targets have a continuous base family; represent it with current base.
    Equivalent +/-180 base endpoints use the representative nearest current.
    All candidates are verified by the existing full-precision FK implementation.
    """
    try:
        target = tuple(float(value) for value in target)
    except (TypeError, ValueError, OverflowError) as exc:
        raise IKError("invalid_input", "Enter three finite target coordinates in millimetres.") from exc
    if len(target) != 3 or not all(isfinite(value) for value in target):
        raise IKError("invalid_input", "Enter three finite target coordinates in millimetres.")
    x, y, z = target
    geometry = model.geometry
    l1, l2 = geometry.upper_arm_length, geometry.forearm_length
    radial = hypot(x, y)
    height = z - geometry.shoulder_height
    distance = hypot(radial, height)
    inner, outer = abs(l1 - l2), l1 + l2
    if distance < inner - POSITION_TOLERANCE_MM or distance > outer + POSITION_TOLERANCE_MM:
        raise IKError("unreachable", f"Geometrically unreachable: shoulder-to-target distance must be {inner:g}–{outer:g} mm.")
    d = (distance * distance - l1*l1 - l2*l2) / (2*l1*l2)
    # Only reach-boundary floating-point overshoot within the position tolerance
    # reaches this point. Never clamp a candidate to joint-angle limits.
    d = min(1.0, max(-1.0, d))
    elbow_magnitude = acos(d)
    notes = []
    on_axis = radial <= AXIS_TOLERANCE_MM
    if on_axis:
        notes.append("Base-axis singularity: current base angle represents the continuous base family.")
        radial_branches = [(0.0, None, "Axis")]
    else:
        yaw = atan2(y, x)
        radial_branches = [(radial, yaw, "Outward"), (-radial, yaw + pi, "Reversed reach")]
    if elbow_magnitude == 0:
        notes.append("Fully extended singularity: elbow branches merge.")
    if distance > outer or distance < inner:
        notes.append("Target is within the reach-boundary numerical tolerance.")
    verifier = RobotModel(geometry)
    solutions = []
    failed_validation = False
    for signed_radius, yaw, radial_name in radial_branches:
        base = model.angles[0] if yaw is None else _normalize(yaw)
        bases = [base]
        if not on_axis and abs(abs(base) - 180) < ANGLE_TOLERANCE_DEG:
            bases = [-180.0, 180.0]
        for elbow in (elbow_magnitude, -elbow_magnitude):
            shoulder = atan2(height, signed_radius) - atan2(l2*sin(elbow), l1 + l2*cos(elbow))
            s, e = _normalize(shoulder), _normalize(elbow)
            for b in bases:
                angles = (b, s, e)
                if any(not low <= value <= high for value, (low, high) in zip(angles, model.joint_limits)):
                    continue
                verifier.set_angles(angles)
                endpoint = verifier.forward_kinematics().endpoint
                error = hypot(*(float(a) - b for a, b in zip(endpoint, target)))
                if not isfinite(error) or error > POSITION_TOLERANCE_MM:
                    failed_validation = True
                    continue
                if abs(e) < ANGLE_TOLERANCE_DEG:
                    elbow_name = "Straight"
                elif on_axis:
                    elbow_name = "Positive elbow" if e > 0 else "Negative elbow"
                else:
                    elbow_name = "Elbow up" if e * signed_radius < 0 else "Elbow down"
                candidate = IKSolution(angles, f"{elbow_name} · {radial_name}", error,
                                       joint_distance(angles, model.angles))
                duplicate = next((i for i, old in enumerate(solutions) if _equivalent(old.angles, angles)), None)
                if duplicate is None:
                    solutions.append(candidate)
                elif candidate.distance_degrees < solutions[duplicate].distance_degrees:
                    solutions[duplicate] = candidate
    if not solutions:
        if failed_validation:
            raise IKError("numerical", "Candidates failed the FK position-tolerance check; try a nearby target.")
        folded = " Fully folded configurations require an elbow angle of 180°, outside its limits." if abs(d + 1) < 1e-12 else ""
        raise IKError("joint_limits", "Geometrically reachable, but no solution satisfies the configured joint limits." + folded)
    solutions.sort(key=lambda solution: (solution.distance_degrees, solution.angles))
    return IKResult(target, tuple(solutions), tuple(notes))
