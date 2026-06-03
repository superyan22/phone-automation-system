#!/usr/bin/env python3
"""
Test script to verify backend code structure and imports.
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test if all modules can be imported."""
    try:
        from app.core.config import Settings
        print("✅ Config module imported successfully")
    except Exception as e:
        print(f"❌ Config module import failed: {e}")
        return False
    
    try:
        from app.models.device import Device
        print("✅ Device model imported successfully")
    except Exception as e:
        print(f"❌ Device model import failed: {e}")
        return False
    
    try:
        from app.models.task import Task, TaskLog
        print("✅ Task models imported successfully")
    except Exception as e:
        print(f"❌ Task models import failed: {e}")
        return False
    
    try:
        from app.services.adb_manager import ADBManager
        print("✅ ADBManager service imported successfully")
    except Exception as e:
        print(f"❌ ADBManager service import failed: {e}")
        return False
    
    try:
        from app.services.phone_controller import PhoneController
        print("✅ PhoneController service imported successfully")
    except Exception as e:
        print(f"❌ PhoneController service import failed: {e}")
        return False
    
    try:
        from app.services.task_executor import TaskExecutor
        print("✅ TaskExecutor service imported successfully")
    except Exception as e:
        print(f"❌ TaskExecutor service import failed: {e}")
        return False
    
    try:
        from app.services.websocket_manager import ConnectionManager
        print("✅ ConnectionManager service imported successfully")
    except Exception as e:
        print(f"❌ ConnectionManager service import failed: {e}")
        return False
    
    return True

def test_fastapi_app():
    """Test if FastAPI app can be created."""
    try:
        from main import app
        print("✅ FastAPI app created successfully")
        print(f"   Routes: {len(app.routes)}")
        return True
    except Exception as e:
        print(f"❌ FastAPI app creation failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Backend Code Verification Test")
    print("=" * 60)
    
    print("\n1. Testing module imports...")
    imports_ok = test_imports()
    
    print("\n2. Testing FastAPI app...")
    app_ok = test_fastapi_app()
    
    print("\n" + "=" * 60)
    if imports_ok and app_ok:
        print("✅ All tests passed! Backend code structure is valid.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)