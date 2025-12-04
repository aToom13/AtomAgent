"""Settings API Routes"""
import json
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.providers import model_manager, PROVIDERS, get_api_key_info
from core.agent import get_agent_executor
from config import config

router = APIRouter(prefix="/api", tags=["settings"])

# Settings file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_FILE = os.path.join(PROJECT_ROOT, ".atom_settings.json")
FALLBACK_FILE = os.path.join(PROJECT_ROOT, ".atom_fallback.json")


class ModelConfig(BaseModel):
    role: str
    provider: str
    model: str
    temperature: Optional[float] = None


class FallbackConfig(BaseModel):
    role: str
    fallbacks: List[Dict[str, str]]


def load_settings_file() -> dict:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"models": {}}


def save_settings_file(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_fallback_file() -> dict:
    if os.path.exists(FALLBACK_FILE):
        with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_fallback_file(data: dict):
    with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


@router.get("/settings")
async def get_settings():
    """Tüm ayarları getir"""
    settings_data = load_settings_file()
    fallback_data = load_fallback_file()
    
    models = {}
    all_roles = ["supervisor", "coder", "researcher", "vision", "audio", "tts"]
    
    for role in all_roles:
        model_settings = settings_data.get("models", {}).get(role, {})
        role_fallbacks = fallback_data.get(role, {}).get("fallbacks", [])
        cfg = model_manager.get_config(role)
        current_provider, current_model = model_manager.get_current_provider_info(role)
        
        models[role] = {
            "provider": model_settings.get("provider", cfg.provider if cfg else "ollama"),
            "model": model_settings.get("model", cfg.model if cfg else ""),
            "temperature": model_settings.get("temperature", cfg.temperature if cfg else 0.0),
            "current_provider": current_provider,
            "current_model": current_model,
            "fallbacks": role_fallbacks
        }
    
    return {
        "models": models,
        "providers": list(PROVIDERS.keys()),
        "allowed_commands": config.execution.allowed_commands,
        "blocked_patterns": config.execution.blocked_patterns,
        "workspace_dir": config.workspace.base_dir
    }


@router.put("/settings/model")
async def update_model(data: ModelConfig):
    """Model ayarını güncelle"""
    from web.state import update_agent
    
    success = model_manager.set_model(data.role, data.provider, data.model, data.temperature)
    
    if success:
        settings_data = load_settings_file()
        if "models" not in settings_data:
            settings_data["models"] = {}
        
        settings_data["models"][data.role] = {
            "provider": data.provider,
            "model": data.model,
            "temperature": data.temperature if data.temperature is not None else 0.0
        }
        save_settings_file(settings_data)
        update_agent()
        return {"success": True}
    
    raise HTTPException(status_code=400, detail="Failed to update model")


@router.put("/settings/fallback")
async def update_fallback(data: FallbackConfig):
    """Fallback ayarlarını güncelle"""
    fallback_data = load_fallback_file()
    fallback_data[data.role] = {"fallbacks": data.fallbacks}
    save_fallback_file(fallback_data)
    
    fallback_tuples = [(f["provider"], f["model"]) for f in data.fallbacks]
    model_manager.set_fallbacks(data.role, fallback_tuples)
    return {"success": True}


@router.delete("/settings/fallback/{role}/{index}")
async def delete_fallback(role: str, index: int):
    """Belirli bir fallback'i sil"""
    fallback_data = load_fallback_file()
    
    if role in fallback_data and "fallbacks" in fallback_data[role]:
        fallbacks = fallback_data[role]["fallbacks"]
        if 0 <= index < len(fallbacks):
            fallbacks.pop(index)
            save_fallback_file(fallback_data)
            fallback_tuples = [(f["provider"], f["model"]) for f in fallbacks]
            model_manager.set_fallbacks(role, fallback_tuples)
            return {"success": True}
    
    raise HTTPException(status_code=404, detail="Fallback not found")


@router.get("/providers")
async def get_providers():
    """Provider listesi"""
    providers = []
    for name, cfg in PROVIDERS.items():
        key_info = get_api_key_info(name)
        providers.append({
            "id": name,
            "name": cfg.name,
            "default_model": cfg.default_model,
            "has_api_key": key_info["total"] > 0,
            "api_key_count": key_info["total"]
        })
    return {"providers": providers}
