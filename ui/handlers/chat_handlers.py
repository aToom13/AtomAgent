"""
Chat Handlers - Agent ile iletişim ve mesaj yönetimi
"""
from datetime import datetime
from rich.text import Text
from textual.widgets import Static, TabbedContent
from langchain_core.messages import HumanMessage, SystemMessage

from utils.logger import get_logger

logger = get_logger()


class ChatHandler:
    """Chat ve agent iletişimini yöneten sınıf"""
    
    def __init__(self, app):
        self.app = app
    
    def get_timestamp(self) -> str:
        """Zaman damgası döndür"""
        return datetime.now().strftime("%H:%M")
    
    def create_user_message(self, text: str) -> Text:
        """Kullanıcı mesajı oluştur"""
        timestamp = self.get_timestamp()
        msg = Text()
        msg.append(f"[{timestamp}] Sen: ", style="bold green")
        msg.append(text)
        return msg
    
    def create_agent_message(self, text: str, style: str = "bold cyan") -> Text:
        """Agent mesajı oluştur"""
        timestamp = self.get_timestamp()
        msg = Text()
        msg.append(f"[{timestamp}] Agent: ", style=style)
        msg.append(text)
        return msg
    
    def create_thinking_message(self) -> Text:
        """Düşünüyor mesajı oluştur"""
        timestamp = self.get_timestamp()
        return Text(f"[{timestamp}] Agent: Düşünüyor...", style="italic")
    
    def create_error_message(self, error: str) -> Text:
        """Hata mesajı oluştur"""
        msg = Text()
        msg.append("Hata: ", style="bold red")
        msg.append(str(error))
        return msg
    
    async def process_stream_chunk(self, chunk_content: str, final_text: str, 
                                    ai_response: Static, chat) -> str:
        """Stream chunk'ını işle"""
        # JSON içeriği filtrele
        if '{"' not in chunk_content and '"}' not in chunk_content:
            final_text += chunk_content
            
            text = Text()
            text.append(f"[{self.get_timestamp()}] Agent: ", style="bold cyan")
            text.append(final_text)
            ai_response.update(text)
            chat.scroll_end()
        
        return final_text
    
    async def handle_tool_start(self, tool_name: str, run_id: str, 
                                 dashboard, loading_widgets: dict,
                                 tool_handler) -> None:
        """Tool başlangıcını işle"""
        status, color = tool_handler.get_status(tool_name)
        self.app._update_status(status, color)
        
        loading = Static(f"[yellow]⚙️ {tool_name}...[/yellow]", classes="loading-card")
        loading_widgets[run_id] = loading
        await dashboard.mount(loading)
    
    async def handle_tool_end(self, tool_name: str, run_id: str, output: str,
                               dashboard, loading_widgets: dict,
                               tool_handler) -> bool:
        """Tool bitişini işle. Permission gerekiyorsa True döner."""
        # Loading widget'ı kaldır
        if run_id in loading_widgets:
            await loading_widgets[run_id].remove()
            del loading_widgets[run_id]
        
        # Permission kontrolü (emoji ile veya emoji olmadan)
        if "PERMISSION_REQUIRED:" in output:
            # "⚠️ PERMISSION_REQUIRED:cmd:full_cmd" formatını parse et
            perm_idx = output.find("PERMISSION_REQUIRED:")
            perm_part = output[perm_idx:]  # "PERMISSION_REQUIRED:cmd:full_cmd"
            parts = perm_part.split(":")
            if len(parts) >= 3:
                base_cmd = parts[1]
                full_cmd = ":".join(parts[2:])
                await self.app._show_permission_dialog(base_cmd, full_cmd)
                return True
        
        # Tool çıktısını işle
        await tool_handler.handle(tool_name, output, dashboard)
        
        # Todo'yu güncelle
        self.app._refresh_todo()
        
        return False
    
    def finalize_response(self, final_text: str, ai_response: Static) -> None:
        """Yanıtı sonlandır"""
        if not final_text:
            final_text = "✓ Tamamlandı"
        
        text = Text()
        text.append(f"[{self.get_timestamp()}] Agent: ", style="bold cyan")
        text.append(final_text)
        ai_response.update(text)
        self.app._update_status("Ready", "dim")
