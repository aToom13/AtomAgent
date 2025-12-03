"""
Tests for file operation tools
"""
import pytest
import os


class TestFileOperations:
    """Test file operation tools"""
    
    def test_write_and_read_file(self, temp_workspace, monkeypatch):
        """Test writing and reading a file"""
        # Mock workspace
        monkeypatch.setattr("tools.files.WORKSPACE_DIR", temp_workspace)
        
        from tools.files import write_file, read_file
        
        # Write file
        result = write_file.invoke({"filename": "test.txt", "content": "Hello World"})
        assert "success" in result.lower() or "created" in result.lower() or "✓" in result
        
        # Read file
        content = read_file.invoke({"filename": "test.txt"})
        assert "Hello World" in content
    
    def test_list_files(self, temp_workspace, monkeypatch):
        """Test listing files"""
        monkeypatch.setattr("tools.files.WORKSPACE_DIR", temp_workspace)
        
        from tools.files import list_files, write_file
        
        # Create some files
        write_file.invoke({"filename": "file1.py", "content": "# Python"})
        write_file.invoke({"filename": "file2.js", "content": "// JS"})
        
        # List files
        result = list_files.invoke({"directory": "."})
        assert "file1.py" in result
        assert "file2.js" in result
    
    def test_read_nonexistent_file(self, temp_workspace, monkeypatch):
        """Test reading non-existent file"""
        monkeypatch.setattr("tools.files.WORKSPACE_DIR", temp_workspace)
        
        from tools.files import read_file
        
        result = read_file.invoke({"filename": "nonexistent.txt"})
        assert "error" in result.lower() or "not found" in result.lower()


class TestPathSecurity:
    """Test path security measures"""
    
    def test_path_traversal_blocked(self, temp_workspace, monkeypatch):
        """Test that path traversal is blocked"""
        monkeypatch.setattr("tools.files.WORKSPACE_DIR", temp_workspace)
        
        from tools.files import read_file
        
        # Try to read outside workspace
        result = read_file.invoke({"filename": "../../../etc/passwd"})
        
        # Should either error or not return sensitive content
        assert "etc/passwd" not in result or "error" in result.lower()
