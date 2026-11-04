"""Motion timing and transitions use a controlled clock, never real sleeps."""

import numpy as np
import pytest

from robotic_arm_simulator.core.motion import (
    MIN_DURATION_SECONDS, MotionEngine, MotionState, SPEEDS, interpolate, smoothstep,
)
from robotic_arm_simulator.core.robot import RobotModel


class Clock:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


@pytest.fixture
def motion():
    return MotionEngine(RobotModel(), Clock())


@pytest.mark.parametrize("time,expected", [(0, 0), (0.25, 0.15625), (0.5, 0.5), (0.75, 0.84375), (1, 1), (-1, 0), (2, 1)])
def test_smoothstep_reference_values(time, expected):
    assert smoothstep(time) == expected


def test_easing_is_monotonic_and_has_zero_endpoint_velocity():
    values = [smoothstep(t) for t in np.linspace(0, 1, 101)]
    assert all(a <= b for a, b in zip(values, values[1:]))
    step = 1e-5
    assert (smoothstep(step) - smoothstep(0))/step < 0.0001
    assert (smoothstep(1) - smoothstep(1-step))/step < 0.0001


@pytest.mark.parametrize("progress,expected", [
    (0, (-180, -90, -135)), (0.25, (-123.75, -61.875, -92.8125)),
    (0.5, (0, 0, 0)), (1, (180, 90, 135)),
])
def test_interpolation_and_bounded_base_route(progress, expected):
    assert interpolate((-180, -90, -135), (180, 90, 135), progress) == expected


def test_interpolation_stays_within_joint_limits():
    for t in np.linspace(0, 1, 1001):
        angles = interpolate((-180, 90, -135), (180, -90, 135), t)
        for value, (low, high) in zip(angles, RobotModel.joint_limits):
            assert low <= value <= high


def test_elapsed_time_and_exact_fractional_completion(motion):
    target = (11.309932474, 46.123456789, -85.21987654)
    initial = motion.model.angles
    motion.start(target)
    motion.advance()
    assert motion.model.angles == initial
    motion.clock.now += motion.duration*0.25
    motion.advance()
    np.testing.assert_allclose(motion.model.angles, [a + 0.15625*(b-a) for a, b in zip(initial, target)])
    # A late timer tick goes directly to the exact target; no tick count drift.
    motion.clock.now += 100
    motion.advance()
    assert motion.model.angles == target
    assert motion.state == MotionState.COMPLETED
    assert motion.progress == 1


def test_pause_resume_excludes_paused_wall_time(motion):
    motion.start((180, 0, 90))
    motion.clock.now += motion.duration*0.25
    motion.pause()
    pose = motion.model.angles
    progress = motion.progress
    motion.clock.now += 1000
    motion.advance()
    motion.pause()
    assert motion.model.angles == pose
    assert motion.progress == progress
    assert motion.state == MotionState.PAUSED
    motion.resume()
    motion.resume()
    motion.advance()
    np.testing.assert_allclose(motion.model.angles, pose)
    motion.clock.now += motion.duration*0.75 + 0.0001
    motion.advance()
    assert motion.state == MotionState.COMPLETED
    assert motion.model.angles == (180, 0, 90)


@pytest.mark.parametrize("paused", [False, True])
def test_stop_holds_pose_and_repeated_controls_are_safe(motion, paused):
    motion.start((180, -90, 135))
    motion.clock.now += motion.duration/2
    if paused:
        motion.pause()
    motion.stop()
    pose = motion.model.angles
    assert motion.state == MotionState.CANCELLED
    motion.clock.now += 100
    motion.advance()
    motion.stop()
    motion.pause()
    motion.resume()
    assert motion.state == MotionState.CANCELLED
    assert motion.model.angles == pose


