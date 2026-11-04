# Phase 4 verification

Verified on 4 November 2026 in the existing project-local Python 3.12.10 Windows environment. No dependencies were added, and no global installation was changed.

## Files and integration

Created:

- `core/inverse_kinematics.py`: pure analytical IK, result/error types, candidate filtering, deduplication, and distance ordering.
- `ui/inverse_controls.py`: target input, calculate/select/apply workflow, solutions, messages, and positioning error.
- `tests/test_inverse_kinematics.py`: independent references, branch and boundary coverage, singularities, failures, and seeded round trips.
- This report and native screenshots in `.impeccable/review/phase4/`.

Modified `ui/controls.py`, `ui/main_window.py`, `ui/results.py`, `ui/theme.qss`, `visualization/viewport.py`, and `tests/test_foundation.py`. Updated README, PRODUCT, DESIGN, and the native design sidecar. The existing robot/FK transformation chain is reused without a second production FK implementation.

## Mathematical behavior

The solver enumerates both elbow signs for both positive and negative signed radial reach. Negative reach uses an equivalent base orientation. It normalizes angles, rejects candidates outside the configured joint limits, verifies each surviving candidate through the existing FK implementation, and removes equivalent configurations. It never changes the application's current robot configuration during calculation.

Distances use actual bounded joint differences in degrees, without wrapping through mechanical stops. Equivalent base endpoints −180°/+180° are represented once, choosing the value nearest the current base. Solutions are sorted nearest first; all other distinct valid branches remain selectable. Elbow labels account for signed radial direction.

Base-axis targets preserve the current base angle and explicitly report the continuous family. Fully extended branches merge. Fully folded configurations are recognized as geometrically reachable but require ±180° elbow rotation, so they fail the configured ±135° joint limit.

Tolerances:

- Position verification: **1e−6 mm** Euclidean endpoint residual.
- Axis classification: **1e−9 mm** XY radius.
- Equivalent-angle comparison: **1e−7 degrees**.
- Analytic angles rounded to ten decimal places to remove exact-limit arithmetic noise; invalid angles are not clamped into limits.

Shoulder-to-target reach is checked against the 50–350 mm geometric shell before acos. Only reach-boundary overshoot within position tolerance is clipped into the acos domain, and resulting poses must still pass FK verification. Errors distinguish invalid input, geometric unreachability, joint-limit exclusion, and failed numerical FK validation.

## UI and state behavior

- Sidebar Joint angles / IK target tabs preserve the robot pose. FK/matrix/copy remain available in either mode.
- Calculate does not move the robot. Apply uses the shared state-update path and updates geometry, FK results, matrix, and angle labels.
- Fractional IK angles are retained in the model. Labels show up to three decimals; the original slider thumbs indicate nearest whole-degree positions. Moving one slider does not round the other joints.
- Editing target text invalidates all old solutions, disables Apply, and hides the previous marker until calculation.
- Invalid or failed calculations preserve the robot pose. Finite unreachable targets still get a requested-target marker.
- The reusable coral wire box is centered on the calculated target and remains distinguishable from the gold endpoint after application. Actor updates do not rebuild the scene or reset the camera.
- Reset arm restores the initial pose, clears IK results/marker, and retains target input text. Reset view changes only the camera.
- Solution ordering reflects the pose at calculation time; users can recalculate after manually changing joints. The listed solutions remain valid for unchanged target text.

## Verification results

Final command: `.venv\Scripts\python.exe -m pytest -q`

**97 passed in 28.02s, with no warnings.** All 56 Phase 1–3 tests remain included.

The 34 new mathematical tests cover independent two-elbow references, all target quadrants, the reversed-radial branch, nearest bounded selection, equivalent base endpoints, preserved base-axis orientations, extension/folding, geometric and limit exclusions, malformed/nonfinite/large targets, boundary tolerance, and numerical-validation failure classification. One round-trip test additionally exercises **155 poses**, including seeded random configurations and limit/signed-radial cases, checking finite angles, strict limits, and FK residuals.

Seven new desktop cases cover fractional IK application, target/endpoint coincidence, UI and matrix synchronization, retained fractional values during later slider movement, failed-calculation safety, stale-solution invalidation, every valid solution being selectable, reset, and success/error layouts at two sizes. Existing tests continue to verify clipboard behavior; the IK test also checks that exported FK text reflects the applied fractional pose.

`pip check` reports **No broken requirements found**. An isolated import check confirms IK loads without Qt, PyVista, VTK, or SciPy. A local 500-solve sample for `(250, 50, 150)` mm averaged approximately **0.119 ms per solve**; this is a single-machine indicative timing, not a cross-platform performance guarantee. Candidate residuals in that sample were at most approximately `2.4e−10 mm`.

## Visual inspection

Reviewed success and unreachable-target captures at **960 × 680** and **1360 × 900** logical sizes, with Windows 125% scaling:

- `ik-960-success.png`, `ik-1360-success.png`
- `ik-960-error.png`, `ik-1360-error.png`
- Additional FK workspace, joint, and matrix regression captures in the same folder.

The dark viewport-led layout remains intact. Sidebar scrolling handles the minimum size; target coordinates, all solution rows, Apply, positioning error, and the shared Reset arm remain accessible. The sparse wire box allows the gold endpoint to remain visible at coincidence. The review found no material UI issue; its documentation finding was corrected and scored resolved in a scoped follow-up verdict.

## Limitations and Phase 5 recommendation

This is position-only analytical IK. Tool orientation follows the selected joints; it is not a separate target. No collision checking means valid configurations can intersect links, base, or floor. Axis targets return the current-base representative of an infinite family, not an infinite list. Base-limit endpoint duplicates are intentionally represented once.

Solution-list angles use two decimals and labels use up to three; tooltips expose ten decimals. Positioning error uses nine decimal places and may round tiny residuals to zero. The model and application retain the solver's finer precision. Targets outside the current view do not trigger a camera reset.

Verification uses programmed Qt/VTK events and visual inspection of captures, not a human physical-mouse usability session. Other GPU/DPI/OS and assistive-technology combinations remain unverified.

Phase 5 should add cancellable, nonblocking interpolation between joint configurations, limits throughout movement, and synchronized live results/controls. Motion animation, path planning, numerical IK optimization, collision detection, multiple robot types, and executable packaging were not implemented. Phase 5 requires separate approval.
