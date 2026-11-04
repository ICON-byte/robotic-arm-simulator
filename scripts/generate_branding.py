"""Render our original SVG with Qt; PNG/ICO conversion uses existing Pillow."""

from pathlib import Path
import sys

from PIL import Image
from PySide6.QtCore import QRectF
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

ROOT = Path(__file__).resolve().parents[1]
RESOURCES = ROOT / "src/robotic_arm_simulator/resources"


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    renderer = QSvgRenderer(str(RESOURCES / "robokin3d.svg"))
    if not renderer.isValid():
        raise RuntimeError("Original icon SVG is invalid")
    image = QImage(1024, 1024, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter, QRectF(0, 0, 1024, 1024))
    painter.end()
    png = RESOURCES / "robokin3d.png"
    if not image.save(str(png)):
        raise RuntimeError("Could not write PNG")
    with Image.open(png) as source:
        source.resize((512, 512), Image.Resampling.LANCZOS).save(png)
        source.save(RESOURCES / "robokin3d.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    print(f"Original PNG and seven-resolution ICO generated in {RESOURCES}")


if __name__ == "__main__":
    main()
