"""
Docker Sandbox Tools - Agent'ın izole çalışma ortamı
Terminal tabanlı, tam kontrol
"""
import subprocess
import os
import time
import threading
from datetime import datetime
from typing import Optional, List, Callable
from langchain_core.tools import tool
from config import config
from utils.logger import get_logger

logger = get_logger()

DOCKER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docker")
SHARED_DIR = os.path.join(DOCKER_DIR, "shared")
CONTAINER_NAME = "atomagent-sandbox"

# Terminal history - UI'da göstermek için
_terminal_history: List[dict] = []
_history_callbacks: List[Callable] = []
_max_history = 100


def _add_to_history(entry_type: str, content: str, exit_code: int = None):
    """Terminal geçmişine ekle"""
    entry = {
        "type": entry_type,  # "command", "output", "error", "system"
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "exit_code": exit_code
    }
    _terminal_history.append(entry)
    
    # Max history limit
    if len(_terminal_history) > _max_history:
        _terminal_history.pop(0)
    
    # Callback'leri çağır (UI güncellemesi için)
    for callback in _history_callbacks:
        try:
            callback(entry)
        except:
            pass


def register_terminal_callback(callback: Callable):
    """Terminal güncellemesi için callback kaydet"""
    _history_callbacks.append(callback)


def unregister_terminal_callback(callback: Callable):
    """Callback kaldır"""
    if callback in _history_callbacks:
        _history_callbacks.remove(callback)


def get_terminal_history() -> List[dict]:
    """Terminal geçmişini döndür"""
    return _terminal_history.copy()


def clear_terminal_history():
    """Terminal geçmişini temizle"""
    _terminal_history.clear()
    _add_to_history("system", "Terminal temizlendi")


def _run_docker_command(cmd: list, timeout: int = 60) -> tuple[bool, str]:
    """Docker komutu çalıştır"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=DOCKER_DIR
        )
        output = result.stdout.strip()
        if result.stderr:
            output += f"\n{result.stderr.strip()}"
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)


def _is_container_running() -> bool:
    """Container çalışıyor mu kontrol et"""
    success, output = _run_docker_command([
        "docker", "ps", "-q", "-f", f"name={CONTAINER_NAME}"
    ])
    return success and bool(output.strip())


@tool
def sandbox_start() -> str:
    """
    Agent sandbox ortamını başlatır.
    Ubuntu container ile tam terminal erişimi sağlar.
    
    Returns:
        Başlatma durumu
    """
    logger.info("Starting sandbox...")
    _add_to_history("system", "Sandbox başlatılıyor...")
    
    # Shared klasörü oluştur
    os.makedirs(SHARED_DIR, exist_ok=True)
    
    # Zaten çalışıyor mu?
    if _is_container_running():
        _add_to_history("system", "Sandbox zaten çalışıyor")
        return "✓ Sandbox zaten çalışıyor!"
    
    # Docker Compose ile başlat
    success, output = _run_docker_command([
        "docker-compose", "up", "-d", "--build"
    ], timeout=300)
    
    if not success:
        _add_to_history("error", f"Başlatma hatası: {output}")
        return f"❌ Sandbox başlatılamadı:\n{output}"
    
    # Başlamasını bekle
    time.sleep(3)
    
    if _is_container_running():
        _add_to_history("system", "✓ Sandbox hazır!")
        logger.info("Sandbox started successfully")
        return """✓ Sandbox başlatıldı!

🐧 Ubuntu 22.04 Container (sudo yetkili)
📁 Çalışma dizini: /home/agent/shared (HOST İLE SENKRON!)
🔧 Python, Node.js, Git, Chromium hazır

⚠️ ÖNEMLİ: Tüm dosyaları /home/agent/shared içinde oluştur!
   Bu klasör host'taki docker/shared ile senkronize.