@pytest.mark.parametrize("state", ["running", "paused", "completed", "cancelled"])
def test_reset_from_each_motion_state(motion, state):
    motion.start((180, 0, 0))
    motion.clock.now += motion.duration/2
    if state == "paused":
        motion.pause()
    elif state == "completed":
        motion.clock.now += motion.duration
        motion.advance()
    elif state == "cancelled":
        motion.stop()
    motion.reset()
    motion.clock.now += 100
    motion.advance()
    assert motion.state == MotionState.IDLE
    assert motion.progress == 0
    assert motion.model.angles == motion.model.initial_angles


@pytest.mark.parametrize("paused", [False, True])
def test_replacement_begins_at_current_interpolated_pose(motion, paused):
    motion.start((180, 0, 90))
    motion.clock.now += motion.duration/2
    if paused:
        motion.pause()
    expected = interpolate(motion.start_angles, motion.target_angles, 0.5)
    motion.start((-30.125, 10.25, -60.5), "Fast")
    assert motion.start_angles == expected
    assert motion.model.angles == expected
    assert motion.state == MotionState.RUNNING
    assert motion.progress == 0
    motion.clock.now += motion.duration
    motion.advance()
    assert motion.model.angles == (-30.125, 10.25, -60.5)


@pytest.mark.parametrize("target", [(181, 0, 0), (0, 91, 0), (0, 0, 136), (float("nan"), 0, 0), (0, 0)])
def test_invalid_target_preserves_active_motion(motion, target):
    motion.start((100, 0, 0))
    before = (motion.model.angles, motion.target_angles, motion.duration, motion.state)
    with pytest.raises(ValueError):
        motion.start(target)
    assert (motion.model.angles, motion.target_angles, motion.duration, motion.state) == before


def test_invalid_speed_and_progress(motion):
    with pytest.raises(ValueError):
        motion.start((0, 0, 0), "Unknown")
    with pytest.raises(ValueError):
        smoothstep(float("nan"))
    assert motion.state == MotionState.IDLE


@pytest.mark.parametrize("speed", SPEEDS)
def test_duration_formula_and_minimum(motion, speed):
    motion.model.set_angles((-180, 0, 0))
    motion.start((180, 0, 0), speed)
    assert motion.duration == pytest.approx(1.5*360/SPEEDS[speed])
    motion.stop()
    motion.start((-179, 0, 0), speed)
    assert motion.duration == MIN_DURATION_SECONDS


def test_same_pose_finishes_without_timer(motion):
    motion.start(motion.model.angles)
    assert motion.state == MotionState.COMPLETED
    assert motion.progress == 1


@pytest.mark.parametrize("terminal", ["idle", "completed", "cancelled"])
def test_instant_pose_clears_stale_terminal_progress(motion, terminal):
    if terminal != "idle":
        motion.start((180, 0, 0))
        motion.clock.now += motion.duration/2
        if terminal == "completed":
            motion.clock.now += motion.duration
            motion.advance()
        else:
            motion.stop()
    motion.apply_instant((20.25, 15.5, -80.125))
    assert motion.state == MotionState.IDLE
    assert motion.progress == 0
    assert motion.model.angles == (20.25, 15.5, -80.125)


@pytest.mark.parametrize("paused", [False, True])
def test_instant_override_cancels_active_motion(motion, paused):
    motion.start((180, 0, 0))
    motion.clock.now += motion.duration/2
    if paused:
        motion.pause()
    motion.apply_instant((5, 10, 15))
    assert motion.state == MotionState.CANCELLED
    assert motion.model.angles == (5, 10, 15)
    motion.clock.now += 100
    motion.advance()
    assert motion.model.angles == (5, 10, 15)


def test_invalid_instant_pose_preserves_running_move(motion):
    motion.start((180, 0, 0))
    previous = (motion.model.angles, motion.target_angles, motion.state)
    with pytest.raises(ValueError):
        motion.apply_instant((181, 0, 0))
    assert (motion.model.angles, motion.target_angles, motion.state) == previous
