# Phase 6 verification

Verified on 4 November 2026 using the existing project-local 64-bit Python 3.12.10 Windows environment. No dependencies, mathematical algorithms, external assets, threads, or executable packaging were introduced.

## Improvements and files

Created `core/presets.py`, `tests/test_presets.py`, `USER_GUIDE.md`, this report, and Phase 6 screenshots/resource evidence under `.impeccable/review/phase6/`.

Modified:

- `ui/controls.py`: compact demonstration dropdown/Load, explicit pose-versus-target hint, reduced spacing, FK/IK names, and reset shortcut.
- `ui/inverse_controls.py`: adjacent Apply now/Animate actions, a larger-font compact solution list with selection counter, field-specific validation and recovery, focus/buddy/Tab/Enter behavior, and a batched target setter.
- `ui/main_window.py`: persistent workflow caption, preset integration, concise feedback, and direct-pose state synchronization.
- `ui/motion_controls.py`, `ui/results.py`, `ui/theme.qss`: accessible labels, tooltips, copy shortcut, and readable error/focus treatment using the existing palette.
- `core/motion.py`: direct-pose bookkeeping to clear stale terminal progress; the interpolation algorithm is unchanged.
- `__main__.py`: recovery guidance in startup dialogs, with exception details logged only to the console.
- `visualization/viewport.py`: explicit Z-up / 50 mm grid caption. Mechanical geometry, materials, lighting, actor reuse, and camera behavior remain intact.
- `tests/test_foundation.py`, `tests/test_motion.py`, README, PRODUCT, DESIGN, and the native design sidecar.

The pre-existing local `.gitignore` improvement was preserved.

## Demonstration presets

| Preset | Validated action |
|---|---|
| Home position | Immediate configured reset to `(0°, 45°, −90°)`; clear IK and motion state. |
| Fully extended | Apply `(0°, 0°, 0°)`; endpoint `(350, 0, 100)` mm. |
| Raised arm | Apply `(0°, 60°, 0°)`; endpoint `(175, 0, 100 + 175√3)` mm. |
| Elbow bend | Apply `(0°, 0°, 90°)`; endpoint `(200, 0, 250)` mm. |
| IK demonstration | Derive the target through shared FK at `(30°, 60°, −90°)` without applying that pose. |

The IK target is approximately `(199.102540378, 114.951905284, 198.205080757)` mm. Independent expectations use `(112.5 + 50√3, 50 + 37.5√3, 25 + 100√3)` mm. Both returned demo solutions have elbow joint centers above the grid. This chosen example is not a collision detector or a claim that arbitrary paths are safe.

Dropdown selection alone has no side effect; Load performs the action named by the hint. Pose presets stop active motion, clear IK/marker, retain target text/camera, and open FK joints. The IK preset stops motion at its current pose, prepares new coordinates, invalidates old solutions, and opens IK target. Calculate and Apply now/Animate remain explicit steps.

## Functional defect corrected

Previously, applying an immediate pose after a completed animation could retain Completed/100% even though the robot had moved to a different pose. `MotionEngine.apply_instant()` now validates before changing state, cancels active movement, and resets stale terminal history to Idle/0% for a new direct command. Active overrides still report Cancelled. Regression tests cover Idle/Completed/Cancelled, running/paused interruption, and invalid-command state preservation.

No FK, IK, transform, joint-limit, or smoothstep mathematical defect was identified within the verified coverage; those algorithms were preserved.

## Automated verification

Final command: `.venv\Scripts\python.exe -m pytest -q`

**161 passed in 62.61 seconds, with no warnings**, including all prior 139 tests.

- **122 core cases:** existing FK/IK/motion checks, independent preset endpoint/target references, valid demo branches, and new direct-pose state regressions.
- **38 desktop integration cases:** existing startup/shutdown, camera, controls, motion, and state tests plus repeated preset loading/interruption, invalid-field focus and keyboard Tab/Enter flow, actual copy/reset shortcuts, repeated workflows, exact-size/action-accessibility captures, and friendly startup-failure handling.
- **1 numeric formatting case:** rounded negative-zero handling.

