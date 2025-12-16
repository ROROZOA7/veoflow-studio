"""
VeoFlow Studio FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.logging_config import setup_logging
import logging

# Setup logging
setup_logging("INFO")
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VeoFlow Studio API",
    version="1.0.0",
    description="Automated video generation using Google Veo 3 Ultra"
)

# Configure CORS
cors_origins = settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS else ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "VeoFlow Studio API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Import API routers
from app.api import projects, scenes, characters, render, queue, setup, logs, scripts, ai_config

# Register API routers
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(scenes.router, prefix="/api/scenes", tags=["scenes"])
app.include_router(characters.router, prefix="/api/characters", tags=["characters"])
app.include_router(scripts.router, prefix="/api", tags=["scripts"])
app.include_router(render.router, prefix="/api/render", tags=["render"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(setup.router, prefix="/api/setup", tags=["setup"])
app.include_router(logs.router, prefix="/api", tags=["logs"])
app.include_router(ai_config.router, prefix="/api", tags=["ai-config"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)

