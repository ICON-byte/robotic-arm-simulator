"""Analytical references, branch completeness, singularities and state safety."""

from math import sqrt

import numpy as np
import pytest

from robotic_arm_simulator.core.inverse_kinematics import (
    IKError, POSITION_TOLERANCE_MM, joint_distance, solve_inverse_kinematics,
)
from robotic_arm_simulator.core.robot import RobotModel


def test_two_independent_elbow_configurations():
    model = RobotModel()
    result = solve_inverse_kinematics(model, (250, 0, 100))
    assert len(result.solutions) == 2
    up, down = result.solutions
    np.testing.assert_allclose(up.angles, (0, 36.869897645844, -90), atol=1e-8)
    np.testing.assert_allclose(down.angles, (0, -36.869897645844, 90), atol=1e-8)
    assert "Elbow up" in up.branch and "Elbow down" in down.branch
    assert model.angles == model.initial_angles


@pytest.mark.parametrize("target,yaw", [
    ((250, 0, 100), 0), ((0, 250, 100), 90), ((0, -250, 100), -90),
    ((-250, 0, 100), 180),
    ((125*sqrt(2), 125*sqrt(2), 100), 45),
    ((-125*sqrt(2), 125*sqrt(2), 100), 135),
    ((-125*sqrt(2), -125*sqrt(2), 100), -135),
    ((125*sqrt(2), -125*sqrt(2), 100), -45),
])
def test_base_quadrants(target, yaw):
    model = RobotModel()
    model.set_angles((yaw, 45, -90))
    result = solve_inverse_kinematics(model, target)
    assert len(result.solutions) == 2
    for solution in result.solutions:
        assert solution.angles[0] == pytest.approx(yaw)
        assert solution.error_mm <= POSITION_TOLERANCE_MM


def test_negative_signed_radial_branch_not_discarded():
    result = solve_inverse_kinematics(RobotModel(), (-150, 0, 300))
    assert len(result.solutions) == 3
    reversed_solution = [s for s in result.solutions if "Reversed reach" in s.branch]
    assert len(reversed_solution) == 1
    np.testing.assert_allclose(reversed_solution[0].angles, (0, 90, 90), atol=1e-8)
    assert any(np.allclose(s.angles, (-180, 90, -90)) for s in result.solutions)


@pytest.mark.parametrize("current,expected", [(170, 180), (-170, -180)])
def test_equivalent_base_endpoints_choose_nearest_bounded_representation(current, expected):
    model = RobotModel()
    model.set_angles((current, 45, -90))
    result = solve_inverse_kinematics(model, (-250, 0, 100))
    assert len(result.solutions) == 2
    assert all(s.angles[0] == expected for s in result.solutions)
    assert joint_distance((179, 0, 0), (-179, 0, 0)) == 358


def test_default_selection_uses_current_configuration():
    model = RobotModel()
    model.set_angles((0, -30, 90))
    result = solve_inverse_kinematics(model, (250, 0, 100))
    assert "Elbow down" in result.solutions[0].branch
    assert result.solutions[0].distance_degrees < result.solutions[1].distance_degrees


@pytest.mark.parametrize("base", [37.25, -180, 180, 179.99999998])
def test_axis_preserves_current_base_and_reports_singularity(base):
    model = RobotModel()
    model.set_angles((base, 0, 0))
    result = solve_inverse_kinematics(model, (0, 0, 450))
    assert len(result.solutions) == 1
    assert result.solutions[0].angles == (base, 90, 0)
    assert any("Base-axis" in note for note in result.notes)


def test_extended_boundary_branches_merge():
    result = solve_inverse_kinematics(RobotModel(), (350, 0, 100))
    assert len(result.solutions) == 1
    assert result.solutions[0].angles == (0, 0, 0)
    assert any("extended" in note for note in result.notes)


@pytest.mark.parametrize("target,code", [
    ((351, 0, 100), "unreachable"), ((0, 0, 100), "unreachable"),
    ((49, 0, 100), "unreachable"), ((100, 0, 100), "joint_limits"),
    ((50, 0, 100), "joint_limits"), ((0, 0, 150), "joint_limits"),
    ((1e308, 1e308, 1e308), "unreachable"),
    ((float("nan"), 0, 0), "invalid_input"),
    ((0, float("inf"), 0), "invalid_input"),
    ((0, 0), "invalid_input"), ((0, 0, 0, 0), "invalid_input"),
    (("bad", 0, 0), "invalid_input"), (None, "invalid_input"),
])
def test_failures_classified_without_mutation(target, code):
    model = RobotModel()
    before = model.angles
    with pytest.raises(IKError) as failure:
        solve_inverse_kinematics(model, target)
    assert failure.value.code == code
    assert model.angles == before


def test_near_workspace_boundary_tolerance_and_no_limit_clamping():
    model = RobotModel()
    result = solve_inverse_kinematics(model, (350 + 0.5e-6, 0, 100))
    assert result.solutions[0].error_mm <= POSITION_TOLERANCE_MM
    with pytest.raises(IKError, match="unreachable"):
        solve_inverse_kinematics(model, (350 + 2e-6, 0, 100))
    # A folded elbow cannot be made valid by forcing its angle to 135 degrees.
    with pytest.raises(IKError) as failure:
        solve_inverse_kinematics(model, (50, 0, 100))
    assert failure.value.code == "joint_limits"
    assert "180" in str(failure.value)


def test_round_trips_include_limits_and_random_configurations():
    rng = np.random.default_rng(401)
    model = RobotModel()
    poses = [(0, 90, 90), (45, -90, -90), (-180, -90, -135),
             (180, 90, 135), model.initial_angles]
    poses.extend(rng.uniform([-180, -90, -135], [180, 90, 135], size=(150, 3)))
    for pose in poses:
        model.set_angles(pose)
        target = model.forward_kinematics().endpoint
        result = solve_inverse_kinematics(model, target)
        assert model.angles == tuple(pose)
        assert any(np.allclose(solution.angles, pose, atol=1e-6) for solution in result.solutions)
        for solution in result.solutions:
            assert all(np.isfinite(solution.angles))
            assert solution.error_mm <= POSITION_TOLERANCE_MM
            for value, (low, high) in zip(solution.angles, model.joint_limits):
                assert low <= value <= high


def test_fk_validation_failure_has_numerical_error(monkeypatch):
    from dataclasses import replace
    original = RobotModel.forward_kinematics
    monkeypatch.setattr(RobotModel, "forward_kinematics", lambda self: replace(original(self), endpoint=np.array([999., 0, 0])))
    with pytest.raises(IKError) as failure:
        solve_inverse_kinematics(RobotModel(), (250, 0, 100))
    assert failure.value.code == "numerical"
