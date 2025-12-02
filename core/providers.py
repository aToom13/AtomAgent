"""
LLM Provider System - Multi-provider support with Fallback
Supports: Ollama, OpenAI, Anthropic, Google, OpenRouter, HuggingFace, Cerebras, XAI
"""
import os
import json
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from langchain_core.language_models import BaseChatModel
from dotenv import load_dotenv

from utils.logger import get_logger

# Load .env file
load_dotenv()

logger = get_logger()

# Fallback settings file
FALLBACK_SETTINGS_FILE = ".atom_fallback.json"


@dataclass
class ProviderConfig:
    """Provider configuration"""
    name: str
    api_key_env: str = ""
    base_url: Optional[str] = None
    default_model: str = ""


# Available providers
PROVIDERS: Dict[str, ProviderConfig] = {
    "ollama": ProviderConfig(
        name="Ollama (Local)",
        api_key_env="",
        base_url="http://localhost:11434",
        default_model="llama3.2"
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini"
    ),
    "anthropic": ProviderConfig(
        name="Anthropic (Claude)",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-3-5-sonnet-20241022"
    ),
    "google": ProviderConfig(
        name="Google (Gemini)",
        api_key_env="GOOGLE_API_KEY",
        default_model="gemini-1.5-flash"
    ),
    "openrouter": ProviderConfig(
        name="OpenRouter",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        default_model="meta-llama/llama-3.1-8b-instruct:free"
    ),
    "huggingface": ProviderConfig(
        name="HuggingFace",
        api_key_env="HUGGINGFACE_API_KEY",
        default_model="meta-llama/Llama-3.1-8B-Instruct"
    ),
    "cerebras": ProviderConfig(
        name="Cerebras",
        api_key_env="CEREBRAS_API_KEY",
        base_url="https://api.cerebras.ai/v1",
        default_model="llama3.1-8b"
    ),
    "xai": ProviderConfig(
        name="xAI (Grok)",
        api_key_env="XAI_API_KEY",
        base_url="https://api.x.ai/v1",
        default_model="grok-beta"
    ),
    "groq": ProviderConfig(
        name="Groq",
        api_key_env="GROQ_API_KEY",
        default_model="llama-3.1-70b-versatile"
    ),
    "together": ProviderConfig(
        name="Together AI",
        api_key_env="TOGETHER_API_KEY",
        base_url="https://api.together.xyz/v1",
        default_model="meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo"
    ),
}


def get_provider_names() -> list:
    return list(PROVIDERS.keys())


def get_provider_config(provider: str) -> Optional[ProviderConfig]:
    return PROVIDERS.get(provider)


# Multi-key tracking - hangi key'in kullanıldığını takip eder
_api_key_index: Dict[str, int] = {}


def get_all_api_keys(provider: str) -> List[str]:
    """Get all API keys for a provider (comma-separated in .env)"""
    config = PROVIDERS.get(provider)
    if not config or not config.api_key_env:
        return []
    
    keys_str = os.getenv(config.api_key_env, "")
    if not keys_str:
        return []
    
    # Split by comma and clean
    keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    return keys


def get_api_key(provider: str) -> Optional[str]:
    """Get current active API key for provider"""
    keys = get_all_api_keys(provider)
    if not keys:
        return None
    
    # Get current index
    idx = _api_key_index.get(provider, 0)
    if idx >= len(keys):
        idx = 0
    
    return keys[idx]


def rotate_api_key(provider: str) -> bool:
    """
    Rotate to next API key for provider.
    Call this when rate limit is hit.
    Returns True if rotated, False if no more keys.
    """
    keys = get_all_api_keys(provider)
    if len(keys) <= 1:
        return False
    
    current_idx = _api_key_index.get(provider, 0)
    next_idx = current_idx + 1
    
    if next_idx >= len(keys):
        logger.warning(f"All API keys exhausted for {provider}")
        return False
    
    _api_key_index[provider] = next_idx
    logger.info(f"Rotated to API key {next_idx + 1}/{len(keys)} for {provider}")
    return True


def reset_api_key_index(provider: str = None):
    """Reset API key index to first key"""
    global _api_key_index
    if provider:
        _api_key_index[provider] = 0
    else:
        _api_key_index.clear()


