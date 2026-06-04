"""
Device routes
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.device import Device

router = APIRouter(prefix="/devices", tags=["devices"])


# ========== Request/Response Models ==========

class DeviceBase(BaseModel):
    serial: str
    device_type: str
    ip_address: Optional[str] = None
    port: int = 5555
    config: dict = {}


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    ip_address: Optional[str] = None
    port: Optional[int] = None
    config: Optional[dict] = None


class DeviceResponse(DeviceBase):
    id: int
    model: Optional[str] = None
    brand: Optional[str] = None
    android_version: Optional[str] = None
    screen_width: Optional[int] = None
    screen_height: Optional[int] = None
    status: str
    is_connected: bool
    last_heartbeat: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    items: List[DeviceResponse]
    total: int
    page: int
    page_size: int


class DeviceCommandRequest(BaseModel):
    command: str
    args: List[str] = []
    timeout: int = 30


class DeviceCommandResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


# ========== API Endpoints ==========

@router.get("/", response_model=DeviceListResponse)
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    device_type: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Get device list
    
    - **page**: Page number
    - **page_size**: Items per page
    - **status**: Filter by status (online/offline/busy)
    - **device_type**: Filter by type (usb/wifi)
    - **search**: Search keyword (serial/model)
    """
    from sqlalchemy import select, func
    
    # Build query
    query = select(Device)
    count_query = select(func.count(Device.id))
    
    # Apply filters
    if status:
        query = query.where(Device.status == status)
        count_query = count_query.where(Device.status == status)
    
    if device_type:
        query = query.where(Device.device_type == device_type)
        count_query = count_query.where(Device.device_type == device_type)
    
    if search:
        search_filter = Device.serial.ilike(f"%{search}%") | Device.model.ilike(f"%{search}%")
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    # Execute query
    result = await db.execute(query)
    devices = result.scalars().all()
    
    return DeviceListResponse(
        items=[DeviceResponse.from_orm(d) for d in devices],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{serial}", response_model=DeviceResponse)
async def get_device(
    serial: str,
    db: AsyncSession = Depends(get_db),
):
    """Get device details"""
    from sqlalchemy import select
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    return DeviceResponse.from_orm(device)


@router.post("/", response_model=DeviceResponse, status_code=201)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register new device
    
    Automatically detects device info and registers
    """
    from sqlalchemy import select
    
    # Check if device already exists
    existing = await db.execute(
        select(Device).where(Device.serial == device.serial)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Device already exists: {device.serial}")
    
    # Create new device
    new_device = Device(**device.model_dump())
    db.add(new_device)
    await db.flush()
    await db.refresh(new_device)
    
    return DeviceResponse.from_orm(new_device)


@router.put("/{serial}", response_model=DeviceResponse)
async def update_device(
    serial: str,
    device: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update device configuration"""
    from sqlalchemy import select
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    existing_device = result.scalar_one_or_none()
    
    if not existing_device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    # Update fields
    update_data = device.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(existing_device, key, value)
    
    await db.flush()
    await db.refresh(existing_device)
    
    return DeviceResponse.from_orm(existing_device)


@router.delete("/{serial}", status_code=204)
async def delete_device(
    serial: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete device"""
    from sqlalchemy import select
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    await db.delete(device)


@router.post("/{serial}/connect", response_model=DeviceResponse)
async def connect_device(
    serial: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Connect device
    
    Establishes ADB connection and starts heartbeat monitoring
    """
    from sqlalchemy import select
    from datetime import datetime
    from app.services.adb_manager import adb_manager, DeviceInfo, DeviceStatus
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    # Register device with ADB manager
    device_info = DeviceInfo(
        serial=serial,
        device_type=device.device_type,
        ip_address=device.ip_address,
        port=device.port,
        status=DeviceStatus.ONLINE
    )
    adb_manager.devices[serial] = device_info
    
    # Update database
    device.status = "online"
    device.is_connected = True
    device.connected_at = datetime.utcnow()
    
    await db.flush()
    await db.refresh(device)
    
    return DeviceResponse.from_orm(device)


@router.post("/{serial}/disconnect", response_model=DeviceResponse)
async def disconnect_device(
    serial: str,
    db: AsyncSession = Depends(get_db),
):
    """Disconnect device"""
    from sqlalchemy import select
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    # TODO: Implement actual ADB disconnect logic
    device.status = "offline"
    device.is_connected = False
    
    await db.flush()
    await db.refresh(device)
    
    return DeviceResponse.from_orm(device)


@router.post("/{serial}/command", response_model=DeviceCommandResponse)
async def execute_command(
    serial: str,
    request: DeviceCommandRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute ADB command
    
    - **command**: ADB command
    - **args**: Command arguments
    - **timeout**: Timeout in seconds
    """
    from sqlalchemy import select
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    # TODO: Implement actual ADB command execution
    return DeviceCommandResponse(
        success=True,
        output=f"Command executed: {request.command} {' '.join(request.args)}",
        error=None,
    )


@router.post("/scan", response_model=List[DeviceResponse])
async def scan_devices(
    scan_type: str = Query("usb", regex="^(usb|wifi|all)$"),
    subnet: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Scan devices
    
    - **scan_type**: Scan type (usb/wifi/all)
    - **subnet**: WiFi scan subnet (wifi type only)
    """
    # TODO: Implement actual device scanning
    return []


@router.get("/{serial}/screenshot")
async def get_screenshot(
    serial: str,
    format: str = "png",
    db: AsyncSession = Depends(get_db),
):
    """
    Get device screenshot
    
    - **format**: Image format (png/jpeg)
    
    Returns base64 encoded image
    """
    from sqlalchemy import select
    from app.services.phone_controller import phone_controller
    
    query = select(Device).where(Device.serial == serial)
    result = await db.execute(query)
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=404, detail=f"Device not found: {serial}")
    
    # Take screenshot using phone controller
    try:
        image_base64 = await phone_controller.take_screenshot(serial)
        if image_base64:
            return {"image": image_base64, "format": format}
        else:
            raise HTTPException(status_code=500, detail="Failed to capture screenshot")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot error: {str(e)}")
