"""
uiautomator2 connection manager
Wraps uiautomator2 connections with a thread-safe connection pool.
All u2 calls are synchronous; exposed via async methods using asyncio.to_thread().
"""
import asyncio
import threading
import base64
from typing import Any, Dict, Optional

import uiautomator2 as u2


class U2Manager:
    """Thread-safe connection pool for uiautomator2 devices."""

    def __init__(self) -> None:
        self._connections: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def _get_device(self, serial: str) -> Any:
        """Get or create a cached u2 device connection (sync, thread-safe)."""
        with self._lock:
            if serial not in self._connections:
                self._connections[serial] = u2.connect(serial)
            return self._connections[serial]

    def connect(self, serial: str) -> Any:
        """Connect to a device (lazy, cached)."""
        return self._get_device(serial)

    def disconnect(self, serial: str) -> None:
        """Remove a cached connection."""
        with self._lock:
            self._connections.pop(serial, None)

    # ── Async wrappers (use from FastAPI endpoints) ──────────────────────

    async def tap(self, serial: str, x: int, y: int) -> None:
        dev = self._get_device(serial)
        await asyncio.to_thread(dev.click, x, y)

    async def long_press(self, serial: str, x: int, y: int, duration: float = 1.0) -> None:
        dev = self._get_device(serial)
        await asyncio.to_thread(dev.long_click, x, y, duration=duration)

    async def swipe(
        self, serial: str, x1: int, y1: int, x2: int, y2: int, duration: float = 0.3
    ) -> None:
        dev = self._get_device(serial)
        await asyncio.to_thread(dev.swipe, x1, y1, x2, y2, duration=duration)

    async def type_text(self, serial: str, text: str) -> None:
        dev = self._get_device(serial)
        await asyncio.to_thread(dev.send_keys, text)

    async def press_key(self, serial: str, key_name: str) -> None:
        dev = self._get_device(serial)
        await asyncio.to_thread(dev.press, key_name)

    async def key_event(self, serial: str, code: int) -> None:
        dev = self._get_device(serial)
        await asyncio.to_thread(dev.press, code)

    async def launch_app(self, serial: str, package: str, activity: str = "") -> None:
        dev = self._get_device(serial)
        if activity:
            await asyncio.to_thread(dev.app_start, package, activity)
        else:
            await asyncio.to_thread(dev.app_start, package)

    async def shell(self, serial: str, command: str) -> str:
        dev = self._get_device(serial)
        result = await asyncio.to_thread(dev.shell, command)
        # u2 shell returns a namedtuple (output, exit_code)
        return result.output if hasattr(result, "output") else str(result)

    async def get_ui_hierarchy(self, serial: str) -> str:
        dev = self._get_device(serial)
        xml = await asyncio.to_thread(dev.dump_hierarchy)
        return xml

    async def screenshot(self, serial: str) -> str:
        """Return a base64-encoded PNG screenshot."""
        dev = self._get_device(serial)
        img = await asyncio.to_thread(dev.screenshot)
        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    async def get_info(self, serial: str) -> Dict[str, Any]:
        dev = self._get_device(serial)
        # dev.info is a property (dict), window_size & app_current are methods
        info = dev.info  # synchronous property access is fine
        window_size = await asyncio.to_thread(dev.window_size)
        current_app = await asyncio.to_thread(dev.app_current)
        return {
            "serial": serial,
            "info": info,
            "window_size": list(window_size) if window_size else None,
            "current_app": current_app,
        }


# Singleton
u2_manager = U2Manager()
