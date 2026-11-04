# Robotic Arm Kinematics Simulator

## Platform
Windows desktop, native Qt widgets.

## Stack
Python 3.12, PySide6, PyVista, PyVistaQt, NumPy; pytest for verification.

## Users and purpose
A university course project for demonstrating a three-joint robotic arm and explaining forward and inverse kinematics. Operates locally without services or a database.

## Approved scope
Phases 1–4 established the desktop shell, shared geometry, joint controls, resets, FK/matrix/copy results, and analytical IK with explicit calculate/select/apply workflow. Phase 5 is approved: smoothstep joint-space motion driven by a monotonic Qt timer, speed selection, pause/resume, cancellation, exact completion, and synchronized FK/IK feedback. Immediate IK application remains available. One shared robot state serves every mode. Collision detection, Cartesian planning, physical dynamics, torque simulation, numerical IK, multiple robot types, and packaging remain outside scope. Phase 6 refinement requires separate approval.

## Visual commitments
Professional dark theme, readable typography, generous viewport, organized sidebar, clear status feedback, and no unnecessary decorative effects. User approved implementation from the proposed plan; routine design decisions are delegated.