def get_api_key_info(provider: str) -> dict:
    """Get info about API keys for provider"""
    keys = get_all_api_keys(provider)
    current_idx = _api_key_index.get(provider, 0)
    
    return {
        "total": len(keys),
        "current": current_idx + 1 if keys else 0,
        "has_more": current_idx < len(keys) - 1 if keys else False
    }


def is_rate_limit_error(error: Exception) -> bool:
    """Check if error is a rate limit error"""
    error_str = str(error).lower()
    rate_limit_indicators = [
        "rate limit",
        "rate_limit",
        "ratelimit",
        "429",
        "too many requests",
        "quota exceeded",
        "quota_exceeded",
        "resource exhausted",
        "resource_exhausted",
        "tokens per minute",
        "requests per minute",
        "rpm limit",
        "tpm limit",
        "credit",
        "insufficient_quota",
        "billing",
        # Ollama cloud specific
        "limit exceeded",
        "weekly limit",
        "daily limit",
        "monthly limit",
        "usage limit",
        "exceeded",
        "exhausted",
        "no capacity",
        "overloaded",
        "503",
        "502",
        "service unavailable",
    ]
    return any(indicator in error_str for indicator in rate_limit_indicators)


def is_fallback_needed(error: Exception) -> bool:
    """
    Check if error requires fallback to another provider.
    Includes rate limits, API errors, model errors, etc.
    """
    error_str = str(error).lower()
    
    # Rate limit hatası
    if is_rate_limit_error(error):
        return True
    
    # API ve model hataları - fallback gerektirir
    fallback_indicators = [
        # HTTP hataları
        "400", "401", "403", "404", "500", "502", "503", "504",
        # Model hataları
        "invalid model",
        "model not found",
        "unexpected model",
        "unknown model",
        "invalid argument",
        "bad request",
        # API hataları
        "api error",
        "api_error",
        "authentication",
        "unauthorized",
        "forbidden",
        "not found",
        # Bağlantı hataları
        "connection",
        "timeout",
        "timed out",
        "network",
        "unreachable",
        # Genel hatalar
        "failed",
        "error",
    ]
    return any(indicator in error_str for indicator in fallback_indicators)


def handle_rate_limit(provider: str) -> bool:
    """
    Handle rate limit by rotating API key.
    Returns True if successfully rotated, False if no more keys.
    """
    key_info = get_api_key_info(provider)
    
    if key_info["has_more"]:
        if rotate_api_key(provider):
            logger.info(f"Rate limit hit - rotated to key {key_info['current'] + 1}/{key_info['total']} for {provider}")
            return True
    
    logger.warning(f"Rate limit hit - no more API keys for {provider}")
    return False


def check_api_key(provider: str) -> bool:
    if provider == "ollama":
        return True
    return bool(get_api_key(provider))


def create_llm(provider: str, model: str, temperature: float = 0.0) -> Optional[BaseChatModel]:
    """Create LLM instance for given provider and model"""
    config = PROVIDERS.get(provider)
    if not config:
        logger.error(f"Unknown provider: {provider}")
        return None
    
    api_key = get_api_key(provider)
    if provider != "ollama" and not api_key:
        logger.error(f"API key not set: {config.api_key_env}")
        return None
    
    try:
        if provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model, temperature=temperature, base_url=config.base_url)
        
        elif provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=temperature, api_key=api_key)
        
        elif provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model, temperature=temperature, api_key=api_key)
        
        elif provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model, temperature=temperature, google_api_key=api_key)
        
        elif provider == "openrouter":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=config.base_url)
        
        elif provider == "huggingface":
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
            llm = HuggingFaceEndpoint(repo_id=model, temperature=temperature, huggingfacehub_api_token=api_key)
            return ChatHuggingFace(llm=llm)
        
        elif provider == "cerebras":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=config.base_url)
        
        elif provider == "xai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=config.base_url)
        
        elif provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(model=model, temperature=temperature, api_key=api_key)
        
        elif provider == "together":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model, temperature=temperature, api_key=api_key, base_url=config.base_url)
        
        else:
            logger.error(f"Provider not implemented: {provider}")
            return None
            
    except ImportError as e:
        logger.error(f"Missing package for {provider}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to create LLM for {provider}/{model}: {e}")
        return None


@dataclass
class FallbackConfig:
    """Fallback provider configuration"""
    provider: str
    model: str
    
    def to_dict(self):
        return {"provider": self.provider, "model": self.model}
    
    @staticmethod
    def from_dict(data: dict):
        return FallbackConfig(data.get("provider", "ollama"), data.get("model", "llama3.2"))


