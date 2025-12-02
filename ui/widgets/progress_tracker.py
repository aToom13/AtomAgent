"""
Progress Tracker Widget - Görev ilerlemesini görsel olarak gösterir
"""
from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from datetime import datetime


class TaskProgressWidget(Static):
    """Görev ilerlemesini gösteren widget"""
    
    current_step = reactive(0)
    total_steps = reactive(0)
    current_message = reactive("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.steps_history = []
        self.start_time = None
    
    def start_task(self, task_name: str, total_steps: int = 0):
        """Yeni görev başlat"""
        self.current_step = 0
        self.total_steps = total_steps
        self.current_message = task_name
        self.steps_history = []
        self.start_time = datetime.now()
        self._update_display()
    
    def update_step(self, step: int, message: str):
        """Adım güncelle"""
        self.current_step = step
        self.current_message = message
        self.steps_history.append({
            "step": step,
            "message": message,
            "time": datetime.now()
        })
        self._update_display()
    
    def increment_step(self, message: str = ""):
        """Bir sonraki adıma geç"""
        self.current_step += 1
        if message:
            self.current_message = message
        self.steps_history.append({
            "step": self.current_step,
            "message": message,
            "time": datetime.now()
        })
        self._update_display()
    
    def complete_task(self, message: str = "Tamamlandı"):
        """Görevi tamamla"""
        self.current_step = self.total_steps if self.total_steps > 0 else self.current_step
        self.current_message = message
        self._update_display(completed=True)
    
    def fail_task(self, error: str):
        """Görev başarısız"""
        self.current_message = f"❌ {error}"
        self._update_display(failed=True)
    
    def _update_display(self, completed: bool = False, failed: bool = False):
        """Görüntüyü güncelle"""
        text = Text()
        
        # Progress bar
        if self.total_steps > 0:
            progress = self.current_step / self.total_steps
            bar_width = 20
            filled = int(bar_width * progress)
            empty = bar_width - filled
            
            if completed:
                bar_char = "█"
                bar_style = "green"
            elif failed:
                bar_char = "█"
                bar_style = "red"
            else:
                bar_char = "█"
                bar_style = "yellow"
            
            text.append("[", style="dim")
            text.append(bar_char * filled, style=bar_style)
            text.append("░" * empty, style="dim")
            text.append("]", style="dim")
            text.append(f" {self.current_step}/{self.total_steps}", style="cyan")
        else:
            # Belirsiz progress (spinner tarzı)
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            spinner_idx = self.current_step % len(spinner_chars)
            
            if completed:
                text.append("✅ ", style="green")
            elif failed:
                text.append("❌ ", style="red")
            else:
                text.append(f"{spinner_chars[spinner_idx]} ", style="yellow")
        
        # Mesaj
        text.append(f" {self.current_message}")
        
        # Geçen süre
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            if elapsed > 1:
                text.append(f" ({elapsed:.1f}s)", style="dim")
        
        self.update(text)
    
    def get_summary(self) -> str:
        """Görev özetini döndür"""
        if not self.steps_history:
            return "Henüz adım yok"
        
        lines = ["📋 Görev Özeti:"]
        for item in self.steps_history[-5:]:  # Son 5 adım
            lines.append(f"  • {item['message']}")
        
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            lines.append(f"\n⏱ Toplam süre: {elapsed:.1f}s")
        
        return "\n".join(lines)


class ToolActivityWidget(Static):
    """Tool aktivitelerini gösteren widget"""
    
    def __init__(self, max_items: int = 10, **kwargs):
        super().__init__(**kwargs)
        self.activities = []
        self.max_items = max_items
    
    def add_activity(self, tool_name: str, status: str = "running"):
        """Aktivite ekle"""
        activity = {
            "tool": tool_name,
            "status": status,
            "time": datetime.now()
        }
        self.activities.append(activity)
        
        # Maksimum sayıyı aşarsa eski olanları sil
        if len(self.activities) > self.max_items:
            self.activities = self.activities[-self.max_items:]
        
        self._update_display()
    
    def update_activity(self, tool_name: str, status: str):
        """Aktivite durumunu güncelle"""
        for activity in reversed(self.activities):
            if activity["tool"] == tool_name and activity["status"] == "running":
                activity["status"] = status
                break
        self._update_display()
    
    def clear(self):
        """Aktiviteleri temizle"""
        self.activities = []
        self._update_display()
    
    def _update_display(self):
        """Görüntüyü güncelle"""
        if not self.activities:
            self.update("[dim]Aktivite yok[/dim]")
            return
        
        text = Text()
        text.append("🔧 Tool Aktiviteleri\n", style="bold cyan")
        
        for activity in self.activities[-5:]:  # Son 5 aktivite
            status = activity["status"]
            tool = activity["tool"]
            
            if status == "running":
                text.append("  ⚙️ ", style="yellow")
            elif status == "success":
                text.append("  ✅ ", style="green")
            elif status == "error":
                text.append("  ❌ ", style="red")
            else:
                text.append("  • ", style="dim")
            
            text.append(f"{tool}\n")
        
        self.update(text)
