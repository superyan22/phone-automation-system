"""
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import init_db, close_db
from app.services.adb_manager import adb_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles startup and shutdown events
    """
    # Startup
    print("Starting up...")
    await init_db()
    print("Database initialized")
    
    # Start ADB Manager
    await adb_manager.start()
    print("ADB Manager started")
    
    yield
    
    # Shutdown
    print("Shutting down...")
    await adb_manager.stop()
    print("ADB Manager stopped")
    await close_db()
    print("Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Web-based phone automation control system",
    lifespan=lifespan,
)

# CORS middleware - restrict origins for security
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:80",
    "http://127.0.0.1:3000",
    "https://yan3321.github.io",  # GitHub Pages frontend (set via GITHUB_PAGES_URL env var in production)
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health():
    """
    Health check endpoint with dependency checks.
    Returns status of database and Redis connectivity.
    """
    from sqlalchemy import text
    from app.core.database import engine
    
    health_status = {"status": "healthy", "checks": {}}
    
    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["database"] = f"unhealthy: {str(e)[:100]}"
    
    # Check Redis
    try:
        import redis.asyncio as aioredis
        # Try to connect with the configured URL
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.close()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["redis"] = f"unhealthy: {str(e)[:100]}"
    
    return health_status


# Import and include routers
from app.api.routes import devices, tasks, websocket, phone

app.include_router(devices.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(websocket.router)
app.include_router(phone.router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
