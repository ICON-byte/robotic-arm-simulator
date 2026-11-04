# Robotic Arm Kinematics Simulator

Phase 5 of a university course project: a native Windows desktop application with an interactive 3-DOF robotic arm, live forward kinematics, analytical inverse kinematics, and cancellable smooth joint motion. Adjust joints, apply an IK solution instantly or animate toward it, inspect live coordinates/matrices, and copy results for a course report.

## Launch

From this project directory in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m robotic_arm_simulator
```

No environment activation or PowerShell execution-policy change is necessary. The application runs locally without a server, API, database, or internet connection once dependencies are installed.

## Recreate the environment

Python 3.12 (64-bit) is required. The initial environment uses the existing Python 3.12.10 installation.

The GUI uses the official `PySide6-Essentials` distribution, which provides the `PySide6` QtWidgets/QtGui/QtCore modules used here. The full PySide6 meta-package would also install unused PDF and embedded-browser components. VTK and QtPy are installed through the visualization dependencies.

VTK is fixed at 9.5.2 rather than automatically selecting the newest renderer. NumPy is constrained below 2.5 to avoid upstream VTK array-shape deprecation warnings. The complete environment is recorded in the lock file after verification.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
```

`requirements-lock.txt` records the verified Windows environment. For dependency updates, use `pip install -e ".[dev]"`, verify the application, then regenerate the lock with `pip freeze --exclude-editable`.

If the Windows Store Python cannot write temporary files under a restricted shell, set `TEMP` and `TMP` to a writable temporary directory before creating the environment. Do not replace the global interpreter.

## Camera interaction

- Left drag: orbit the scene.
- Mouse wheel or right drag: zoom.
- Middle drag or Shift + left drag: pan.
- **Reset view** or **Ctrl+Home**: restore the perspective camera.

The ground grid has 50 mm spacing. The orientation marker identifies X/Y/Z; Z is upward. Switch the sidebar between **Joint angles** and **IK target** without resetting the robot. FK coordinates, the matrix, and Copy results remain available in either mode.

## Joint controls and geometry

| Parameter | Value |
|---|---|
| Shoulder height | 100 mm |
| Upper-arm length | 200 mm |
| Forearm length | 150 mm |
| Base limits | −180° to +180° |
| Shoulder limits | −90° to +90° |
| Elbow limits | −135° to +135° |
| Initial configuration | 0°, 45°, −90° |

Sliders use whole-degree positions and show the current angle and permitted range. Arrow keys adjust a focused slider; Home/End select its limits. After IK, labels retain fractional angles (up to three decimals), while slider thumbs indicate the nearest whole-degree position. Moving one slider changes only that joint; the other joints retain their exact IK angles. **Reset arm** restores the initial configuration, clears IK solutions/marker, and keeps the camera and target input text. **Reset view** restores the camera without changing the arm or target.

The right-handed frame has X forward, Y left, and Z up. Positive base rotation turns X toward Y. At shoulder 0°, the upper arm points horizontally outward; positive elevation raises it toward Z (a rotation about the local negative Y-axis). Elbow angles are relative to the upper arm; 0° is straight. The gold sphere is centered on the exact mathematical endpoint; decorative joint caps and tool collar do not extend link lengths.

`core/robot.py` owns the dimensions, limits, current angles, and homogeneous transforms. The shoulder frame is at the 100 mm pivot; the elbow and endpoint follow the 200 mm and 150 mm link translations. `visualization/arm.py` builds geometry once in these local frames and applies model transforms to existing actors. It never independently calculates joint positions. Calculations use radians internally, and invalid/nonfinite or out-of-limit configurations are rejected atomically.

## Forward kinematics

The panel below the scene updates immediately with the joint controls and Reset arm. The **Coordinates** tab shows X/Y/Z in millimetres and the current angles in degrees. The **4 × 4 matrix** tab displays every element of the tool-to-world homogeneous transform. Tabs share the same compact panel so the viewport retains its space.

Coordinates and matrices use three decimal places; rounded negative zero displays as `0.000`. Angle labels show up to three decimals, including fractional IK angles. Display rounding does not change the full-precision calculation or arm position.

**Copy results** writes a plain-text report containing joint angles, XYZ coordinates, units, and the full matrix to the local clipboard. Copying uses the current displayed result, including after a reset. Confirmation appears in the status bar.

`RobotModel.forward_kinematics()` returns an independent result snapshot containing the angles, shoulder position, elbow position, endpoint position, and final transform. It calls the existing transform chain; no second FK implementation or numerical solver is introduced. The core remains independent of GUI and rendering libraries.

