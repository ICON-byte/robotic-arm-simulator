# Robotic Arm Kinematics Simulator

Phase 1 of a university course project: a native Windows desktop shell with an interactive 3D reference scene. No robot model, joint movement, forward/inverse kinematics, or animation is implemented yet.

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

The 80 mm cube is a temporary rendering reference, not a robotic arm. The ground grid has 50 mm spacing. The orientation marker identifies X/Y/Z; Z is upward. Placeholder sidebar sections intentionally have no inputs or calculated values.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
```

The integration test opens a real Qt/VTK window, checks nonblank rendering, delivers VTK interaction events for orbit/pan/zoom, clicks Reset view, checks two window sizes, and verifies renderer shutdown. It requires a desktop session and a working OpenGL driver; it is not a headless mathematical test. Optional screenshots: set `SIMULATOR_CAPTURE_DIR` to a writable directory before running pytest.

## Structure

- `core/`: reserved for GUI-independent geometry and mathematics.
- `visualization/viewport.py`: reference scene, camera, renderer lifecycle.
- `ui/`: window layout, future-control explanations, and packaged Qt stylesheet.
- `tests/`: foundation integration check. Mathematical tests arrive with their implementations.

## Limitations and next phase

Hardware rendering depends on the local graphics driver. Dependency metadata alone cannot guarantee compatibility on other machines. Packaging and testing without a Python installation belong to Phase 7.

Phase 2 will introduce configurable robot geometry, construct the base/shoulder/elbow/links/end effector, and verify basic joint movement against the shared model. It requires separate approval.
