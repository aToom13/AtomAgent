# Web API Routes
from .sessions import router as sessions_router
from .settings import router as settings_router
from .prompts import router as prompts_router
from .workspace import router as workspace_router
from .docker import router as docker_router
from .canvas import router as canvas_router

__all__ = [
    "sessions_router",
    "settings_router", 
    "prompts_router",
    "workspace_router",
    "docker_router",
    "canvas_router"
]
