---
name: Robotic Arm Simulator
description: Native Windows Qt workspace for manipulating a three-joint robotic arm.
colors:
  accent: "#7ed5c7"
  arm-accent: "#59bdb0"
  arm-base: "#657788"
  arm-bearing: "#263b49"
  arm-beam: "#8fa4b5"
  arm-axle: "#d7e2e9"
  endpoint: "#e2b77c"
  ik-target: "#f59a87"
  error: "#f59a87"
  canvas: "#10161d"
  scene: "#151c24"
  sidebar: "#18212b"
  raised: "#1b2530"
  placeholder: "#202b36"
  text: "#e5edf3"
  text-secondary: "#a8b8c7"
  text-pending: "#c2ced9"
  text-placeholder: "#b5c3cf"
  text-disabled: "#8796a5"
  scene-caption: "#aebdc9"
  divider: "#33414f"
  control-border: "#455b6b"
  button: "#273743"
  button-hover: "#344a57"
  button-pressed: "#203d40"
  scene-grid: "#35424e"
typography:
  headline:
    fontFamily: "Segoe UI"
    fontSize: "21px"
    fontWeight: 600
  title:
    fontFamily: "Segoe UI"
    fontSize: "15px"
    fontWeight: 600
  body:
    fontFamily: "Segoe UI"
    fontSize: "13px"
  label:
    fontFamily: "Segoe UI"
    fontSize: "12px"
  coordinate:
    fontFamily: "Segoe UI"
    fontSize: "19px"
    fontWeight: 600
  matrix:
    fontFamily: "Consolas"
    fontSize: "12px"
  solution:
    fontFamily: "Segoe UI"
    fontSize: "12px"
  emphasis:
    fontFamily: "Segoe UI"
    fontSize: "13px"
    fontWeight: 600
rounded:
  control: "4px"
  panel: "5px"
  slider-track: "2px"
  slider-handle: "9px"
  motion-progress: "3px"
spacing:
  matrix-gap: "2px"
  compact: "4px"
  results-gap: "6px"
  control-block: "8px"
  section: "12px"
  control-inline: "14px"
  panel-inline: "16px"
  header-block: "18px"
  workspace-block: "20px"
  outer: "24px"
components:
  button:
    backgroundColor: "{colors.button}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "8px 14px"
  button-hover:
    backgroundColor: "{colors.button-hover}"
  button-pressed:
    backgroundColor: "{colors.button-pressed}"
  button-focus:
    padding: "7px 13px"
  button-disabled:
    backgroundColor: "{colors.placeholder}"
    textColor: "{colors.text-disabled}"
  placeholder:
    backgroundColor: "{colors.placeholder}"
    textColor: "{colors.text-placeholder}"
    rounded: "{rounded.panel}"
    padding: "12px"
  results:
    backgroundColor: "{colors.raised}"
    rounded: "{rounded.panel}"
    padding: "12px 16px"
  coordinate-value:
    textColor: "{colors.accent}"
    typography: "{typography.coordinate}"
  matrix-value:
    typography: "{typography.matrix}"
  results-tab:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.text-secondary}"
    padding: "5px 10px"
  results-tab-selected:
    textColor: "{colors.text}"
  results-tab-hover:
    backgroundColor: "{colors.button}"
  sidebar:
    backgroundColor: "{colors.sidebar}"
    padding: "16px"
  slider-track:
    backgroundColor: "{colors.control-border}"
    rounded: "{rounded.slider-track}"
    height: "4px"
  slider-fill:
    backgroundColor: "{colors.arm-accent}"
    rounded: "{rounded.slider-track}"
  slider-handle:
    backgroundColor: "{colors.text-pending}"
    rounded: "{rounded.slider-handle}"
    width: "16px"
  slider-handle-hover:
    backgroundColor: "{colors.accent}"
  target-field:
    backgroundColor: "{colors.placeholder}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "6px"
  error-message:
    textColor: "{colors.error}"
  solution-list:
    backgroundColor: "{colors.placeholder}"
    textColor: "{colors.text}"
    typography: "{typography.solution}"
  solution-item:
    padding: "4px"
  solution-item-selected:
    backgroundColor: "{colors.button-hover}"
    textColor: "{colors.text}"
  motion-transport:
    backgroundColor: "{colors.sidebar}"
    padding: "12px"
  speed-selector:
    backgroundColor: "{colors.placeholder}"
    textColor: "{colors.text}"
    rounded: "{rounded.control}"
    padding: "5px"
  speed-selector-disabled:
    textColor: "{colors.text-disabled}"
  motion-progress:
    backgroundColor: "{colors.divider}"
    rounded: "{rounded.motion-progress}"
    height: "6px"
  motion-progress-fill:
    backgroundColor: "{colors.arm-accent}"
    rounded: "{rounded.motion-progress}"
  viewport:
    backgroundColor: "{colors.scene}"
