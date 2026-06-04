"""
Phone Controller - Screenshot, coordinate mapping, input management
"""
import asyncio
import base64
import subprocess
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
import json

from loguru import logger

from app.services.adb_manager import adb_manager, DeviceInfo


class InputMethod(str, Enum):
    """Input method"""
    TAP = "tap"
    SWIPE = "swipe"
    LONG_PRESS = "long_press"
    KEY_EVENT = "key_event"
    TEXT = "text"


@dataclass
class Coordinate:
    """Screen coordinate"""
    x: int
    y: int


@dataclass
class TapAction:
    """Tap action"""
    x: int
    y: int
    duration: int = 100  # milliseconds


@dataclass
class SwipeAction:
    """Swipe action"""
    x1: int
    y1: int
    x2: int
    y2: int
    duration: int = 300  # milliseconds


@dataclass
class TextAction:
    """Text input action"""
    text: str
    clear_first: bool = False


class PhoneController:
    """
    Phone Controller for device interaction
    
    Handles screenshots, coordinate mapping, input management,
    and batch operations.
    """
    
    def __init__(self):
        """Initialize Phone Controller"""
        self.screenshot_cache: Dict[str, bytes] = {}
        self.coordinate_cache: Dict[str, Dict[str, int]] = {}
        
    # ========== Screenshot Management ==========
    
    async def take_screenshot(self, serial: str, method: str = "screencap") -> Optional[str]:
        """
        Take screenshot from device
        
        Args:
            serial: Device serial
            method: Screenshot method (screencap/scrcpy)
            
        Returns:
            Base64 encoded image or None
        """
        logger.info(f"Taking screenshot from {serial} using {method}")
        
        if method == "screencap":
            return await self._screencap_screenshot(serial)
        elif method == "scrcpy":
            return await self._scrcpy_screenshot(serial)
        else:
            raise ValueError(f"Unknown screenshot method: {method}")
            
    async def _screencap_screenshot(self, serial: str) -> Optional[str]:
        """
        Take screenshot using screencap command
        
        Returns:
            Base64 encoded PNG image
        """
        try:
            # Execute screencap command (binary output)
            success, output = await adb_manager._execute_adb_command_binary(
                serial, "shell screencap -p"
            )
            
            if not success:
                logger.error(f"Screencap failed: {output}")
                return None
                
            # Fix potential line ending issues (CR LF -> LF)
            if isinstance(output, bytes):
                output = output.replace(b'\r\n', b'\n')
            
            return base64.b64encode(output).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Screencap error: {e}")
            return None
            
    async def _scrcpy_screenshot(self, serial: str) -> Optional[str]:
        """
        Take screenshot using scrcpy
        
        Returns:
            Base64 encoded JPEG image
        """
        try:
            # Use scrcpy with no-display mode
            cmd = [
                "scrcpy",
                "--serial", serial,
                "--no-display",
                "--no-window",
                "--record", "-",  # Record to stdout
                "--max-fps", "1",
                "--frames", "1"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=5
            )
            
            if process.returncode == 0 and stdout:
                return base64.b64encode(stdout).decode('utf-8')
            else:
                logger.error(f"Scrcpy failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Scrcpy error: {e}")
            return None
            
    # ========== Coordinate Mapping ==========
    
    def map_coordinates(
        self,
        serial: str,
        x: float,
        y: float,
        screen_width: int,
        screen_height: int
    ) -> Tuple[int, int]:
        """
        Map relative coordinates (0-1) to absolute coordinates
        
        Args:
            serial: Device serial
            x: Relative X (0-1)
            y: Relative Y (0-1)
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            
        Returns:
            Tuple of (absolute_x, absolute_y)
        """
        abs_x = int(x * screen_width)
        abs_y = int(y * screen_height)
        
        return abs_x, abs_y
        
    def map_coordinates_to_relative(
        self,
        serial: str,
        x: int,
        y: int,
        screen_width: int,
        screen_height: int
    ) -> Tuple[float, float]:
        """
        Map absolute coordinates to relative (0-1)
        
        Args:
            serial: Device serial
            x: Absolute X
            y: Absolute Y
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            
        Returns:
            Tuple of (relative_x, relative_y)
        """
        rel_x = x / screen_width
        rel_y = y / screen_height
        
        return rel_x, rel_y
        
    # ========== Input Management ==========
    
    async def tap(self, serial: str, x: int, y: int, duration: int = 100) -> bool:
        """
        Tap on screen
        
        Args:
            serial: Device serial
            x: X coordinate
            y: Y coordinate
            duration: Tap duration in milliseconds
            
        Returns:
            True if successful
        """
        logger.debug(f"Tapping ({x}, {y}) on {serial}")
        
        if duration > 100:
            # Long press
            success, output = await adb_manager.execute_command(
                serial, f"shell input swipe {x} {y} {x} {y} {duration}"
            )
        else:
            # Regular tap
            success, output = await adb_manager.execute_command(
                serial, f"shell input tap {x} {y}"
            )
            
        return success
        
    async def swipe(
        self,
        serial: str,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        duration: int = 300
    ) -> bool:
        """
        Swipe on screen
        
        Args:
            serial: Device serial
            x1: Start X
            y1: Start Y
            x2: End X
            y2: End Y
            duration: Swipe duration in milliseconds
            
        Returns:
            True if successful
        """
        logger.debug(f"Swiping from ({x1}, {y1}) to ({x2}, {y2}) on {serial}")
        
        success, output = await adb_manager.execute_command(
            serial, f"shell input swipe {x1} {y1} {x2} {y2} {duration}"
        )
        
        return success
        
    async def long_press(self, serial: str, x: int, y: int, duration: int = 1000) -> bool:
        """
        Long press on screen
        
        Args:
            serial: Device serial
            x: X coordinate
            y: Y coordinate
            duration: Press duration in milliseconds
            
        Returns:
            True if successful
        """
        logger.debug(f"Long pressing ({x}, {y}) on {serial} for {duration}ms")
        
        return await self.swipe(serial, x, y, x, y, duration)
        
    async def input_text(self, serial: str, text: str, clear_first: bool = False) -> bool:
        """
        Input text on device
        
        Args:
            serial: Device serial
            text: Text to input
            clear_first: Clear existing text first
            
        Returns:
            True if successful
        """
        logger.debug(f"Inputting text on {serial}")
        
        if clear_first:
            # Select all and delete
            await self.key_event(serial, "KEYCODE_MOVE_END")
            await self.key_event(serial, "KEYCODE_DEL")
            
        # Escape special characters for shell
        escaped_text = text.replace("'", "\\'").replace('"', '\\"')
        
        success, output = await adb_manager.execute_command(
            serial, f"shell input text '{escaped_text}'"
        )
        
        return success
        
    async def input_chinese_text(self, serial: str, text: str) -> bool:
        """
        Input Chinese text using clipboard method
        
        Args:
            serial: Device serial
            text: Chinese text to input
            
        Returns:
            True if successful
        """
        logger.debug(f"Inputting Chinese text on {serial}")
        
        # Method 1: Use ADB Keyboard (if installed)
        success, output = await adb_manager.execute_command(
            serial, f"shell am broadcast -a ADB_INPUT_TEXT --es msg '{text}'"
        )
        
        if success and "result=0" in output.lower():
            return True
            
        # Method 2: Use clipboard + paste
        logger.debug("Falling back to clipboard method")
        
        # Set clipboard
        success, _ = await adb_manager.execute_command(
            serial, f"shell input text '{text}'"
        )
        
        if not success:
            # Use service call clipboard
            import base64
            encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
            success, _ = await adb_manager.execute_command(
                serial, f"shell service call clipboard 1 i32 1 i64 0 s16 '{encoded}'"
            )
            
        if success:
            # Paste
            await self.key_event(serial, "KEYCODE_PASTE")
            
        return success
        
    async def key_event(self, serial: str, keycode: str, count: int = 1) -> bool:
        """
        Send key event
        
        Args:
            serial: Device serial
            keycode: Android keycode
            count: Number of times to send
            
        Returns:
            True if successful
        """
        logger.debug(f"Sending key event {keycode} on {serial}")
        
        for _ in range(count):
            success, _ = await adb_manager.execute_command(
                serial, f"shell input keyevent {keycode}"
            )
            if not success:
                return False
                
        return True
        
    async def press_back(self, serial: str) -> bool:
        """Press back button"""
        return await self.key_event(serial, "KEYCODE_BACK")
        
    async def press_home(self, serial: str) -> bool:
        """Press home button"""
        return await self.key_event(serial, "KEYCODE_HOME")
        
    async def press_enter(self, serial: str) -> bool:
        """Press enter key"""
        return await self.key_event(serial, "KEYCODE_ENTER")
        
    # ========== Batch Operations ==========
    
    async def execute_actions(self, serial: str, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple actions on device
        
        Args:
            serial: Device serial
            actions: List of action dictionaries
            
        Returns:
            List of action results
        """
        results = []
        
        for action in actions:
            action_type = action.get("type")
            params = action.get("params", {})
            
            try:
                if action_type == "tap":
                    success = await self.tap(
                        serial,
                        params["x"],
                        params["y"],
                        params.get("duration", 100)
                    )
                elif action_type == "swipe":
                    success = await self.swipe(
                        serial,
                        params["x1"],
                        params["y1"],
                        params["x2"],
                        params["y2"],
                        params.get("duration", 300)
                    )
                elif action_type == "text":
                    success = await self.input_text(
                        serial,
                        params["text"],
                        params.get("clear_first", False)
                    )
                elif action_type == "key":
                    success = await self.key_event(
                        serial,
                        params["keycode"],
                        params.get("count", 1)
                    )
                elif action_type == "wait":
                    await asyncio.sleep(params.get("seconds", 1))
                    success = True
                else:
                    logger.warning(f"Unknown action type: {action_type}")
                    success = False
                    
                results.append({
                    "action": action_type,
                    "success": success,
                    "params": params
                })
                
            except Exception as e:
                logger.error(f"Action {action_type} failed: {e}")
                results.append({
                    "action": action_type,
                    "success": False,
                    "error": str(e),
                    "params": params
                })
                
        return results
        
    # ========== App Management ==========
    
    async def start_app(self, serial: str, package_name: str) -> bool:
        """
        Start an app
        
        Args:
            serial: Device serial
            package_name: App package name
            
        Returns:
            True if successful
        """
        logger.debug(f"Starting app {package_name} on {serial}")
        
        # Get main activity
        success, output = await adb_manager.execute_command(
            serial,
            f"shell cmd package resolve-activity --brief {package_name}"
        )
        
        if success and "/" in output:
            activity = output.strip().split("/")[-1]
            success, _ = await adb_manager.execute_command(
                serial,
                f"shell am start -n {package_name}/{activity}"
            )
            return success
            
        # Fallback: try to launch with monkey
        success, _ = await adb_manager.execute_command(
            serial,
            f"shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
        )
        
        return success
        
    async def stop_app(self, serial: str, package_name: str) -> bool:
        """
        Stop an app
        
        Args:
            serial: Device serial
            package_name: App package name
            
        Returns:
            True if successful
        """
        logger.debug(f"Stopping app {package_name} on {serial}")
        
        success, _ = await adb_manager.execute_command(
            serial,
            f"shell am force-stop {package_name}"
        )
        
        return success
        
    async def is_app_running(self, serial: str, package_name: str) -> bool:
        """
        Check if app is running
        
        Args:
            serial: Device serial
            package_name: App package name
            
        Returns:
            True if app is running
        """
        success, output = await adb_manager.execute_command(
            serial,
            f"shell pidof {package_name}"
        )
        
        return success and output.strip() != ""


# Singleton instance
phone_controller = PhoneController()
