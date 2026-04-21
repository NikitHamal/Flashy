from __future__ import annotations

import base64
import io
import platform
import shutil
import subprocess
import time
import webbrowser
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from PIL import Image


class DesktopAutomationError(RuntimeError):
    pass


@dataclass(slots=True)
class ActionResult:
    ok: bool
    message: str
    details: Dict[str, Any]

    def to_tool_payload(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "message": self.message,
            "details": self.details,
        }


class DesktopController:
    def __init__(self) -> None:
        self.platform = platform.system().lower()
        self._pyautogui = None
        self._mss = None
        self._set_sane_defaults()

    def _set_sane_defaults(self) -> None:
        try:
            pag = self._load_pyautogui()
            pag.FAILSAFE = True
            pag.PAUSE = 0.08
        except Exception:
            pass

    def _load_pyautogui(self):
        if self._pyautogui is None:
            import pyautogui

            self._pyautogui = pyautogui
        return self._pyautogui

    def _load_mss(self):
        if self._mss is None:
            from mss import mss

            self._mss = mss
        return self._mss

    def _require_tooling(self) -> None:
        missing = []
        for module in ("pyautogui", "mss", "PIL"):
            try:
                __import__(module)
            except Exception:
                missing.append(module)
        if missing:
            raise DesktopAutomationError(
                "Computer Use dependencies are missing. Install: " + ", ".join(missing)
            )

    def capture_observation(self, max_width: int = 1440) -> Dict[str, Any]:
        self._require_tooling()
        pag = self._load_pyautogui()
        with self._load_mss()() as sct:
            monitor = sct.monitors[0]
            raw = sct.grab(monitor)
            image = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

        width, height = image.size
        if width > max_width:
            ratio = max_width / width
            image = image.resize((int(width * ratio), int(height * ratio)), Image.LANCZOS)
        data_url = self._image_to_data_url(image)
        cursor_x, cursor_y = pag.position()
        return {
            "width": width,
            "height": height,
            "platform": self.platform,
            "cursor_x": int(cursor_x),
            "cursor_y": int(cursor_y),
            "screenshot_data_url": data_url,
        }

    @staticmethod
    def _image_to_data_url(image: Image.Image) -> str:
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=82, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"

    def wait(self, seconds: float) -> ActionResult:
        time.sleep(max(0.0, min(seconds, 30.0)))
        return ActionResult(True, f"Waited {seconds:.2f}s", {"seconds": seconds})

    def move_cursor(self, x: int, y: int, duration: float = 0.15) -> ActionResult:
        pag = self._load_pyautogui()
        pag.moveTo(int(x), int(y), duration=max(0.0, min(duration, 2.0)))
        return ActionResult(True, f"Moved cursor to ({x}, {y})", {"x": x, "y": y, "duration": duration})

    def click(self, x: int, y: int, button: str = "left", clicks: int = 1) -> ActionResult:
        pag = self._load_pyautogui()
        pag.click(int(x), int(y), clicks=max(1, min(clicks, 4)), interval=0.12, button=button)
        return ActionResult(True, f"Clicked {button} at ({x}, {y})", {"x": x, "y": y, "button": button, "clicks": clicks})

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.35) -> ActionResult:
        pag = self._load_pyautogui()
        pag.moveTo(int(start_x), int(start_y), duration=0.05)
        pag.dragTo(int(end_x), int(end_y), duration=max(0.1, min(duration, 3.0)), button="left")
        return ActionResult(
            True,
            f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})",
            {
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "duration": duration,
            },
        )

    def scroll(self, amount: int, x: Optional[int] = None, y: Optional[int] = None) -> ActionResult:
        pag = self._load_pyautogui()
        if x is not None and y is not None:
            pag.moveTo(int(x), int(y), duration=0.05)
        pag.scroll(int(amount))
        return ActionResult(True, f"Scrolled {amount}", {"amount": amount, "x": x, "y": y})

    def press_keys(self, keys: Iterable[str]) -> ActionResult:
        pag = self._load_pyautogui()
        normalized = [str(key).lower() for key in keys if key]
        if not normalized:
            raise DesktopAutomationError("press_keys requires at least one key")
        if len(normalized) == 1:
            pag.press(normalized[0])
        else:
            pag.hotkey(*normalized)
        return ActionResult(True, f"Pressed {' + '.join(normalized)}", {"keys": normalized})

    def type_text(self, text: str, paste: bool = True) -> ActionResult:
        pag = self._load_pyautogui()
        if paste:
            try:
                import pyperclip

                pyperclip.copy(text)
                if self.platform == "darwin":
                    pag.hotkey("command", "v")
                else:
                    pag.hotkey("ctrl", "v")
                return ActionResult(True, "Pasted text from clipboard", {"length": len(text), "mode": "paste"})
            except Exception:
                pass
        pag.write(text, interval=0.012)
        return ActionResult(True, "Typed text", {"length": len(text), "mode": "type"})

    def open_url(self, url: str, preferred_browser: Optional[str] = None) -> ActionResult:
        url = url.strip()
        if not url:
            raise DesktopAutomationError("open_url requires a non-empty url")

        launched = False
        browser = (preferred_browser or "").strip()
        if browser:
            launched = self._open_in_named_browser(url, browser)
        if not launched:
            launched = webbrowser.open(url, new=2)
        if not launched:
            raise DesktopAutomationError(f"Unable to open URL: {url}")
        return ActionResult(True, f"Opened URL {url}", {"url": url, "browser": browser or "default"})

    def _open_in_named_browser(self, url: str, browser_name: str) -> bool:
        browser_name = browser_name.strip()
        try:
            if self.platform == "windows":
                command = f'start "" "{browser_name}" "{url}"'
                subprocess.Popen(["cmd", "/c", command])
                return True
            if self.platform == "darwin":
                subprocess.Popen(["open", "-a", browser_name, url])
                return True
            subprocess.Popen([browser_name, url])
            return True
        except Exception:
            return False

    def open_application(self, app_name: str) -> ActionResult:
        app_name = app_name.strip()
        if not app_name:
            raise DesktopAutomationError("open_application requires a non-empty app_name")

        if self.platform == "windows":
            command = f'Start-Process -FilePath "{app_name}"'
            completed = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                capture_output=True,
                text=True,
            )
            if completed.returncode == 0:
                return ActionResult(True, f"Launched {app_name}", {"app_name": app_name})
            fallback = subprocess.run(["cmd", "/c", "start", "", app_name], capture_output=True, text=True)
            if fallback.returncode == 0:
                return ActionResult(True, f"Launched {app_name}", {"app_name": app_name, "mode": "cmd-start"})
            raise DesktopAutomationError((completed.stderr or fallback.stderr or "Unable to launch application").strip())

        if self.platform == "darwin":
            completed = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
            if completed.returncode == 0:
                return ActionResult(True, f"Launched {app_name}", {"app_name": app_name})
            raise DesktopAutomationError((completed.stderr or "Unable to launch application").strip())

        candidates = [app_name]
        if shutil.which("gtk-launch"):
            candidates.insert(0, f"gtk-launch::{app_name}")
        last_error = None
        for candidate in candidates:
            try:
                if candidate.startswith("gtk-launch::"):
                    subprocess.Popen(["gtk-launch", candidate.split("::", 1)[1]])
                else:
                    subprocess.Popen([candidate])
                return ActionResult(True, f"Launched {app_name}", {"app_name": app_name})
            except Exception as exc:
                last_error = exc
        raise DesktopAutomationError(str(last_error or f"Unable to launch {app_name}"))

    def run_action(self, name: str, arguments: Dict[str, Any]) -> ActionResult:
        handlers = {
            "move_cursor": lambda: self.move_cursor(arguments["x"], arguments["y"], arguments.get("duration", 0.15)),
            "click": lambda: self.click(arguments["x"], arguments["y"], arguments.get("button", "left"), arguments.get("clicks", 1)),
            "drag": lambda: self.drag(
                arguments["start_x"],
                arguments["start_y"],
                arguments["end_x"],
                arguments["end_y"],
                arguments.get("duration", 0.35),
            ),
            "scroll": lambda: self.scroll(arguments["amount"], arguments.get("x"), arguments.get("y")),
            "press_keys": lambda: self.press_keys(arguments.get("keys", [])),
            "type_text": lambda: self.type_text(arguments["text"], arguments.get("paste", True)),
            "open_url": lambda: self.open_url(arguments["url"], arguments.get("preferred_browser")),
            "open_application": lambda: self.open_application(arguments["app_name"]),
            "wait": lambda: self.wait(float(arguments.get("seconds", 1.0))),
        }
        if name not in handlers:
            raise DesktopAutomationError(f"Unsupported action: {name}")
        return handlers[name]()