Komut: sandbox_shell("komut")
Dosya: sandbox_upload() / sandbox_download()"""
    
    return "❌ Sandbox başlatıldı ama container çalışmıyor"


@tool
def sandbox_stop() -> str:
    """
    Sandbox ortamını durdurur.
    
    Returns:
        Durdurma durumu
    """
    logger.info("Stopping sandbox...")
    _add_to_history("system", "Sandbox durduruluyor...")
    
    success, output = _run_docker_command(["docker-compose", "down"])
    
    if success:
        _add_to_history("system", "Sandbox durduruldu")
        return "✓ Sandbox durduruldu"
    
    return f"⚠️ Hata: {output}"


@tool
def sandbox_shell(command: str, workdir: str = "/home/agent/shared") -> str:
    """
    Sandbox içinde shell komutu çalıştırır.
    Tam terminal erişimi - istediğin komutu çalıştır.
    
    ÖNEMLİ: Tüm dosya işlemleri /home/agent/shared klasöründe yapılmalı!
    Bu klasör host ile senkronize - dosyalar otomatik görünür.
    
    Args:
        command: Çalıştırılacak komut (örn: "ls -la", "python3 script.py", "sudo apt install vim")
        workdir: Çalışma dizini (varsayılan: /home/agent/shared)
    
    Returns:
        Komut çıktısı
    """
    if not _is_container_running():
        return "❌ Sandbox çalışmıyor. Önce sandbox_start() çalıştır."
    
    # Komutu history'e ekle
    _add_to_history("command", f"[{workdir}]$ {command}")
    logger.info(f"Sandbox shell: {command}")
    
    # Komutu çalıştır (workdir'de)
    full_command = f"cd {workdir} && {command}"
    try:
        result = subprocess.run(
            ["docker", "exec", "-i", CONTAINER_NAME, "bash", "-c", full_command],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=DOCKER_DIR
        )
        
        output = result.stdout
        if result.stderr:
            output += result.stderr
        
        output = output.strip() if output else "(çıktı yok)"
        
        # Çıktıyı history'e ekle
        if result.returncode == 0:
            _add_to_history("output", output, exit_code=0)
        else:
            _add_to_history("error", output, exit_code=result.returncode)
        
        return output
        
    except subprocess.TimeoutExpired:
        _add_to_history("error", "Komut zaman aşımına uğradı (5 dk)")
        return "❌ Timeout (5 dakika)"
    except Exception as e:
        _add_to_history("error", str(e))
        return f"❌ Hata: {e}"


@tool
def sandbox_upload(local_path: str, remote_path: str = None) -> str:
    """
    Dosyayı sandbox'a yükler (host → container).
    
    Args:
        local_path: Yerel dosya yolu (workspace içinde)
        remote_path: Container'daki hedef yol (varsayılan: /home/agent/shared/)
    
    Returns:
        Sonuç
    """
    if not _is_container_running():
        return "❌ Sandbox çalışmıyor."
    
    # Workspace'den tam yol
    full_local = os.path.join(config.workspace.base_dir, local_path)
    
    if not os.path.exists(full_local):
        return f"❌ Dosya bulunamadı: {local_path}"
    
    # Shared klasöre kopyala (volume mount)
    filename = os.path.basename(local_path)
    shared_path = os.path.join(SHARED_DIR, filename)
    
    try:
        import shutil
        if os.path.isdir(full_local):
            shutil.copytree(full_local, shared_path, dirs_exist_ok=True)
        else:
            shutil.copy2(full_local, shared_path)
        
        _add_to_history("system", f"📤 Upload: {local_path} → /home/agent/shared/{filename}")
        return f"✓ Yüklendi: /home/agent/shared/{filename}"
    except Exception as e:
        return f"❌ Hata: {e}"


@tool
def sandbox_download(remote_path: str, local_path: str = None) -> str:
    """
    Dosyayı sandbox'tan indirir (container → host).
    
    Args:
        remote_path: Container'daki dosya yolu
        local_path: Yerel hedef yol (varsayılan: workspace)
    
    Returns:
        Sonuç
    """
    if not _is_container_running():
        return "❌ Sandbox çalışmıyor."
    
    filename = os.path.basename(remote_path)
    
    # Önce shared klasöre kopyala
    copy_cmd = f"cp {remote_path} /home/agent/shared/{filename}"
    result = sandbox_shell.invoke({"command": copy_cmd})
    
    if "❌" in result:
        return result
    
    # Shared'dan workspace'e taşı
    shared_file = os.path.join(SHARED_DIR, filename)
    
    if not os.path.exists(shared_file):
        return f"❌ Dosya kopyalanamadı"
    
    target = local_path or filename
    full_target = os.path.join(config.workspace.base_dir, target)
    
    try:
        import shutil
        shutil.move(shared_file, full_target)
        _add_to_history("system", f"📥 Download: {remote_path} → {target}")
        return f"✓ İndirildi: {target}"
    except Exception as e:
        return f"❌ Hata: {e}"


@tool
def sandbox_status() -> str:
    """
    Sandbox durumunu gösterir.
    
    Returns:
        Durum bilgisi
    """
    if _is_container_running():
        # Sistem bilgisi al
        info = sandbox_shell.invoke({"command": "uname -a && python3 --version && node --version"})
        return f"""🖥️ Sandbox: ✅ Çalışıyor

{info}

📁 Shared: /home/agent/shared
🔧 Komut: sandbox_shell("...")"""
    
    return "🖥️ Sandbox: ⏹️ Durdurulmuş\n\nBaşlatmak için: sandbox_start()"


def get_sandbox_info() -> dict:
    """Sandbox bilgilerini döndür (UI için)"""
    return {
        "running": _is_container_running(),
        "history_count": len(_terminal_history),
        "shared_dir": SHARED_DIR
    }
