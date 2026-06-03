"""
Task Executor - Task scheduling, execution, and management
"""
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from loguru import logger

from app.services.adb_manager import adb_manager
from app.services.phone_controller import phone_controller


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskExecutor:
    """
    Task Executor for automation tasks
    
    Handles task scheduling, step execution, error handling,
    and progress reporting.
    """
    
    def __init__(self):
        """Initialize Task Executor"""
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_progress: Dict[str, Dict[str, Any]] = {}
        
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an automation task
        
        Args:
            task: Task dictionary with steps
            
        Returns:
            Task execution result
        """
        task_id = task["task_id"]
        device_serial = task.get("device_serial")
        steps = task.get("steps", [])
        
        logger.info(f"Executing task {task_id} on device {device_serial}")
        
        # Update task status
        task["status"] = TaskStatus.RUNNING.value
        task["started_at"] = datetime.now().isoformat()
        
        try:
            # Check device connection
            if device_serial:
                device = adb_manager.get_device(device_serial)
                if not device or device["status"] != "online":
                    raise Exception(f"Device {device_serial} not connected")
                    
            # Execute steps
            for i, step in enumerate(steps):
                # Check if task is cancelled
                if task.get("status") == TaskStatus.CANCELLED.value:
                    raise Exception("Task cancelled")
                    
                # Update progress
                task["current_step"] = i
                task["progress"] = int((i / len(steps)) * 100)
                
                # Execute step
                success = await self._execute_step(device_serial, step, task)
                
                if not success:
                    raise Exception(f"Step {i} failed: {step.get('name', 'Unknown')}")
                    
            # Task completed
            task["status"] = TaskStatus.COMPLETED.value
            task["progress"] = 100
            task["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"Task {task_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            task["status"] = TaskStatus.FAILED.value
            task["error_message"] = str(e)
            task["completed_at"] = datetime.now().isoformat()
            
        return task
        
    async def _execute_step(
        self,
        device_serial: str,
        step: Dict[str, Any],
        task: Dict[str, Any]
    ) -> bool:
        """
        Execute a single step
        
        Args:
            device_serial: Device serial
            step: Step dictionary
            task: Parent task
            
        Returns:
            True if successful
        """
        step_type = step.get("type")
        params = step.get("params", {})
        step_name = step.get("name", "Unknown")
        
        logger.debug(f"Executing step: {step_name} ({step_type})")
        
        try:
            if step_type == "tap":
                return await phone_controller.tap(
                    device_serial,
                    params["x"],
                    params["y"],
                    params.get("duration", 100)
                )
                
            elif step_type == "swipe":
                return await phone_controller.swipe(
                    device_serial,
                    params["x1"],
                    params["y1"],
                    params["x2"],
                    params["y2"],
                    params.get("duration", 300)
                )
                
            elif step_type == "text":
                if params.get("is_chinese", False):
                    return await phone_controller.input_chinese_text(
                        device_serial,
                        params["text"]
                    )
                else:
                    return await phone_controller.input_text(
                        device_serial,
                        params["text"],
                        params.get("clear_first", False)
                    )
                    
            elif step_type == "key":
                return await phone_controller.key_event(
                    device_serial,
                    params["keycode"],
                    params.get("count", 1)
                )
                
            elif step_type == "wait":
                await asyncio.sleep(params.get("seconds", 1))
                return True
                
            elif step_type == "screenshot":
                image = await phone_controller.take_screenshot(
                    device_serial,
                    params.get("method", "screencap")
                )
                if image:
                    # Store screenshot in task result
                    if "screenshots" not in task:
                        task["screenshots"] = []
                    task["screenshots"].append({
                        "step": step_name,
                        "image": image
                    })
                return image is not None
                
            elif step_type == "check":
                return await self._execute_check(device_serial, params)
                
            elif step_type == "launch":
                return await phone_controller.start_app(
                    device_serial,
                    params["package_name"]
                )
                
            elif step_type == "back":
                return await phone_controller.press_back(device_serial)
                
            elif step_type == "home":
                return await phone_controller.press_home(device_serial)
                
            else:
                logger.warning(f"Unknown step type: {step_type}")
                return False
                
        except Exception as e:
            logger.error(f"Step execution failed: {e}")
            return False
            
    async def _execute_check(self, device_serial: str, params: Dict[str, Any]) -> bool:
        """
        Execute check step
        
        Args:
            device_serial: Device serial
            params: Check parameters
            
        Returns:
            True if check passed
        """
        check_type = params.get("type")
        timeout = params.get("timeout", 5)
        
        if check_type == "app_running":
            package_name = params.get("package_name")
            start_time = datetime.now()
            
            while (datetime.now() - start_time).seconds < timeout:
                if await phone_controller.is_app_running(device_serial, package_name):
                    return True
                await asyncio.sleep(0.5)
                
            return False
            
        elif check_type == "element_exists":
            # For element detection, we need screenshot + OCR
            # This is a simplified version
            return True
            
        return True
        
    async def pause_task(self, task_id: str) -> bool:
        """
        Pause a running task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if paused successfully
        """
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            return True
        return False
        
    async def resume_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resume a paused task
        
        Args:
            task: Task dictionary
            
        Returns:
            Updated task
        """
        return await self.execute_task(task)
        
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if cancelled successfully
        """
        if task_id in self.running_tasks:
            self.running_tasks[task_id].cancel()
            return True
        return False
        
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status dictionary
        """
        return self.task_progress.get(task_id)


# Singleton instance
task_executor = TaskExecutor()
