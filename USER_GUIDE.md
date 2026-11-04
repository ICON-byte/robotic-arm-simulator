# Robotic Arm Simulator — demonstration guide

## Start

Follow README.md to install the local environment once. Then open PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe -m robotic_arm_simulator
```

The application runs offline once installed. The scene occupies most of the window. The sidebar holds demonstrations and FK/IK workflows; its motion controls stay fixed at the bottom. Scroll the sidebar body when needed.

## Forward kinematics: angles to position

1. Choose **Fully extended** and click **Load**. Loading a pose changes it immediately; changing the dropdown alone does nothing.
2. Show that all three angles are 0° and the endpoint is **X 350, Y 0, Z 100 mm**.
3. Move Base to 90°. The arm rotates about Z and the endpoint becomes **X 0, Y 350, Z 100 mm**.
4. Load **Raised arm** to demonstrate shoulder elevation, then **Elbow bend** for relative elbow movement.
5. Open **4 × 4 matrix**. The last column contains XYZ in mm, the upper-left block represents orientation, and the last row is `[0, 0, 0, 1]`.
6. Use **Copy results** or **Ctrl+Shift+C** to paste the report into a document.

FK answers: “Where does the tool end up for these joint angles?” The gold marker is centered on that mathematical endpoint.

## Inverse kinematics: position to angles

1. Load **Home position**, then **IK demonstration**. The second preset prepares target inputs and opens IK target; it does not apply the seed pose.
2. Click **Calculate IK** or press Enter in an XYZ field. Calculation does not move the arm. A coral box marks the target.
3. Inspect the valid solutions. B/S/E mean base/shoulder/elbow. The closest configuration is initially selected, and a counter identifies the selection.
4. Choose a branch with the mouse or arrow keys. **Apply now** changes pose immediately; **Animate** moves smoothly at the selected speed.
5. Observe live XYZ/matrix updates. On completion, the gold endpoint lies at the box center and positioning error should be within **0.000001 mm** (often displayed as zero after rounding).
6. Select the other branch and animate again to show different angles reaching the same point.

IK answers: “Which valid joint angles reach this target?” Tool orientation follows those joints; it is not independently requested.

## Validation examples

- Enter `500, 0, 100`: geometrically unreachable; the pose stays unchanged.
- Enter `100, 0, 100`: geometrically reachable but excluded by the configured joint limits.
- Enter a blank, nonnumeric value, `nan`, or `inf`: the error names affected coordinates, marks their fields, and focuses the first invalid input. Use a decimal point; scientific notation is accepted.
- Editing a target clears stale solutions and hides its old marker. Calculate again before applying or animating.

## Motion controls

- Choose **Slow**, **Normal**, or **Fast** before Animate. Presets change duration for longer moves; very short moves retain a 1-second minimum. Switching elbow branches makes motion easier to observe.
- **Pause** freezes the pose and becomes **Resume**. Paused time does not advance the move.
- **Stop** cancels and holds the current pose. Resume cannot revive a stopped move; use Animate for a fresh move from that pose.
- **Reset arm** immediately restores the home pose and clears IK/marker, retaining camera and target text. **Reset view** changes only the camera.
- Editing/recalculating a target, loading a preset, moving a slider, or Apply now interrupts active motion. Mode/tab switches, copying results, and camera interaction do not.

## Camera and keyboard

| Action | Input |
|---|---|
| Rotate | Left drag |
| Zoom | Wheel or right drag |
| Pan | Middle drag or Shift + left drag |
| Reset camera | Reset view / Ctrl+Home |
| Reset arm | Reset arm / Ctrl+R |
| Copy FK report | Copy results / Ctrl+Shift+C |
| Navigate | Tab / Shift+Tab |
| Focus X/Y/Z | Alt+X / Alt+Y / Alt+Z |
| Calculate without moving | Enter in a target field |
| Adjust joint / select solution | Arrow keys on the focused control |

The header shows the current FK or IK workflow. Focus outlines show keyboard location, and written status/errors do not rely only on color. Each grid division is **50 mm**; **Z points upward**.

## Limits to explain during the demonstration

Sliders indicate whole degrees while labels retain fractional IK/motion values. The model retains finer precision than rounded readouts and clipboard output.

Valid joint limits do not prevent link/base/floor collisions. Motion is a joint-space curve, not a guaranteed straight or collision-free tool path. No dynamics or motor torque is simulated.

A 20 ms timer requests about 50 visual updates/s; actual rate depends on the machine. Scroll and zoom/pan as needed on smaller displays. A standalone Windows executable has not been packaged yet.