---

# Design System: Robotic Arm Simulator

## Overview

**Creative North Star: "The Quiet 3D Workspace"**

A professional dark desktop workspace gives the rendered scene the most space and visual attention. Native Qt widgets provide readable controls, organized supporting information, and clear status feedback. The shell stays quiet and never imitates a physical instrument panel.

This document records the implemented Phase 6 forward- and inverse-kinematics workspace with compact demonstrations, explicit input feedback, and smooth joint-space motion. Three limited joint sliders and an explicit target calculate/select/move-or-apply workflow share one robot state, live endpoint coordinates, joint summaries, and the final tool-to-world matrix. Color and shape decisions come from the Qt stylesheet and the mechanical arm scene. The north star is a descriptive name for that existing direction, not a new identity proposal.

**Key Characteristics:**

- Viewport-led composition with an adjustable, scrollable sidebar.
- Dark tonal surfaces, restrained mint emphasis, and readable text.
- Small corner radii, readable joint values, and immediate native interaction feedback.
- Explicit calculation, selection, motion or instant application, and positioning-error feedback for inverse kinematics.
- Fixed sidebar transport with speed, progress, pause/resume, stop, and immediate reset.
- Compact preset loading, persistent mode context, and keyboard-accessible validation feedback.

## Colors

Dark blue-gray neutrals support restrained mint controls, cool mechanical surfaces, a gold endpoint marker, and a coral IK target.

### Primary

- **Mint accent** (`accent`): keyboard focus, button hover borders, positioning-error feedback, joint angle values, live coordinates, and selected-tab underline.
- **Arm mint** (`arm-accent`): slider and motion progress and the turntable, joint caps, and beam inlays.

### Secondary

- **Target coral** (`ik-target`): the unlit wire cube distinguishes the requested world-space target from the current endpoint.
- **Error coral** (`error`): invalid-field borders and actionable error messages reuse target coral; explanatory text and focus supplement color.
- **Endpoint gold** (`endpoint`): the tool endpoint sphere and asymmetric base index make the endpoint and base yaw easy to locate.

### Neutral

- **Mechanical surfaces** (`arm-base`, `arm-bearing`, `arm-beam`, `arm-axle`): distinguish the base plate, dark bearings and collar, cool beams and pedestal, and bright axle centers. These are renderer materials.

- **Canvas and scene** (`canvas`, `scene`): separate the desktop shell from the 3D rendering surface.
- **Sidebar and raised surface** (`sidebar`, `raised`): organize supporting controls, header, results, and status bar.
- **Placeholder surface** (`placeholder`): supports target fields, the solution list, disabled buttons, and the retained placeholder style.
- **Text hierarchy** (`text`, `text-secondary`, `text-pending`, `text-placeholder`, `text-disabled`): distinguish primary content, guidance, future section titles, placeholder details, and disabled actions.
- **Structural lines** (`divider`, `control-border`): separate regions and define button and scrollbar edges.
- **Button states** (`button`, `button-hover`, `button-pressed`): provide immediate feedback without animation.
- **Scene support** (`scene-grid`, `scene-caption`): keep spatial references, the arm caption, and coordinate-axis labels legible without competing with geometry.

**The Reserved Accent Rule.** Use mint emphasis for focus, actionable hover feedback, joint values, live coordinates, slider progress, selected tabs, and positioning-error feedback; keep general shell surfaces neutral. Coordinate-axis shafts retain PyVista's conventional colors; their labels use the scene-caption token.

## Typography

Segoe UI is the native application family. The application initializes a 10-point Qt font; the stylesheet establishes the widget body size through its body token. No web font, display face, fixed line-height, or letter-spacing system is installed.

- **Headline:** application heading, using the headline token.
- **Title:** sidebar, scene, and results section headings, using the title token.
- **Body:** standard widget copy and button text, using the body token.
- **Label:** secondary guidance and camera instructions, using the label token.
- **Coordinate:** mint endpoint values, using the 19px semibold coordinate token.
- **Matrix:** aligned numeric transform cells, using the 12px Consolas matrix token.
- **Solution:** compact branch names and angle summaries, using the 12px solution token.
- **Emphasis:** joint headings and mint angle values, using the emphasis token with their role colors.