For base `b`, shoulder `s`, elbow `e`, shoulder height `h`, and lengths `L1`, `L2`, the equivalent analytical equations are:

```text
r = L1*cos(s) + L2*cos(s + e)
x = r*cos(b)
y = r*sin(b)
z = h + L1*sin(s) + L2*sin(s + e)
```

These equations use radians. Independent tests compare them with the matrix chain. With all joints at 0°, the endpoint is `(350, 0, 100)` mm. The default pose gives approximately `(247.487, 0, 135.355)` mm.

The tool frame inherits forearm orientation: +X follows the forearm, +Y follows the yawed hinge axis, and +Z completes the right-handed frame. For homogeneous column vectors, `p_world = T_world_tool @ p_tool`. The last column contains the endpoint XYZ in millimetres; the upper-left 3 × 3 block is a dimensionless proper rotation, and the bottom row is `[0, 0, 0, 1]`. Orientation is determined by the three joints; it cannot be prescribed independently.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

The mathematical tests use independent reference poses, analytical FK/IK expectations, tool orientations, geometric invariants, branch checks, edge cases, and seeded round trips. Integration checks cover FK, IK calculate/select/apply, fractional angles, stale-target invalidation, marker agreement, failure-state preservation, resets, clipboard export, camera interaction, resizing, and shutdown. GUI tests require a desktop session and a working OpenGL driver. Optional screenshots: set `SIMULATOR_CAPTURE_DIR` to a writable directory before pytest. Headless checks: `python -m pytest tests/test_robot.py tests/test_inverse_kinematics.py -q`.

## Inverse kinematics

1. Open **IK target** and enter finite world-space X/Y/Z values in millimetres. Decimal and scientific notation are accepted; use a decimal point.
2. Click **Calculate IK**. The coral wire box marks the calculated target, including finite unreachable targets. Calculation does not move the robot.
3. Inspect every valid solution in the list (B = base, S = shoulder, E = elbow). The closest configuration is selected by default. List angles are rounded to two decimals; tooltips expose additional precision.
4. Select a solution and click **Apply instantly** for an immediate pose change, or **Move to solution** for smooth motion. Both use the full-precision configuration, update FK/matrix/angle readouts, and report Euclidean positioning error in mm. On completion, the gold endpoint should lie at the coral target's center.

Editing any target field clears stale solutions, disables Apply, and hides the old marker until Calculate is pressed again. Invalid inputs and failed calculations never change the robot pose. Existing solutions remain mathematically valid after manual joint changes; Calculate again to refresh their nearest-first order. Reset arm clears them.

`core/inverse_kinematics.py` solves both elbow signs with both signed radial branches: standard outward reach and an equivalent base orientation with reversed radial reach. Every candidate is normalized, checked against joint limits, verified through the existing FK implementation, and deduplicated. No out-of-limit angle is forced into range. Only an isolated temporary model is used for FK verification; the application has one shared current robot state.

Solutions are sorted by unweighted Euclidean joint distance in degrees. Each joint is bounded, so distance does not wrap through a mechanical stop. Physically equivalent base endpoints −180°/+180° appear once, using the representation nearest the current base. Elbow-up/down labels describe the elbow relative to the world-space shoulder-to-target chord; the reversed radial branch can reverse the usual elbow-sign label.

The base-axis singularity represents a continuous family with the current base angle, reported explicitly instead of returning infinitely many configurations. Fully extended elbow branches merge. Fully folded poses are geometrically reachable at the 50 mm inner boundary but require ±180° elbow rotation and are rejected under the configured ±135° limit.

### Numerical conventions

- FK position validation tolerance: **1e−6 mm**.
- Base-axis radius threshold: **1e−9 mm**.
- Equivalent-angle duplicate tolerance: **1e−7 degrees**.
- Analytic angles are rounded to ten decimal places to remove roundoff at exact limits; this is not joint-limit clamping.
- Shoulder-to-target reach is checked against 50–350 mm before evaluating acos. Only floating-point reach overshoot within the position tolerance is clipped to the acos domain; each solution still has to pass FK validation.

Errors distinguish invalid inputs, geometric unreachability, joint-limit restrictions, and numerical FK-validation failures. Singularity/boundary notes accompany successful calculations. No SciPy, background thread, numerical optimization, or network access is required.

## Motion controls

