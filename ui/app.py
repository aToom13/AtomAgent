"""
AtomAgent UI - Modern Terminal Interface
v4.1 - Modular Architecture
"""
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll, Container
from textual.widgets import (
    Footer, Input, Markdown, Label, Static,
    TabbedContent, TabPane, DirectoryTree, TextArea, Button
)
from textual.binding import Binding
from rich.text import Text
from langchain_core.messages import HumanMessage, SystemMessage
from datetime import datetime

from core.agent import get_agent_executor, get_thread_config
from core.providers import model_manager, get_api_key_info, get_all_api_keys
from config import config
from utils.logger import get_logger
from tools.todo_tools import get_todo_content
from tools.execution import add_allowed_command, execute_command_direct
from ui.styles import APP_CSS
from ui.handlers import ToolOutputHandler, FileHandler, ChatHandler
from ui.widgets import ModelSelectorModal, apply_saved_settings, FallbackSelectorModal

logger = get_logger()
WORKSPACE_DIR = config.workspace.base_dir


class AtomAgentApp(App):
    """AtomAgent - AI-Powered Development Assistant"""

    CSS = APP_CSS
    TITLE = "AtomAgent"
    SUB_TITLE = "AI Development Assistant"

    BINDINGS = [
        Binding("ctrl+c", "request_quit", "Quit", priority=True),
        Binding("ctrl+s", "save_file", "Save"),
        Binding("f5", "run_file", "Run"),
        Binding("ctrl+l", "clear_chat", "Clear Chat"),
        Binding("ctrl+r", "refresh_workspace", "Refresh"),
        Binding("ctrl+shift+c", "copy_last", "Copy Last"),
        Binding("ctrl+y", "copy_last", "Copy"),
    ]

    def __init__(self):
        super().__init__()
        
        # Kaydedilmiş ayarları yükle
        apply_saved_settings()
        
        self.agent_executor, _, self.system_prompt = get_agent_executor()
        self.loading_widgets = {}
        self.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.message_history = []
        self.pending_command = None
        self.quit_requested = False
        self._last_ai_response = ""  # Son AI yanıtını sakla

        # Handlers
        self.tool_handler = ToolOutputHandler(self)
        self.file_handler = FileHandler(self)
        self.chat_handler = ChatHandler(self)

        logger.info("AtomAgent started")

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            # Left Panel - Chat
            with Vertical(id="left-panel"):
                yield Label("🤖 ATOMAGENT", id="chat-header")
                yield VerticalScroll(id="chat-scroll")
                # Status/Permission bar - dinamik olarak değişir
                with Vertical(id="status-container"):
                    yield Static("[dim]Ready[/dim]", id="status-bar")
                with Container(id="input-container"):
                    yield Input(placeholder="Mesajınızı yazın...", id="user-input")

            # Right Panel - Dashboard
            with Vertical(id="right-panel"):
                with TabbedContent():
                    with TabPane("� Darshboard", id="tab-dashboard"):
                        yield VerticalScroll(id="dashboard-view")

                    with TabPane("📁 Workspace", id="tab-workspace"):
                        with Vertical(id="workspace-container"):
                            yield Label("WORKSPACE", id="workspace-header")
                            yield DirectoryTree(WORKSPACE_DIR, id="workspace-tree")

                    with TabPane("✅ Todo", id="tab-todo"):
                        with VerticalScroll(id="todo-scroll"):
                            yield Markdown("*Görev yok*", id="todo-area")

                    with TabPane("📝 Editor", id="tab-editor"):
                        with Vertical(id="editor-container"):
                            yield Label("Dosya açık değil", id="editor-header")
                            yield TextArea(
                                language="python",
                                show_line_numbers=True,
                                id="code-editor",
                                theme="monokai"
                            )

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#user-input").focus()
        self._add_system_message("AtomAgent hazır! 🚀")
        self._refresh_todo()
        self._show_model_info()
    
    def _show_model_info(self):
        """Dashboard'da aktif model ve API key bilgisini göster"""
        dashboard = self.query_one("#dashboard-view")
        
        # Eski kartları kaldır (tümünü)
        for card in list(self.query(".model-info-card")):
            card.remove()
        
        # Model bilgisi kartı
        supervisor = model_manager.get_config("supervisor")
        coder = model_manager.get_config("coder")
        researcher = model_manager.get_config("researcher")
        
        model_info = f"""[bold cyan]🤖 Aktif Modeller[/bold cyan]
[green]Supervisor:[/green] {supervisor.provider}/{supervisor.model}
[green]Coder:[/green] {coder.provider}/{coder.model}
[green]Researcher:[/green] {researcher.provider}/{researcher.model}

[dim]Model değiştirmek için :model yazın[/dim]"""
        
        dashboard.mount(Static(model_info, classes="tool-card model-info-card"))
        
        # API Key durumu kartı
        self._show_api_key_status(dashboard)
    
    def _show_api_key_status(self, dashboard=None):
        """API key durumunu göster"""
        if dashboard is None:
            dashboard = self.query_one("#dashboard-view")
        
        # Eski kartı kaldır
        for card in list(self.query(".api-key-card")):
            card.remove()
        
        # Aktif provider'ları bul
        providers_in_use = set()
        for role in ["supervisor", "coder", "researcher"]:
            config = model_manager.get_config(role)
            if config:
                providers_in_use.add(config.provider)
        
        # API key bilgilerini topla
        key_lines = []
        for provider in providers_in_use:
            if provider == "ollama":
                continue  # Ollama API key gerektirmez
            
            info = get_api_key_info(provider)
            if info["total"] > 0:
                status = f"[green]●[/green]" if info["current"] <= info["total"] else "[red]●[/red]"
                key_lines.append(f"{status} {provider}: Key {info['current']}/{info['total']}")
            else:
                key_lines.append(f"[red]●[/red] {provider}: API key yok!")
        
        if key_lines:
            key_info = "[bold yellow]🔑 API Key Durumu[/bold yellow]\n" + "\n".join(key_lines)
            dashboard.mount(Static(key_info, classes="tool-card api-key-card"))
    
    def _on_model_changed(self, saved: bool):
        """Model ayarları değiştiğinde çağrılır"""
        if saved:
            # Cache'leri temizle
            model_manager.clear_cache()
            
            # Sub-agent cache'lerini temizle
            from tools.agents import clear_agent_cache
            clear_agent_cache()
            
            # Agent'ı yeniden oluştur
            self.agent_executor, _, self.system_prompt = get_agent_executor()
            
            # Dashboard'u güncelle
            self._show_model_info()

    # === HELPER METHODS ===

    def _add_system_message(self, text: str):
        chat = self.query_one("#chat-scroll")
        chat.mount(Static(f"[dim]{text}[/dim]", classes="system-msg"))
    
    def _copy_to_clipboard(self, text: str):
        """Metni panoya kopyala"""
        if not text:
            self.notify("Kopyalanacak metin yok", severity="warning", timeout=2)
            return
        
        try:
            # Önce pyperclip dene
            import pyperclip
            pyperclip.copy(text)
            self.notify("📋 Panoya kopyalandı", severity="information", timeout=2)
        except ImportError:
            # pyperclip yoksa xclip/xsel dene (Linux)
            try:
                import subprocess
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                          stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                self.notify("📋 Panoya kopyalandı", severity="information", timeout=2)
            except:
                try:
                    import subprocess
                    process = subprocess.Popen(['xsel', '--clipboard', '--input'], 
                                              stdin=subprocess.PIPE)
                    process.communicate(text.encode('utf-8'))
                    self.notify("📋 Panoya kopyalandı", severity="information", timeout=2)
                except:
                    # Hiçbiri çalışmazsa dosyaya yaz
                    with open("/tmp/atomagent_clipboard.txt", "w") as f:
                        f.write(text)
                    self.notify("📋 /tmp/atomagent_clipboard.txt dosyasına kaydedildi", 
                               severity="information", timeout=3)

    def _update_status(self, text: str, color: str = "white"):
        try:
            self.query_one("#status-bar", Static).update(f"[{color}]{text}[/{color}]")
        except:
            # Permission dialog açıkken status-bar yok, yeni oluştur
            status_container = self.query_one("#status-container")
            status_container.remove_children()
            status_container.mount(Static(f"[{color}]{text}[/{color}]", id="status-bar"))

    def _refresh_todo(self):
        content = get_todo_content()
        if content:
            self.query_one("#todo-area", Markdown).update(content)

    # === PERMISSION DIALOG ===

    async def _show_permission_dialog(self, base_cmd: str, full_command: str):
        """Status bar'ı permission dialog'a dönüştür"""
        self.pending_command = (base_cmd, full_command)
        status_container = self.query_one("#status-container")
        
        # Mevcut içeriği temizle
        status_container.remove_children()
        
        # Permission mesajı
        await status_container.mount(Static(
            f"[yellow]⚠️ '{base_cmd}' komutuna izin verilsin mi?[/yellow]",
            id="perm-text"
        ))
        
        # Butonlar
        btn_row = Horizontal(id="perm-buttons")
        await status_container.mount(btn_row)
        await btn_row.mount(Button("Bir Kez", id="btn-allow", variant="success"))
        await btn_row.mount(Button("Kalıcı", id="btn-always", variant="primary"))
        await btn_row.mount(Button("Reddet", id="btn-deny", variant="error"))

    def _hide_permission_dialog(self):
        """Permission dialog'u kapat, normal status bar'a dön"""
        status_container = self.query_one("#status-container")
        status_container.remove_children()
        status_container.mount(Static("[dim]Ready[/dim]", id="status-bar"))
        self.pending_command = None

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if not self.pending_command:
            return

        base_cmd, full_command = self.pending_command
        dashboard = self.query_one("#dashboard-view")

        if event.button.id == "btn-allow":
            output = execute_command_direct(full_command)
            await dashboard.mount(Static(f"[cyan]Terminal:[/cyan]\n{output}", classes="tool-card"))
        elif event.button.id == "btn-always":
            add_allowed_command(base_cmd)
            output = execute_command_direct(full_command)
            await dashboard.mount(Static(f"[green]✓ '{base_cmd}' izin listesine eklendi[/green]", classes="success-msg"))
            await dashboard.mount(Static(f"[cyan]Terminal:[/cyan]\n{output}", classes="tool-card"))
        elif event.button.id == "btn-deny":
            await dashboard.mount(Static(f"[red]✗ Komut reddedildi: {base_cmd}[/red]", classes="error-msg"))

        self._hide_permission_dialog()
        self._update_status("Ready", "dim")
        dashboard.scroll_end()

    # === FILE ACTIONS ===

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        event.stop()
        self.file_handler.open_file(str(event.path))

    def action_save_file(self) -> None:
        self.file_handler.save_file()

    def action_run_file(self) -> None:
        dashboard = self.query_one("#dashboard-view")
        self.file_handler.run_file(dashboard)

    # === APP ACTIONS ===

    def action_clear_chat(self) -> None:
        chat = self.query_one("#chat-scroll")
        chat.remove_children()
        self._add_system_message("Chat temizlendi")
        self.message_history.clear()
        self.thread_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"New session: {self.thread_id}")

    def action_refresh_workspace(self) -> None:
        self.query_one("#workspace-tree", DirectoryTree).reload()
        self._refresh_todo()
    
    def action_copy_last(self) -> None:
        """Son AI mesajını panoya kopyala"""
        self._copy_to_clipboard(self._last_ai_response)

    def action_request_quit(self) -> None:
        if self.quit_requested:
            logger.info("AtomAgent closed by user")
            self.exit()
        else:
            self.quit_requested = True
            self._update_status("⚠️ Çıkmak için tekrar Ctrl+C basın", "yellow")
            self.notify("Çıkmak için tekrar Ctrl+C basın", severity="warning", timeout=3)
            self.set_timer(3, self._reset_quit_request)

    def _reset_quit_request(self) -> None:
        if self.quit_requested:
            self.quit_requested = False
            self._update_status("Ready", "dim")

    # === CHAT & AGENT ===

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        if not user_input:
            return

        self.query_one("#user-input", Input).value = ""

        # Özel komutları kontrol et
        if user_input.lower() == ":model" or user_input.lower() == ":models":
            self.push_screen(ModelSelectorModal(), callback=self._on_model_changed)
            return
        
        if user_input.lower() == ":fallback" or user_input.lower() == ":yedek":
            self.push_screen(FallbackSelectorModal())
            return
        
        if user_input.lower() == ":help":
            self._show_help()
            return
        
        if user_input.lower() == ":keys" or user_input.lower() == ":apikeys":
            self._show_api_keys_detail()
            return
        
        if user_input.lower() == ":resetkeys":
            from core.providers import reset_api_key_index
            reset_api_key_index()
            self._add_system_message("API key indeksleri sıfırlandı")
            self._show_api_key_status()
            return
        
        if user_input.lower() == ":copy":
            self._copy_to_clipboard(self._last_ai_response)
            return

        chat = self.query_one("#chat-scroll")
        user_text = self.chat_handler.create_user_message(user_input)
        await chat.mount(Static(user_text, classes="user-msg"))
        chat.scroll_end()

        self.message_history.append(HumanMessage(content=user_input))
        self.run_worker(self._run_agent(user_input), exclusive=True)
    
    def _show_help(self):
        """Yardım mesajını göster"""
        help_text = """[bold cyan]Özel Komutlar:[/bold cyan]
  :model     - Model ayarları penceresi
  :fallback  - Yedek provider ayarları
  :keys      - API key durumu detayı
  :resetkeys - API key indekslerini sıfırla
  :copy      - Son AI yanıtını kopyala
  :help      - Bu yardım mesajı
  
[bold cyan]Kısayollar:[/bold cyan]
  Ctrl+C       - Çıkış (2 kez bas)
  Ctrl+S       - Dosya kaydet
  Ctrl+L       - Chat temizle
  Ctrl+R       - Workspace yenile
  Ctrl+Y       - Son yanıtı kopyala
  Ctrl+Shift+C - Son yanıtı kopyala
  F5           - Dosya çalıştır"""
        
        chat = self.query_one("#chat-scroll")
        chat.mount(Static(help_text, classes="system-msg"))
    
    def _show_api_keys_detail(self):
        """Detaylı API key bilgisini göster"""
        from core.providers import PROVIDERS, get_all_api_keys, get_api_key_info
        
        lines = ["[bold cyan]🔑 API Key Detayları[/bold cyan]\n"]
        
        for provider_id, config in PROVIDERS.items():
            if provider_id == "ollama":
                continue
            
            keys = get_all_api_keys(provider_id)
            info = get_api_key_info(provider_id)
            
            if keys:
                status = "[green]✓[/green]"
                key_preview = ", ".join([f"...{k[-8:]}" for k in keys])
                lines.append(f"{status} [bold]{provider_id}[/bold]: {info['total']} key (aktif: {info['current']})")
                lines.append(f"   [dim]{key_preview}[/dim]")
            else:
                lines.append(f"[red]✗[/red] [bold]{provider_id}[/bold]: Key tanımlı değil")
        
        lines.append("\n[dim]Birden fazla key için .env'de virgülle ayırın[/dim]")
        lines.append("[dim]Örnek: OPENAI_API_KEY=key1,key2,key3[/dim]")
        
        chat = self.query_one("#chat-scroll")
        chat.mount(Static("\n".join(lines), classes="system-msg"))

    async def _run_agent(self, user_input: str, retry_count: int = 0):
        from core.providers import is_rate_limit_error, handle_rate_limit
        from tools.agents import clear_agent_cache
        
        chat = self.query_one("#chat-scroll")
        dashboard = self.query_one("#dashboard-view")
        self.query_one(TabbedContent).active = "tab-dashboard"

        ai_response = Static(self.chat_handler.create_thinking_message(), classes="ai-msg")
        await chat.mount(ai_response)

        final_text = ""
        max_retries = 3

        try:
            messages = [SystemMessage(content=self.system_prompt)] + self.message_history
            thread_config = get_thread_config(self.thread_id)
            thread_config["recursion_limit"] = 100  # Sınırsız gibi - karmaşık görevler için

            self._update_status("⚙️ Çalışıyor...", "yellow")

            async for event in self.agent_executor.astream_events(
                {"messages": messages},
                config=thread_config,
                version="v1"
            ):
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        final_text = await self.chat_handler.process_stream_chunk(
                            chunk.content, final_text, ai_response, chat
                        )

                elif kind == "on_tool_start":
                    await self.chat_handler.handle_tool_start(
                        event['name'], event['run_id'],
                        dashboard, self.loading_widgets, self.tool_handler
                    )

                elif kind == "on_tool_end":
                    output = str(event['data'].get('output', ''))
                    await self.chat_handler.handle_tool_end(
                        event['name'], event['run_id'], output,
                        dashboard, self.loading_widgets, self.tool_handler
                    )

            self.chat_handler.finalize_response(final_text, ai_response)
            self._last_ai_response = final_text  # Son yanıtı sakla

        except Exception as e:
            error_str = str(e).lower()
            
            # Recursion limit hatası - artık 100 olduğu için nadiren olacak
            if "recursion limit" in error_str or "recursion_limit" in error_str:
                logger.error(f"Recursion limit: {e}")
                self.notify("🔄 Çok fazla işlem yapıldı", severity="warning", timeout=5)
                await dashboard.mount(Static(
                    "[yellow]⚠️ Çok fazla işlem yapıldı. Görev tamamlanmış olabilir.[/yellow]",
                    classes="error-msg"
                ))
                ai_response.update(Text(f"[{self.chat_handler.get_timestamp()}] Agent: İşlem tamamlandı (limit)", style="italic yellow"))
                self._update_status("Done", "yellow")
                return
            
            logger.error(f"Error: {e}", exc_info=True)
            
            # Rate limit kontrolü - otomatik key rotasyonu
            if is_rate_limit_error(e) and retry_count < max_retries:
                supervisor_config = model_manager.get_config("supervisor")
                
                # Önce aynı provider'ın diğer key'lerini dene
                if supervisor_config and handle_rate_limit(supervisor_config.provider):
                    self.notify(f"🔄 API key değiştirildi ({retry_count + 1}/{max_retries})", severity="warning", timeout=2)
                    self._show_api_key_status()
                    
                    # Agent'ı yeniden oluştur (cache temizle ama index'i koru)
                    model_manager.clear_cache()
                    clear_agent_cache()
                    self.agent_executor, _, self.system_prompt = get_agent_executor()
                    
                    # Mesajı kaldır ve tekrar dene
                    await ai_response.remove()
                    self.run_worker(self._run_agent(user_input, retry_count + 1), exclusive=True)
                    return
                
                # Key'ler bittiyse fallback provider'a geç
                elif model_manager.switch_to_fallback("supervisor"):
                    self.notify("🔄 Yedek provider'a geçildi", severity="warning", timeout=2)
                    self._show_api_key_status()
                    self._show_model_info()
                    
                    # Cache temizle - get_llm artık doğru fallback'i kullanacak
                    model_manager.clear_cache()
                    clear_agent_cache()
                    self.agent_executor, _, self.system_prompt = get_agent_executor()
                    
                    await ai_response.remove()
                    self.run_worker(self._run_agent(user_input, retry_count + 1), exclusive=True)
                    return
                
                # Tüm provider'lar tükendi
                else:
                    self.notify("❌ Tüm API limitleri doldu!", severity="error", timeout=10)
                    await dashboard.mount(Static(
                        "[red]❌ Tüm API limitleri doldu![/red]\n"
                        "[yellow]Öneriler:[/yellow]\n"
                        "• Biraz bekleyin (saatlik limitler sıfırlanır)\n"
                        "• :model ile farklı bir provider seçin\n"
                        "• .env'ye yeni API key'ler ekleyin",
                        classes="error-msg"
                    ))
                    ai_response.update(Text(f"[{self.chat_handler.get_timestamp()}] Agent: API limiti doldu", style="italic red"))
                    self._update_status("API Limit", "red")
                    return
            
            # Hata mesajını göster
            await dashboard.mount(Static(self.chat_handler.create_error_message(e), classes="error-msg"))
            ai_response.update(Text(f"[{self.chat_handler.get_timestamp()}] Agent: Hata oluştu", style="italic red"))
            self._update_status("Error", "red")


def main():
    app = AtomAgentApp()
    app.run()


if __name__ == "__main__":
    main()
