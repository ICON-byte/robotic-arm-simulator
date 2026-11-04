"""Launch with python -m robotic_arm_simulator."""

import os
import sys
import logging
from importlib.resources import files

# Select the same binding for QtPy and the application before visualization imports.
os.environ["QT_API"] = "pyside6"

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox
from . import __version__
from .branding import APP_NAME, application_icon, set_windows_identity
from .startup import StartupController, configure_logging


def main() -> int:
    log_path = configure_logging()
    set_windows_identity()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    app.setOrganizationName(APP_NAME)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    try:
        app.setWindowIcon(application_icon())
        app.setStyleSheet(files("robotic_arm_simulator.ui").joinpath("theme.qss").read_text())
        logging.getLogger(__name__).info("%s %s starting; frozen=%s", APP_NAME, __version__, getattr(sys, "frozen", False))
        startup = StartupController(app, log_path)
        startup.start()
    except Exception:
        logging.getLogger(__name__).exception("Unable to initialize the desktop workspace")
        QMessageBox.critical(None, f"{APP_NAME} could not start",
                             "Application resources could not be initialized. Extract the complete distribution and try again. See the startup log for details.")
        return 1
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