Calculate IK, select a valid solution, choose **Slow**, **Normal**, or **Fast**, and click **Move to solution**. The fixed transport below the scrollable sidebar keeps **Pause / Resume**, **Stop**, **Reset arm**, progress, status, and speed visible in either mode.

- **Pause** samples the current elapsed time and holds the interpolated pose. **Resume** continues the same motion, excluding paused wall time.
- **Stop** cancels and holds the current pose. It does not jump to the start, target, or default pose.
- **Reset arm** cancels motion and immediately restores `(0°, 45°, −90°)`, clears IK solutions/marker, retains target text and camera, and returns motion state to Idle. Reset is intentionally immediate.
- **Move to solution** during another move replaces it from the current sampled pose. Selecting a different solution alone does not move the arm.
- Editing/recalculating an IK target cancels active/paused motion before clearing stale solutions. A stale Move action cannot start a move.
- Manual sliders and **Apply instantly** cancel motion and apply the requested pose. Fractional values in the other joints remain intact when one slider changes.
- Switching Joint angles / IK target modes, choosing a result tab, copying results, or using camera controls does not stop motion. Closing the window stops the timer before renderer shutdown.

Motion states are **Idle**, **Running**, **Paused**, **Completed**, and **Cancelled**. Completed/Cancelled record the last motion until a new move or reset. Repeated inactive controls are harmless. A zero-distance move completes immediately at 100%. During active/paused motion the speed selector is locked; speed changes apply to the next movement.

### Timing and speed

The pure core engine interpolates each bounded joint with `theta = start + (3*t² − 2*t³)*(target − start)`. Here `t` is elapsed active time divided by duration, normalized to `[0, 1]`. There is no shortest-angle wrapping through a mechanical joint stop. Targets are validated before a current move is replaced; invalid targets are rejected without silently clamping them.

| Preset | Peak interpolated joint speed |
|---|---|
| Slow | 45°/s |
| Normal | 90°/s |
| Fast | 180°/s |

`duration = max(1.0 seconds, 1.5 * largest_absolute_joint_change / selected_peak_speed)`. The factor 1.5 accounts for smoothstep's maximum slope. All joints share that duration and arrive together. The 1-second minimum makes short moves observable. These are interpolation rates, not a physical actuator model.

A precise Qt timer requests an update every 20 ms (approximately 50 Hz). Motion uses `time.monotonic()` elapsed time, not a fixed tick count; missed frames skip to the correct elapsed pose, and the final frame assigns the exact target tuple. Fractional model angles, blocked slider updates, XYZ, matrix, target error, and existing actor transforms stay synchronized. Actual visual update rate depends on rendering hardware and system load.

## Structure

- `core/robot.py`: GUI-independent geometry, shared angle validation, joint state, transforms, and FK result snapshots.
- `core/motion.py`: GUI-independent smoothstep interpolation, monotonic timing, speed durations, and explicit motion state machine.
- `core/inverse_kinematics.py`: analytical candidate generation, validation, singularity handling, deduplication, and selection ordering.
- `visualization/arm.py`: reusable base, joints, links, and endpoint actors.
- `visualization/viewport.py`: arm scene, grid, camera, and renderer lifecycle.
- `ui/`: window layout, functional joint controls, future-mode explanations, and packaged Qt stylesheet.
- `ui/results.py`: live coordinates, joint summary, matrix tab, and clipboard export.
- `ui/inverse_controls.py`: target input, calculate/select/apply workflow, messages, and positioning-error feedback.
- `ui/motion_controls.py`: fixed speed, status/progress, pause/resume, stop, and reset transport; the main window owns its Qt timer.
- `tests/`: geometric reference checks and Qt/VTK integration regressions.

## Limitations and next phase

Hardware rendering depends on the local graphics driver. Dependency metadata alone cannot guarantee compatibility on other machines. Packaging and testing without a Python installation belong to Phase 7.

Joint limits do not provide collision avoidance: valid poses and interpolated motion can intersect the robot, base, or floor. Motion is a joint-space curve, not a straight Cartesian path or collision-free plan. There is no physical dynamics, torque, or actuator simulation. IK controls position only; tool orientation follows the chosen joints. The target marker may lie outside the current camera view; solving never resets the camera. No collision checks, Cartesian planning, numerical optimization, alternative robot selector, or standalone packaging is included.

Phase 6 should refine UI/accessibility and engineering presentation, validate edge cases, and address defects discovered in demonstration workflows. It requires separate approval. See the Phase 1–4 verification reports for history and `PHASE5_VERIFICATION.md` for current evidence.
