# Phase 2 verification

Verified on 4 November 2026 using the existing Windows environment and project-local Python 3.12.10 virtual environment. No dependency or global environment changes were required.

## Implemented scope

- Replaced the reference cube with a cylindrical base, rotating turntable and pedestal, shoulder and elbow bearings/caps, upper-arm and forearm beams, tool collar, and gold endpoint marker.
- Added `core/robot.py` as the GUI-independent source of geometry, validated current joint state, joint positions, and homogeneous transforms.
- Dimensions: shoulder height 100 mm, upper arm 200 mm, forearm 150 mm. Limits: base ±180°, shoulder ±90°, elbow ±135°. Initial/reset angles: 0°, 45°, −90°.
- Added three 1° sliders with visible angles, ranges, keyboard access, and a separate Reset arm action. Existing Reset view and camera gestures are preserved.
- Geometry is created once. Joint changes replace actor transform matrices and render the scene; meshes, lights, grid, and camera are not rebuilt or reset.
- Revised initially dim PBR materials to explicit Phong lighting coefficients using the existing PyVista light kit, producing more readable mechanical surfaces without external assets.

## Automated verification

Final command: `.venv\Scripts\python.exe -m pytest -q`

**36 passed in 16.32s, with no warnings.**

Thirty mathematical checks cover the initial configuration, independently derived initial joint positions, nine known axis-aligned poses, shoulder height, rigid transform properties, constant link lengths, accepted joint boundaries, rejection of invalid/nonfinite angles without partial mutation, positive dimensions, relative elbow motion, and reset.

Six Qt/VTK integration checks cover:

- The existing Phase 1 orbit, pan, zoom, camera reset, nonblank rendering, resize, and clean renderer shutdown regression.
- Production entrypoint launch and timed clean exit.
- Separate base, shoulder, and elbow changes through actual Qt sliders, keyboard interaction, angle labels, model/actor synchronization, unchanged actor identities, fixed base components, connected link tips, endpoint-marker placement, unchanged camera, and arm reset.
- Slider clamping, repeated live updates with Qt event processing, stable actor count, and reset.

`python -m pip check` reports **No broken requirements found**. The mathematical core also imports without loading Qt, PyVista, QtPy, or VTK. Dependencies remain as recorded in `requirements-lock.txt`.

## Visual inspection

Inspected native widget captures under `.impeccable/review/phase2/`:

- `workspace-960.png`: minimum 960 × 680 logical window size; scrollable sidebar and usable viewport.
- `workspace-1360.png`: default 1360 × 900 logical window size; initial 0°, 45°, −90° configuration.
- `joint-0.png`: base at 90°, with the arm assembly yawed and base plate stationary.
- `joint-1.png`: shoulder at 0°, with the upper arm horizontal and forearm still connected.
- `joint-2.png`: elbow at 0°, with the forearm straight relative to the unchanged upper arm.

The final visual review returned **ship** at Phase 2 scope with no material fixes. The arm's silhouette, joints, lit materials, focus states, visible values, and inherited dark layout remain readable. Captures use the machine's Windows 125% display scaling; screenshot physical pixel dimensions exceed logical window sizes.

## Limitations

Joint and camera interactions were exercised programmatically and their resulting images visually inspected; this is not a human physical-mouse usability session. No claim is made about every GPU, screen configuration, or frame rate.

No collision detection is implemented. Permitted angles can produce self-intersections, base intersections, or movement below the reference floor. The tool collar and endpoint sphere are presentation geometry; the sphere center is the mathematical endpoint and does not add reach. Sliders use 1° increments.

No full forward-kinematics UI, inverse solver, target inputs, animation, robot selector, or executable packaging was added. Phase 3 requires separate approval.
