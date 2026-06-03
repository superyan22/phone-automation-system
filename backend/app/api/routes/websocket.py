"""
WebSocket routes
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import json

from app.services.websocket_manager import connection_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/device/{serial}")
async def device_websocket(websocket: WebSocket, serial: str):
    """
    Device WebSocket endpoint
    
    Handles real-time device control:
    - Screen capture
    - Touch events (tap, swipe)
    - Text input
    - Key events
    """
    await connection_manager.connect_device(websocket, serial)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle message
            await connection_manager.handle_device_message(websocket, serial, message)
            
    except WebSocketDisconnect:
        await connection_manager.disconnect_device(websocket, serial)
    except Exception as e:
        await connection_manager.disconnect_device(websocket, serial)
        raise


@router.websocket("/ws/task/{task_id}")
async def task_websocket(websocket: WebSocket, task_id: str):
    """
    Task WebSocket endpoint
    
    Handles real-time task monitoring:
    - Progress updates
    - Step completion
    - Error notifications
    """
    await connection_manager.connect_task(websocket, task_id)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        await connection_manager.disconnect_task(websocket, task_id)
    except Exception as e:
        await connection_manager.disconnect_task(websocket, task_id)
        raise


@router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket):
    """
    Global notifications WebSocket endpoint
    
    Receives:
    - Device connected/disconnected
    - Task created/completed/failed
    - System notifications
    """
    await connection_manager.connect_global(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        await connection_manager.disconnect_global(websocket)
    except Exception as e:
        await connection_manager.disconnect_global(websocket)
        raise
