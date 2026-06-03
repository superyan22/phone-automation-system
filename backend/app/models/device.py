"""
Device model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON
from sqlalchemy.sql import func
from typing import Optional, Dict, Any

from app.core.database import Base


class Device(Base):
    """Device model"""
    
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    serial = Column(String(100), unique=True, nullable=False, index=True)
    device_type = Column(String(20), nullable=False)  # usb/wifi
    ip_address = Column(String(50), nullable=True)
    port = Column(Integer, default=5555)
    
    # Device info
    model = Column(String(100), nullable=True)
    brand = Column(String(50), nullable=True)
    android_version = Column(String(20), nullable=True)
    screen_width = Column(Integer, nullable=True)
    screen_height = Column(Integer, nullable=True)
    screen_density = Column(Float, default=1.0)
    
    # Status
    status = Column(String(20), default="offline")  # online/offline/busy/error
    is_connected = Column(Boolean, default=False)
    last_heartbeat = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    config = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    connected_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Device(serial='{self.serial}', model='{self.model}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "serial": self.serial,
            "device_type": self.device_type,
            "ip_address": self.ip_address,
            "port": self.port,
            "model": self.model,
            "brand": self.brand,
            "android_version": self.android_version,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "screen_density": self.screen_density,
            "status": self.status,
            "is_connected": self.is_connected,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
        }
