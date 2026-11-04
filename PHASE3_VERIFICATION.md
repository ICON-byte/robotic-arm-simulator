# Phase 3 verification

Verified on 4 November 2026 using the existing project-local Python 3.12.10 Windows environment. No dependencies, global environment settings, or packaging configuration were changed.

## Implementation

`RobotModel.forward_kinematics()` exposes a result snapshot with current angles, world-space shoulder/elbow/endpoint positions, and the 4 × 4 tool-to-world transform. It reuses the Phase 2 transformation chain. Production code does not implement a second analytical calculation or solver.

The tool frame inherits forearm orientation: local +X follows the forearm, local +Y follows the yawed hinge axis, and local +Z completes the right-handed basis. Matrices multiply homogeneous column vectors. Rotation is dimensionless, translation uses millimetres, and the last row is `[0, 0, 0, 1]`.

The new `ui/results.py` panel provides:

- Live X/Y/Z coordinates, explicitly labeled in mm, plus base/shoulder/elbow angles in degrees.
- A compact second tab showing all 16 matrix elements, labeled tool-to-world with translation units.
- Consistent three-decimal numeric formatting and normalization of rounded negative zero. Full-precision calculations and renderer transforms are unaffected by display rounding.
- A Copy results button exporting readable plain text containing angles, endpoint coordinates, units, and matrix, with confirmation in the status bar.

Slider changes and Reset arm update the readout. The gold endpoint marker from Phase 2 remains centered on the mathematical endpoint and visually distinct from the dark tool collar. The same model transforms continue to position existing actors; no scene rebuilding, optional label clutter, or new animation was introduced.

## Verification results

Final command: `.venv\Scripts\python.exe -m pytest -q`

**56 passed in 18.90s, with no warnings.** All existing Phase 1/2 tests remain included.

- **44 mathematical checks:** initial and known poses; positive/negative shoulder and elbow changes; joint boundaries; valid dimensions; rigid transforms and fixed link lengths; atomic validation; reset; known tool orientations; full 4 × 4 matrix shape; proper rotation/orthogonality; translation consistency; independent analytical FK comparisons; and independent result snapshots.
- **11 desktop integration checks:** camera gestures, resizing, rendering, startup/shutdown, slider/keyboard interaction, reusable and connected actors, both resets, FK coordinates/angles updating live, all matrix cells matching the calculation within display precision, endpoint marker agreeing with the FK frame, actual clipboard export after changes/reset, and both result tabs fitting at both window sizes.
- **1 numeric formatting check:** rounded negative zero is normalized while a small meaningful negative value is preserved.

Independent references include the zero-angle endpoint `(350, 0, 100)` mm, known yaw/elevation rotation matrices, the default endpoint `(175√2, 0, 100 + 25√2)` mm, and planar analytical equations evaluated separately from the matrix-product implementation.

`python -m pip check` reports **No broken requirements found**. A separate import check confirmed that the FK core loads without Qt, PyVista, QtPy, or VTK. The default full-precision endpoint is approximately `(247.48737342, 0, 135.35533906)` mm.

## Visual evidence

Native widget captures are under `.impeccable/review/phase3/`:

- `results-960-tab0.png`, `results-960-tab1.png`: coordinates and complete matrix at 960 × 680 logical size.
- `results-1360-tab0.png`, `results-1360-tab1.png`: both tabs at the default 1360 × 900 size.
- `workspace-960.png`, `workspace-1360.png`: camera/lifecycle regression captures.
- `joint-0.png`, `joint-1.png`, `joint-2.png`: independent joint configurations and live readouts.

Captures use Windows 125% scaling. Review returned **ship** for the Phase 3 extension, with no material fixes. All matrix values remain visible, primary controls remain accessible, and secondary sidebar content scrolls at minimum size. The visual reviewer inspected source and images; interaction evidence comes from the automated integration checks.

## Limitations and next phase

UI angles use existing 1° sliders. Coordinates and matrices are rounded for display and clipboard output; they are not lossless exports. Tool orientation follows the joints and is not independently controllable.

Verification covers this Windows machine and two logical sizes at one DPI setting. Other GPUs, operating systems, screen readers, and physical mouse/trackpad usability sessions have not been verified. Rendering still requires an OpenGL-capable driver.

Joint limits do not prevent self/base/floor intersections. No inverse kinematics, target input, path planning, motion animation, collision detection, robot selector, or standalone executable was added. Phase 4 requires separate approval.
