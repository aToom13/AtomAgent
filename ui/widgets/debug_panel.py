"""
Debug Panel Widget - Agent aktivitelerini ve logları gösterir
"""
from textual.widgets import Static, RichLog
from textual.containers import Vertical
from rich.text import Text
from datetime import datetime
from collections import deque


class DebugLogWidget(RichLog):
    """Debug loglarını gösteren widget"""
    
    def __init__(self, max_lines: int = 100, **kwargs):
        super().__init__(max_lines=max_lines, wrap=True, highlight=True, **kwargs)
        self.log_history = deque(maxlen=max_lines)
    
    def log_info(self, message: str):
        """Info log ekle"""
        self._add_log("INFO", message, "cyan")
    
    def log_success(self, message: str):
        """Success log ekle"""
        self._add_log("OK", message, "green")
    
    def log_warning(self, message: str):
        """Warning log ekle"""
        self._add_log("WARN", message, "yellow")
    
    def log_error(self, message: str):
        """Error log ekle"""
        self._add_log("ERR", message, "red")
    
    def log_tool(self, tool_name: str, status: str = "start"):
        """Tool log ekle"""
        if status == "start":
            self._add_log("TOOL", f"▶ {tool_name}", "magenta")
        elif status == "end":
            self._add_log("TOOL", f"✓ {tool_name}", "green")
        elif status == "error":
            self._add_log("TOOL", f"✗ {tool_name}", "red")
    
    def log_agent(self, agent_name: str, action: str):
        """Agent log ekle"""
        self._add_log("AGENT", f"{agent_name}: {action}", "blue")
    
    def _add_log(self, level: str, message: str, color: str):
        """Log ekle"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        text = Text()
        text.append(f"[{timestamp}] ", style="dim")
        text.append(f"[{level}] ", style=f"bold {color}")
        text.append(message)
        
        self.write(text)
        self.log_history.append({
            "time": timestamp,
            "level": level,
            "message": message
        })
    
    def get_recent_logs(self, count: int = 10) -> list:
        """Son logları döndür"""
        return list(self.log_history)[-count:]
    
    def export_logs(self) -> str:
        """Logları text olarak export et"""
        lines = []
        for log in self.log_history:
            lines.append(f"[{log['time']}] [{log['level']}] {log['message']}")
        return "\n".join(lines)


class AgentStateWidget(Static):
    """Agent durumunu gösteren widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = {
            "status": "idle",
            "current_task": None,
            "tools_used": 0,
            "errors": 0,
            "start_time": None
        }
        self.models = {
            "supervisor": ("unknown", "unknown"),
            "coder": ("unknown", "unknown"),
            "researcher": ("unknown", "unknown")
        }
    
    def set_idle(self):
        """Boşta durumuna geç"""
        self.state["status"] = "idle"
        self.state["current_task"] = None
        self._update_display()
    
    def set_thinking(self, task: str = ""):
        """Düşünüyor durumuna geç"""
        self.state["status"] = "thinking"
        self.state["current_task"] = task
        self.state["start_time"] = datetime.now()
        self._update_display()
    
    def set_working(self, task: str = ""):
        """Çalışıyor durumuna geç"""
        self.state["status"] = "working"
        self.state["current_task"] = task
        self._update_display()
    
    def set_error(self, error: str = ""):
        """Hata durumuna geç"""
        self.state["status"] = "error"
        self.state["errors"] += 1
        self._update_display()
    
    def increment_tools(self):
        """Tool sayacını artır"""
        self.state["tools_used"] += 1
        self._update_display()
    
    def reset_stats(self):
        """İstatistikleri sıfırla"""
        self.state["tools_used"] = 0
        self.state["errors"] = 0
        self.state["start_time"] = None
        self._update_display()
    
    def update_models(self):
        """Model bilgilerini güncelle"""
        try:
            from core.providers import model_manager
            for role in ["supervisor", "coder", "researcher"]:
                provider, model = model_manager.get_current_provider_info(role)
                if provider and model:
                    # Model adını kısalt
                    short_model = model.split("/")[-1] if "/" in model else model
                    if len(short_model) > 25:
                        short_model = short_model[:22] + "..."
                    self.models[role] = (provider, short_model)
        except:
            pass
        self._update_display()
    
    def _update_display(self):
        """Görüntüyü güncelle"""
        text = Text()
        text.append("🤖 Agent Durumu\n", style="bold cyan")
        
        # Status
        status = self.state["status"]
        if status == "idle":
            text.append("  Durum: ", style="dim")
            text.append("⚪ Boşta\n", style="dim")
        elif status == "thinking":
            text.append("  Durum: ", style="dim")
            text.append("🟡 Düşünüyor\n", style="yellow")
        elif status == "working":
            text.append("  Durum: ", style="dim")
            text.append("🟢 Çalışıyor\n", style="green")
        elif status == "error":
            text.append("  Durum: ", style="dim")
            text.append("🔴 Hata\n", style="red")
        
        # Current task
        if self.state["current_task"]:
            task = self.state["current_task"][:40]
            text.append(f"  Görev: {task}\n", style="dim")
        
        # Stats
        text.append(f"  Tools: {self.state['tools_used']}", style="dim")
        if self.state["errors"] > 0:
            text.append(f" | Hatalar: {self.state['errors']}", style="red")
        
        # Elapsed time
        if self.state["start_time"]:
            elapsed = (datetime.now() - self.state["start_time"]).total_seconds()
            text.append(f" | Süre: {elapsed:.1f}s", style="dim")
        
        # Model bilgileri
        text.append("\n\n🔧 Aktif Modeller\n", style="bold cyan")
        for role, (provider, model) in self.models.items():
            role_icon = {"supervisor": "👔", "coder": "💻", "researcher": "🔍"}.get(role, "•")
            role_name = {"supervisor": "Supervisor", "coder": "Coder", "researcher": "Researcher"}.get(role, role)
            
            if provider != "unknown":
                text.append(f"  {role_icon} {role_name}: ", style="dim")
                text.append(f"{provider}", style="green")
                text.append(f"/{model}\n", style="yellow")
            else:
                text.append(f"  {role_icon} {role_name}: ", style="dim")
                text.append("yüklenmedi\n", style="dim")
        
        self.update(text)


