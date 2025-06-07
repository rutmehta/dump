import logging
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routes import whatsapp_webhook, voice_call_handler
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('life-os.log')
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events"""
    
    # Startup
    logger.info("🚀 Starting Life OS with Enhanced Gemini Gen AI SDK...")
    logger.info(f"Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"Server: {settings.HOST}:{settings.PORT}")
    logger.info(f"Model: {settings.DEFAULT_MODEL}")
    logger.info(f"Context Window: {settings.MAX_CONTEXT_TOKENS:,} tokens")
    
    # Validate critical configuration
    if not settings.GEMINI_API_KEY:
        logger.error("❌ GEMINI_API_KEY not configured")
        raise ValueError("GEMINI_API_KEY is required")
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        logger.warning("⚠️  Twilio credentials not configured - WhatsApp/Voice features may not work")
    
    logger.info("✅ Life OS startup complete with enhanced capabilities")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Life OS...")
    # Cleanup is handled by individual service shutdown handlers
    logger.info("✅ Life OS shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="Life OS",
    description="AI-powered Life Operating System with WhatsApp integration using Gemini 2.0",
    version="2.0.0",  # Updated version for new SDK
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://api.twilio.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    whatsapp_webhook.router,
    prefix="/api/v1",
    tags=["WhatsApp"]
)

app.include_router(
    voice_call_handler.router,
    prefix="/api/v1",
    tags=["Voice"]
)

@app.get("/")
async def root():
    """Root endpoint with basic system info"""
    return {
        "service": "Life OS",
        "description": "AI-powered Life Operating System with enhanced Gemini 2.0 capabilities",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_model": settings.DEFAULT_MODEL,
        "context_window": f"{settings.MAX_CONTEXT_TOKENS:,} tokens",
        "capabilities": [
            "multimodal_processing",
            "long_context",
            "video_understanding",
            "enhanced_audio",
            "proactive_memory"
        ],
        "endpoints": {
            "whatsapp_webhook": "/api/v1/whatsapp",
            "voice_incoming": "/api/v1/voice/incoming",
            "status_check": "/api/v1/whatsapp/status",
            "docs": "/docs" if settings.DEBUG else "disabled"
        }
    }

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "ai_model": settings.DEFAULT_MODEL,
            "context_window": f"{settings.MAX_CONTEXT_TOKENS:,} tokens",
            "services": {
                "api": "healthy",
                "whatsapp": "unknown",
                "voice": "healthy",
                "ai": "unknown",
                "memory": "unknown",
                "storage": "healthy"
            },
            "capabilities": {
                "video_processing": settings.ENABLE_VIDEO_PROCESSING,
                "audio_native": settings.ENABLE_AUDIO_NATIVE,
                "long_context": settings.ENABLE_LONG_CONTEXT
            }
        }
        
        # Try to get detailed status from WhatsApp service
        try:
            from app.routes.whatsapp_webhook import ai_processor, memory_manager, file_storage
            
            # Check AI processor (updated for new SDK)
            if ai_processor.client:
                health_status["services"]["ai"] = "healthy"
            else:
                health_status["services"]["ai"] = "unhealthy"
            
            # Check memory manager
            if memory_manager.vector_db.client:
                health_status["services"]["memory"] = "healthy"
            else:
                health_status["services"]["memory"] = "unhealthy"
                
            health_status["services"]["whatsapp"] = "healthy"
            
        except Exception as e:
            logger.warning(f"Health check services probe failed: {e}")
            health_status["services"]["whatsapp"] = "degraded"
        
        # Determine overall health
        service_statuses = list(health_status["services"].values())
        if any(status == "unhealthy" for status in service_statuses):
            health_status["status"] = "unhealthy"
        elif any(status in ["degraded", "unknown"] for status in service_statuses):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )

@app.get("/api/v1/config")
async def get_config():
    """Get non-sensitive configuration information"""
    if not settings.DEBUG:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "debug": settings.DEBUG,
        "host": settings.HOST,
        "port": settings.PORT,
        "ai_model": settings.DEFAULT_MODEL,
        "long_context_model": settings.LONG_CONTEXT_MODEL,
        "max_file_size_mb": settings.MAX_FILE_SIZE / (1024 * 1024),
        "max_context_tokens": settings.MAX_CONTEXT_TOKENS,
        "context_memory_limit": settings.CONTEXT_MEMORY_LIMIT,
        "lru_cache_size": settings.LRU_CACHE_SIZE,
        "vector_search_limit": settings.VECTOR_SEARCH_LIMIT,
        "graph_traverse_depth": settings.GRAPH_TRAVERSE_DEPTH,
        "multimodal_capabilities": {
            "video_processing": settings.ENABLE_VIDEO_PROCESSING,
            "audio_native": settings.ENABLE_AUDIO_NATIVE,
            "long_context": settings.ENABLE_LONG_CONTEXT
        },
        "services_configured": {
            "gemini": bool(settings.GEMINI_API_KEY),
            "twilio": bool(settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN),
            "weaviate": bool(settings.WEAVIATE_URL),
            "neo4j": bool(settings.NEO4J_URI),
            "assemblyai": bool(settings.ASSEMBLYAI_API_KEY),
            "redis": bool(settings.REDIS_URL)
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return {
        "error": "Internal server error",
        "message": "An unexpected error occurred",
        "timestamp": datetime.utcnow().isoformat(),
        "path": str(request.url)
    }

if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if settings.DEBUG else "warning",
        access_log=True
    ) 