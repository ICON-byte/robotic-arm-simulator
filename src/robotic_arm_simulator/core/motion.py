"""Deterministic smoothstep motion; Qt only supplies periodic advance calls."""

from enum import Enum
from math import isfinite
from time import monotonic

from .robot import RobotModel

# Peak joint speeds in degrees/s; smoothstep has a maximum slope of 1.5.
SPEEDS = {"Slow": 45.0, "Normal": 90.0, "Fast": 180.0}
MIN_DURATION_SECONDS = 1.0


class MotionState(str, Enum):
    IDLE = "Idle"
    RUNNING = "Running"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


def smoothstep(progress):
    if not isfinite(progress):
        raise ValueError("Motion progress must be finite.")
    t = min(1.0, max(0.0, progress))
    return min(1.0, max(0.0, 3*t*t - 2*t*t*t))


def interpolate(start, target, progress):
    start = RobotModel.validate_angles(start)
    target = RobotModel.validate_angles(target)
    factor = smoothstep(progress)
    if factor == 0:
        return start
    if factor == 1:
        return target
    return tuple(a + factor*(b-a) for a, b in zip(start, target))


class MotionEngine:
    """One bounded motion on the shared robot; injectable clock for tests.

    Start validates before touching an old move. Replacements sample the old
    move's current time, then start from that pose. Stop and pause also sample
    the current time; paused wall time is excluded on resume. Reset is immediate.
    """

    def __init__(self, model, clock=monotonic):
        self.model = model
        self.clock = clock
        self.state = MotionState.IDLE
        self.start_angles = model.angles
        self.target_angles = model.angles
        self.speed = "Normal"
        self.duration = 0.0
        self.elapsed = 0.0
        self._started_at = 0.0

    @property
    def active(self):
        return self.state in (MotionState.RUNNING, MotionState.PAUSED)

    @property
    def progress(self):
        if self.state == MotionState.COMPLETED:
            return 1.0
        return min(1.0, self.elapsed / self.duration) if self.duration else 0.0

    def start(self, target, speed="Normal"):
        target = self.model.validate_angles(target)
        if speed not in SPEEDS:
            raise ValueError("Select Slow, Normal, or Fast motion speed.")
        if self.state == MotionState.RUNNING:
            self.advance()
        self.start_angles = self.model.angles
        self.target_angles = target
        self.speed = speed
        delta = max(abs(b-a) for a, b in zip(self.start_angles, target))
        self.elapsed = 0.0
        self._started_at = self.clock()
        if delta == 0:
            self.duration = 0.0
            self.model.set_angles(target)
            self.state = MotionState.COMPLETED
        else:
            self.duration = max(MIN_DURATION_SECONDS, 1.5*delta/SPEEDS[speed])
            self.state = MotionState.RUNNING

    def advance(self):
        if self.state != MotionState.RUNNING:
            return self.model.angles
        self.elapsed = min(self.duration, max(0.0, self.clock() - self._started_at))
        if self.elapsed >= self.duration:
            self.model.set_angles(self.target_angles)
            self.state = MotionState.COMPLETED
        else:
            self.model.set_angles(interpolate(self.start_angles, self.target_angles, self.progress))
        return self.model.angles

    def pause(self):
        if self.state == MotionState.RUNNING:
            self.advance()
            if self.state == MotionState.RUNNING:
                self.state = MotionState.PAUSED

    def resume(self):
        if self.state == MotionState.PAUSED:
            self._started_at = self.clock() - self.elapsed
            self.state = MotionState.RUNNING

    def stop(self):
        if self.state == MotionState.RUNNING:
            self.advance()
        if self.active:
            self.state = MotionState.CANCELLED

    def apply_instant(self, target):
        """Take direct control, clearing stale terminal progress for a new pose."""
        target = self.model.validate_angles(target)
        interrupted = self.active
        self.stop()
        self.model.set_angles(target)
        if interrupted:
            self.state = MotionState.CANCELLED
        else:
            self.start_angles = self.target_angles = target
            self.elapsed = self.duration = 0.0
            self.state = MotionState.IDLE

    def reset(self):
        self.model.reset()
        self.start_angles = self.target_angles = self.model.angles
        self.elapsed = self.duration = 0.0
        self.state = MotionState.IDLE
