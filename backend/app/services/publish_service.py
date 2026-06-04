"""
一键发布小红书服务
自动完成：数据抓取 → 图片生成 → ADB推送 → 小红书发布
"""
import asyncio
import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

import httpx
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, get_db


class PublishStatus(str, Enum):
    PENDING = "pending"
    DATA_FETCHING = "data_fetching"
    IMAGE_GENERATING = "image_generating"
    PUSHING_TO_PHONE = "pushing_to_phone"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"


class PublishTask(Base):
    """发布任务模型"""
    __tablename__ = "publish_tasks"
    
    id = Column(String(50), primary_key=True)
    status = Column(String(20), default=PublishStatus.PENDING)
    progress = Column(Integer, default=0)
    current_step = Column(String(50))
    data_source = Column(String(100), default="latest")
    title = Column(String(200))
    content = Column(Text)
    images = Column(JSON, default=list)
    screenshot = Column(String(500))
    phone_serial = Column(String(100))
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)


class PublishService:
    """一键发布服务"""
    
    def __init__(self):
        self.base_dir = Path("/home/yan/phone-automation-system")
        self.data_dir = self.base_dir / "data"
        self.templates_dir = self.base_dir / "templates" / "xhs"
        self.images_dir = self.base_dir / "generated_images"
        self.screenshots_dir = self.base_dir / "screenshots"
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def publish_one_click(
        self,
        db: AsyncSession,
        data_source: str = "latest",
        phone_serial: str = "192.168.31.177:37107"
    ) -> str:
        """
        一键发布流程
        返回任务ID
        """
        # 创建任务
        task_id = f"PUB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        task = PublishTask(
            id=task_id,
            status=PublishStatus.PENDING,
            data_source=data_source,
            phone_serial=phone_serial
        )
        db.add(task)
        await db.commit()
        
        # 启动后台任务
        asyncio.create_task(self._execute_publish(task_id, db))
        
        return task_id
    
    async def _execute_publish(self, task_id: str, db: AsyncSession):
        """执行发布流程"""
        try:
            # Step 1: 数据抓取
            await self._update_progress(db, task_id, PublishStatus.DATA_FETCHING, 0, "正在抓取数据...")
            data = await self._fetch_data(task_id)
            await self._update_progress(db, task_id, PublishStatus.DATA_FETCHING, 100, "数据抓取完成")
            
            # Step 2: 图片生成
            await self._update_progress(db, task_id, PublishStatus.IMAGE_GENERATING, 0, "正在生成图片...")
            images = await self._generate_images(task_id, data)
            await self._update_progress(db, task_id, PublishStatus.IMAGE_GENERATING, 100, "图片生成完成")
            
            # Step 3: ADB推送
            await self._update_progress(db, task_id, PublishStatus.PUSHING_TO_PHONE, 0, "正在推送到手机...")
            await self._push_to_phone(task_id, images)
            await self._update_progress(db, task_id, PublishStatus.PUSHING_TO_PHONE, 100, "推送完成")
            
            # Step 4: 小红书发布
            await self._update_progress(db, task_id, PublishStatus.PUBLISHING, 0, "正在发布到小红书...")
            screenshot = await self._publish_to_xhs(task_id, data)
            await self._update_progress(db, task_id, PublishStatus.PUBLISHING, 100, "发布完成")
            
            # 完成
            await self._complete_task(db, task_id, screenshot)
            
        except Exception as e:
            await self._fail_task(db, task_id, str(e))
    
    async def _fetch_data(self, task_id: str) -> Dict[str, Any]:
        """抓取招聘数据"""
        # 读取最新的招聘数据
        data_file = self.data_dir / "recruitment_latest.json"
        
        if not data_file.exists():
            # 如果没有最新数据，使用示例数据
            return {
                "title": "太原事业单位招聘30人",
                "source": "太原市人社局",
                "date": datetime.now().strftime("%Y.%m.%d"),
                "positions": [
                    {"name": "综合岗", "count": 5, "requirements": "本科及以上"},
                    {"name": "技术岗", "count": 10, "requirements": "计算机相关专业"},
                    {"name": "管理岗", "count": 15, "requirements": "本科及以上"}
                ],
                "deadline": "2026-06-15",
                "url": "https://rsj.taiyuan.gov.cn"
            }
        
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    async def _generate_images(self, task_id: str, data: Dict[str, Any]) -> List[str]:
        """生成小红书图片"""
        images = []
        
        # 生成封面图
        cover_path = await self._render_template(task_id, "xhs_hook_1.html", data, "cover")
        images.append(cover_path)
        
        # 生成内容图
        content_path = await self._render_template(task_id, "xhs_hook_2.html", data, "content")
        images.append(content_path)
        
        # 生成岗位表图
        job_list_path = await self._render_template(task_id, "xhs_job_list_detail.html", data, "job_list")
        images.append(job_list_path)
        
        return images
    
    async def _render_template(self, task_id: str, template_name: str, data: Dict[str, Any], output_name: str) -> str:
        """使用Pillow生成图片"""
        output_path = self.images_dir / f"{task_id}_{output_name}.png"
        
        # 使用Pillow生成简单图片
        from PIL import Image, ImageDraw, ImageFont
        
        # 创建图片
        img = Image.new('RGB', (1080, 1440), color=(102, 126, 234))
        draw = ImageDraw.Draw(img)
        
        # 绘制文字
        try:
            font_large = ImageFont.truetype("/home/yan/.local/share/fonts/simhei.ttf", 72)
            font_medium = ImageFont.truetype("/home/yan/.local/share/fonts/simhei.ttf", 48)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
        
        # 绘制标题
        title = data.get("title", "招聘信息")
        draw.text((540, 600), title, fill="white", font=font_large, anchor="mm")
        
        # 绘制日期
        date = data.get("date", "")
        draw.text((540, 750), date, fill="white", font=font_medium, anchor="mm")
        
        # 保存图片
        img.save(str(output_path))
        
        return str(output_path)
    
    async def _push_to_phone(self, task_id: str, images: List[str]):
        """推送图片到手机"""
        serial = "192.168.31.177:37107"
        
        # 清理旧图片
        cleanup_cmd = f"adb -s {serial} shell rm -rf /sdcard/DCIM/Camera/xhs_*.png"
        subprocess.run(cleanup_cmd, shell=True, capture_output=True)
        
        # 推送新图片
        for i, image_path in enumerate(images):
            filename = f"xhs_post_{i+1}.png"
            remote_path = f"/sdcard/DCIM/Camera/{filename}"
            
            push_cmd = f"adb -s {serial} push {image_path} {remote_path}"
            subprocess.run(push_cmd, shell=True, capture_output=True)
            
            # 触发媒体扫描
            scan_cmd = f"adb -s {serial} shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://{remote_path}"
            subprocess.run(scan_cmd, shell=True, capture_output=True)
        
        # 等待媒体扫描完成
        await asyncio.sleep(2)
    
    async def _publish_to_xhs(self, task_id: str, data: Dict[str, Any]) -> str:
        """发布到小红书"""
        import uiautomator2 as u2
        
        serial = "192.168.31.177:37107"
        d = u2.connect(serial)
        
        # 打开小红书
        d.app_start("com.xingin.xhs")
        await asyncio.sleep(3)
        
        # 点击发布按钮（通过content-desc定位）
        d(description="发布").click()
        await asyncio.sleep(2)
        
        # 选择"发布笔记"
        d(text="发布笔记").click()
        await asyncio.sleep(2)
        
        # 从相册选择图片
        d(text="从相册选择").click()
        await asyncio.sleep(2)
        
        # 选择图片（选择最新的3张）
        # 这里需要根据实际情况调整选择逻辑
        await asyncio.sleep(1)
        
        # 点击下一步
        d(text="下一步").click()
        await asyncio.sleep(2)
        
        # 填写标题
        title_edit = d(className="android.widget.EditText")
        title_edit.set_text(data.get("title", ""))
        await asyncio.sleep(1)
        
        # 填写正文
        # 正文在第二个EditText
        edits = d(className="android.widget.EditText")
        if len(edits) > 1:
            edits[1].set_text(data.get("content", ""))
        await asyncio.sleep(1)
        
        # 点击发布
        d(text="发布笔记").click()
        await asyncio.sleep(5)
        
        # 截图保存结果
        screenshot_path = self.screenshots_dir / f"{task_id}_result.png"
        d.screenshot(str(screenshot_path))
        
        return str(screenshot_path)
    
    async def _update_progress(
        self,
        db: AsyncSession,
        task_id: str,
        status: PublishStatus,
        progress: int,
        message: str
    ):
        """更新任务进度"""
        from sqlalchemy import update
        
        await db.execute(
            update(PublishTask)
            .where(PublishTask.id == task_id)
            .values(
                status=status,
                progress=progress,
                current_step=message,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
    
    async def _complete_task(self, db: AsyncSession, task_id: str, screenshot: str):
        """完成任务"""
        from sqlalchemy import update
        
        await db.execute(
            update(PublishTask)
            .where(PublishTask.id == task_id)
            .values(
                status=PublishStatus.COMPLETED,
                progress=100,
                screenshot=screenshot,
                completed_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()
    
    async def _fail_task(self, db: AsyncSession, task_id: str, error: str):
        """任务失败"""
        from sqlalchemy import update
        
        await db.execute(
            update(PublishTask)
            .where(PublishTask.id == task_id)
            .values(
                status=PublishStatus.FAILED,
                error=error,
                updated_at=datetime.utcnow()
            )
        )
        await db.commit()


# 单例
publish_service = PublishService()