class MemoryUsageWidget(Static):
    """Memory/Context kullanımını gösteren widget"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.usage = {
            "messages": 0,
            "tokens_estimate": 0,
            "rag_chunks": 0
        }
    
    def update_usage(self, messages: int = 0, tokens: int = 0, rag_chunks: int = 0):
        """Kullanımı güncelle"""
        self.usage["messages"] = messages
        self.usage["tokens_estimate"] = tokens
        self.usage["rag_chunks"] = rag_chunks
        self._update_display()
    
    def _update_display(self):
        """Görüntüyü güncelle"""
        text = Text()
        text.append("📊 Context Kullanımı\n", style="bold cyan")
        
        # Messages
        msg_count = self.usage["messages"]
        text.append(f"  Mesajlar: {msg_count}\n", style="dim")
        
        # Token estimate
        tokens = self.usage["tokens_estimate"]
        if tokens > 0:
            # Token bar (max 8000 varsayalım)
            max_tokens = 8000
            usage_pct = min(tokens / max_tokens, 1.0)
            bar_width = 15
            filled = int(bar_width * usage_pct)
            
            text.append("  Tokens: [", style="dim")
            
            if usage_pct > 0.8:
                bar_color = "red"
            elif usage_pct > 0.5:
                bar_color = "yellow"
            else:
                bar_color = "green"
            
            text.append("█" * filled, style=bar_color)
            text.append("░" * (bar_width - filled), style="dim")
            text.append(f"] ~{tokens}\n", style="dim")
        
        # RAG chunks
        if self.usage["rag_chunks"] > 0:
            text.append(f"  RAG: {self.usage['rag_chunks']} chunk\n", style="dim")
        
        self.update(text)
