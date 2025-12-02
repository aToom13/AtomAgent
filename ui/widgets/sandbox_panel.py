"""
Sandbox Panel - Agent'ın terminalini canlı izleme
"""
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Static, Label, RichLog
from textual.widget import Widget
from textual.message import Message
from rich.text import Text

from tools.sandbox import (
    get_sandbox_info, get_terminal_history, clear_terminal_history,
    register_terminal_callback, unregister_terminal_callback,
    sandbox_start, sandbox_stop
)
from utils.logger import get_logger

logger = get_logger()


class SandboxTerminal(RichLog):
    """Sandbox terminal çıktısını gösteren widget"""
    
    DEFAULT_CSS = """
    SandboxTerminal {
        height: 1fr;
        background: #1d2021;
        border: solid #3c3836;
        padding: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(highlight=True, markup=True, **kwargs)


class SandboxPanel(Vertical):
    """Agent'ın sandbox terminali paneli"""
    
    DEFAULT_CSS = """
    SandboxPanel {
        height: 100%;
        background: #1d2021;
        padding: 1;
    }
    
    #sandbox-header {
        height: 3;
        background: #282828;
        padding: 1;
        border-bottom: solid #3c3836;
    }
    
    #sandbox-title {
        color: #d3869b;
        text-style: bold;
    }
    
    #sandbox-status-indicator {
        color: #928374;
    }
    
    #sandbox-controls {
        height: auto;
        padding: 1;
        background: #282828;
        border-bottom: solid #3c3836;
    }
    
    #sandbox-controls Button {
        margin-right: 1;
        min-width: 12;
    }
    
    #btn-sandbox-start {
        background: #98971a;
        color: #1d2021;
    }
    
    #btn-sandbox-stop {
        background: #cc241d;
        color: #ebdbb2;
    }
    
    #btn-sandbox-clear {
        background: #458588;
        color: #ebdbb2;
    }
    
    #terminal-container {
        height: 1fr;
        padding: 0;
    }
    
    #sandbox-terminal {
        height: 1fr;
        background: #0d0d0d;
        color: #ebdbb2;
        padding: 1;
        border: solid #3c3836;
    }
    
    #sandbox-footer {
        height: auto;
        padding: 1;
        background: #282828;
        border-top: solid #3c3836;
        color: #928374;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._terminal: SandboxTerminal = None
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="sandbox-header"):
            yield Label("🖥️ Agent Terminali", id="sandbox-title")
            yield Static("", id="sandbox-status-indicator")
        
        with Horizontal(id="sandbox-controls"):
            yield Button("▶ Başlat", id="btn-sandbox-start", variant="success")
            yield Button("⏹ Durdur", id="btn-sandbox-stop", variant="error")
            yield Button("🗑 Temizle", id="btn-sandbox-clear", variant="default")
        
        with Vertical(id="terminal-container"):
            yield SandboxTerminal(id="sandbox-terminal")
        
        yield Static("[dim]Agent komutları burada görünür[/dim]", id="sandbox-footer")
    
    def on_mount(self) -> None:
        self._terminal = self.query_one("#sandbox-terminal", SandboxTerminal)
        
        # Terminal callback kaydet
        register_terminal_callback(self._on_terminal_update)
        
        # Mevcut history'i yükle
        self._load_history()
        
        # Durum güncelle
        self._update_status()
        
        # Periyodik güncelleme
        self.set_interval(3, self._update_status)
    
    def on_unmount(self) -> None:
        unregister_terminal_callback(self._on_terminal_update)
    
    def _on_terminal_update(self, entry: dict):
        """Yeni terminal girişi geldiğinde"""
        self._write_entry(entry)
    
    def _write_entry(self, entry: dict):
        """Terminal girişini yaz"""
        if not self._terminal:
            return
        
        timestamp = entry.get("timestamp", "")
        content = entry.get("content", "")
        entry_type = entry.get("type", "output")
        
        if entry_type == "command":
            # Komut - yeşil
            self._terminal.write(Text(f"[{timestamp}] ", style="dim"))
            self._terminal.write(Text(content, style="bold green"))
        
        elif entry_type == "output":
            # Normal çıktı
            self._terminal.write(Text(content, style="white"))
        
        elif entry_type == "error":
            # Hata - kırmızı
            self._terminal.write(Text(content, style="red"))
        
        elif entry_type == "system":
            # Sistem mesajı - sarı
            self._terminal.write(Text(f"[{timestamp}] {content}", style="yellow italic"))
    
    def _load_history(self):
        """Mevcut history'i yükle"""
        history = get_terminal_history()
        for entry in history:
            self._write_entry(entry)
    
    def _update_status(self):
        """Sandbox durumunu güncelle"""
        try:
            info = get_sandbox_info()
            status = self.query_one("#sandbox-status-indicator", Static)
            
            if info["running"]:
                status.update("[green]● Çalışıyor[/green]")
                self.query_one("#btn-sandbox-start", Button).disabled = True
                self.query_one("#btn-sandbox-stop", Button).disabled = False
            else:
                status.update("[red]● Durdurulmuş[/red]")
                self.query_one("#btn-sandbox-start", Button).disabled = False
                self.query_one("#btn-sandbox-stop", Button).disabled = True
        except Exception as e:
            logger.error(f"Status update error: {e}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        
        if button_id == "btn-sandbox-start":
            await self._start_sandbox()
        
        elif button_id == "btn-sandbox-stop":
            await self._stop_sandbox()
        
        elif button_id == "btn-sandbox-clear":
            self._clear_terminal()
    
    async def _start_sandbox(self):
        """Sandbox başlat"""
        self.query_one("#sandbox-status-indicator", Static).update("[yellow]⏳ Başlatılıyor...[/yellow]")
        self.app.notify("Sandbox başlatılıyor...", severity="information")
        
        # Tool'u çağır
        result = sandbox_start.invoke({})
        
        self._update_status()
        
        if "✓" in result:
            self.app.notify("Sandbox hazır!", severity="information")
        else:
            self.app.notify("Başlatma hatası", severity="error")
    
    async def _stop_sandbox(self):
        """Sandbox durdur"""
        self.query_one("#sandbox-status-indicator", Static).update("[yellow]⏳ Durduruluyor...[/yellow]")
        
        result = sandbox_stop.invoke({})
        
        self._update_status()
        
        if "✓" in result:
            self.app.notify("Sandbox durduruldu", severity="information")
    
    def _clear_terminal(self):
        """Terminal temizle"""
        if self._terminal:
            self._terminal.clear()
        clear_terminal_history()
        self.app.notify("Terminal temizlendi", severity="information")
