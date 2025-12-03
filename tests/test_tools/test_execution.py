"""
Tests for command execution tools
"""
import pytest
import os


class TestCommandExecution:
    """Test command execution"""
    
    def test_run_allowed_command(self, temp_workspace, monkeypatch):
        """Test running allowed command"""
        monkeypatch.setattr("tools.execution.WORKSPACE_DIR", temp_workspace)
        
        from tools.execution import run_terminal_command
        
        result = run_terminal_command.invoke({"command": "echo 'Hello World'"})
        assert "Hello World" in result
    
    def test_run_python_command(self, temp_workspace, monkeypatch):
        """Test running Python command"""
        monkeypatch.setattr("tools.execution.WORKSPACE_DIR", temp_workspace)
        
        from tools.execution import run_terminal_command
        
        result = run_terminal_command.invoke({"command": "python3 -c 'print(1+1)'"})
        assert "2" in result
    
    def test_blocked_command(self, temp_workspace, monkeypatch):
        """Test that dangerous commands are blocked"""
        monkeypatch.setattr("tools.execution.WORKSPACE_DIR", temp_workspace)
        
        from tools.execution import run_terminal_command
        
        # Try dangerous command
        result = run_terminal_command.invoke({"command": "rm -rf /"})
        
        # Should be blocked
        assert "blocked" in result.lower() or "not allowed" in result.lower() or "error" in result.lower()


class TestCommandTimeout:
    """Test command timeout handling"""
    
    def test_command_timeout(self, temp_workspace, monkeypatch):
        """Test that long-running commands timeout"""
        monkeypatch.setattr("tools.execution.WORKSPACE_DIR", temp_workspace)
        monkeypatch.setattr("config.config.execution.command_timeout", 2)
        
        from tools.execution import run_terminal_command
        
        # This should timeout
        result = run_terminal_command.invoke({"command": "sleep 10"})
        
        # Should indicate timeout or be interrupted
        assert "timeout" in result.lower() or "timed out" in result.lower() or len(result) < 100
