"""Global State Management"""
import json
import os
from utils.logger import get_logger
from core.agent import get_agent_executor
from core.providers import model_manager

logger = get_logger()

# Global state
agent_executor = None
system_prompt = None

# Settings file paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(PROJECT_ROOT, ".atom_settings.json")
FALLBACK_FILE = os.path.join(PROJECT_ROOT, ".atom_fallback.json")


def load_saved_model_settings():
    """Kaydedilmiş model ayarlarını yükle"""
    logger.info(f"Loading settings from {SETTINGS_FILE}")
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
            
            models = settings.get("models", {})
            logger.info(f"Found {len(models)} model configs")
            
            for role, cfg in models.items():
                provider = cfg.get("provider", "ollama")
                model = cfg.get("model", "llama3.2")
                temp = cfg.get("temperature", 0.0)
                
                if role in model_manager.ROLES:
                    success = model_manager.set_model(role, provider, model, temp)
                    if success:
                        logger.info(f"✓ Loaded {role}: {provider}/{model}")
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    if os.path.exists(FALLBACK_FILE):
        try:
            with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
                fallbacks = json.load(f)
            
            for role, cfg in fallbacks.items():
                if role in model_manager.ROLES:
                    fb_list = cfg.get("fallbacks", [])
                    fallback_tuples = [(f["provider"], f["model"]) for f in fb_list]
                    model_manager.set_fallbacks(role, fallback_tuples)
                    logger.info(f"Loaded {len(fb_list)} fallbacks for {role}")
        except Exception as e:
            logger.error(f"Failed to load fallbacks: {e}")


def init_agent():
    """Agent'ı başlat"""
    global agent_executor, system_prompt
    load_saved_model_settings()
    agent_executor, _, system_prompt = get_agent_executor()
    logger.info("Agent initialized")


def update_agent():
    """Agent'ı yeniden oluştur"""
    global agent_executor, system_prompt
    agent_executor, _, system_prompt = get_agent_executor()
    logger.info("Agent updated")


def get_agent():
    """Mevcut agent'ı döndür"""
    return agent_executor
