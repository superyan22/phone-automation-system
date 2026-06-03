"""
WebSocket Manager - Real-time communication for device control and task monitoring
"""
import asyncio
import json
from typing import Dict, Any, Optional, Set
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger

from app.services.adb_manager import adb_manager
from app.services.phone_controller import phone_controller


class ConnectionManager:
    """
    WebSocket Connection Manager
    
    Manages WebSocket connections for device control and task monitoring.
    """
    
    def __init__(self):
        """Initialize Connection Manager"""
        # Device connections: serial -> set of websockets
        self.device_connections: Dict[str, Set[WebSocket]] = {}
        # Task connections: task_id -> set of websockets
        self.task_connections: Dict[str, Set[WebSocket]] = {}
        # Global connections: set of websockets for notifications
        self.global_connections: Set[WebSocket] = set()
        
    async def connect_device(self, websocket: WebSocket, serial: str):
        """
        Connect to device WebSocket
        
        Args:
            websocket: WebSocket connection
            serial: Device serial
        """
        await websocket.accept()
        
        if serial not in self.device_connections:
            self.device_connections[serial] = set()
        self.device_connections[serial].add(websocket)
        
        logger.info(f"WebSocket connected to device {serial}")
        
    async def disconnect_device(self, websocket: WebSocket, serial: str):
        """
        Disconnect from device WebSocket
        
        Args:
            websocket: WebSocket connection
            serial: Device serial
        """
        if serial in self.device_connections:
            self.device_connections[serial].discard(websocket)
            if not self.device_connections[serial]:
                del self.device_connections[serial]
                
        logger.info(f"WebSocket disconnected from device {serial}")
        
    async def connect_task(self, websocket: WebSocket, task_id: str):
        """
        Connect to task WebSocket
        
        Args:
            websocket: WebSocket connection
            task_id: Task ID
        """
        await websocket.accept()
        
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(websocket)
        
        logger.info(f"WebSocket connected to task {task_id}")
        
    async def disconnect_task(self, websocket: WebSocket, task_id: str):
        """
        Disconnect from task WebSocket
        
        Args:
            websocket: WebSocket connection
            task_id: Task ID
        """
        if task_id in self.task_connections:
            self.task_connections[task_id].discard(websocket)
            if not self.task_connections[task_id]:
                del self.task_connections[task_id]
                
        logger.info(f"WebSocket disconnected from task {task_id}")
        
    async def connect_global(self, websocket: WebSocket):
        """
        Connect to global WebSocket
        
        Args:
            websocket: WebSocket connection
        """
        await websocket.accept()
        self.global_connections.add(websocket)
        logger.info("WebSocket connected to global channel")
        
    async def disconnect_global(self, websocket: WebSocket):
        """
        Disconnect from global WebSocket
        
        Args:
            websocket: WebSocket connection
        """
        self.global_connections.discard(websocket)
        logger.info("WebSocket disconnected from global channel")
        
    async def send_to_device(self, serial: str, message: Dict[str, Any]):
        """
        Send message to all connections for a device
        
        Args:
            serial: Device serial
            message: Message dictionary
        """
        if serial not in self.device_connections:
            return
            
        disconnected = set()
        for websocket in self.device_connections[serial]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
                
        # Remove disconnected websockets
        for ws in disconnected:
            self.device_connections[serial].discard(ws)
            
    async def send_to_task(self, task_id: str, message: Dict[str, Any]):
        """
        Send message to all connections for a task
        
        Args:
            task_id: Task ID
            message: Message dictionary
        """
        if task_id not in self.task_connections:
            return
            
        disconnected = set()
        for websocket in self.task_connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
                
        # Remove disconnected websockets
        for ws in disconnected:
            self.task_connections[task_id].discard(ws)
            
    async def broadcast_global(self, message: Dict[str, Any]):
        """
        Broadcast message to all global connections
        
        Args:
            message: Message dictionary
        """
        disconnected = set()
        for websocket in self.global_connections:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.add(websocket)
                
        # Remove disconnected websockets
        for ws in disconnected:
            self.global_connections.discard(ws)
            
    async def handle_device_message(self, websocket: WebSocket, serial: str, message: Dict[str, Any]):
        """
        Handle device WebSocket message
        
        Args:
            websocket: WebSocket connection
            serial: Device serial
            message: Received message
        """
        msg_type = message.get("type")
        params = message.get("params", {})
        
        try:
            if msg_type == "screenshot":
                # Take screenshot and send back
                image = await phone_controller.take_screenshot(
                    serial,
                    params.get("method", "screencap")
                )
                await websocket.send_json({
                    "type": "screenshot",
                    "data": {
                        "image": image,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
            elif msg_type == "start_stream":
                # Start screen streaming
                await self._start_screen_stream(websocket, serial)
                
            elif msg_type == "stop_stream":
                # Stop screen streaming
                await self._stop_screen_stream(websocket, serial)
                
            elif msg_type == "tap":
                # Handle tap
                x = params.get("x", 0)
                y = params.get("y", 0)
                
                # Get device info for coordinate mapping
                device = adb_manager.get_device(serial)
                if device:
                    screen_width = device.get("screen_width", 1080)
                    screen_height = device.get("screen_height", 1920)
                    
                    # Map relative coordinates to absolute
                    abs_x = int(x * screen_width)
                    abs_y = int(y * screen_height)
                    
                    success = await phone_controller.tap(serial, abs_x, abs_y)
                    
                    await websocket.send_json({
                        "type": "tap_response",
                        "data": {"success": success}
                    })
                    
            elif msg_type == "swipe":
                # Handle swipe
                x1 = params.get("x1", 0)
                y1 = params.get("y1", 0)
                x2 = params.get("x2", 0)
                y2 = params.get("y2", 0)
                duration = params.get("duration", 300)
                
                device = adb_manager.get_device(serial)
                if device:
                    screen_width = device.get("screen_width", 1080)
                    screen_height = device.get("screen_height", 1920)
                    
                    abs_x1 = int(x1 * screen_width)
                    abs_y1 = int(y1 * screen_height)
                    abs_x2 = int(x2 * screen_width)
                    abs_y2 = int(y2 * screen_height)
                    
                    success = await phone_controller.swipe(
                        serial, abs_x1, abs_y1, abs_x2, abs_y2, duration
                    )
                    
                    await websocket.send_json({
                        "type": "swipe_response",
                        "data": {"success": success}
                    })
                    
            elif msg_type == "input":
                # Handle text input
                text = params.get("text", "")
                is_chinese = params.get("is_chinese", False)
                
                if is_chinese:
                    success = await phone_controller.input_chinese_text(serial, text)
                else:
                    success = await phone_controller.input_text(serial, text)
                    
                await websocket.send_json({
                    "type": "input_response",
                    "data": {"success": success}
                })
                
            elif msg_type == "key":
                # Handle key event
                keycode = params.get("keycode", "")
                success = await phone_controller.key_event(serial, keycode)
                
                await websocket.send_json({
                    "type": "key_response",
                    "data": {"success": success}
                })
                
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": f"Unknown message type: {msg_type}"}
                })
                
        except Exception as e:
            logger.error(f"Error handling device message: {e}")
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
            
    async def _start_screen_stream(self, websocket: WebSocket, serial: str):
        """Start screen streaming"""
        # Implementation for screen streaming
        pass
        
    async def _stop_screen_stream(self, websocket: WebSocket, serial: str):
        """Stop screen streaming"""
        # Implementation for screen streaming
        pass


# Singleton instance
connection_manager = ConnectionManager()
