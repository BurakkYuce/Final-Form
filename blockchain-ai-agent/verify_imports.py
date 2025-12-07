#!/usr/bin/env python3
"""
Import Verification Script
Tests that all imports work correctly
"""

import sys
import os

# Add current directory to path (should already be there, but just in case)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports"""
    errors = []

    print("Testing imports...\n")

    # Test config
    try:
        from config import settings
        print("[OK] config.settings imported successfully")
    except Exception as e:
        errors.append(f"[ERR] config.settings: {e}")
        print(f"[ERR] config.settings: {e}")

    # Test models
    try:
        from models.schemas import (
            ChatRequest, ChatResponse, TokenType, IntentAction
        )
        print("[OK] models.schemas imported successfully")
    except Exception as e:
        errors.append(f"[ERR] models.schemas: {e}")
        print(f"[ERR] models.schemas: {e}")

    # Test services
    try:
        from services.openai_service import openai_service
        print("[OK] services.openai_service imported successfully")
    except Exception as e:
        errors.append(f"[ERR] services.openai_service: {e}")
        print(f"[ERR] services.openai_service: {e}")

    try:
        from services.sui_service import sui_service
        print("[OK] services.sui_service imported successfully")
    except Exception as e:
        errors.append(f"[ERR] services.sui_service: {e}")
        print(f"[ERR] services.sui_service: {e}")

    try:
        from services.walrus_service import walrus_service
        print("[OK] services.walrus_service imported successfully")
    except Exception as e:
        errors.append(f"[ERR] services.walrus_service: {e}")
        print(f"[ERR] services.walrus_service: {e}")

    try:
        from services.seal_service import seal_service
        print("[OK] services.seal_service imported successfully")
    except Exception as e:
        errors.append(f"[ERR] services.seal_service: {e}")
        print(f"[ERR] services.seal_service: {e}")

    # Test routers
    try:
        from routers.chat import router
        print("[OK] routers.chat imported successfully")
    except Exception as e:
        errors.append(f"[ERR] routers.chat: {e}")
        print(f"[ERR] routers.chat: {e}")

    # Test main app
    try:
        from main import app
        print("[OK] main.app imported successfully")
    except Exception as e:
        errors.append(f"[ERR] main.app: {e}")
        print(f"[ERR] main.app: {e}")

    # Summary
    print("\n" + "="*50)
    if errors:
        print(f"[ERR] {len(errors)} import error(s) found:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print("[SUCCESS] All imports successful!")
        print("[OK] Application is ready to run")
        return True


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