@dataclass
class AgentModelConfig:
    """Configuration for a specific agent role with fallback support"""
    provider: str = "ollama"
    model: str = "llama3.2"
    temperature: float = 0.0
    fallbacks: List[FallbackConfig] = field(default_factory=list)
    
    def to_dict(self):
        return {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "fallbacks": [f.to_dict() for f in self.fallbacks]
        }


class ModelManager:
    """Manages model configurations with fallback support"""
    
    ROLES = ["supervisor", "coder", "researcher", "vision", "audio", "tts"]
    
    def __init__(self):
        self.configs: Dict[str, AgentModelConfig] = {
            "supervisor": AgentModelConfig("ollama", "llama3.2", 0.1),
            "coder": AgentModelConfig("ollama", "llama3.2", 0.0),
            "researcher": AgentModelConfig("ollama", "llama3.2", 0.0),
            "vision": AgentModelConfig("openai", "gpt-4o", 0.2),
            "audio": AgentModelConfig("openai", "whisper-1", 0.0),
            "tts": AgentModelConfig("openai", "tts-1", 0.0),
        }
        self._llm_cache: Dict[str, BaseChatModel] = {}
        self._current_provider: Dict[str, int] = {}  # Track which provider is active (0 = primary)
        self._load_fallback_settings()
    
    def _load_fallback_settings(self):
        """Load fallback settings from file"""
        try:
            if os.path.exists(FALLBACK_SETTINGS_FILE):
                with open(FALLBACK_SETTINGS_FILE, "r") as f:
                    data = json.load(f)
                
                for role in self.ROLES:
                    if role in data:
                        role_data = data[role]
                        fallbacks = [FallbackConfig.from_dict(fb) for fb in role_data.get("fallbacks", [])]
                        self.configs[role].fallbacks = fallbacks
                
                logger.info("Fallback settings loaded")
        except Exception as e:
            logger.warning(f"Could not load fallback settings: {e}")
    
    def _save_fallback_settings(self):
        """Save fallback settings to file"""
        try:
            data = {}
            for role in self.ROLES:
                config = self.configs[role]
                data[role] = {
                    "fallbacks": [f.to_dict() for f in config.fallbacks]
                }
            
            with open(FALLBACK_SETTINGS_FILE, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info("Fallback settings saved")
        except Exception as e:
            logger.error(f"Could not save fallback settings: {e}")
    
    def set_model(self, role: str, provider: str, model: str, temperature: float = None):
        """Set primary model for a role"""
        if role not in self.ROLES:
            logger.error(f"Unknown role: {role}")
            return False
        
        if provider not in PROVIDERS:
            logger.error(f"Unknown provider: {provider}")
            return False
        
        config = self.configs[role]
        config.provider = provider
        config.model = model
        if temperature is not None:
            config.temperature = temperature
        
        # Reset to primary provider
        self._current_provider[role] = 0
        
        # Clear cache
        if role in self._llm_cache:
            del self._llm_cache[role]
        
        logger.info(f"Model set for {role}: {provider}/{model}")
        return True
    
    def set_fallbacks(self, role: str, fallbacks: List[tuple]):
        """
        Set fallback providers for a role.
        
        Args:
            role: Agent role (supervisor, coder, researcher)
            fallbacks: List of (provider, model) tuples in priority order
        """
        if role not in self.ROLES:
            logger.error(f"Unknown role: {role}")
            return False
        
        config = self.configs[role]
        config.fallbacks = [FallbackConfig(p, m) for p, m in fallbacks]
        
        self._save_fallback_settings()
        logger.info(f"Fallbacks set for {role}: {fallbacks}")
        return True
    
    def get_fallbacks(self, role: str) -> List[FallbackConfig]:
        """Get fallback list for a role"""
        if role not in self.ROLES:
            return []
        return self.configs[role].fallbacks
    
    def get_llm(self, role: str) -> Optional[BaseChatModel]:
        """Get LLM instance with fallback support"""
        if role not in self.ROLES:
            return None
        
        # Check cache
        if role in self._llm_cache:
            return self._llm_cache[role]
        
        config = self.configs[role]
        
        # Build provider list: primary + fallbacks
        providers_to_try = [(config.provider, config.model)]
        for fb in config.fallbacks:
            providers_to_try.append((fb.provider, fb.model))
        
        # Start from current provider index (important for fallback persistence)
        start_idx = self._current_provider.get(role, 0)
        
        # Try each provider starting from current index
        for i in range(start_idx, len(providers_to_try)):
            provider, model = providers_to_try[i]
            if not check_api_key(provider):
                logger.warning(f"Skipping {provider} - no API key")
                continue
            
            llm = create_llm(provider, model, config.temperature)
            if llm:
                self._llm_cache[role] = llm
                self._current_provider[role] = i
                
                if i > 0:
                    logger.warning(f"Using fallback for {role}: {provider}/{model}")
                
                return llm
        
        # If we started from a fallback and failed, try from beginning
        if start_idx > 0:
            for i in range(0, start_idx):
                provider, model = providers_to_try[i]
                if not check_api_key(provider):
                    continue
                
                llm = create_llm(provider, model, config.temperature)
                if llm:
                    self._llm_cache[role] = llm
                    self._current_provider[role] = i
                    return llm
        
        logger.error(f"All providers failed for {role}")
        return None
    
    def get_llm_with_fallback(self, role: str) -> Optional[BaseChatModel]:
        """
        Get LLM, trying fallbacks if primary fails during invocation.
        Use this for runtime fallback when rate limits hit.
        """
        return self.get_llm(role)
    
    def switch_to_fallback(self, role: str) -> bool:
        """
        Manually switch to next fallback provider.
        Call this when you detect rate limit or error.
        """
        if role not in self.ROLES:
            return False
        
        config = self.configs[role]
        current_idx = self._current_provider.get(role, 0)
        
        # Build provider list
        providers = [(config.provider, config.model)]
        for fb in config.fallbacks:
            providers.append((fb.provider, fb.model))
        
        logger.info(f"Attempting fallback for {role}, current index: {current_idx}, total providers: {len(providers)}")
        
        # Try next provider
        for i in range(current_idx + 1, len(providers)):
            provider, model = providers[i]
            logger.info(f"Trying fallback {i}: {provider}/{model}")
            
            if not check_api_key(provider):
                logger.warning(f"Skipping {provider} - no API key")
                continue
            
            llm = create_llm(provider, model, config.temperature)
            if llm:
                # Clear old cache and set new
                if role in self._llm_cache:
                    del self._llm_cache[role]
                
                self._llm_cache[role] = llm
                self._current_provider[role] = i
                
                logger.warning(f"Switched {role} to fallback: {provider}/{model}")
                return True
            else:
                logger.warning(f"Failed to create LLM for {provider}/{model}")
        
        # Wrap around - try from beginning if we haven't
        if current_idx > 0:
            for i in range(0, current_idx):
                provider, model = providers[i]
                if not check_api_key(provider):
                    continue
                
                llm = create_llm(provider, model, config.temperature)
                if llm:
                    if role in self._llm_cache:
                        del self._llm_cache[role]
                    
                    self._llm_cache[role] = llm
                    self._current_provider[role] = i
                    logger.warning(f"Wrapped around to {provider}/{model} for {role}")
                    return True
        
        logger.error(f"No more fallbacks available for {role}")
        return False
    
    def get_current_provider_info(self, role: str) -> tuple:
        """Get current active provider and model for a role"""
        if role not in self.ROLES:
            return None, None
        
        config = self.configs[role]
        idx = self._current_provider.get(role, 0)
        
        if idx == 0:
            return config.provider, config.model
        
        fb_idx = idx - 1
        if fb_idx < len(config.fallbacks):
            fb = config.fallbacks[fb_idx]
            return fb.provider, fb.model
        
        return config.provider, config.model
    
    def reset_to_primary(self, role: str = None):
        """Reset to primary provider (clear fallback state)"""
        if role:
            self._current_provider[role] = 0
            if role in self._llm_cache:
                del self._llm_cache[role]
        else:
            self._current_provider.clear()
            self._llm_cache.clear()
        
        logger.info(f"Reset to primary provider: {role or 'all'}")
    
    def get_config(self, role: str) -> Optional[AgentModelConfig]:
        return self.configs.get(role)
    
    def clear_cache(self, role: str = None):
        if role:
            if role in self._llm_cache:
                del self._llm_cache[role]
        else:
            self._llm_cache.clear()


# Global model manager instance
model_manager = ModelManager()
