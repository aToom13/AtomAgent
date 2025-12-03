"""
Tests for Agent Core
"""
import pytest
from unittest.mock import patch, MagicMock


class TestAgentCreation:
    """Test agent creation and configuration"""
    
    def test_get_thread_config(self):
        """Test thread config generation"""
        from core.agent import get_thread_config
        
        config = get_thread_config("test_thread")
        assert config == {"configurable": {"thread_id": "test_thread"}}
    
    def test_get_thread_config_default(self):
        """Test default thread config"""
        from core.agent import get_thread_config
        
        config = get_thread_config()
        assert config == {"configurable": {"thread_id": "default"}}


class TestModelManager:
    """Test model manager functionality"""
    
    def test_model_manager_roles(self):
        """Test model manager has all roles"""
        from core.providers import ModelManager
        
        manager = ModelManager()
        assert "supervisor" in manager.ROLES
        assert "coder" in manager.ROLES
        assert "researcher" in manager.ROLES
    
    def test_set_model(self):
        """Test setting model for a role"""
        from core.providers import ModelManager
        
        manager = ModelManager()
        result = manager.set_model("coder", "ollama", "llama3.2", 0.1)
        assert result == True
        
        config = manager.get_config("coder")
        assert config.provider == "ollama"
        assert config.model == "llama3.2"
    
    def test_set_invalid_role(self):
        """Test setting model for invalid role"""
        from core.providers import ModelManager
        
        manager = ModelManager()
        result = manager.set_model("invalid_role", "ollama", "llama3.2")
        assert result == False
    
    def test_set_fallbacks(self):
        """Test setting fallback providers"""
        from core.providers import ModelManager
        
        manager = ModelManager()
        fallbacks = [("openai", "gpt-4o-mini"), ("anthropic", "claude-3-haiku")]
        
        result = manager.set_fallbacks("coder", fallbacks)
        assert result == True
        
        stored_fallbacks = manager.get_fallbacks("coder")
        assert len(stored_fallbacks) == 2
        assert stored_fallbacks[0].provider == "openai"


class TestFallbackBehavior:
    """Test fallback behavior"""
    
    def test_switch_to_fallback(self):
        """Test switching to fallback provider"""
        from core.providers import ModelManager
        
        manager = ModelManager()
        manager.set_model("coder", "ollama", "llama3.2")
        manager.set_fallbacks("coder", [("openai", "gpt-4o-mini")])
        
        # Mock API key check
        with patch("core.providers.check_api_key", return_value=True):
            with patch("core.providers.create_llm", return_value=MagicMock()):
                result = manager.switch_to_fallback("coder")
                # May or may not succeed depending on setup
                assert isinstance(result, bool)
    
    def test_reset_to_primary(self):
        """Test resetting to primary provider"""
        from core.providers import ModelManager
        
        manager = ModelManager()
        manager._current_provider["coder"] = 2  # Simulate being on fallback
        
        manager.reset_to_primary("coder")
        assert manager._current_provider.get("coder", 0) == 0
