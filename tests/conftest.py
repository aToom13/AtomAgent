"""
Pytest configuration and fixtures for AtomAgent tests
"""
import os
import sys
import pytest
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing"""
    temp_dir = tempfile.mkdtemp(prefix="atom_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_python_file(temp_workspace):
    """Create a sample Python file for testing"""
    file_path = os.path.join(temp_workspace, "sample.py")
    content = '''
def hello(name: str) -> str:
    """Say hello to someone"""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

class Calculator:
    """Simple calculator class"""
    
    def __init__(self):
        self.result = 0
    
    def add(self, value: int):
        self.result += value
        return self
    
    def subtract(self, value: int):
        self.result -= value
        return self
'''
    with open(file_path, "w") as f:
        f.write(content)
    return file_path


@pytest.fixture
def mock_config(monkeypatch, temp_workspace):
    """Mock config for testing"""
    monkeypatch.setattr("config.config.workspace.base_dir", temp_workspace)
    return temp_workspace
