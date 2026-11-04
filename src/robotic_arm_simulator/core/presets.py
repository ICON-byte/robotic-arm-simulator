"""Small, explicit demonstrations for the existing robot, not robot variants."""

from .robot import INITIAL_ANGLES, RobotModel

POSE_PRESETS = {
    "Home position": INITIAL_ANGLES,
    "Fully extended": (0.0, 0.0, 0.0),
    "Raised arm": (0.0, 60.0, 0.0),
    "Elbow bend": (0.0, 0.0, 90.0),
}
IK_PRESET_NAME = "IK demonstration"
PRESET_NAMES = (*POSE_PRESETS, IK_PRESET_NAME)


def demonstration_target(model):
    """Derive a reachable target through shared FK without changing the pose."""
    reference = RobotModel(model.geometry)
    reference.set_angles((30.0, 60.0, -90.0))
    return tuple(float(value) for value in reference.forward_kinematics().endpoint)
