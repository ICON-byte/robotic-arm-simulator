# Phase 1 verification

Verified on 4 November 2026 on this Windows machine using the existing 64-bit Python 3.12.10 installation and a project-local `.venv`. No global interpreter or system packages were changed.

## Installed stack

| Component | Version |
|---|---|
| PySide6 Essentials | 6.12.0 |
| PyVista | 0.49.2 |
| PyVistaQt | 0.13.2 |
| VTK | 9.5.2 |
| NumPy | 2.4.6 |
| QtPy | 2.4.3 |
| pytest | 9.2.0 |

All transitive package versions are recorded in `requirements-lock.txt`. Setuptools and pip are local environment tooling. SciPy and PyInstaller are intentionally deferred.

## Results

- Dependency consistency: `python -m pip check` returned **No broken requirements found**.
- Integration verification: `python -m pytest -q` returned **2 passed in 16.53s**, with no warnings.
- Production entrypoint initialized its real application, displayed the desktop window, and exited successfully using an automatic close timer.
- Real Qt/VTK viewport rendered a nonblank scene.
- VTK input-event checks verified orbit, Shift/left-drag pan, middle-drag pan, wheel zoom, and right-drag zoom.
- A Qt mouse click on Reset view restored the initial camera.
- Both 960 × 680 and 1360 × 900 logical window sizes retained a usable viewport; widget screenshots were captured under `.impeccable/review/`.
- Main-window closure closed the renderer successfully.
- Visual review of both captures confirmed readable axes, a nonwrapping scene hint, the intended sidebar surface, visible keyboard focus, and no content clipping. The reviewer scored all three visual fixes resolved.

## Issues resolved during setup and verification

- Restricted temporary-file access prevented initial pip bootstrapping. The authorized environment setup completed outside that restriction, using the same project-local environment.
- A VTK 9.7.2 download timed out and a retry transferred too slowly. The selected VTK 9.5.2 wheel downloaded successfully and passed runtime verification.
- Used the official PySide6 Essentials distribution to avoid unnecessary PDF/browser modules while retaining the required PySide6 APIs.
- NumPy 2.5 triggered upstream VTK array-shape deprecation warnings. Constrained NumPy below 2.5; the verified environment uses 2.4.6.
- Corrected a test helper that assumed PyVista's CameraPosition object converted directly to a numeric NumPy array. The application camera implementation was unaffected.
- Explicitly set light axes-label color, enabled sidebar background painting, and prevented toolbar hint wrapping after screenshot review.

## Scope and limitations

This is a reference scene with an 80 mm cube, a 50 mm ground grid, and X/Y/Z orientation axes. It contains no robot geometry, joint movement, kinematics, or animation. Future controls are explanatory placeholders.

Interaction checks deliver VTK events programmatically; they do not replace user evaluation of physical mouse/trackpad behavior. Verification covers this machine and two logical window sizes (captured at Windows 125% scaling), not every GPU or display configuration. Rendering requires an OpenGL-capable graphics driver. Standalone executable packaging and testing without Python remain Phase 7 work.

Phase 2 requires separate approval before robot modeling begins.
