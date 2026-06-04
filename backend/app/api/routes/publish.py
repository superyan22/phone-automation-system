"""
一键发布API路由
"""
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
import json

from app.core.database import get_db
from app.services.publish_service import publish_service, PublishTask, PublishStatus

router = APIRouter(prefix="/api/v1/publish", tags=["publish"])


class PublishRequest(BaseModel):
    """发布请求"""
    data_source: str = "latest"
    phone_serial: str = "192.168.31.177:37107"


class PublishResponse(BaseModel):
    """发布响应"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    id: str
    status: str
    progress: int
    current_step: Optional[str]
    title: Optional[str]
    images: list
    screenshot: Optional[str]
    error: Optional[str]
    created_at: str
    updated_at: str


@router.post("/start", response_model=PublishResponse)
async def start_publish(
    request: PublishRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    一键发布到小红书
    
    自动完成：数据抓取 → 图片生成 → ADB推送 → 小红书发布
    """
    # 检查是否有正在运行的任务
    from sqlalchemy import select
    result = await db.execute(
        select(PublishTask).where(
            PublishTask.status.in_([
                PublishStatus.PENDING,
                PublishStatus.DATA_FETCHING,
                PublishStatus.IMAGE_GENERATING,
                PublishStatus.PUSHING_TO_PHONE,
                PublishStatus.PUBLISHING
            ])
        )
    )
    running_task = result.scalar_one_or_none()
    
    if running_task:
        raise HTTPException(
            status_code=409,
            detail=f"有正在运行的任务: {running_task.id}"
        )
    
    # 创建新任务
    task_id = await publish_service.publish_one_click(
        db=db,
        data_source=request.data_source,
        phone_serial=request.phone_serial
    )
    
    return PublishResponse(
        task_id=task_id,
        status="started",
        message="发布任务已启动"
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db)
):
    """获取任务状态"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(PublishTask).where(PublishTask.id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return TaskStatusResponse(
        id=task.id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        title=task.title,
        images=task.images or [],
        screenshot=task.screenshot,
        error=task.error,
        created_at=task.created_at.isoformat() if task.created_at else "",
        updated_at=task.updated_at.isoformat() if task.updated_at else ""
    )


@router.get("/list")
async def list_tasks(
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """获取任务列表"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(PublishTask)
        .order_by(PublishTask.created_at.desc())
        .limit(limit)
    )
    tasks = result.scalars().all()
    
    return {
        "items": [
            {
                "id": task.id,
                "status": task.status,
                "progress": task.progress,
                "title": task.title,
                "created_at": task.created_at.isoformat() if task.created_at else ""
            }
            for task in tasks
        ]
    }


@router.websocket("/ws/{task_id}")
async def websocket_task_progress(
    websocket: WebSocket,
    task_id: str
):
    """
    WebSocket实时推送任务进度
    
    客户端连接后，会实时收到进度更新
    """
    await websocket.accept()
    
    from sqlalchemy import select
    from app.core.database import async_session
    
    last_progress = -1
    
    try:
        while True:
            async with async_session() as db:
                result = await db.execute(
                    select(PublishTask).where(PublishTask.id == task_id)
                )
                task = result.scalar_one_or_none()
                
                if not task:
                    await websocket.send_json({"error": "任务不存在"})
                    break
                
                # 发送进度更新
                if task.progress != last_progress:
                    await websocket.send_json({
                        "type": "progress",
                        "task_id": task.id,
                        "status": task.status,
                        "progress": task.progress,
                        "current_step": task.current_step,
                        "screenshot": task.screenshot
                    })
                    last_progress = task.progress
                
                # 任务完成或失败
                if task.status in [PublishStatus.COMPLETED, PublishStatus.FAILED]:
                    await websocket.send_json({
                        "type": "complete",
                        "task_id": task.id,
                        "status": task.status,
                        "screenshot": task.screenshot,
                        "error": task.error
                    })
                    break
            
            # 每秒检查一次
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
    finally:
        await websocket.close()


import asyncio
