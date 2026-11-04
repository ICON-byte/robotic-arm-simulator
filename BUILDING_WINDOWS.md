# Building RoboKin3D for Windows

Use the existing 64-bit Python 3.12.10 project environment on Windows. Build tools are local to `.venv`; no system installation or online service is required after dependencies are installed.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m pip install --no-deps --no-build-isolation -e .
.\.venv\Scripts\python.exe scripts/build_windows.py
```

The script validates Windows/x64/Python 3.12 and the project environment, runs `pip check` and the full test suite, builds the spec, checks assets, and writes the portable ZIP. `--skip-tests` is reserved for a source tree whose exact contents have already passed the full suite. Tool versions are pinned in `requirements-build.txt`; this is a repeatable build procedure, not a claim of byte-identical output.

Outputs (ignored by Git):

- `dist/RoboKin3D/RoboKin3D.exe` plus `_internal`, README.txt and USER_GUIDE.md.
- `dist/RoboKin3D-v1.0.0-Windows-x64.zip` containing that complete directory.
- `build/build-metrics.json` with build time, file count and sizes.

The application uses windowed `onedir` mode, original multi-resolution ICO resources, and version 1.0.0 executable metadata. `RoboKin3D.spec` includes only the required Qt stylesheet and branding assets explicitly; PyInstaller's dependency hooks resolve imported Qt, NumPy, PyVista and VTK runtime libraries. Matplotlib uses the Agg backend for packaging, avoiding a separate GUI binding. PyQt and unrelated developer tooling are excluded. VTK's dynamically imported modules are listed explicitly following the [PyVista packaging guidance](https://docs.pyvista.org/extras/pyinstaller.html). The build does not collect all installed packages.

Resources resolve relative to the installed package's `__file__`, including inside `_internal`, following [PyInstaller runtime guidance](https://pyinstaller.org/en/stable/runtime-information.html). `packaging/entrypoint.py` imports the existing production entrypoint; no test mode or development controls are shipped.

The original vector icon is `src/robotic_arm_simulator/resources/robokin3d.svg`. To regenerate its 512px PNG and seven-size ICO using existing QtSvg/Pillow dependencies:

```powershell
.\.venv\Scripts\python.exe scripts/generate_branding.py
```

Always rebuild and reverify after changing assets or startup code:

```powershell
.\.venv\Scripts\python.exe scripts/verify_frozen_branding.py
```

That external developer harness inspects the PE icon frames/GUI subsystem, launches from an unrelated temporary directory with Python environment variables removed and a system-only PATH, drives the actual Windows accessibility controls, checks bundled runtime loading, and closes the application. It is not included in the portable ZIP. It requires an interactive Windows desktop and the existing local build environment. `--executable <path>` can target an independently extracted copy. Source visual checks use `scripts/verify_branding.py <capture-directory>`; `QT_SCALE_FACTOR` multiplies the monitor's existing scale rather than replacing it.

Startup diagnostics rotate at `%LOCALAPPDATA%\RoboKin3D\logs\startup.log` (one 512 KB backup). `ROBOKIN3D_LOG_DIR` optionally selects a different writable directory. The graphical error message provides recovery advice; full exceptions remain in the log. If the log directory is unwritable, startup can continue without file logging. Native crashes before Python/Qt initialization cannot be handled by this Python error dialog.

Extract the entire ZIP before running. Never distribute only the EXE. Windows 10/11 x64 and a working graphics driver are the intended targets; the current host was tested, not a fresh VM or every graphics configuration. The executable is unsigned; no installer, registry change, GitHub release or upload is performed by the build script.
