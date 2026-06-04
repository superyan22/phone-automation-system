"""
ADB Manager - Device discovery, connection pool, and management
"""
import asyncio
import subprocess
import re
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from loguru import logger


class DeviceStatus(str, Enum):
    """Device status"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"


@dataclass
class DeviceInfo:
    """Device information"""
    serial: str
    device_type: str  # usb/wifi
    ip_address: Optional[str] = None
    port: int = 5555
    model: Optional[str] = None
    brand: Optional[str] = None
    android_version: Optional[str] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    screen_density: float = 1.0
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_heartbeat: Optional[datetime] = None


class ADBManager:
    """
    ADB Manager for device management
    
    Handles device discovery, connection pool, heartbeat monitoring,
    and reconnection strategies.
    """
    
    def __init__(self, adb_path: str = "adb", heartbeat_interval: int = 5):
        """
        Initialize ADB Manager
        
        Args:
            adb_path: Path to ADB executable
            heartbeat_interval: Heartbeat check interval in seconds
        """
        self.adb_path = adb_path
        self.heartbeat_interval = heartbeat_interval
        self.devices: Dict[str, DeviceInfo] = {}
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """Start ADB Manager"""
        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("ADB Manager started")
        
    async def stop(self):
        """Stop ADB Manager"""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        logger.info("ADB Manager stopped")
        
    async def _run_adb_command(self, args: List[str], timeout: int = 30, binary: bool = False) -> tuple:
        """
        Run ADB command
        
        Args:
            args: Command arguments
            timeout: Command timeout
            binary: If True, return raw bytes instead of decoded string
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        cmd = [self.adb_path] + args
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            if binary:
                return process.returncode, stdout, stderr.decode()
            return process.returncode, stdout.decode(), stderr.decode()
        except asyncio.TimeoutError:
            process.kill()
            return -1, b"" if binary else "", "Command timed out"
        except Exception as e:
            return -1, b"" if binary else "", str(e)
            
    # Allowed ADB commands whitelist for security
    ALLOWED_ADB_COMMANDS = {
        "devices", "shell", "push", "pull", "install", "uninstall",
        "start-server", "kill-server", "reconnect", "get-state",
        "get-serialno", "get-devpath", "remount", "reboot", "reboot-bootloader",
    }
    
    def _validate_adb_command(self, command: str) -> List[str]:
        """
        Validate and parse ADB command safely.
        
        Only allows whitelisted commands to prevent injection attacks.
        
        Args:
            command: Raw command string
            
        Returns:
            List of validated command arguments
            
        Raises:
            ValueError: If command is not allowed
        """
        import shlex
        
        try:
            # Use shlex for safe parsing (handles quotes, escapes)
            parts = shlex.split(command)
        except ValueError as e:
            raise ValueError(f"Invalid command syntax: {e}")
        
        if not parts:
            raise ValueError("Empty command")
        
        # Check if base command is allowed
        base_cmd = parts[0].lower()
        if base_cmd not in self.ALLOWED_ADB_COMMANDS:
            raise ValueError(
                f"Command '{base_cmd}' not allowed. "
                f"Allowed: {', '.join(sorted(self.ALLOWED_ADB_COMMANDS))}"
            )
        
        # For shell commands, validate the shell command too
        if base_cmd == "shell" and len(parts) > 1:
            shell_cmd = parts[1].lower()
            # Block dangerous shell commands
            blocked_patterns = ["rm ", "mkfs", "dd ", "format", "> /dev"]
            for pattern in blocked_patterns:
                if pattern in shell_cmd:
                    raise ValueError(f"Dangerous shell command blocked: {pattern}")
        
        return parts
    
    async def _execute_adb_command(self, serial: str, command: str, timeout: int = 30) -> tuple:
        """
        Execute ADB command on specific device
        
        Returns:
            Tuple of (success, output)
        """
        validated_args = self._validate_adb_command(command)
        args = ["-s", serial] + validated_args
        returncode, stdout, stderr = await self._run_adb_command(args, timeout)
        return returncode == 0, stdout if returncode == 0 else stderr
    
    async def _execute_adb_command_binary(self, serial: str, command: str, timeout: int = 30) -> tuple:
        """
        Execute ADB command that returns binary data
        
        Returns:
            Tuple of (success, output_bytes)
        """
        validated_args = self._validate_adb_command(command)
        args = ["-s", serial] + validated_args
        returncode, stdout, stderr = await self._run_adb_command(args, timeout, binary=True)
        return returncode == 0, stdout if returncode == 0 else stderr.encode()
        
    # ========== Device Discovery ==========
    
    async def discover_usb_devices(self) -> List[DeviceInfo]:
        """
        Discover USB connected devices
        
        Returns:
            List of discovered devices
        """
        logger.info("Discovering USB devices...")
        
        returncode, stdout, stderr = await self._run_adb_command(["devices", "-l"])
        if returncode != 0:
            logger.error(f"Failed to list devices: {stderr}")
            return []
            
        devices = []
        for line in stdout.strip().split("\n")[1:]:
            if not line or "offline" in line:
                continue
                
            parts = line.split()
            if len(parts) >= 2:
                serial = parts[0]
                status = "device" if parts[1] == "device" else "offline"
                
                # Extract model and product info
                model = None
                product = None
                for part in parts[2:]:
                    if part.startswith("model:"):
                        model = part.split(":")[1]
                    elif part.startswith("product:"):
                        product = part.split(":")[1]
                        
                device = DeviceInfo(
                    serial=serial,
                    device_type="usb",
                    model=model,
                    brand=product,
                    status=DeviceStatus.ONLINE if status == "device" else DeviceStatus.OFFLINE
                )
                devices.append(device)
                self.devices[serial] = device
                
        logger.info(f"Discovered {len(devices)} USB devices")
        return devices
        
    async def discover_wifi_devices(self, subnet: str = "192.168.1") -> List[DeviceInfo]:
        """
        Discover WiFi connected devices
        
        Args:
            subnet: Network subnet to scan
            
        Returns:
            List of discovered devices
        """
        logger.info(f"Scanning WiFi devices on subnet {subnet}...")
        
        devices = []
        
        # Try to connect to known ports
        for i in range(1, 255):
            ip = f"{subnet}.{i}"
            for port in [5555, 5556]:
                serial = f"{ip}:{port}"
                
                # Try to connect
                returncode, stdout, stderr = await self._run_adb_command(
                    ["connect", serial],
                    timeout=5
                )
                
                if returncode == 0 and "connected" in stdout.lower():
                    # Get device info
                    device = DeviceInfo(
                        serial=serial,
                        device_type="wifi",
                        ip_address=ip,
                        port=port,
                        status=DeviceStatus.ONLINE
                    )
                    
                    # Try to get model info
                    success, output = await self._execute_adb_command(
                        serial, "shell getprop ro.product.model"
                    )
                    if success:
                        device.model = output.strip()
                        
                    devices.append(device)
                    self.devices[serial] = device
                    
        logger.info(f"Discovered {len(devices)} WiFi devices")
        return devices
        
    async def discover_all(self, wifi_subnet: str = "192.168.1") -> List[DeviceInfo]:
        """
        Discover all devices (USB + WiFi)
        
        Args:
            wifi_subnet: WiFi subnet to scan
            
        Returns:
            List of all discovered devices
        """
        usb_devices = await self.discover_usb_devices()
        wifi_devices = await self.discover_wifi_devices(wifi_subnet)
        return usb_devices + wifi_devices
        
    # ========== Connection Management ==========
    
    async def connect_device(self, serial: str) -> bool:
        """
        Connect to device
        
        Args:
            serial: Device serial number
            
        Returns:
            True if connected successfully
        """
        logger.info(f"Connecting to device: {serial}")
        
        # Check if already connected
        if serial in self.devices and self.devices[serial].status == DeviceStatus.ONLINE:
            logger.info(f"Device {serial} already connected")
            return True
            
        # Try to connect
        returncode, stdout, stderr = await self._run_adb_command(["connect", serial])
        
        if returncode == 0 and "connected" in stdout.lower():
            # Get device info
            device = self.devices.get(serial, DeviceInfo(serial=serial, device_type="wifi"))
            device.status = DeviceStatus.ONLINE
            device.last_heartbeat = datetime.now()
            
            # Get device properties
            await self._update_device_info(device)
            
            self.devices[serial] = device
            logger.info(f"Connected to device: {serial}")
            return True
        else:
            logger.error(f"Failed to connect to {serial}: {stderr}")
            return False
            
    async def disconnect_device(self, serial: str) -> bool:
        """
        Disconnect device
        
        Args:
            serial: Device serial number
            
        Returns:
            True if disconnected successfully
        """
        logger.info(f"Disconnecting device: {serial}")
        
        returncode, stdout, stderr = await self._run_adb_command(["disconnect", serial])
        
        if serial in self.devices:
            self.devices[serial].status = DeviceStatus.OFFLINE
            
        return returncode == 0
        
    async def _update_device_info(self, device: DeviceInfo):
        """Update device information"""
        serial = device.serial
        
        # Get model
        success, output = await self._execute_adb_command(
            serial, "shell getprop ro.product.model"
        )
        if success:
            device.model = output.strip()
            
        # Get brand
        success, output = await self._execute_adb_command(
            serial, "shell getprop ro.product.brand"
        )
        if success:
            device.brand = output.strip()
            
        # Get Android version
        success, output = await self._execute_adb_command(
            serial, "shell getprop ro.build.version.release"
        )
        if success:
            device.android_version = output.strip()
            
        # Get screen size
        success, output = await self._execute_adb_command(
            serial, "shell wm size"
        )
        if success:
            match = re.search(r"(\d+)x(\d+)", output)
            if match:
                device.screen_width = int(match.group(1))
                device.screen_height = int(match.group(2))
                
        # Get screen density
        success, output = await self._execute_adb_command(
            serial, "shell wm density"
        )
        if success:
            match = re.search(r"(\d+)", output)
            if match:
                device.screen_density = int(match.group(1)) / 160.0
                
        logger.debug(f"Updated device info: {device}")
        
    # ========== Heartbeat Monitoring ==========
    
    async def _heartbeat_loop(self):
        """Heartbeat monitoring loop"""
        while self._running:
            try:
                await self._check_heartbeats()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(self.heartbeat_interval)
                
    async def _check_heartbeats(self):
        """Check heartbeats for all connected devices"""
        for serial, device in list(self.devices.items()):
            if device.status != DeviceStatus.ONLINE:
                continue
                
            try:
                # Send ping command
                success, output = await self._execute_adb_command(
                    serial, "shell echo ping", timeout=5
                )
                
                if success:
                    device.last_heartbeat = datetime.now()
                else:
                    # Device not responding, mark as offline
                    logger.warning(f"Device {serial} not responding to heartbeat")
                    device.status = DeviceStatus.OFFLINE
                    await self._handle_device_disconnect(serial)
                    
            except Exception as e:
                logger.error(f"Heartbeat check failed for {serial}: {e}")
                device.status = DeviceStatus.ERROR
                
    async def _handle_device_disconnect(self, serial: str):
        """Handle device disconnection"""
        logger.info(f"Handling disconnect for device: {serial}")
        
        # Try to reconnect
        for attempt in range(3):
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            if await self.connect_device(serial):
                logger.info(f"Reconnected to device {serial} on attempt {attempt + 1}")
                return
                
        logger.error(f"Failed to reconnect to device {serial} after 3 attempts")
        
    # ========== Command Execution ==========
    
    async def execute_command(self, serial: str, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute command on device
        
        Args:
            serial: Device serial
            command: ADB command (without adb prefix)
            timeout: Command timeout
            
        Returns:
            Dict with success, output, error
        """
        if serial not in self.devices or self.devices[serial].status != DeviceStatus.ONLINE:
            return {
                "success": False,
                "output": "",
                "error": f"Device {serial} not connected"
            }
            
        success, output = await self._execute_adb_command(serial, command, timeout)
        
        return {
            "success": success,
            "output": output,
            "error": None if success else output
        }
        
    async def get_device_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all devices
        
        Returns:
            List of device dictionaries
        """
        await self.discover_usb_devices()
        
        return [
            {
                "serial": device.serial,
                "device_type": device.device_type,
                "ip_address": device.ip_address,
                "port": device.port,
                "model": device.model,
                "brand": device.brand,
                "android_version": device.android_version,
                "screen_width": device.screen_width,
                "screen_height": device.screen_height,
                "screen_density": device.screen_density,
                "status": device.status.value,
                "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None,
            }
            for device in self.devices.values()
        ]
        
    def get_device(self, serial: str) -> Optional[Dict[str, Any]]:
        """Get single device info"""
        device = self.devices.get(serial)
        if not device:
            return None
            
        return {
            "serial": device.serial,
            "device_type": device.device_type,
            "ip_address": device.ip_address,
            "port": device.port,
            "model": device.model,
            "brand": device.brand,
            "android_version": device.android_version,
            "screen_width": device.screen_width,
            "screen_height": device.screen_height,
            "screen_density": device.screen_density,
            "status": device.status.value,
            "last_heartbeat": device.last_heartbeat.isoformat() if device.last_heartbeat else None,
        }


# Singleton instance
adb_manager = ADBManager()
