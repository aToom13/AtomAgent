"""
Prompt Management System
JSON dosyalarından agent promptlarını yükler
"""
import json
import os
from typing import Optional
from utils.logger import get_logger

logger = get_logger()

PROMPTS_DIR = os.path.dirname(__file__)

# Cache for loaded prompts
_prompt_cache = {}


def load_prompt(agent_name: str, use_cache: bool = True) -> str:
    """
    Load system prompt for an agent from TXT or JSON file.
    
    Args:
        agent_name: Agent name (supervisor, coder, researcher, planner)
        use_cache: Whether to use cached prompt (default True)
    
    Returns:
        System prompt string
    """
    global _prompt_cache
    
    # Check cache
    if use_cache and agent_name in _prompt_cache:
        return _prompt_cache[agent_name]
    
    # Önce .txt dosyasını dene (daha okunabilir format)
    txt_path = os.path.join(PROMPTS_DIR, f"{agent_name}.txt")
    json_path = os.path.join(PROMPTS_DIR, f"{agent_name}.json")
    
    prompt = None
    version = "?"
    
    # TXT dosyası varsa onu kullan
    if os.path.exists(txt_path):
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                prompt = f.read().strip()
            version = "txt"
            logger.info(f"Loaded prompt from TXT: {agent_name}")
        except Exception as e:
            logger.error(f"Error loading TXT prompt {agent_name}: {e}")
    
    # TXT yoksa veya boşsa JSON'dan yükle
    if not prompt and os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            prompt = data.get("system_prompt", "")
            version = data.get("version", "?")
            logger.info(f"Loaded prompt from JSON: {agent_name} (v{version})")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {json_path}: {e}")
        except Exception as e:
            logger.error(f"Error loading JSON prompt {agent_name}: {e}")
    
    # Hiçbiri yoksa default
    if not prompt:
        logger.warning(f"No prompt file found for: {agent_name}")
        return f"Sen {agent_name} agentisin."
    
    # Cache it
    _prompt_cache[agent_name] = prompt
    return prompt


def reload_prompts():
    """Clear prompt cache to force reload from files"""
    global _prompt_cache
    _prompt_cache.clear()
    logger.info("Prompt cache cleared")


def get_prompt_info(agent_name: str) -> Optional[dict]:
    """Get full prompt info including metadata"""
    file_path = os.path.join(PROMPTS_DIR, f"{agent_name}.json")
    
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None


def list_prompts() -> list:
    """List all available prompt files"""
    prompts = []
    for file in os.listdir(PROMPTS_DIR):
        if file.endswith(".json"):
            name = file.replace(".json", "")
            info = get_prompt_info(name)
            prompts.append({
                "name": name,
                "description": info.get("description", "") if info else "",
                "version": info.get("version", "") if info else ""
            })
    return prompts
