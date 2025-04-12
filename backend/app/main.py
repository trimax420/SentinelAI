from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

# Import logging configuration early
from app.core import logging_config

from app.api.endpoints import cameras, live_cameras, analytics, alerts, suspects
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cameras.router, prefix="/api/cameras", tags=["cameras"])
app.include_router(live_cameras.router, prefix="/api/live-cameras", tags=["live-cameras"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(suspects.router, prefix="/api/suspects", tags=["suspects"])

# Serve static files from the snapshots directory
snapshots_dir = os.path.join(os.getcwd(), settings.SNAPSHOT_BASE_DIR)
if os.path.exists(snapshots_dir):
    app.mount("/api/snapshots", StaticFiles(directory=snapshots_dir), name="snapshots")

@app.get("/")
async def root():
    return {"message": "Welcome to the Security Monitoring System API"} 