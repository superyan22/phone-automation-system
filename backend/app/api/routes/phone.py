"""
Phone control routes – uiautomator2 based.

All heavy u2 work runs in a thread via asyncio.to_thread so the async
event loop stays responsive.
"""
import shlex
from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.services.u2_manager import u2_manager

router = APIRouter(prefix="/api/v1/phone", tags=["phone"])


def _decode_serial(serial: str) -> str:
    """FastAPI path params get percent-encoded; decode back."""
    return unquote(serial)

# ── Dangerous command whitelist for /shell endpoint ─────────────────────
ALLOWED_SHELL_PREFIXES = (
    "ls", "cat", "echo", "getprop", "dumpsys", "pm list",
    "settings get", "settings list", "wm size", "wm density",
    "input", "am start", "am force-stop", "screencap", "id",
)

# ── Request / response models ───────────────────────────────────────────

class TapRequest(BaseModel):
    x: int
    y: int


class SwipeRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int
    duration: int = Field(default=300, description="Swipe duration in ms")


class TypeRequest(BaseModel):
    text: str


class PressRequest(BaseModel):
    key: str = Field(description="home / back / volume_up / volume_down / etc.")


class LaunchRequest(BaseModel):
    package: str
    activity: str = ""


class ShellRequest(BaseModel):
    command: str


class LongPressRequest(BaseModel):
    x: int
    y: int
    duration: int = Field(default=1000, description="Long-press duration in ms")


class KeyEventRequest(BaseModel):
    code: int = Field(description="Android KeyEvent code")


# ── Helpers ─────────────────────────────────────────────────────────────

def _validate_shell(command: str) -> None:
    """Raise 400 if the command isn't on the allowlist."""
    first_token = shlex.split(command)[0] if command.strip() else ""
    # Check if command starts with any allowed prefix
    if not any(command.strip().startswith(prefix) for prefix in ALLOWED_SHELL_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Command not allowed. Allowed prefixes: {ALLOWED_SHELL_PREFIXES}",
        )


# ── Routes ──────────────────────────────────────────────────────────────

@router.post("/{serial}/tap")
async def tap(serial: str, body: TapRequest):
    """Tap at (x, y)."""
    s = _decode_serial(serial)
    await u2_manager.tap(s, body.x, body.y)
    return {"status": "ok", "action": "tap", "x": body.x, "y": body.y}


@router.post("/{serial}/long_press")
async def long_press(serial: str, body: LongPressRequest):
    """Long press at (x, y) for *duration* ms."""
    s = _decode_serial(serial)
    await u2_manager.long_press(s, body.x, body.y, duration=body.duration / 1000)
    return {"status": "ok", "action": "long_press", "x": body.x, "y": body.y, "duration": body.duration}


@router.post("/{serial}/swipe")
async def swipe(serial: str, body: SwipeRequest):
    """Swipe from (x1,y1) to (x2,y2)."""
    s = _decode_serial(serial)
    await u2_manager.swipe(s, body.x1, body.y1, body.x2, body.y2, duration=body.duration / 1000)
    return {"status": "ok", "action": "swipe"}


@router.post("/{serial}/type")
async def type_text(serial: str, body: TypeRequest):
    """Type text via send_keys."""
    s = _decode_serial(serial)
    await u2_manager.type_text(s, body.text)
    return {"status": "ok", "action": "type", "length": len(body.text)}


@router.post("/{serial}/press")
async def press_key(serial: str, body: PressRequest):
    """Press a named key (home, back, volume_up, …)."""
    s = _decode_serial(serial)
    await u2_manager.press_key(s, body.key)
    return {"status": "ok", "action": "press", "key": body.key}


@router.post("/{serial}/key")
async def key_event(serial: str, body: KeyEventRequest):
    """Send an Android KeyEvent by numeric code."""
    s = _decode_serial(serial)
    await u2_manager.key_event(s, body.code)
    return {"status": "ok", "action": "key_event", "code": body.code}


@router.post("/{serial}/launch")
async def launch_app(serial: str, body: LaunchRequest):
    """Start an app by package (and optional activity)."""
    s = _decode_serial(serial)
    await u2_manager.launch_app(s, body.package, body.activity)
    return {"status": "ok", "action": "launch", "package": body.package, "activity": body.activity}


@router.post("/{serial}/shell")
async def shell(serial: str, body: ShellRequest):
    """Run a whitelisted ADB shell command."""
    s = _decode_serial(serial)
    _validate_shell(body.command)
    output = await u2_manager.shell(s, body.command)
    return {"status": "ok", "output": output}


@router.get("/{serial}/ui")
async def ui_hierarchy(serial: str):
    """Return the current UI hierarchy XML."""
    s = _decode_serial(serial)
    xml = await u2_manager.get_ui_hierarchy(s)
    return {"xml": xml}


@router.get("/{serial}/screenshot")
async def screenshot(serial: str):
    """Return a base64-encoded PNG screenshot."""
    s = _decode_serial(serial)
    b64 = await u2_manager.screenshot(s)
    return {"base64_png": b64}


@router.get("/{serial}/info")
async def device_info(serial: str):
    """Return device info (screen size, current app, etc.)."""
    s = _decode_serial(serial)
    info = await u2_manager.get_info(s)
    return info
