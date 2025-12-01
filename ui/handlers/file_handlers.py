"""
File Handlers - Dosya işlemleri (açma, kaydetme, çalıştırma)
"""
import os
import subprocess
from textual.widgets import DirectoryTree, TextArea, Label, TabbedContent, Static

from config import config
from utils.logger import get_logger

logger = get_logger()
WORKSPACE_DIR = config.workspace.base_dir

# Dosya uzantısı -> dil eşlemesi
LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".json": "json", ".md": "markdown", ".html": "html",
    ".css": "css", ".yaml": "yaml", ".sh": "bash"
}

# Dosya uzantısı -> çalıştırma komutu
RUN_CMD_MAP = {".py": "python", ".js": "node"}


class FileHandler:
    """Dosya işlemlerini yöneten sınıf"""
    
    def __init__(self, app):
        self.app = app
        self.current_file_path = None
    
    def open_file(self, file_path: str) -> bool:
        """Dosyayı editörde aç"""
        if not os.path.isfile(file_path):
            return False
        
        self.current_file_path = file_path
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            ext = os.path.splitext(file_path)[1].lower()
            
            editor = self.app.query_one("#code-editor", TextArea)
            editor.text = content
            editor.language = LANG_MAP.get(ext, "python")
            
            self.app.query_one("#editor-header", Label).update(
                f"📄 {os.path.basename(file_path)}"
            )
            self.app.query_one(TabbedContent).active = "tab-editor"
            
            return True
            
        except Exception as e:
            logger.error(f"File open error: {e}")
            self.app.notify(f"Hata: {e}", severity="error")
            return False
    
    def save_file(self) -> bool:
        """Mevcut dosyayı kaydet"""
        if not self.current_file_path:
            return False
        
        try:
            editor = self.app.query_one("#code-editor", TextArea)
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(editor.text)
            
            self.app.notify(f"Kaydedildi: {os.path.basename(self.current_file_path)}")
            return True
            
        except Exception as e:
            logger.error(f"File save error: {e}")
            self.app.notify(f"Hata: {e}", severity="error")
            return False
    
    def run_file(self, dashboard) -> bool:
        """Mevcut dosyayı çalıştır"""
        if not self.current_file_path:
            return False
        
        filename = os.path.basename(self.current_file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext not in RUN_CMD_MAP:
            return False
        
        try:
            result = subprocess.run(
                f"{RUN_CMD_MAP[ext]} {filename}",
                shell=True, cwd=WORKSPACE_DIR,
                capture_output=True, text=True, timeout=10
            )
            
            output = result.stdout or "[Çıktı yok]"
            if result.stderr:
                output += f"\n[red]{result.stderr}[/red]"
            
            dashboard.mount(Static(
                f"[cyan]▶ {filename}:[/cyan]\n{output}",
                classes="tool-card"
            ))
            return True
            
        except subprocess.TimeoutExpired:
            dashboard.mount(Static(
                f"[red]Timeout: {filename} 10 saniyede tamamlanmadı[/red]",
                classes="error-msg"
            ))
            return False
        except Exception as e:
            logger.error(f"File run error: {e}")
            dashboard.mount(Static(f"[red]Hata: {e}[/red]", classes="error-msg"))
            return False
