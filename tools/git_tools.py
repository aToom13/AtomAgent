"""
Git Tools - Version control integration
"""
import subprocess
import os
from langchain_core.tools import tool
from config import config
from utils.logger import get_logger

WORKSPACE_DIR = config.workspace.base_dir
logger = get_logger()


def _run_git(args: list, cwd: str = None) -> tuple[bool, str]:
    """Run git command and return (success, output)"""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or WORKSPACE_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout.strip()
        if result.stderr and result.returncode != 0:
            output += f"\n{result.stderr.strip()}"
        return result.returncode == 0, output or "OK"
    except FileNotFoundError:
        return False, "Git yüklü değil"
    except subprocess.TimeoutExpired:
        return False, "Git komutu zaman aşımına uğradı"
    except Exception as e:
        return False, f"Hata: {e}"


@tool
def git_init() -> str:
    """
    Workspace'te yeni git repository başlatır.
    Eğer zaten varsa bilgi verir.
    """
    git_dir = os.path.join(WORKSPACE_DIR, ".git")
    if os.path.exists(git_dir):
        return "Git repository zaten mevcut"
    
    success, output = _run_git(["init"])
    if success:
        logger.info("Git repository initialized")
        return "✓ Git repository oluşturuldu"
    return f"✗ {output}"


@tool
def git_status() -> str:
    """
    Git durumunu gösterir.
    Değişen, eklenen, silinen dosyaları listeler.
    """
    success, output = _run_git(["status", "--short"])
    if not success:
        if "not a git repository" in output.lower():
            return "Git repository yok. Önce git_init() çalıştırın."
        return f"✗ {output}"
    
    if not output:
        return "✓ Çalışma dizini temiz - değişiklik yok"
    
    # Parse status
    lines = output.split("\n")
    result = ["📊 Git Durumu:", ""]
    
    for line in lines:
        if line.startswith("??"):
            result.append(f"  🆕 {line[3:]} (yeni)")
        elif line.startswith("M ") or line.startswith(" M"):
            result.append(f"  📝 {line[3:]} (değişti)")
        elif line.startswith("A "):
            result.append(f"  ➕ {line[3:]} (eklendi)")
        elif line.startswith("D ") or line.startswith(" D"):
            result.append(f"  🗑️ {line[3:]} (silindi)")
        elif line.startswith("R "):
            result.append(f"  📛 {line[3:]} (yeniden adlandırıldı)")
        else:
            result.append(f"  {line}")
    
    return "\n".join(result)


@tool
def git_add(files: str = ".") -> str:
    """
    Dosyaları staging area'ya ekler.
    
    Args:
        files: Eklenecek dosyalar. "." tüm dosyalar, veya "file1.py file2.py" gibi
    """
    file_list = files.split() if files != "." else ["."]
    success, output = _run_git(["add"] + file_list)
    
    if success:
        logger.info(f"Git add: {files}")
        return f"✓ Dosyalar eklendi: {files}"
    return f"✗ {output}"


@tool
def git_commit(message: str) -> str:
    """
    Değişiklikleri commit eder.
    
    Args:
        message: Commit mesajı (açıklayıcı olmalı)
    """
    if not message or len(message) < 3:
        return "✗ Commit mesajı çok kısa"
    
    # Check if there's anything to commit
    success, status = _run_git(["status", "--porcelain"])
    if success and not status:
        return "Commit edilecek değişiklik yok"
    
    success, output = _run_git(["commit", "-m", message])
    
    if success:
        logger.info(f"Git commit: {message[:50]}")
        return f"✓ Commit yapıldı: {message}"
    
    if "nothing to commit" in output.lower():
        return "Commit edilecek değişiklik yok"
    if "please tell me who you are" in output.lower():
        return "✗ Git kullanıcı bilgisi ayarlanmamış. Şunu çalıştırın:\ngit config user.email 'you@example.com'\ngit config user.name 'Your Name'"
    
    return f"✗ {output}"