The viewport caption is a separate PyVista text actor using Arial and the renderer's `font_size=10` setting. This is not a Qt body-font token. Labels generally wrap their text; the scene toolbar hint stays on one line. Native layout and font metrics determine line height.

## Layout

The initial window is 1360 by 900, with a minimum of 960 by 680. A full-width header sits above a horizontal splitter; a native status bar anchors the bottom. The right workspace receives spare width. Neither splitter pane collapses.

The sidebar explicitly enables Qt styled-background painting so its sidebar surface token is honored. The sidebar scroll container spans 285–355 logical pixels; its child sidebar spans 270–340. Its outer padding is 16 pixels, with eight-pixel spacing between its heading, compact preset chooser, pose/target hint, mode tabs, and mode content. A separate fixed transport sits below the scroll container, with 12-pixel margins, eight-pixel gaps, and a top divider; it keeps speed, state/percentage, a six-pixel progress bar, Pause/Resume, Stop, and the shared Reset arm visible in either mode. The FK joints page uses an eight-pixel top inset and eight-pixel spacing; the IK target page uses the same inset and six-pixel spacing. The solution list stays between 68 and 100 pixels tall; its selection counter and adjacent Apply now / Animate actions keep the workflow compact. The workspace uses outer horizontal and workspace-block vertical margins, and section spacing between toolbar, scene, camera guidance, and results. The header uses outer horizontal and header-block vertical padding. Results use panel-inline horizontal and section vertical padding, with a six-pixel gap between the header and tabs. The tab widget has a maximum height of 136 logical pixels. Coordinate content uses eight-pixel margins and four-pixel vertical gaps; matrix content uses eight-pixel horizontal and four-pixel vertical margins with two-pixel cell gaps.

The viewport expands vertically. Compact tabbed results stay below it, and camera instructions remain visible between them. Resizing uses Qt layouts and sidebar scrolling; there are no web breakpoints or alternate mobile compositions. The native Windows title bar remains OS-controlled.

## Elevation & Depth

The shell uses tonal layering and thin separators, with no application-defined drop shadows. Raised surfaces distinguish header, results, and status from the canvas. The rendered scene supplies real three-dimensional depth; shell panels do not add artificial lighting or decorative elevation. Arm actors use smooth Phong shading with split sharp edges: ambient 0.25, diffuse 0.75, specular power 32, and default specular 0.35. Beam inlays and the endpoint use specular 0.2; the base index uses 0.1. These are conventional renderer materials, not PBR materials.

**The Quiet Shell Rule.** Convey shell structure through surface tone, spacing, and borders so the scene retains visual priority.

## Shapes

Controls and scrollbar handles use the control radius; placeholder rows and results use the panel radius. Header and sidebar boundaries remain rectangular. Buttons use a one-pixel border at rest; focused buttons use a two-pixel accent border with reduced padding to preserve their footprint. The splitter is a thin divider. There are no pill chips or ornamental frames.

## Components

### Buttons

**Calculate IK**, **Apply now** and **Animate**, **Reset arm**, **Reset view**, and **Copy results** are native `QPushButton` actions. Their default, hover, pressed, disabled, and focus variants are recorded in the frontmatter. Hover changes the fill and border; pressed changes the fill; keyboard focus thickens the mint border. Feedback is immediate with no custom transition. Reset view supports Ctrl+Home and has a tooltip describing that shortcut; it restores the camera without changing the pose. Reset arm immediately cancels motion, returns transport state to Idle, restores base 0 degrees, shoulder 45 degrees, and elbow -90 degrees, clears IK solutions and the marker, and retains the camera and target input text. Reset arm supports Ctrl+R. Copy results supports Ctrl+Shift+C and exports the current angles, world-frame endpoint coordinates, and homogeneous transform as plain text to the local clipboard; the status bar confirms the copy. Its tooltip describes the exported content.

### Cards / Containers

The results frame is a quiet raised container with panel corners. The placeholder style remains available in the stylesheet but the joint controls are now working native sliders; no placeholder joint rows are rendered.

### Sidebar and Status

The scrollable sidebar body groups arm configuration into **FK joints** and **IK target** native tabs. Switching mode preserves active or paused motion and keeps live results available. The persistent header caption reads FK · Joint controls or IK · Target workflow, including when the sidebar body is scrolled. The fixed transport below the scrollable body contains the shared Reset arm action. The joint page identifies live forward kinematics and explains gold endpoint versus coral target. A raised native status bar reports readiness, joint updates, and clipboard confirmation while retaining the native size grip. The sidebar's vertical scrollbar is 10 logical pixels wide; its handle has a minimum height of 24. Mode tabs share the results tabs' hover, selected, and focus treatment.

### Demonstration Presets

