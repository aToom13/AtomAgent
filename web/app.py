"""
AtomAgent Web API - Main Application
Modüler FastAPI uygulaması
"""
import os
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from utils.logger import get_logger
from web import state
from web.websocket import handle_chat
from web.routes import sessions_router, settings_router, prompts_router, workspace_router, docker_router

logger = get_logger()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup/shutdown"""
    state.init_agent()
    logger.info("Web API started")
    yield
    logger.info("Web API stopped")


# Create FastAPI app
app = FastAPI(
    title="AtomAgent Web API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(sessions_router)
app.include_router(settings_router)
app.include_router(prompts_router)
app.include_router(workspace_router)
app.include_router(docker_router)


# === ROOT ROUTES ===

@app.get("/")
async def root():
    """Serve main HTML page"""
    html_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    return {"message": "AtomAgent Web API", "status": "running"}


@app.get("/api/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# === WEBSOCKET ===

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat(websocket: WebSocket, client_id: str):
    """WebSocket chat endpoint"""
    await handle_chat(websocket, client_id)


# === SERVER ===

def run_server(host: str = "0.0.0.0", port: int = 8000):
    """Web sunucusunu başlat"""
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
