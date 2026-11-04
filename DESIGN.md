---
name: Robotic Arm Simulator
description: Native Windows Qt workspace for inspecting a three-dimensional reference scene.
colors:
  accent: "#7ed5c7"
  reference-object: "#59bdb0"
  reference-edge: "#244f50"
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
  emphasis:
    fontFamily: "Segoe UI"
    fontSize: "13px"
    fontWeight: 600
rounded:
  control: "4px"
  panel: "5px"
spacing:
  compact: "4px"
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
    padding: "14px 16px"
  sidebar:
    backgroundColor: "{colors.sidebar}"
    padding: "24px"
  viewport:
    backgroundColor: "{colors.scene}"
---

# Design System: Robotic Arm Simulator

## Overview

**Creative North Star: "The Quiet 3D Workspace"**

A professional dark desktop workspace gives the rendered scene the most space and visual attention. Native Qt widgets provide readable controls, organized supporting information, and clear status feedback. The shell stays quiet and never imitates a physical instrument panel.

This document records the implemented Phase 1 foundation, rather than future robot controls or calculations. Color and shape decisions come from the Qt stylesheet and reference viewport. The north star is a descriptive name for that existing direction, not a new identity proposal.

**Key Characteristics:**

- Viewport-led composition with an adjustable, scrollable sidebar.
- Dark tonal surfaces, restrained mint emphasis, and readable text.
- Small corner radii and immediate native interaction feedback.
- Explicit explanations where later-phase functionality is unavailable.

## Colors

Dark blue-gray neutrals support a restrained mint accent and a distinct reference object.

### Primary

- **Mint accent** (`accent`): keyboard focus, button hover borders, and the current foundation scope label.
- **Reference mint** (`reference-object`, `reference-edge`): the cube and its darker edges inside the scene; these are rendering materials rather than control states.

### Neutral

- **Canvas and scene** (`canvas`, `scene`): separate the desktop shell from the 3D rendering surface.
- **Sidebar and raised surface** (`sidebar`, `raised`): organize supporting controls, header, results, and status bar.
- **Placeholder surface** (`placeholder`): identifies explanatory future-control rows and disabled buttons.
- **Text hierarchy** (`text`, `text-secondary`, `text-pending`, `text-placeholder`, `text-disabled`): distinguish primary content, guidance, future section titles, placeholder details, and disabled actions.
- **Structural lines** (`divider`, `control-border`): separate regions and define button and scrollbar edges.
- **Button states** (`button`, `button-hover`, `button-pressed`): provide immediate feedback without animation.
- **Scene support** (`scene-grid`, `scene-caption`): keep spatial references, the cube caption, and coordinate-axis labels legible without competing with geometry.

**The Reserved Accent Rule.** Use mint emphasis for focus, actionable hover feedback, and the current scope marker; keep general shell surfaces neutral. Coordinate-axis shafts retain PyVista's conventional colors; their labels use the scene-caption token.

## Typography

Segoe UI is the native application family. The application initializes a 10-point Qt font; the stylesheet establishes the widget body size through its body token. No web font, display face, fixed line-height, or letter-spacing system is installed.

- **Headline:** application heading, using the headline token.
- **Title:** sidebar, scene, and results section headings, using the title token.
- **Body:** standard widget copy and button text, using the body token.
- **Label:** secondary guidance and camera instructions, using the label token.
- **Emphasis:** pending section names and the phase marker, using the emphasis token with their role colors.

The viewport caption is a separate PyVista text actor using Arial and the renderer's `font_size=10` setting. This is not a Qt body-font token. Labels generally wrap their text; the scene toolbar hint stays on one line. Native layout and font metrics determine line height.

## Layout

The initial window is 1360 by 900, with a minimum of 960 by 680. A full-width header sits above a horizontal splitter; a native status bar anchors the bottom. The right workspace receives spare width. Neither splitter pane collapses.

The sidebar explicitly enables Qt styled-background painting so its sidebar surface token is honored. The sidebar scroll container spans 285–355 logical pixels; its child sidebar spans 270–340. Its outer padding uses the outer spacing token, with section spacing between labels and placeholder rows. The workspace uses outer horizontal and workspace-block vertical margins, and section spacing between toolbar, scene, camera guidance, and results. The header uses outer horizontal and header-block vertical padding. Results use panel-inline horizontal and control-inline vertical padding.

The viewport expands vertically. Explanatory results stay below it, and camera instructions remain visible between them. Resizing uses Qt layouts and sidebar scrolling; there are no web breakpoints or alternate mobile compositions. The native Windows title bar remains OS-controlled.

## Elevation & Depth

The shell uses tonal layering and thin separators, with no application-defined drop shadows. Raised surfaces distinguish header, results, and status from the canvas. The rendered scene supplies real three-dimensional depth; shell panels do not add artificial lighting or decorative elevation.

**The Quiet Shell Rule.** Convey shell structure through surface tone, spacing, and borders so the scene retains visual priority.

## Shapes

Controls and scrollbar handles use the control radius; placeholder rows and results use the panel radius. Header and sidebar boundaries remain rectangular. Buttons use a one-pixel border at rest; focused buttons use a two-pixel accent border with reduced padding to preserve their footprint. The splitter is a thin divider. There are no pill chips or ornamental frames.

## Components

### Buttons

The implemented action is **Reset view**, a native `QPushButton`. Its default, hover, pressed, disabled, and focus variants are recorded in the frontmatter. Hover changes the fill and border; pressed changes the fill; keyboard focus thickens the mint border. Feedback is immediate with no custom transition. The action supports Ctrl+Home and has a tooltip describing that shortcut.

### Cards / Containers

The results frame is a quiet raised container with panel corners. Future joint-control rows are explanatory `QLabel` blocks with placeholder fill, panel corners, internal section padding, and a minimum height of 58 logical pixels. They are not input fields or buttons.

### Sidebar and Status

The scrollable sidebar groups arm configuration and kinematics descriptions, then uses flexible space before the foundation marker. Pending headings remain legible and explanatory copy states that calculations are unavailable. A raised native status bar reports readiness and retains the native size grip. Its vertical scrollbar is 10 logical pixels wide; its handle has a minimum height of 24.

### Reference Viewport

A PyVistaQt interactor displays an 80 mm cube, a wire grid, conventional coordinate axes, and a reference-object caption. Trackball interaction supports rotation, zoom, and pan. Reset view restores perspective and the initial camera. The scene is an interactive reference, with no robot, joint values, or computed coordinates in Phase 1.

## Do's and Don'ts

### Do:

- **Do** keep the viewport dominant and supporting information organized in the sidebar and results frame.
- **Do** preserve visible keyboard focus, camera guidance, and the Reset view shortcut.
- **Do** use explanatory text for unavailable future controls and calculations.
- **Do** use native Qt layout behavior and the established surface and typography tokens.

### Don't:

- **Don't** present placeholder rows as working inputs or show fabricated calculation values.
- **Don't** add decorative shadows, instrument-panel ornament, or competing shell accents.
- **Don't** treat the reference cube as a robot model or extend Phase 1 into kinematics.
- **Don't** substitute browser layouts or web component libraries for the native Qt interface.
