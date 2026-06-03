"""
Task routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from app.core.database import get_db
from app.models.task import Task, TaskLog

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ========== Request/Response Models ==========

class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStep(BaseModel):
    name: str
    type: str  # tap/swipe/input/wait/screenshot/check
    params: dict
    timeout: int = 30
    retry_count: int = 0


class TaskCreate(BaseModel):
    name: str
    description: Optional[str] = None
    task_type: str = "automation"
    steps: List[TaskStep]
    params: dict = {}
    config: dict = {}
    device_serial: Optional[str] = None
    priority: int = 0
    max_retries: int = 3
    scheduled_at: Optional[datetime] = None
    timeout_seconds: int = 3600


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[TaskStep]] = None
    params: Optional[dict] = None
    config: Optional[dict] = None
    priority: Optional[int] = None
    max_retries: Optional[int] = None


class TaskResponse(BaseModel):
    id: int
    task_id: str
    name: str
    description: Optional[str]
    task_type: str
    status: TaskStatus
    priority: int
    progress: int
    steps: List[dict]
    params: dict
    config: dict
    device_serial: Optional[str]
    current_step: int
    retry_count: int
    max_retries: int
    result: Optional[dict]
    error_message: Optional[str]
    scheduled_at: Optional[datetime]
    timeout_seconds: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskActionResponse(BaseModel):
    success: bool
    message: str
    task: TaskResponse


class TaskStatistics(BaseModel):
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    success_rate: float
    avg_duration_seconds: Optional[float]


# ========== API Endpoints ==========

@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[TaskStatus] = None,
    task_type: Optional[str] = None,
    device_serial: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|priority|status)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get task list
    
    Supports pagination, filtering, and sorting
    """
    from sqlalchemy import select, func
    
    # Build query
    query = select(Task)
    count_query = select(func.count(Task.id))
    
    # Apply filters
    if status:
        query = query.where(Task.status == status.value)
        count_query = count_query.where(Task.status == status.value)
    
    if task_type:
        query = query.where(Task.task_type == task_type)
        count_query = count_query.where(Task.task_type == task_type)
    
    if device_serial:
        query = query.where(Task.device_serial == device_serial)
        count_query = count_query.where(Task.device_serial == device_serial)
    
    if search:
        search_filter = Task.name.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply sorting
    sort_column = getattr(Task, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(
        items=[TaskResponse.from_orm(t) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    db: AsyncSession = Depends(get_db),
):
    """Get task statistics"""
    from sqlalchemy import select, func
    
    # Get counts by status
    total = await db.execute(select(func.count(Task.id)))
    pending = await db.execute(select(func.count(Task.id)).where(Task.status == "pending"))
    running = await db.execute(select(func.count(Task.id)).where(Task.status == "running"))
    completed = await db.execute(select(func.count(Task.id)).where(Task.status == "completed"))
    failed = await db.execute(select(func.count(Task.id)).where(Task.status == "failed"))
    
    total_count = total.scalar()
    completed_count = completed.scalar()
    failed_count = failed.scalar()
    
    # Calculate success rate
    success_rate = (completed_count / total_count * 100) if total_count > 0 else 0
    
    # Calculate average duration
    avg_duration = await db.execute(
        select(func.avg(func.extract("epoch", Task.completed_at - Task.started_at)))
        .where(Task.status == "completed")
    )
    avg_duration_seconds = avg_duration.scalar()
    
    return TaskStatistics(
        total=total_count,
        pending=pending.scalar(),
        running=running.scalar(),
        completed=completed_count,
        failed=failed_count,
        success_rate=round(success_rate, 2),
        avg_duration_seconds=round(avg_duration_seconds, 2) if avg_duration_seconds else None,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get task details"""
    from sqlalchemy import select
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    return TaskResponse.from_orm(task)


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create task
    
    If device_serial is specified and device is online, task will be queued for execution
    """
    import uuid
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Create new task
    new_task = Task(
        task_id=task_id,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        steps=[step.model_dump() for step in task.steps],
        params=task.params,
        config=task.config,
        device_serial=task.device_serial,
        priority=task.priority,
        max_retries=task.max_retries,
        scheduled_at=task.scheduled_at,
        timeout_seconds=task.timeout_seconds,
    )
    
    db.add(new_task)
    await db.flush()
    await db.refresh(new_task)
    
    return TaskResponse.from_orm(new_task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task: TaskUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update task (only pending status can be updated)"""
    from sqlalchemy import select
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    existing_task = result.scalar_one_or_none()
    
    if not existing_task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if existing_task.status != "pending":
        raise HTTPException(status_code=400, detail="Can only update pending tasks")
    
    # Update fields
    update_data = task.model_dump(exclude_unset=True)
    if "steps" in update_data:
        update_data["steps"] = [step.model_dump() for step in update_data["steps"]]
    
    for key, value in update_data.items():
        setattr(existing_task, key, value)
    
    await db.flush()
    await db.refresh(existing_task)
    
    return TaskResponse.from_orm(existing_task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete task (only pending/completed/failed status can be deleted)"""
    from sqlalchemy import select
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task.status not in ["pending", "completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot delete running/paused tasks")
    
    await db.delete(task)


@router.post("/{task_id}/start", response_model=TaskActionResponse)
async def start_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Start task
    
    Add task to execution queue
    """
    from sqlalchemy import select
    from datetime import datetime
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task.status not in ["pending", "queued", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot start task in {task.status} status")
    
    # Update task status
    task.status = "running"
    task.started_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(task)
    
    # TODO: Add task to Celery queue
    
    return TaskActionResponse(
        success=True,
        message="Task started successfully",
        task=TaskResponse.from_orm(task),
    )


@router.post("/{task_id}/pause", response_model=TaskActionResponse)
async def pause_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Pause task"""
    from sqlalchemy import select
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task.status != "running":
        raise HTTPException(status_code=400, detail="Can only pause running tasks")
    
    task.status = "paused"
    
    await db.flush()
    await db.refresh(task)
    
    return TaskActionResponse(
        success=True,
        message="Task paused successfully",
        task=TaskResponse.from_orm(task),
    )


@router.post("/{task_id}/resume", response_model=TaskActionResponse)
async def resume_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Resume task"""
    from sqlalchemy import select
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task.status != "paused":
        raise HTTPException(status_code=400, detail="Can only resume paused tasks")
    
    task.status = "running"
    
    await db.flush()
    await db.refresh(task)
    
    return TaskActionResponse(
        success=True,
        message="Task resumed successfully",
        task=TaskResponse.from_orm(task),
    )


@router.post("/{task_id}/cancel", response_model=TaskActionResponse)
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel task"""
    from sqlalchemy import select
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task.status in ["completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/cancelled tasks")
    
    task.status = "cancelled"
    
    await db.flush()
    await db.refresh(task)
    
    return TaskActionResponse(
        success=True,
        message="Task cancelled successfully",
        task=TaskResponse.from_orm(task),
    )


@router.post("/{task_id}/retry", response_model=TaskActionResponse)
async def retry_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retry failed task"""
    from sqlalchemy import select
    from datetime import datetime
    
    query = select(Task).where(Task.task_id == task_id)
    result = await db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    if task.status != "failed":
        raise HTTPException(status_code=400, detail="Can only retry failed tasks")
    
    if task.retry_count >= task.max_retries:
        raise HTTPException(status_code=400, detail="Max retries exceeded")
    
    # Reset task for retry
    task.status = "running"
    task.retry_count += 1
    task.current_step = 0
    task.progress = 0
    task.started_at = datetime.utcnow()
    task.error_message = None
    
    await db.flush()
    await db.refresh(task)
    
    return TaskActionResponse(
        success=True,
        message=f"Task retry {task.retry_count}/{task.max_retries}",
        task=TaskResponse.from_orm(task),
    )


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: str,
    level: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get task execution logs
    
    - **level**: Log level filter
    - **limit**: Max items to return
    - **offset**: Pagination offset
    """
    from sqlalchemy import select, func
    
    # Check if task exists
    task_query = select(Task).where(Task.task_id == task_id)
    task_result = await db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    # Build query
    query = select(TaskLog).where(TaskLog.task_id == task_id)
    count_query = select(func.count(TaskLog.id)).where(TaskLog.task_id == task_id)
    
    if level:
        query = query.where(TaskLog.level == level)
        count_query = count_query.where(TaskLog.level == level)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply ordering and pagination
    query = query.order_by(TaskLog.created_at.desc())
    query = query.offset(offset).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": log.id,
                "level": log.level,
                "step_index": log.step_index,
                "step_name": log.step_name,
                "message": log.message,
                "details": log.details,
                "screenshot_path": log.screenshot_path,
                "duration_ms": log.duration_ms,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
