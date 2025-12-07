"""
Main FastAPI Application Entry Point

Sui Blockchain AI Agent - MVP Backend
Handles natural language blockchain interactions with privacy-first contact management
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import chat_router, contacts_router

# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logging with both console and file handlers
log_level = getattr(logging, settings.LOG_LEVEL)
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create root logger
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)
console_handler.setFormatter(logging.Formatter(log_format))
root_logger.addHandler(console_handler)

# File handler with rotation (10MB max, keep 5 backups)
file_handler = RotatingFileHandler(
    os.path.join(LOGS_DIR, "app.log"),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))
root_logger.addHandler(file_handler)

# Separate error log file
error_file_handler = RotatingFileHandler(
    os.path.join(LOGS_DIR, "error.log"),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(logging.Formatter(log_format))
root_logger.addHandler(error_file_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured. Log files: {LOGS_DIR}")

# Create FastAPI app
app = FastAPI(
    title="Sui Blockchain AI Agent",
    description="""
    An AI-powered blockchain agent that parses natural language intents
    and executes them on the Sui blockchain with privacy-first contact management.

    Features:
    - Natural language transaction parsing using OpenAI GPT-4
    - Strict mode function calling (guaranteed valid outputs)
    - Privacy-first encrypted contact storage (On-Chain + Seal)
    - Programmable Transaction Blocks (PTB) support
    - Dry-run summaries for transaction safety
    """,
    version="1.0.0-mvp",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",  # Alternative frontend port
        # Add production domains here
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(chat_router)
app.include_router(contacts_router)


# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Application startup tasks
    """
    logger.info("Starting Sui Blockchain AI Agent...")
    logger.info(f"Environment: {settings.SUI_NETWORK}")
    logger.info(f"Sui RPC: {settings.SUI_RPC_URL}")
    logger.info(f"Walrus Publisher: {settings.WALRUS_PUBLISHER_URL}")
    logger.info(f"OpenAI Model: {settings.OPENAI_MODEL}")
    logger.info("Application started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Application shutdown tasks
    """
    logger.info("Shutting down Sui Blockchain AI Agent...")


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "service": "Sui Blockchain AI Agent",
        "version": "1.0.0-mvp",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/v1/chat",
            "execute": "/api/v1/execute",
            "contacts_create_address_book": "/contacts/address-book/create",
            "contacts_info": "/contacts/address-book/info",
            "contacts_add": "/contacts/add",
            "contacts_health": "/contacts/health",
            "health": "/api/v1/health"
        },
        "features": [
            "Natural language transaction parsing",
            "OpenAI GPT-4 with strict mode",
            "Privacy-first contact encryption (Seal)",
            "On-chain contact storage",
            "Sui blockchain integration"
        ]
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        reload_excludes=["logs/*", "*.log"] if settings.DEBUG else None,
        log_level=settings.LOG_LEVEL.lower()
    )
