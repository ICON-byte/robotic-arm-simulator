"""Native startup splash and staged initialization; no artificial delay."""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from time import perf_counter

from PySide6.QtCore import QEventLoop, QObject, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QProgressBar, QSplashScreen

from . import __version__
from .branding import APP_NAME, RESOURCE_DIR


def configure_logging():
    directory = Path(os.environ.get("ROBOKIN3D_LOG_DIR") or
                     str(Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP_NAME / "logs"))
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(directory / "startup.log", maxBytes=512_000, backupCount=1, encoding="utf-8")
    except OSError:
        logging.getLogger(__name__).warning("Startup file log unavailable")
        return None
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    return directory / "startup.log"


class StartupSplash(QSplashScreen):
    def __init__(self):
        # Paint at device pixel ratio, retaining logical layout on high-DPI screens.
        screen = QApplication.primaryScreen()
        ratio = screen.devicePixelRatio() if screen else 1.0
        pixmap = QPixmap(round(560*ratio), round(300*ratio))
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(QColor("#101c2b"))
        mark = QPixmap(str(RESOURCE_DIR / "robokin3d.png"))
        if mark.isNull():
            raise RuntimeError("Splash icon PNG is missing")
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.drawPixmap(28, 38, 96, 96, mark)
        painter.setPen(QColor("#e5edf3"))
        painter.setFont(QFont("Segoe UI", 28, QFont.Weight.DemiBold))
        painter.drawText(QRectF(144, 42, 390, 50), APP_NAME)
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor("#a8b8c7"))
        painter.drawText(QRectF(144, 98, 390, 24), "3D Robotic Arm Kinematics Simulator")
        painter.setPen(QColor("#e2b77c"))
        painter.drawText(QRectF(32, 170, 490, 24), f"Version {__version__}")
        painter.end()
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(f"{APP_NAME} · Starting")
        self.status = QLabel("Preparing application…", self)
        self.status.setGeometry(32, 214, 496, 28)
        self.status.setStyleSheet("background: transparent; color: #a8b8c7; font: 13px 'Segoe UI';")
        self.progress = QProgressBar(self)
        self.progress.setGeometry(32, 260, 496, 5)
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("QProgressBar {background:#263b49;border:0;} QProgressBar::chunk {background:#59bdb0;}")

    def set_status(self, message):
        self.status.setText(message)
        self.repaint()
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def mousePressEvent(self, event):
        # QSplashScreen normally hides on click; initialization owns dismissal.
        event.accept()


class StartupController(QObject):
    ready = Signal(object)
    failed = Signal()

    def __init__(self, app, log_path=None):
        super().__init__(app)
        self.app = app
        self.log_path = log_path
        self.splash = StartupSplash()
        self.window = None
        self.window_class = None
        self.started = perf_counter()

    def start(self):
        self.splash.show()
        self.splash.set_status("Loading 3D engine…")
        QTimer.singleShot(0, self._load)

    def _load(self):
        try:
            from .ui.main_window import MainWindow
            self.window_class = MainWindow
            self.splash.set_status("Creating robotics workspace…")
            QTimer.singleShot(0, self._create)
        except Exception:
            self._failure()

    def _create(self):
        try:
            self.window = self.window_class()
            self.splash.set_status("Preparing 3D view and controls…")
            self.window.show()
            QTimer.singleShot(0, self._finish)
        except Exception:
            self._failure()

    def _finish(self):
        try:
            self.splash.finish(self.window)
            logging.getLogger(__name__).info("Main window ready in %.3f seconds", perf_counter()-self.started)
            self.ready.emit(self.window)
        except Exception:
            self._failure()

    def _failure(self):
        logging.getLogger(__name__).exception("Unable to initialize the desktop workspace")
        self.splash.close()
        if self.window is not None:
            self.window.close()
        message = "The 3D workspace could not be initialized. Check the application dependencies and graphics driver, then restart."
        if self.log_path:
            message += f"\n\nStartup diagnostics: {self.log_path}"
        QMessageBox.critical(None, f"{APP_NAME} could not start", message)
        self.failed.emit()
        self.app.exit(1)