@tool
def git_log(count: int = 5) -> str:
    """
    Son commit'leri gösterir.
    
    Args:
        count: Gösterilecek commit sayısı (varsayılan 5)
    """
    success, output = _run_git([
        "log", 
        f"-{count}", 
        "--oneline",
        "--decorate"
    ])
    
    if not success:
        if "not a git repository" in output.lower():
            return "Git repository yok"
        if "does not have any commits" in output.lower():
            return "Henüz commit yok"
        return f"✗ {output}"
    
    if not output:
        return "Henüz commit yok"
    
    lines = output.split("\n")
    result = ["📜 Son Commit'ler:", ""]
    for line in lines:
        result.append(f"  • {line}")
    
    return "\n".join(result)


@tool
def git_diff(file: str = None) -> str:
    """
    Değişiklikleri gösterir.
    
    Args:
        file: Belirli dosya (opsiyonel). None ise tüm değişiklikler.
    """
    args = ["diff", "--stat"]
    if file:
        args.append(file)
    
    success, output = _run_git(args)
    
    if not success:
        return f"✗ {output}"
    
    if not output:
        # Try staged changes
        args = ["diff", "--cached", "--stat"]
        if file:
            args.append(file)
        success, output = _run_git(args)
        
        if not output:
            return "Değişiklik yok"
    
    return f"📊 Değişiklikler:\n{output}"


@tool
def git_branch(name: str = None) -> str:
    """
    Branch işlemleri.
    
    Args:
        name: Yeni branch adı (opsiyonel). None ise mevcut branch'leri listeler.
    """
    if name:
        # Create new branch
        success, output = _run_git(["checkout", "-b", name])
        if success:
            logger.info(f"Git branch created: {name}")
            return f"✓ Yeni branch oluşturuldu: {name}"
        if "already exists" in output.lower():
            # Switch to existing branch
            success, output = _run_git(["checkout", name])
            if success:
                return f"✓ Branch'e geçildi: {name}"
        return f"✗ {output}"
    else:
        # List branches
        success, output = _run_git(["branch", "-a"])
        if not success:
            return f"✗ {output}"
        
        if not output:
            return "Henüz branch yok"
        
        return f"🌿 Branch'ler:\n{output}"


@tool
def git_stash(action: str = "push") -> str:
    """
    Değişiklikleri geçici olarak saklar veya geri yükler.
    
    Args:
        action: "push" (sakla), "pop" (geri yükle), "list" (listele)
    """
    if action == "push":
        success, output = _run_git(["stash", "push", "-m", "Auto stash"])
        if success:
            return "✓ Değişiklikler saklandı"
        return f"✗ {output}"
    
    elif action == "pop":
        success, output = _run_git(["stash", "pop"])
        if success:
            return "✓ Değişiklikler geri yüklendi"
        if "No stash entries" in output:
            return "Saklanan değişiklik yok"
        return f"✗ {output}"
    
    elif action == "list":
        success, output = _run_git(["stash", "list"])
        if not output:
            return "Saklanan değişiklik yok"
        return f"📦 Saklanan değişiklikler:\n{output}"
    
    return f"Bilinmeyen action: {action}. Kullanım: push, pop, list"


@tool
def git_reset(mode: str = "soft") -> str:
    """
    Son commit'i geri alır.
    
    Args:
        mode: "soft" (değişiklikler korunur), "hard" (değişiklikler silinir)
    """
    if mode not in ["soft", "hard"]:
        return "Mode 'soft' veya 'hard' olmalı"
    
    success, output = _run_git(["reset", f"--{mode}", "HEAD~1"])
    
    if success:
        logger.info(f"Git reset: {mode}")
        if mode == "soft":
            return "✓ Son commit geri alındı (değişiklikler korundu)"
        return "✓ Son commit geri alındı (değişiklikler silindi)"
    
    return f"✗ {output}"