A compact native combo and adjacent **Load** button sit above the mode tabs. Changing the selection alone does nothing. The hint distinguishes **Pose · applies immediately** from **Target · calculate before moving**. **Home position** restores (0, 45, -90) degrees through Reset arm. **Fully extended** loads (0, 0, 0), **Raised arm** (0, 60, 0), and **Elbow bend** (0, 0, 90); these immediate poses open FK joints and clear stale IK solutions and the target marker while retaining target text and camera. **IK demonstration** derives a reachable target through shared FK at the seed (30, 60, -90), fills target fields to nine decimals, and opens IK target without moving the arm. Loading any preset interrupts active or paused motion.

### IK Target Fields and Solutions

Three accessible `QLineEdit` fields label X, Y, and Z in millimetres and initially contain the current endpoint to six decimal places. They accept finite decimal or scientific-notation text. Fields use the placeholder surface, primary text, a one-pixel control border, four-pixel radius, and six-pixel padding; focus changes the border to mint without changing its width.

**Calculate IK** parses the target and populates a word-wrapped native `QListWidget` without moving the robot. Each row shows a branch and B/S/E angles to two decimals; its tooltip exposes ten-decimal angles and nine-decimal error. The closest solution is selected by default. The list uses a one-pixel control border, four-pixel item padding, the solution typography token, and a button-hover fill for selection. Keyboard focus changes its border to mint. Invalid fields use the coral error border, and errors use the coral error role with wrapping recovery text. Invalid-input messages name the affected axes and focus the first invalid field; editing clears that field's invalid border. Successful calculation focuses the solution list and uses mint success text. A counter reports **Selected solution n of total** with the branch in its tooltip, or **No solution selected**. **Apply now** and **Animate** use the shared disabled-button treatment until a valid row is selected.

XYZ labels are mnemonic buddies (Alt+X/Y/Z); Enter in any target field calculates without moving. Explicit Tab order follows X, Y, Z, Calculate IK, solutions, Apply now, Animate; the Speed label also has a mnemonic buddy.

Apply now cancels motion and applies the full-precision configuration immediately. Animate interpolates from the current sampled pose to the selected full-precision configuration. Both keep FK, matrix, angle labels, and the mint positioning-error label in millimetres to nine decimals synchronized. Editing or recalculating a target cancels active or paused motion, clears stale solutions and positioning feedback, disables both solution actions, and hides the previous target until recalculation. Invalid input, unreachable targets, joint-limit restrictions, and validation failures leave the pose intact. Finite parsed targets retain their marker even when no solution is found. Successful calculations may include singularity or boundary notes. Manual joint changes keep existing solutions and refresh positioning error; recalculation refreshes their nearest-first order.

### Motion Transport

A fixed native `MotionControls` frame remains below the scrollable sidebar body without changing the viewport or results composition. Its top row holds Speed, a `QComboBox` with **Slow / Normal / Fast** (Normal initially), and mint state/percentage text. The second row is a textless six-pixel `QProgressBar`; the final row contains **Pause / Resume**, **Stop**, and shared **Reset arm**. State text and speed guidance use 12px text. The transport uses the sidebar surface and divider border; the combo reuses field surface, control border, four-pixel corners, five-pixel padding, mint focus border, and muted disabled text. Its popup uses the existing selected-row fill. Progress uses the divider track, arm-mint fill, and three-pixel corners. No new palette colors are introduced.

States are **Idle**, **Running**, **Paused**, **Completed**, and **Cancelled**, with an integer elapsed-time percentage. Pause changes to Resume while paused. Pause/Resume and Stop are enabled only during active or paused motion; the speed selector is disabled in both states and configures the next move. Completed and Cancelled retain the last progress until a new move, reset, or direct pose command. A direct pose after terminal motion returns to Idle at 0%; an override of active or paused motion reports Cancelled. Stop samples and holds the current pose; Reset arm is immediate and returns to Idle at 0%. A zero-distance move completes immediately at 100%. Starting another move samples and replaces the current motion. Manual slider edits and Apply now cancel it. Mode changes, results tabs, clipboard export, and camera interaction preserve it.

Smoothstep `3*t*t - 2*t*t*t` moves the actual robot in bounded joint space, with all joints sharing one duration and the exact target assigned on completion. Slow, Normal, and Fast limit peak interpolated joint speed to 45, 90, and 180 degrees/s. Duration is `max(1 second, 1.5 * largest absolute joint change / selected peak speed)`. A precise 20ms Qt timer requests updates from monotonic elapsed time; paused wall time is excluded. Sliders, actors, coordinates, matrix, and target error follow the same full-precision model. This functional robot motion introduces no decorative shell transitions and makes no collision-avoidance, Cartesian-path, or physical-dynamics claim.

