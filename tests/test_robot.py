"""Independent reference poses and geometric invariants for the 3-DOF arm."""

from math import sqrt

import numpy as np
import pytest

from robotic_arm_simulator.core.robot import INITIAL_ANGLES, RobotGeometry, RobotModel


def test_initial_geometry_and_configuration():
    robot = RobotModel()
    assert robot.angles == (0, 45, -90)
    assert robot.geometry == RobotGeometry(100, 200, 150)
    positions = robot.joint_positions()
    np.testing.assert_allclose(positions["base"], (0, 0, 0), atol=1e-10)
    np.testing.assert_allclose(positions["shoulder"], (0, 0, 100), atol=1e-10)
    np.testing.assert_allclose(positions["elbow"], (100 * sqrt(2), 0, 100 + 100 * sqrt(2)), atol=1e-10)
    np.testing.assert_allclose(positions["endpoint"], (175 * sqrt(2), 0, 100 + 25 * sqrt(2)), atol=1e-10)


@pytest.mark.parametrize("angles,elbow,endpoint", [
    ((0, 0, 0), (200, 0, 100), (350, 0, 100)),
    ((90, 0, 0), (0, 200, 100), (0, 350, 100)),
    ((-90, 0, 0), (0, -200, 100), (0, -350, 100)),
    ((180, 0, 0), (-200, 0, 100), (-350, 0, 100)),
    ((0, 90, 0), (0, 0, 300), (0, 0, 450)),
    ((0, -90, 0), (0, 0, -100), (0, 0, -250)),
    ((0, 0, 90), (200, 0, 100), (200, 0, 250)),
    ((0, 0, -90), (200, 0, 100), (200, 0, -50)),
    ((90, 0, 90), (0, 200, 100), (0, 200, 250)),
])
def test_known_poses(angles, elbow, endpoint):
    robot = RobotModel()
    robot.set_angles(angles)
    positions = robot.joint_positions()
    np.testing.assert_allclose(positions["shoulder"], (0, 0, 100), atol=1e-10)
    np.testing.assert_allclose(positions["elbow"], elbow, atol=1e-10)
    np.testing.assert_allclose(positions["endpoint"], endpoint, atol=1e-10)
    result = robot.forward_kinematics()
    np.testing.assert_allclose(result.shoulder, (0, 0, 100), atol=1e-10)
    np.testing.assert_allclose(result.elbow, elbow, atol=1e-10)
    np.testing.assert_allclose(result.endpoint, endpoint, atol=1e-10)
    np.testing.assert_allclose(result.transform[:3, 3], endpoint, atol=1e-10)


@pytest.mark.parametrize("angles", [
    (-180, -90, -135), (180, 90, 135), (40, 23, -70), INITIAL_ANGLES,
])
def test_rigid_transforms_and_link_lengths(angles):
    robot = RobotModel()
    robot.set_angles(angles)
    transforms = robot.transforms()
    for transform in transforms.values():
        rotation = transform[:3, :3]
        np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-12)
        assert np.linalg.det(rotation) == pytest.approx(1)
        np.testing.assert_array_equal(transform[3], (0, 0, 0, 1))
    positions = robot.joint_positions()
    assert np.linalg.norm(positions["elbow"] - positions["shoulder"]) == pytest.approx(200)
    assert np.linalg.norm(positions["endpoint"] - positions["elbow"]) == pytest.approx(150)


@pytest.mark.parametrize("angles", [
    (181, 0, 0), (-181, 0, 0), (0, 91, 0), (0, -91, 0),
    (0, 0, 136), (0, 0, -136), (float("nan"), 0, 0),
    (0, float("inf"), 0), (0, 0, -float("inf")), (0, 0), (0, 0, 0, 0),
])
def test_invalid_angles_rejected_atomically(angles):
    robot = RobotModel()
    with pytest.raises(ValueError):
        robot.set_angles(angles)
    assert robot.angles == INITIAL_ANGLES


