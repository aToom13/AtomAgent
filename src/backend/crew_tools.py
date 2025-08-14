#!/usr/bin/env python3
"""
CrewAI Araçları ve Sandboxing Sistemi
"""

import os
import subprocess
import tempfile
import shutil
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from crewai.tools import BaseTool
from crewai.tools import tool
import docker
from pathlib import Path

@dataclass
class SandboxEnvironment:
    """Sandbox ortamı veri yapısı"""
    agent_id: str
    base_path: str
    container_id: Optional[str] = None
    is_active: bool = False

class FileOperationTool(BaseTool):
    """Dosya işlemleri için araç"""
    name: str = "file_operation"
    description: str = "Dosya okuma, yazma, listeleme ve silme işlemleri"
    
    def _run(self, operation: str, path: str, content: str = "", create_dirs: bool = True) -> str:
        """Dosya işlemleri çalıştır"""
        try:
            if operation == "read":
                if not os.path.exists(path):
                    return f"Hata: Dosya bulunamadı: {path}"
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif operation == "write":
                if create_dirs:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Dosya başarıyla yazıldı: {path}"
            
            elif operation == "append":
                if create_dirs:
                    os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(content)
                return f"İçerik başarıyla eklendi: {path}"
            
            elif operation == "list":
                if not os.path.exists(path):
                    return f"Hata: Dizin bulunamadı: {path}"
                return str(os.listdir(path))
            
            elif operation == "delete":
                if os.path.exists(path):
                    if os.path.isfile(path):
                        os.remove(path)
                        return f"Dosya silindi: {path}"
                    else:
                        shutil.rmtree(path)
                        return f"Dizin silindi: {path}"
                else:
                    return f"Hata: {path} bulunamadı"
            
            else:
                return f"Desteklenmeyen işlem: {operation}"
                
        except Exception as e:
            return f"Dosya işlemi hatası: {str(e)}"

class TerminalTool(BaseTool):
    """Terminal komutları için araç"""
    name: str = "terminal"
    description: str = "Terminal komutları çalıştırma aracı"
    
    def _run(self, command: str, working_dir: str = "/tmp", timeout: int = 30) -> str:
        """Terminal komutu çalıştır"""
        try:
            # Güvenlik kontrolü
            if any(danger in command.lower() for danger in ['rm -rf', 'del /f', 'format', 'mkfs', 'dd=', 'chmod 777']):
                return "Güvenlik ihlali: Tehlikeli komut çalıştırılamaz"
            
            # Komut çalıştır
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=working_dir,
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            
            # Çıktıyı formatla
            output = f"Çıktı:\n{result.stdout}"
            if result.stderr:
                output += f"\nHata:\n{result.stderr}"
            
            return output
            
        except subprocess.TimeoutExpired:
            return f"Komut zaman aşımına uğradı: {timeout} saniye"
        except Exception as e:
            return f"Komut çalıştırma hatası: {str(e)}"

class PackageManagerTool(BaseTool):
    """Paket yönetimi için araç"""
    name: str = "package_manager"
    description: str = "Python paket kurulumu ve yönetimi"
    
    def _run(self, package_name: str, manager: str = "pip") -> str:
        """Paket kur"""
        try:
            if manager == "pip":
                cmd = f"pip install {package_name}"
            elif manager == "conda":
                cmd = f"conda install -y {package_name}"
            else:
                return f"Desteklenmeyen paket yöneticisi: {manager}"
            
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=120
            )
            
            if result.returncode == 0:
                return f"Paket başarıyla kuruldu: {package_name}"
            else:
                return f"Paket kurulum hatası: {result.stderr}"
                
        except Exception as e:
            return f"Paket kurulum hatası: {str(e)}"