The existing IK test also exercises 155 seeded/reference round trips. The expanded repeated-workflow case runs 12 cycles through rapid slider changes, repeated FK/IK mode switches, repeated calculations, tiny base-axis coordinates, workspace boundaries, pause/stop/restart, completion, and report export. Actor identities/count remain stable. Existing tests cover resizing during motion, fractional precision, target cancellation, both resets, and clean active-motion shutdown.

`pip check` reports **No broken requirements found**. No source/build packaging was attempted. Source whitespace checks pass, and the design sidecar parses as valid JSON.

## Accessibility and visual inspection

Keyboard navigation uses native controls and explicit target-field order. Enter calculates without moving and focuses solutions on success; errors name invalid axes and focus the first bad field. Field borders supplement written messages. Alt+X/Y/Z buddies are provided, Ctrl+R resets the arm, Ctrl+Home retains camera reset, and Ctrl+Shift+C copies the current FK report. Tab/Enter and copy/reset shortcuts were exercised in GUI tests; buddy declarations were reviewed in source. Screen-reader operation was not independently verified.

Sampled stylesheet foreground/background contrast ratios:

| Text role and background | Ratio |
|---|---|
| Primary `#e5edf3` on canvas `#10161d` | 15.37:1 |
| Secondary `#a8b8c7` on sidebar `#18212b` | 8.01:1 |
| Error `#f59a87` on canvas `#10161d` | 8.54:1 |
| Disabled button `#8796a5` on `#202b36` | 4.75:1 |

These are targeted color-pair calculations, not a comprehensive accessibility certification.

Captured presets, matrix, error, and scrolled IK actions with exact client-size assertions at **960 × 680**, **1100 × 760**, and **1360 × 900** logical pixels. At Windows 125% DPI, corresponding images are **1200 × 850**, **1375 × 950**, and **1700 × 1125** physical pixels. Tests temporarily enforce client size to avoid desktop constraints silently reducing the large captures; production minimum/default sizing is unchanged.

Named evidence: `demo-{960,1100,1360}-{fully-extended,raised-arm,elbow-bend,ik-matrix,ik-actions,invalid}.png`, plus `view-angle-0.png` and `view-angle-1.png`. Representative captures at every size and both additional camera directions were visually inspected. The reviewer found no material UI blockers; lower IK actions remain accessible by scrolling, and the fixed transport and persistent mode caption preserve context. All sixteen matrix cells remain readable.

## Performance/resource sample

An isolated real Qt/VTK run warmed up for 300 motion frames, then sampled **1,800 frames** across repeated demo/IK/motion cycles. Measurements are preserved in `resource-sample.json` beside the screenshots.

- Renderer actor count remained **24**, with unchanged arm actor identities.
- Child Qt timer count remained **3**.
- Python traced heap after two equal 900-frame batches: **49,394 bytes**, then **59,889 bytes** (growth **10,495 bytes**, about 10 KB).
- Peak traced Python allocation: **199,904 bytes**.
- Active child timers after window closure: **0**.

The sample found no evidence of excessive Python growth or accumulating actors/timers, so no speculative rendering/math optimization was added. Tracemalloc excludes native VTK, driver, and GPU allocations; this is not a long-duration leak guarantee or a frame-rate benchmark.

## Remaining limitations and packaging readiness

Joint limits do not prevent collisions with links, base, or floor. IK is position-only; interpolation is joint-space, not Cartesian planning or physical dynamics. Whole-degree sliders approximate fractional state; labels/reports use documented rounding. Actual rendering speed depends on hardware.

Validation covers this Windows machine and display scaling, not all GPUs, DPI settings, operating systems, assistive technologies, or physical input-device usability sessions. Captures and automated interaction establish the stated evidence; they do not replace continuous human review of every rendered frame. Windows may constrain the initial window height to available desktop space.

Before distribution, Phase 7 must collect and verify Qt/VTK libraries/plugins and packaged stylesheet resources, test launching on a clean Windows system without Python, and document installation and diagnostics. The application currently requires the documented Python environment. No installer, executable, or clean-machine packaging test has been produced.

Phase 6 ends here. Executable packaging requires separate approval.
