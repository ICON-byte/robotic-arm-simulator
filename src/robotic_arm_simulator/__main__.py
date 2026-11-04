"""Launch with python -m robotic_arm_simulator."""

import os
import sys
from importlib.resources import files

# Select the same binding for QtPy and the application before visualization imports.
os.environ["QT_API"] = "pyside6"

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Robotic Arm Simulator")
    app.setOrganizationName("Robotics Lab")
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(files("robotic_arm_simulator.ui").joinpath("theme.qss").read_text())
    try:
        from .ui.main_window import MainWindow

        window = MainWindow()
        window.show()
    except Exception as exc:
        QMessageBox.critical(None, "Unable to start the 3D workspace", f"{exc}\n\nCheck your graphics driver and the installed dependencies. See README.md for setup instructions.")
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