### Joint Sliders

Three native horizontal `QSlider` controls pair a joint heading with a right-aligned mint degree value and a muted signed limits label. Base spans -180 degrees to +180 degrees, shoulder -90 degrees to +90 degrees, and elbow -135 degrees to +135 degrees. Arrow keys change by 1 degree; accessible names identify each joint and tooltips repeat limits and keyboard guidance. Labels retain fractional IK angles up to three decimals with trailing zeros removed; slider thumbs indicate the nearest whole degree. Moving a slider changes only its joint and preserves the other exact angles. Values and geometry refresh immediately.

The slider has a 24-pixel minimum height, a four-pixel track, mint progress, and a 16-pixel-wide pale handle with a two-pixel sidebar-colored border and -8-pixel vertical margins. Hover turns the handle mint; keyboard focus also changes its border to the primary text color. Track and handle radii use their frontmatter tokens.

### Arm Viewport

A PyVistaQt interactor displays one mechanically modeled 3-DOF arm: a base plate, bearing, turntable, pedestal, paired beam segments with mint inlays, joint bearings with caps and axles, tool collar, and gold endpoint sphere. Shared core-model transforms position the actors; mesh detail does not alter the underlying link lengths. The shoulder height is 100 mm, upper arm 200 mm, and forearm 150 mm. The endpoint marker is centered on the mathematical endpoint and the collar stops there.

The scene retains a wire grid, conventional coordinate axes, and the caption "Z UP  /  50 mm GRID". Trackball interaction supports rotation, zoom, and pan. Reset view restores perspective and the initial camera. Joint motion leaves the camera in place. The gold endpoint marker matches the calculated endpoint shown in the results panel. A coral wire cube, 30 mm wide on each axis with two-pixel lines and no lighting, marks the last finite calculated target. It starts hidden, does not change the camera, and clears on target edits or Reset arm. After instant application or completed motion, the gold endpoint lies at its center within the reported positioning error.

### Forward-Kinematics Results

A native `ResultsPanel` keeps a section heading and Copy results action above two `QTabWidget` pages. **Coordinates** presents X, Y, and Z in millimetres across three equal-width columns, followed by a compact current-angle summary with up to three decimals and trailing zeros removed. **4 × 4 matrix** presents the tool-to-world homogeneous transform in four aligned columns; its caption states that the translation column is in millimetres. Both pages update after joint changes, instant IK application, every motion update, and Reset arm, independently of the camera.

Coordinate and matrix values use three decimal places and normalize rounded negative zero to `0.000`. Every numeric coordinate and matrix cell supports mouse text selection and has an accessible name identifying the axis or matrix row and column. Matrix cells are right aligned and do not wrap. Copy results includes both pages' data regardless of the selected tab.

Tabs use the raised surface, muted unselected text, and a two-pixel bottom border. Selection changes text to the primary text color and the underline to mint; hover uses the button surface, and keyboard focus uses a primary-text underline. The pane has no border. Keep the results compact so the scene remains dominant at all supported review widths (960, 1100, and 1360 pixels).

## Do's and Don'ts

### Do:

- **Do** keep the viewport dominant and supporting information organized in the sidebar and results frame.
- **Do** preserve visible keyboard focus, signed joint limits, degree values, camera guidance, and the distinct Reset arm and Reset view behaviors.
- **Do** keep live coordinates and matrix values synchronized with the arm, state millimetres and frame direction, and preserve text selection and clipboard export.
- **Do** preserve the explicit calculate/select/move-or-apply workflow, target invalidation, positioning feedback, and coral-target/gold-endpoint distinction.
- **Do** keep motion transport visible, distinguish Animate from Apply now, and retain immediate Reset arm.
- **Do** use native Qt layout behavior and the established surface and typography tokens.

### Don't:

- **Don't** present placeholder rows as working inputs or show fabricated calculation values.
- **Don't** add decorative shadows, instrument-panel ornament, or competing shell accents.
- **Don't** move the arm during calculation, apply invalid or stale solutions, or imply collision avoidance, independent orientation control, Cartesian planning, or physical dynamics.
- **Don't** substitute browser layouts or web component libraries for the native Qt interface.

Native review captures for Phase 6 are stored under `.impeccable/review/phase6/`: `demo-{960,1100,1360}-{fully-extended,raised-arm,elbow-bend,ik-matrix,ik-actions,invalid}.png` and `view-angle-{0,1}.png`. These are desktop captures, not browser previews.
