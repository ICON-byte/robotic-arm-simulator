# RoboKin3D v1.0.0

The first stable release of RoboKin3D, a Python-based desktop application for interactive 3D robotic arm simulation and forward/inverse kinematics.

### Features

- Interactive 3-DOF robotic arm visualization.
- Forward kinematics calculations.
- Analytical inverse kinematics.
- Multiple IK solutions.
- Joint-angle controls.
- Homogeneous transformation matrix display.
- Smooth robotic arm motion animation.
- Pause, resume, stop, and reset controls.
- Demonstration presets.
- Interactive 3D camera controls.
- Custom application branding and splash screen.
- Portable Windows executable.

### Installation

1. Download `RoboKin3D-v1.0.0-Windows-x64.zip`.
2. Extract the ZIP archive.
3. Open the extracted `RoboKin3D` folder.
4. Run `RoboKin3D.exe`.

Python installation is not required. Keep the `_internal` folder beside the executable.

### System Requirements

- Windows 10 or Windows 11 (64-bit).
- Compatible graphics hardware and drivers supporting the application's VTK/OpenGL rendering requirements.

### Known Limitations

- Supports the configured 3-DOF robotic arm.
- Does not simulate collision detection or physical dynamics.
- Rendering performance depends on graphics hardware.
- Clean-machine compatibility has not yet been independently verified.

### Verification

169 automated tests passed during the latest development verification.

The portable executable was tested after extraction and launched successfully from another directory.
