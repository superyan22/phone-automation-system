"""
Task model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional, Dict, Any, List

from app.core.database import Base


class Task(Base):
    """Task model"""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Task info
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # automation/batch/test/template
    
    # Status
    status = Column(String(20), default="pending")  # pending/queued/running/paused/completed/failed/cancelled
    priority = Column(Integer, default=0)  # 0=normal, 1=high, 2=urgent
    progress = Column(Integer, default=0)  # 0-100
    
    # Configuration
    steps = Column(JSON, nullable=False, default=list)
    params = Column(JSON, default=dict)
    config = Column(JSON, default=dict)
    
    # Execution info
    device_serial = Column(String(100), ForeignKey("devices.serial", ondelete="SET NULL"), nullable=True)
    current_step = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Result
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Scheduling
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    timeout_seconds = Column(Integer, default=3600)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Task(task_id='{self.task_id}', name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "task_type": self.task_type,
            "status": self.status,
            "priority": self.priority,
            "progress": self.progress,
            "steps": self.steps,
            "params": self.params,
            "config": self.config,
            "device_serial": self.device_serial,
            "current_step": self.current_step,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result,
            "error_message": self.error_message,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "timeout_seconds": self.timeout_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class TaskLog(Base):
    """Task log model"""
    
    __tablename__ = "task_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(50), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Log info
    level = Column(String(20), default="info")  # debug/info/warning/error/critical
    step_index = Column(Integer, nullable=True)
    step_name = Column(String(100), nullable=True)
    
    # Content
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    
    # Screenshot
    screenshot_path = Column(String(500), nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    
    # Performance
    duration_ms = Column(Integer, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    task = relationship("Task", back_populates="logs")
    
    def __repr__(self):
        return f"<TaskLog(task_id='{self.task_id}', level='{self.level}')>"
