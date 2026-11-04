RoboKin3D 1.0.0 — Windows x64 portable application

Extract the ENTIRE ZIP to a writable local folder before launching RoboKin3D.exe.
Keep RoboKin3D.exe and _internal together. No separate Python installation,
virtual environment, VS Code or internet connection is required to run.
Requires Windows 10/11 x64 with a working graphics driver for Qt/VTK rendering.

The navy robotic-arm splash displays real startup stages and closes when the
workspace is ready. The thin teal loading indicator is indeterminate.
See USER_GUIDE.md for FK/IK, camera and motion controls.

If startup fails, consult %LOCALAPPDATA%\RoboKin3D\logs\startup.log.
The error dialog contains recovery advice; the log preserves diagnostic details.
Extract the complete archive again and check your graphics driver.
This educational simulator does not control physical robots.

Windows can cache icons for existing shortcuts/pinned items. Unpin an old item,
launch this executable, and pin the running RoboKin3D item again if necessary.
No installer, registry modification, or automatic icon-cache reset is performed.
