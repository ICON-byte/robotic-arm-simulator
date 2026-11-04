"""External smoke test: does not add test code to the shipped application."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from PIL import ImageGrab
import pefile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--executable", type=Path, default=ROOT / "dist/RoboKin3D/RoboKin3D.exe")
EXE = parser.parse_args().executable.resolve()
OUTPUT = ROOT / ".impeccable/review/branding/frozen"
OUTPUT.mkdir(parents=True, exist_ok=True)
pe = pefile.PE(str(EXE))
groups = [e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id == 14]
frames = [e for e in pe.DIRECTORY_ENTRY_RESOURCE.entries if e.id == 3]
assert groups and len(frames[0].directory.entries) == 7
assert pe.OPTIONAL_HEADER.Subsystem == 2
user32 = ctypes.windll.user32
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.SendMessageW.restype = ctypes.c_void_p
callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
report = {"exe_icon_frames": 7, "windows_gui_subsystem": True}
env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME")}
env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
env["ROBOKIN3D_LOG_DIR"] = str(ROOT / ".tmp/frozen-branding-logs")
with tempfile.TemporaryDirectory(prefix="robokin3d-startup-") as directory:
    started = time.perf_counter()
    process = subprocess.Popen([str(EXE)], cwd=directory, env=env)
    seen_splash = False
    main = None
    try:
        while time.perf_counter() - started < 60:
            windows = []
            @callback_type
            def collect(handle, unused):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(handle, ctypes.byref(pid))
                if pid.value == process.pid and user32.IsWindowVisible(handle):
                    title = ctypes.create_unicode_buffer(512)
                    user32.GetWindowTextW(handle, title, 512)
                    windows.append((handle, title.value))
                return True
            user32.EnumWindows(collect, 0)
            for handle, title in windows:
                if "Starting" in title:
                    seen_splash = True
                if title.startswith("RoboKin3D —"):
                    main = handle
            if main:
                break
            assert process.poll() is None, "Executable exited before showing the main window"
            time.sleep(0.1)
        assert main, "Main window did not appear; inspect startup.log"
        time.sleep(1)
        report.update(splash_observed=seen_splash, main_window_visible=True,
                      seconds_to_native_window=round(time.perf_counter()-started, 3),
                      native_small_icon=bool(user32.SendMessageW(main, 0x7f, 0, 0)),
                      native_large_icon=bool(user32.SendMessageW(main, 0x7f, 1, 0)),
                      unrelated_cwd=True, python_environment_removed=True)
        controls = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                                   "-File", str(ROOT / "scripts/verify_windows_controls.ps1"),
                                   "-ApplicationProcessId", str(process.pid)],
                                  capture_output=True, text=True, timeout=45)
        report["packaged_controls"] = controls.stdout.strip()
        assert controls.returncode == 0, controls.stdout + controls.stderr
        rect = wintypes.RECT()
        user32.GetWindowRect(main, ctypes.byref(rect))
        ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, min(rect.bottom, rect.top+38))).save(OUTPUT / "titlebar.png")
        user32.PostMessageW(main, 0x10, 0, 0)
        report["exit_code"] = process.wait(timeout=20)
        assert report["exit_code"] == 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
(OUTPUT / "verification.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
