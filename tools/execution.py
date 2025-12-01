"""
Terminal Command Execution with Permission System
"""
from langchain_core.tools import tool
import subprocess
import shlex
import os
from config import config
from utils.logger import get_logger

WORKSPACE_DIR = config.workspace.base_dir
logger = get_logger()

# Runtime'da eklenen izinli komutlar
_runtime_allowed_commands = set()

# Bekleyen komut onayları (UI tarafından kontrol edilir)
_pending_command = None
_command_callback = None


class CommandPermissionRequired(Exception):
    """Komut için izin gerektiğinde fırlatılır"""
    def __init__(self, command: str, base_cmd: str):
        self.command = command
        self.base_cmd = base_cmd
        super().__init__(f"Permission required for: {base_cmd}")


def add_allowed_command(cmd: str):
    """Runtime'da izinli komut ekler"""
    _runtime_allowed_commands.add(cmd)
    logger.info(f"Command added to allowed list: {cmd}")


def get_all_allowed_commands() -> list:
    """Tüm izinli komutları döndürür"""
    return list(config.execution.allowed_commands) + list(_runtime_allowed_commands)


def set_command_callback(callback):
    """UI'dan komut onay callback'i ayarlar"""
    global _command_callback
    _command_callback = callback


def _is_command_safe(command: str) -> tuple[bool, str, str]:
    """
    Komutu güvenlik açısından kontrol eder.
    Returns: (is_safe, reason, base_cmd)
    """
    # Blocked patterns kontrolü
    for pattern in config.execution.blocked_patterns:
        if pattern.lower() in command.lower():
            return False, f"Blocked: {pattern}", ""
    
    # Tehlikeli karakterler
    dangerous_chars = [';', '&&', '||', '`', '$(']
    for char in dangerous_chars:
        if char in command:
            return False, f"Dangerous: {char}", ""
    
    # İlk komutun allowed listesinde olup olmadığını kontrol et
    try:
        parts = shlex.split(command)
        if parts:
            base_cmd = os.path.basename(parts[0])
            all_allowed = get_all_allowed_commands()
            
            if base_cmd not in all_allowed:
                return False, f"Not allowed: {base_cmd}", base_cmd
    except ValueError:
        return False, "Invalid syntax", ""
    
    return True, "OK", ""


def execute_command_direct(command: str) -> str:
    """Komutu direkt çalıştırır (güvenlik kontrolü yapılmış varsayılır)"""
    try:
        if not os.path.exists(WORKSPACE_DIR):
            os.makedirs(WORKSPACE_DIR)
        
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=config.execution.command_timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[STDERR]\n{result.stderr}"
            
        if not output.strip():
            output = "✓ OK"
        
        # Kısalt
        if len(output) > 1000:
            output = output[:1000] + "\n...[truncated]"
        
        return output
        
    except subprocess.TimeoutExpired:
        return f"⏱ Timeout ({config.execution.command_timeout}s)"
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
def run_terminal_command(command: str) -> str:
    """
    Executes a terminal command in the workspace.
    
    Args:
        command: Command to execute (e.g., 'python script.py')
        
    Returns:
        Command output or error message
    """
    logger.info(f"Command: {command}")
    
    # Güvenlik kontrolü
    is_safe, reason, base_cmd = _is_command_safe(command)
    
    if not is_safe:
        if base_cmd:
            # İzin gerekiyor - özel mesaj döndür
            logger.warning(f"Permission needed: {base_cmd}")
            return f"⚠️ PERMISSION_REQUIRED:{base_cmd}:{command}"
        else:
            # Tamamen engellendi
            logger.warning(f"Blocked: {command}")
            return f"❌ {reason}"
    
    # Güvenli, çalıştır
    return execute_command_direct(command)