def test_elbow_motion_preserves_upstream_frames_and_reset():
    robot = RobotModel()
    original = robot.transforms()
    robot.set_angles((0, 45, 30))
    changed = robot.transforms()
    for name in ("base", "shoulder"):
        np.testing.assert_allclose(changed[name], original[name])
    np.testing.assert_allclose(changed["elbow"][:3, 3], original["elbow"][:3, 3])
    assert not np.allclose(changed["endpoint"], original["endpoint"])
    robot.reset()
    assert robot.angles == INITIAL_ANGLES
    np.testing.assert_allclose(robot.transforms()["endpoint"], original["endpoint"])


@pytest.mark.parametrize("dimension", [0, -1, float("nan"), float("inf")])
def test_dimensions_must_be_positive_and_finite(dimension):
    with pytest.raises(ValueError):
        RobotGeometry(upper_arm_length=dimension)


@pytest.mark.parametrize("angles,expected", [
    ((0, 0, 0), [[1, 0, 0, 350], [0, 1, 0, 0], [0, 0, 1, 100], [0, 0, 0, 1]]),
    ((90, 0, 0), [[0, -1, 0, 0], [1, 0, 0, 350], [0, 0, 1, 100], [0, 0, 0, 1]]),
    ((0, 90, 0), [[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 450], [0, 0, 0, 1]]),
    ((0, -90, 0), [[0, 0, 1, 0], [0, 1, 0, 0], [-1, 0, 0, -250], [0, 0, 0, 1]]),
])
def test_fk_tool_frame_known_orientations(angles, expected):
    robot = RobotModel()
    robot.set_angles(angles)
    np.testing.assert_allclose(robot.forward_kinematics().transform, expected, atol=1e-10)


@pytest.mark.parametrize("base", [-180, 33, 180])
@pytest.mark.parametrize("shoulder,elbow", [(-90, -135), (90, 135), (27, -63)])
def test_fk_against_independent_closed_form(base, shoulder, elbow):
    robot = RobotModel()
    robot.set_angles((base, shoulder, elbow))
    result = robot.forward_kinematics()
    b, s, e = np.deg2rad([base, shoulder, elbow])
    # Independent planar trigonometry, rather than replaying matrix products.
    radius = 200 * np.cos(s) + 150 * np.cos(s + e)
    expected = (radius * np.cos(b), radius * np.sin(b),
                100 + 200 * np.sin(s) + 150 * np.sin(s + e))
    np.testing.assert_allclose(result.endpoint, expected, atol=1e-10)
    expected_rotation = [[np.cos(b)*np.cos(s+e), -np.sin(b), -np.cos(b)*np.sin(s+e)],
                         [np.sin(b)*np.cos(s+e), np.cos(b), -np.sin(b)*np.sin(s+e)],
                         [np.sin(s+e), 0, np.cos(s+e)]]
    assert result.transform.shape == (4, 4)
    rotation = result.transform[:3, :3]
    np.testing.assert_allclose(rotation, expected_rotation, atol=1e-10)
    np.testing.assert_allclose(rotation.T @ rotation, np.eye(3), atol=1e-12)
    assert np.linalg.det(rotation) == pytest.approx(1)
    np.testing.assert_array_equal(result.transform[:3, 3], result.endpoint)
    np.testing.assert_array_equal(result.transform[3], (0, 0, 0, 1))


def test_fk_default_and_independent_snapshot():
    robot = RobotModel()
    result = robot.forward_kinematics()
    np.testing.assert_allclose(result.endpoint, (175*sqrt(2), 0, 100+25*sqrt(2)), atol=1e-10)
    assert result.angles == INITIAL_ANGLES
    robot.set_angles((0, 0, 0))
    assert result.angles == INITIAL_ANGLES
    result.transform[0, 3] = -999
    np.testing.assert_allclose(result.endpoint, (175*sqrt(2), 0, 100+25*sqrt(2)), atol=1e-10)
    np.testing.assert_allclose(robot.forward_kinematics().endpoint, (350, 0, 100))
