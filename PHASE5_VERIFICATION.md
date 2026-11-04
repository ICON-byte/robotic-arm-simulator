# Phase 5 verification

Verified on 4 November 2026 in the existing project-local Python 3.12.10 Windows environment. No frameworks, threads, dependencies, global environment changes, or packaging work were introduced.

## Files and architecture

Created:

- `core/motion.py`: pure smoothstep interpolation, speed durations, monotonic timing, and explicit motion states.
- `ui/motion_controls.py`: fixed transport with speed, state/progress, Pause/Resume, Stop, and shared Reset arm.
- `tests/test_motion.py`: deterministic interpolation and state-transition verification with an injected clock.
- This report and motion captures under `.impeccable/review/phase5/`.

Modified `core/robot.py` to share nonmutating angle validation with motion. Modified `ui/main_window.py`, `ui/inverse_controls.py`, `ui/controls.py`, and `ui/theme.qss` for timer integration, move/instant actions, and transport layout. Extended `tests/test_foundation.py`. Updated README, PRODUCT, DESIGN, and the native design sidecar. Existing FK/IK mathematics and reusable arm geometry remain the source of truth.

## Motion contract

The engine interpolates each joint from a captured start to a validated target with `f(t) = 3t² − 2t³`. All three joints share the normalized elapsed-time factor and arrive together. The easing derivative is zero at each endpoint. Direct bounded joint differences are used, including full base rotations through the permitted interval; no shortest-angle wrapping crosses a mechanical stop.

The state machine has Idle, Running, Paused, Completed, and Cancelled states. It drives the application's one shared robot model. Targets are validated before an existing move is touched. Intermediate configurations are validated through the same model constraints. On completion the exact target tuple is assigned, avoiding accumulated interpolation drift and preserving fractional IK angles.

A precise QTimer requests updates every **20 ms**, targeting approximately **50 visual updates/s** where the machine can keep up. The engine uses `time.monotonic()` elapsed time, not timer tick counts. Late timer events sample the appropriate current pose rather than extending movement duration. The pure engine has an injectable clock for deterministic tests.

### Speed and duration

| Speed | Peak interpolated joint rate |
|---|---|
| Slow | 45°/s |
| Normal | 90°/s |
| Fast | 180°/s |

`duration = max(1.0 s, 1.5 × largest absolute joint change / peak rate)`. Smoothstep's maximum slope is 1.5. The minimum keeps short moves observable; sufficiently small moves can share the same 1-second duration at different presets. A zero-distance command completes immediately. The speed selector is locked during Running/Paused and changes apply to the next move.

## Controls and consistency

- **Move to solution** animates to the selected valid IK configuration. **Apply instantly** retains immediate application and cancels any active move.
- **Pause** samples the current monotonic time, holds that pose, and stops the timer. **Resume** excludes paused wall time and restarts the timer for the remaining motion.
- **Stop** cancels and holds the current sampled pose. It does not jump to the start, default, or target.
- **Reset arm** immediately stops motion, restores `(0°, 45°, −90°)`, returns to Idle/0%, and clears IK solutions/marker. Target input text, camera, and speed selection are retained.
- A replacement Move samples the current pose and starts a fresh curve from it. Selecting a different solution alone does not move the arm.
- Target edits or recalculation cancel Running/Paused movement before invalidating stale IK choices. Invalidated choices cannot initiate another move.
- Manual sliders cancel movement and apply the requested configuration, preserving the other joints' fractional values.
- Mode/result-tab switches, camera interaction, and copying results do not cancel movement. Completed/Cancelled transport states record the last motion until a new move or reset.
- Every update refreshes joint labels, blocked whole-degree slider thumbs, XYZ, the matrix, target error, and existing actor transforms from shared state. The coral target remains visible while moving.
- Closing the window stops the motion timer before renderer shutdown.

The transport is fixed below the scrollable sidebar, keeping Pause/Resume, Stop, Reset arm, speed, and progress visible at the minimum size. At that size, users scroll the sidebar body to reach lower IK actions. Paused, running, completed, and cancelled messages agree with the transport state.

## Automated verification

Final command: `.venv\Scripts\python.exe -m pytest -q`

**139 passed in 40.60s, with no warnings**, including all previous 97 tests.

The **33 new core cases** cover reference smoothstep values, monotonic easing and endpoint velocity, t=0/t=1/intermediate interpolation, a 1,001-sample joint-limit check, exact fractional completion, skipped-tick handling, pause/resume timing, stop in running/paused states, reset from four motion states, replacement from running/paused poses, invalid targets/speed/progress, duration presets/minimums, and zero-distance completion. Mathematical tests use controlled clocks and no sleeps.

The **nine new GUI cases** cover live FK/matrix/marker agreement during motion, fractional-angle preservation, actor identity reuse, transport state, pause/resume/completion, mode switching, final IK error, Stop/Reset/target-edit/manual/instant/replacement interruptions, stale Move rejection, actual QTimer advancement, active-motion shutdown, and verified-size captures.

`pip check` reports **No broken requirements found**. An isolated import check confirms the motion core loads without Qt or rendering libraries. No visual-update-rate guarantee is inferred from the timer interval or test timings.

## Visual evidence

Inspected poses at 25%, 50%, and 75%, plus paused state, at both requested client sizes:

- `motion-960-{25,50,75,paused}.png`: **1200 × 850 physical pixels**, matching **960 × 680 logical** at 125% DPI.
- `motion-1360-{25,50,75,paused}.png`: **1700 × 1125 physical pixels**, matching **1360 × 900 logical** at 125% DPI.

The initial large captures were constrained by Windows to a shorter available desktop height. This evidence issue was fixed by enforcing and asserting client size in the capture test only, recapturing, and rerunning the full suite. Production minimum/default sizing was not changed. Other regression captures in the folder may reflect the desktop's ordinary size constraints; the eight named motion captures are the verified-size evidence.

The final visual review returned **ship** after verifying corrected dimensions. The viewport remains dominant, the fixed transport stays visible, focus/status/progress are clear, and live coordinates correspond to the sampled arm poses. Functional easing is verified mathematically; inspection used sampled rendered frames plus a separate real-QTimer integration test, not continuous human observation of every frame.

## Limitations and Phase 6 recommendation

Motion is a joint-space interpolation, not a Cartesian straight-line path, physical dynamics model, motor/torque simulation, or collision-free plan. Valid configurations and paths can intersect links, base, or floor. IK remains position-only. Whole-degree slider thumbs approximate the fractional shared state, whose labels and numerical results use documented rounding.

Actual frame rate depends on hardware and system load; missed frames are possible even though elapsed-time completion remains correct. Source/automated tests/captures cover this Windows machine, not all GPU/DPI/OS, screen-reader, or physical input-device combinations. Windows may constrain the actual initial window height to the available desktop space.

Phase 6 should refine UI/accessibility and engineering presentation, validate demonstration edge cases, and fix defects found through user workflows. No collision detection, Cartesian planning, dynamics, numerical IK, additional robot types, or executable packaging was implemented. Phase 6 requires separate approval.
