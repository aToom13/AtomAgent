"""
Tests for LLM Provider System
"""
import pytest
import os
from unittest.mock import patch, MagicMock


class TestProviderConfig:
    """Test provider configuration"""
    
    def test_get_provider_names(self):
        """Test getting list of provider names"""
        from core.providers import get_provider_names
        
        names = get_provider_names()
        assert isinstance(names, list)
        assert "ollama" in names
        assert "openai" in names
        assert "anthropic" in names
    
    def test_get_provider_config(self):
        """Test getting provider config"""
        from core.providers import get_provider_config
        
        config = get_provider_config("openai")
        assert config is not None
        assert config.name == "OpenAI"
        assert config.api_key_env == "OPENAI_API_KEY"
    
    def test_get_unknown_provider(self):
        """Test getting unknown provider returns None"""
        from core.providers import get_provider_config
        
        config = get_provider_config("unknown_provider")
        assert config is None


class TestAPIKeyManagement:
    """Test API key management"""
    
    def test_get_all_api_keys_empty(self):
        """Test getting keys when none set"""
        from core.providers import get_all_api_keys
        
        with patch.dict(os.environ, {}, clear=True):
            keys = get_all_api_keys("openai")
            assert keys == []
    
    def test_get_all_api_keys_single(self):
        """Test getting single API key"""
        from core.providers import get_all_api_keys
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            keys = get_all_api_keys("openai")
            assert keys == ["test_key"]
    
    def test_get_all_api_keys_multiple(self):
        """Test getting multiple API keys"""
        from core.providers import get_all_api_keys
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key1,key2,key3"}):
            keys = get_all_api_keys("openai")
            assert keys == ["key1", "key2", "key3"]
    
    def test_rotate_api_key(self):
        """Test API key rotation"""
        from core.providers import rotate_api_key, get_api_key, reset_api_key_index
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key1,key2"}):
            reset_api_key_index("openai")
            
            # First key
            assert get_api_key("openai") == "key1"
            
            # Rotate
            assert rotate_api_key("openai") == True
            assert get_api_key("openai") == "key2"
            
            # No more keys
            assert rotate_api_key("openai") == False


class TestRateLimitDetection:
    """Test rate limit error detection"""
    
    def test_is_rate_limit_error(self):
        """Test rate limit error detection"""
        from core.providers import is_rate_limit_error
        
        # Should detect rate limit
        assert is_rate_limit_error(Exception("Rate limit exceeded"))
        assert is_rate_limit_error(Exception("Error 429: Too many requests"))
        assert is_rate_limit_error(Exception("quota exceeded"))
        
        # Should not detect as rate limit
        assert not is_rate_limit_error(Exception("Connection error"))
        assert not is_rate_limit_error(Exception("Invalid API key"))
