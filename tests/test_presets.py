"""Course demonstrations have independent expected geometry and valid targets."""

from math import sqrt

import numpy as np
import pytest

from robotic_arm_simulator.core.inverse_kinematics import solve_inverse_kinematics
from robotic_arm_simulator.core.presets import POSE_PRESETS, demonstration_target
from robotic_arm_simulator.core.robot import RobotModel


@pytest.mark.parametrize("name,expected", [
    ("Home position", (175*sqrt(2), 0, 100+25*sqrt(2))),
    ("Fully extended", (350, 0, 100)),
    ("Raised arm", (175, 0, 100+175*sqrt(3))),
    ("Elbow bend", (200, 0, 250)),
])
def test_pose_presets_have_independent_expected_endpoints(name, expected):
    model = RobotModel()
    model.set_angles(POSE_PRESETS[name])
    np.testing.assert_allclose(model.forward_kinematics().endpoint, expected, atol=1e-10)


def test_ik_preset_uses_shared_geometry_without_changing_current_pose():
    model = RobotModel()
    model.set_angles((70, 20, -30))
    target = demonstration_target(model)
    expected = (112.5+50*sqrt(3), 50+37.5*sqrt(3), 25+100*sqrt(3))
    np.testing.assert_allclose(target, expected, atol=1e-10)
    assert model.angles == (70, 20, -30)
    result = solve_inverse_kinematics(model, target)
    assert len(result.solutions) >= 2
    assert all(solution.error_mm <= 1e-6 for solution in result.solutions)
    for solution in result.solutions:
        model.set_angles(solution.angles)
        assert model.joint_positions()["elbow"][2] > 0
