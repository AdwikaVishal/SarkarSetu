"""FastAPI application entry point."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.businesses import router as businesses_router
from app.api.chat import router as chat_router
from app.api.conversation import router as conversation_router
from app.api.eligibility import router as eligibility_router
from app.api.health import router as health_router
from app.api.intent import router as intent_router
from app.api.knowledge import router as knowledge_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.database.connection import close_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    setup_logging()
    yield
    await close_db()


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        description="AI-powered government services guidance platform for Indian entrepreneurs",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # Include routers
    application.include_router(health_router, prefix=settings.api_prefix)
    application.include_router(auth_router, prefix=settings.api_prefix)
    application.include_router(businesses_router, prefix=settings.api_prefix)
    application.include_router(ai_router, prefix=settings.api_prefix)
    application.include_router(intent_router, prefix=settings.api_prefix)
    application.include_router(conversation_router, prefix=settings.api_prefix)
    application.include_router(chat_router, prefix=settings.api_prefix)
    application.include_router(eligibility_router, prefix=settings.api_prefix)
    application.include_router(knowledge_router, prefix=settings.api_prefix)

    # Root endpoint
    @application.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": "1.0.0",
            "docs": "/docs",
        }

    return application


app = create_application()