class CodeExecutionTool(BaseTool):
    """Kod çalıştırma için araç"""
    name: str = "code_execution"
    description: str = "Python ve JavaScript kodu çalıştırma"
    
    def _run(self, code: str, language: str = "python") -> str:
        """Kod çalıştır"""
        try:
            if language == "python":
                # Python kodu çalıştır
                result = subprocess.run(
                    ["python", "-c", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return f"Python çıktısı:\n{result.stdout}"
                else:
                    return f"Python hatası:\n{result.stderr}"
            
            elif language == "javascript":
                # JavaScript kodu çalıştır (Node.js)
                result = subprocess.run(
                    ["node", "-e", code],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return f"JavaScript çıktısı:\n{result.stdout}"
                else:
                    return f"JavaScript hatası:\n{result.stderr}"
            
            else:
                return f"Desteklenmeyen dil: {language}"
                
        except Exception as e:
            return f"Kod çalıştırma hatası: {str(e)}"

class GitTool(BaseTool):
    """Git işlemleri için araç"""
    name: str = "git_tool"
    description: str = "Git reposu işlemleri"
    
    def _run(self, operation: str, repo_url: str = "", message: str = "") -> str:
        """Git işlemi çalıştır"""
        try:
            if operation == "clone":
                if not repo_url:
                    return "Repo URL gerekli"
                
                # Güvenlik kontrolü
                if not repo_url.startswith(('https://github.com/', 'git@github.com:', 'https://gitlab.com/')):
                    return "Güvenlik: Sadece GitHub ve GitLab reposu destekleniyor"
                
                result = subprocess.run(
                    f"git clone {repo_url}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    return f"Repo başarıyla klonlandı: {repo_url}"
                else:
                    return f"Klonlama hatası: {result.stderr}"
            
            elif operation == "commit":
                if not message:
                    return "Commit mesajı gerekli"
                
                result = subprocess.run(
                    f'git add . && git commit -m "{message}"',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    return f"Commit başarıyla yapıldı: {message}"
                else:
                    return f"Commit hatası: {result.stderr}"
            
            else:
                return f"Desteklenmeyen Git işlemi: {operation}"
                
        except Exception as e:
            return f"Git işlemi hatası: {str(e)}"

class DockerSandboxTool(BaseTool):
    """Docker sandbox için araç"""
    name: str = "docker_sandbox"
    description: str = "Docker konteyneri oluşturma ve yönetimi"
    
    def __init__(self):
        self._client = None
        self._containers = {}
        try:
            self._client = docker.from_env()
        except Exception:
            self._client = None
    
    def _run(self, operation: str, image: str = "python:3.11", command: str = "", 
             container_name: str = None) -> str:
        """Docker işlemi çalıştır"""
        try:
            if not self._client:
                return "Docker istemcisi başlatılamadı. Docker kurulu olmalı."
            
            if operation == "create":
                container = self._client.containers.create(
                    image=image,
                    command=command,
                    name=container_name,
                    detach=True,
                    tty=True
                )
                self._containers[container.id] = container
                return f"Konteyner oluşturuldu: {container.id[:12]}"
            
            elif operation == "start":
                if container_name:
                    container = self._client.containers.get(container_name)
                    container.start()
                    return f"Konteyner başlatıldı: {container_name}"
                else:
                    return "Konteyner adı gerekli"
            
            elif operation == "stop":
                if container_name:
                    container = self._client.containers.get(container_name)
                    container.stop()
                    return f"Konteyner durduruldu: {container_name}"
                else:
                    return "Konteyner adı gerekli"
            
            elif operation == "remove":
                if container_name:
                    container = self._client.containers.get(container_name)
                    container.remove()
                    if container_name in self._containers:
                        del self._containers[container_name]
                    return f"Konteyner silindi: {container_name}"
                else:
                    return "Konteyner adı gerekli"
            
            elif operation == "execute":
                if not container_name or not command:
                    return "Konteyner adı ve komut gerekli"
                
                container = self._client.containers.get(container_name)
                result = container.exec_run(command)
                return f"Çıktı:\n{result.output.decode('utf-8')}"
            
            else:
                return f"Desteklenmeyen Docker işlemi: {operation}"
                
        except Exception as e:
            return f"Docker işlemi hatası: {str(e)}"

# Araç örnekleri oluşturma (DockerTool'ü global olarak değil, sadece kullanırken oluşturacağız)
file_tool = FileOperationTool()
terminal_tool = TerminalTool()
package_tool = PackageManagerTool()
code_tool = CodeExecutionTool()
git_tool = GitTool()

# Tüm araçlar listesi (DockerTool'ü dahil etmiyoruz, sadece ihtiyaç olduğunda oluşturulacak)
ALL_TOOLS = [
    file_tool,
    terminal_tool,
    package_tool,
    code_tool,
    git_tool
]

# CrewAI için araç decorator'ları
@tool
def read_file(file_path: str) -> str:
    """Dosya oku"""
    return file_tool._run("read", file_path)

@tool
def write_file(file_path: str, content: str) -> str:
    """Dosya yaz"""
    return file_tool._run("write", file_path, content)

@tool
def list_directory(directory_path: str) -> str:
    """Dizin listele"""
    return file_tool._run("list", directory_path)

@tool
def run_command(command: str, working_dir: str = None) -> str:
    """Terminal komutu çalıştır"""
    return terminal_tool._run(command, working_dir)

@tool
def install_package(package_name: str, manager: str = "pip") -> str:
    """Paket yükle"""
    return package_tool._run("install", package_name, manager)

@tool
def execute_python_code(code: str) -> str:
    """Python kodu çalıştır"""
    return code_tool._run(code, "python")

@tool
def execute_javascript_code(code: str) -> str:
    """JavaScript kodu çalıştır"""
    return code_tool._run(code, "javascript")

@tool
def git_clone(repo_url: str) -> str:
    """Git reposu klonla"""
    return git_tool._run("clone", repo_url)

@tool
def git_commit(message: str) -> str:
    """Git commit yap"""
    return git_tool._run("commit", message=message)

@tool
def create_sandbox_directory(agent_id: str, project_name: str) -> str:
    """Ajan için sandbox dizini oluştur"""
    sandbox_path = f"/tmp/atomagent_{agent_id}_{project_name}"
    os.makedirs(sandbox_path, exist_ok=True)
    return f"Sandbox dizini oluşturuldu: {sandbox_path}"

@tool
def cleanup_sandbox(agent_id: str, project_name: str) -> str:
    """Sandbox temizle"""
    sandbox_path = f"/tmp/atomagent_{agent_id}_{project_name}"
    if os.path.exists(sandbox_path):
        shutil.rmtree(sandbox_path)
        return f"Sandbox temizlendi: {sandbox_path}"
    return f"Sandbox bulunamadı: {sandbox_path}"

# Docker araçlarını dinamik olarak oluşturma fonksiyonu
def get_docker_tool():
    """Docker araçını döndür"""
    return DockerSandboxTool()
