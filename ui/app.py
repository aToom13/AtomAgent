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
# from tools.todo_tools import get_todo_content  # Todo kaldırıldı
from tools.execution import add_allowed_command, execute_command_direct
from textual.command import Command, DiscoveryHit, Hit
from ui.styles import BASE_CSS, get_theme_variables, THEMES

from ui.handlers import ToolOutputHandler, FileHandler, ChatHandler
from ui.widgets import (
    ModelSelectorModal, apply_saved_settings, FallbackSelectorModal,
    TaskProgressWidget, ToolActivityWidget, DebugLogWidget, 
    AgentStateWidget, MemoryUsageWidget,
    SessionBrowserModal, SessionInfoWidget, RenameSessionModal,
    SessionSidebar, SandboxPanel, ToolFactoryPanel, SandboxTree
)
from core.session_manager import session_manager, Session
from tools.tool_factory import register_tool_callback

logger = get_logger()
WORKSPACE_DIR = config.workspace.base_dir


class AtomAgentApp(App):
    """AtomAgent - AI-Powered Development Assistant"""

    CSS = ""  # Styles loaded dynamically in on_mount
    TITLE = "AtomAgent"
    SUB_TITLE = "AI Development Assistant"
    ENABLE_COMMAND_PALETTE = False  # Palette butonunu kaldırmak için devre dışı bırakıldı

    BINDINGS = [
        Binding("ctrl+c", "request_quit", "Quit", priority=True),
        Binding("ctrl+s", "save_file", "Save", show=False),
        Binding("f5", "run_file", "Run", show=False),
        Binding("ctrl+l", "clear_chat", "Clear Chat", show=False),
        Binding("ctrl+r", "refresh_workspace", "Refresh", show=False),
        Binding("ctrl+shift+c", "copy_last", "Copy Last", show=False),
        Binding("ctrl+y", "copy_last", "Copy", show=False),
        Binding("ctrl+d", "toggle_debug", "Debug", show=False),
        Binding("ctrl+h", "show_history", "History", show=False),
        Binding("ctrl+n", "new_session", "New Session", show=False),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar", show=False),
        Binding("ctrl+z", "toggle_zen_mode", "Zen Mode", show=False),
        # Binding("ctrl+p", "command_palette", "Palette", show=False), # Palette devre dışı
        # Resize Bindings
        Binding("ctrl+left", "resize_left_dec", "Shrink Left", show=False),
        Binding("ctrl+right", "resize_left_inc", "Grow Left", show=False),
        Binding("alt+left", "resize_right_inc", "Grow Right", show=False),
        Binding("alt+right", "resize_right_dec", "Shrink Right", show=False),
    ]

    def __init__(self):
        super().__init__()
        
        # Kaydedilmiş ayarları yükle
        apply_saved_settings()
        
        self.agent_executor, _, self.system_prompt = get_agent_executor()
        self.loading_widgets = {}
        self.message_history = []
        self.pending_command = None
        self.quit_requested = False
        self._last_ai_response = ""  # Son AI yanıtını sakla
        self._stop_requested = False  # Agent durdurma flag'i
        self._agent_running = False  # Agent çalışıyor mu?
        
        # Panel Widths (Default)
        self.left_width = 35
        self.right_width = 45
        
        # Session management
        self.current_session: Session = None
        self._init_session()

        # Handlers
        self.tool_handler = ToolOutputHandler(self)
        self.file_handler = FileHandler(self)
        self.chat_handler = ChatHandler(self)
        
        # Debug mode
        self.debug_mode = False
        self.debug_log = None
        self.agent_state = None
        self.progress_tracker = None
        self.tool_activity = None
        
        # Sidebar reference
        self.session_sidebar = None
        
        # Tool Factory callback - yeni tool oluşturulduğunda agent'ı güncelle
        register_tool_callback(self._on_custom_tool_created)

        logger.info("AtomAgent started")
    
    def _on_custom_tool_created(self, tool_name: str, tool_instance):
        """Custom tool oluşturulduğunda çağrılır"""
        # Agent'ı yeniden oluştur (yeni tool'u dahil etmek için)
        self.agent_executor, _, self.system_prompt = get_agent_executor()
        logger.info(f"Agent updated with new tool: {tool_name}")
        
        # Tool Factory panelini güncelle
        try:
            panel = self.query_one("#tool-factory-panel", ToolFactoryPanel)
            panel.refresh_tools()
        except:
            pass
        
        self.notify(f"🔧 Yeni tool eklendi: {tool_name}", severity="information", timeout=3)
    
    def _init_session(self):
        """Yeni session başlat veya mevcut session'ı yükle"""
        self.current_session = session_manager.create_session()
        self.thread_id = self.current_session.id
        logger.info(f"Session initialized: {self.thread_id}")
    
    def _save_message_to_session(self, role: str, content: str, metadata: dict = None):
        """Mesajı session'a kaydet"""
        if self.current_session:
            session_manager.add_message(
                self.current_session.id,
                role=role,
                content=content,
                metadata=metadata
            )
            # Session'ı güncelle
            self.current_session = session_manager.get_session(self.current_session.id)
    
    def _load_session(self, session: Session):
        """Mevcut bir session'ı yükle"""
        self.current_session = session
        self.thread_id = session.id
        self.message_history.clear()
        
        # Chat'i temizle
        chat = self.query_one("#chat-scroll")
        chat.remove_children()
        
        # Mesajları yükle
        messages = session_manager.get_messages(session.id)
        
        for msg in messages:
            if msg.role == "human":
                user_text = self.chat_handler.create_user_message(msg.content)
                chat.mount(Static(user_text, classes="user-msg"))
                self.message_history.append(HumanMessage(content=msg.content))
            elif msg.role == "ai":
                ai_text = self.chat_handler.format_ai_response(msg.content)
                chat.mount(Static(ai_text, classes="ai-msg"))
            elif msg.role == "system":
                chat.mount(Static(f"[dim]{msg.content}[/dim]", classes="system-msg"))
        
        chat.scroll_end()
        self._add_system_message(f"📂 Session yüklendi: {session.title[:40]}")
        self._update_session_info()
        logger.info(f"Session loaded: {session.id}")
    
    def _update_session_info(self):
        """Dashboard'da session bilgisini güncelle"""
        dashboard = self.query_one("#dashboard-view")
        
        # Eski session kartını kaldır
        for card in list(self.query(".session-info-card")):
            card.remove()
        
        if self.current_session:
            try:
                dt = datetime.fromisoformat(self.current_session.created_at)
                date_str = dt.strftime("%d %b %H:%M")
            except:
                date_str = "?"
            
            session_info = f"""[bold magenta]📝 Aktif Session[/bold magenta]
[cyan]{self.current_session.title[:35]}[/cyan]
[dim]ID: {self.current_session.id}[/dim]
[dim]Mesaj: {self.current_session.message_count} • {date_str}[/dim]

[dim]:history veya Ctrl+H ile geçmişe göz atın[/dim]"""
            
            dashboard.mount(Static(session_info, classes="tool-card session-info-card"))

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            # === LEFT PANEL: PROJECT EXPLORER ===
            with Vertical(id="left-sidebar"):
                with TabbedContent(id="left-tabs"):
                    # 1. Files Tab
                    with TabPane("📂 Files", id="tab-files"):
                        with Vertical(id="workspace-container"):
                            yield Label("Workspace", classes="tree-label")
                            yield DirectoryTree(WORKSPACE_DIR, id="workspace-tree")
                            yield Button("Refresh Files", id="btn-refresh-files", variant="primary")
                            yield Label("Sandbox", classes="tree-label")
                            yield SandboxTree("/home/agent", id="sandbox-tree")
                    
                    # 2. Sessions Tab
                    with TabPane("💬 Chats", id="tab-sessions"):
                        yield SessionSidebar(id="session-sidebar")
                    
                    # 3. Memory Tab
                    with TabPane("🧠 Memory", id="tab-memory"):
                        with Vertical(id="memory-container"):
                            yield MemoryUsageWidget(id="memory-widget")
                            yield Label("Context Status", classes="section-label")
                            yield Static("RAG Memory: Active\nVector DB: Ready", classes="info-box")
                            yield Label("Quick Search", classes="section-label")
                            yield Input(placeholder="Search memory...", id="memory-search-input")
                            yield VerticalScroll(id="memory-search-results")

            # === CENTER PANEL: CHAT ===
            with Vertical(id="left-panel"):
                yield Label("🤖 ATOMAGENT", id="chat-header")
                yield VerticalScroll(id="chat-scroll")
                # Status/Permission bar
                with Vertical(id="status-container"):
                    yield Static("[dim]Ready[/dim]", id="status-bar")
                with Horizontal(id="input-container"):
                    yield Input(placeholder="Mesajınızı yazın...", id="user-input")
                    yield Button("⏹", id="btn-stop", variant="error", classes="stop-btn")

            # === RIGHT PANEL: DEV TOOLS ===
            with Vertical(id="right-panel"):
                with TabbedContent(id="right-tabs"):
                    # 1. Terminal (Sandbox)
                    with TabPane("💻 Terminal", id="tab-terminal"):
                        yield SandboxPanel(id="sandbox-panel")

                    # 2. Editor
                    with TabPane("📝 Editor", id="tab-editor"):
                        with Vertical(id="editor-container"):
                            with Horizontal(id="editor-toolbar"):
                                yield Label("Dosya açık değil", id="editor-header")
                                yield Button("Save", id="btn-save-file", variant="success", classes="small-btn")
                                yield Button("Run", id="btn-run-file", variant="warning", classes="small-btn")
                            yield TextArea(
                                language="python",
                                show_line_numbers=True,
                                id="code-editor",
                                theme="monokai"
                            )
                    
                    # 3. Monitor (Dashboard + Debug)
                    with TabPane("📊 Monitor", id="tab-monitor"):
                        with VerticalScroll(id="monitor-scroll"):
                            yield Label("System Status", classes="section-label")
                            yield AgentStateWidget(id="agent-state")
                            yield TaskProgressWidget(id="task-progress")
                            
                            yield Label("Live Activity", classes="section-label")
                            yield ToolActivityWidget(id="tool-activity")
                            
                            yield Label("Debug Log", classes="section-label")
                            yield DebugLogWidget(id="debug-log")
                            
                            yield Label("Dashboard", classes="section-label")
                            yield Vertical(id="dashboard-view") # Nested for dynamic content

                    # 4. Tools (Extensions)
                    with TabPane("🔧 Tools", id="tab-tools"):
                        yield ToolFactoryPanel(id="tool-factory-panel")
            
        yield Footer()

    def on_mount(self) -> None:
        """App mounted"""
        # Initialize Theme
        self.stylesheet.set_variables(get_theme_variables("gruvbox"))
        self.stylesheet.add_source(BASE_CSS)
        
        self.title = "AtomAgent"
        self.query_one("#user-input").focus()
        self._add_system_message("AtomAgent hazır! 🚀")
        self._show_model_info()
        self._update_session_info()
        
        # Sidebar referansı ve aktif session ayarla
        try:
            self.session_sidebar = self.query_one("#session-sidebar", SessionSidebar)
            if self.current_session:
                self.session_sidebar.set_active_session(self.current_session.id)
        except:
            pass
        
        # Debug widget'larını referansla
        try:
            self.debug_log = self.query_one("#debug-log", DebugLogWidget)
            self.agent_state = self.query_one("#agent-state", AgentStateWidget)
            self.progress_tracker = self.query_one("#task-progress", TaskProgressWidget)
            self.tool_activity = self.query_one("#tool-activity", ToolActivityWidget)
            self._log_debug("info", "AtomAgent başlatıldı")
            # Model bilgilerini güncelle
            if self.agent_state:
                self.agent_state.update_models()
        except:
            pass
    
    def _log_debug(self, level: str, message: str):
        """Debug log ekle"""
        if self.debug_log:
            if level == "info":
                self.debug_log.log_info(message)
            elif level == "success":
                self.debug_log.log_success(message)
            elif level == "warning":
                self.debug_log.log_warning(message)
            elif level == "error":
                self.debug_log.log_error(message)
    
    def action_toggle_debug(self) -> None:
        """Debug panelini aç/kapat"""
        self.debug_mode = not self.debug_mode
        if self.debug_mode:
            self.query_one("#right-tabs", TabbedContent).active = "tab-debug"
            self.notify("Debug modu açık", severity="information", timeout=2)
        else:
            self.query_one("#right-tabs", TabbedContent).active = "tab-dashboard"
            self.notify("Debug modu kapalı", severity="information", timeout=2)
    
    def _show_model_info(self):
        """Dashboard'da aktif model ve API key bilgisini göster"""
        dashboard = self.query_one("#dashboard-view")
        
        # Eski kartları kaldır (tümünü)
        for card in list(self.query(".model-info-card")):
            card.remove()
        
        # Gerçek kullanılan modelleri al (fallback dahil)
        sup_provider, sup_model = model_manager.get_current_provider_info("supervisor")
        cod_provider, cod_model = model_manager.get_current_provider_info("coder")
        res_provider, res_model = model_manager.get_current_provider_info("researcher")
        
        # Model adlarını kısalt
        def shorten(model):
            if not model:
                return "?"
            short = model.split("/")[-1] if "/" in model else model
            return short[:30] + "..." if len(short) > 30 else short
        
        model_info = f"""[bold cyan]🤖 Aktif Modeller[/bold cyan]
[green]Supervisor:[/green] {sup_provider}/{shorten(sup_model)}
[green]Coder:[/green] {cod_provider}/{shorten(cod_model)}
[green]Researcher:[/green] {res_provider}/{shorten(res_model)}

[dim]Model değiştirmek için :model yazın[/dim]"""
        
        dashboard.mount(Static(model_info, classes="tool-card model-info-card"))
        
        # API Key durumu kartı
        self._show_api_key_status(dashboard)
        
        # Debug panelini de güncelle
        if self.agent_state:
            self.agent_state.update_models()
    
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

    def _stop_agent(self):
        """Agent'ı durdur"""
        if self._agent_running:
            self._stop_requested = True
            self._update_status("⏹ Durduruluyor...", "yellow")
            self.notify("Agent durduruluyor...", severity="warning", timeout=2)
            self._log_debug("warning", "Agent durdurma isteği alındı")
        else:
            self.notify("Agent şu anda çalışmıyor", severity="information", timeout=2)

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
        if event.button.id == "btn-refresh-files":
            self.action_refresh_workspace()
            return

        if event.button.id == "btn-save-file":
            self.action_save_file()
            return
            
        if event.button.id == "btn-run-file":
            self.action_run_file()
            return
        
        if event.button.id == "btn-stop":
            self._stop_agent()
            return

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

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "memory-search-input":
            query = event.value
            if query:
                from tools.rag import search_codebase
                result = search_codebase.invoke({"query": query})
                results_container = self.query_one("#memory-search-results")
                results_container.remove_children()
                await results_container.mount(Static(result, classes="info-box"))
            return

        user_input = event.value.strip()
        if not user_input:
            return
        
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
        """Chat'i temizle ve yeni session başlat"""
        chat = self.query_one("#chat-scroll")
        chat.remove_children()
        self._add_system_message("Chat temizlendi - Yeni session başlatıldı")
        self.message_history.clear()
        
        # Yeni session oluştur
        self._init_session()
        self._update_session_info()
        
        # Sidebar'ı güncelle (refresh=True ile tek seferde)
        if self.session_sidebar:
            self.session_sidebar.set_active_session(self.current_session.id, refresh=True)
        
        logger.info(f"New session: {self.thread_id}")
    
    def action_new_session(self) -> None:
        """Yeni session başlat (Ctrl+N)"""
        self.action_clear_chat()
    
    def action_show_history(self) -> None:
        """Session geçmişini göster (Ctrl+H)"""
        self.push_screen(SessionBrowserModal(), callback=self._on_session_selected)
    
    def _on_session_selected(self, session: Session):
        """Session seçildiğinde çağrılır"""
        if session:
            self._load_session(session)
            # Sidebar'ı güncelle (refresh=True ile veritabanından yeniden yükle)
            if self.session_sidebar:
                self.session_sidebar.set_active_session(session.id, refresh=True)
    
    def on_session_sidebar_session_selected(self, event: SessionSidebar.SessionSelected) -> None:
        """Sidebar'dan session seçildiğinde"""
        event.stop()
        self._load_session(event.session)
        if self.session_sidebar:
            # Sidebar'dan seçildiğinde sadece active class güncelle, refresh gerekmez
            self.session_sidebar.set_active_session(event.session.id, refresh=False)
    
    def on_session_sidebar_new_session_requested(self, event: SessionSidebar.NewSessionRequested) -> None:
        """Sidebar'dan yeni session istendiğinde"""
        event.stop()
        self.action_new_session()
    
    def on_session_sidebar_session_deleted(self, event: SessionSidebar.SessionDeleted) -> None:
        """Sidebar'dan session silindiğinde"""
        event.stop()
        # Sidebar zaten güncellendi, sadece log
        logger.info(f"Session deleted: {event.session_id}")
    
    def action_toggle_sidebar(self) -> None:
        """Sidebar'ı aç/kapat (Ctrl+B)"""
        if self.session_sidebar:
            if self.session_sidebar.display:
                self.session_sidebar.display = False
                self.notify("Sidebar gizlendi", severity="information", timeout=1)
            else:
                self.session_sidebar.display = True
                self.session_sidebar.refresh_sessions()
                self.notify("Sidebar gösterildi", severity="information", timeout=1)

    def action_refresh_workspace(self) -> None:
        self.query_one("#workspace-tree", DirectoryTree).reload()
    
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

    # === PANEL RESIZING ===

    def action_resize_left_dec(self):
        self.left_width = max(20, self.left_width - 2)
        self.query_one("#left-sidebar").styles.width = self.left_width
        self.notify(f"Left Panel: {self.left_width}")

    def action_resize_left_inc(self):
        self.left_width = min(60, self.left_width + 2)
        self.query_one("#left-sidebar").styles.width = self.left_width
        self.notify(f"Left Panel: {self.left_width}")

    def action_resize_right_dec(self):
        self.right_width = max(30, self.right_width - 2)
        self.query_one("#right-panel").styles.width = self.right_width
        self.notify(f"Right Panel: {self.right_width}")

    def action_resize_right_inc(self):
        self.right_width = min(80, self.right_width + 2)
        self.query_one("#right-panel").styles.width = self.right_width
        self.notify(f"Right Panel: {self.right_width}")

    # === ZEN MODE ===
    
    def action_toggle_zen_mode(self) -> None:
        """Zen modunu aç/kapat (Ctrl+Z)"""
        left_sidebar = self.query_one("#left-sidebar")
        right_panel = self.query_one("#right-panel")
        
        if left_sidebar.display:
            # Zen mode ON
            left_sidebar.display = False
            right_panel.display = False
            self.notify("🧘 Zen Modu Açık", severity="information")
            self._update_status("ZEN MODE", "magenta")
        else:
            # Zen mode OFF
            left_sidebar.display = True
            right_panel.display = True
            self.notify("Zen Modu Kapalı", severity="information")
            self._update_status("Ready", "dim")

    # === CHAT & AGENT ===

    def on_mount(self) -> None:
        """App mounted"""
        # Initialize Theme
        self.stylesheet.set_variables(get_theme_variables("gruvbox"))
        self.stylesheet.add_source(BASE_CSS)
        
        self.title = "AtomAgent"
        self.query_one("#user-input").focus()
        
        # Startup Banner
        banner = """[bold magenta]
    ___  __                  __                    __ 
   /   |/ /_____  ____ ___  /   | ____ ____  ____  / /_
  / /| / __/ __ \\/ __ `__ \\/ /| |/ __ `/ _ \\/ __ \\/ __/
 / ___/ /_/ /_/ / / / / / / ___ / /_/ /  __/ / / / /_  
/_/  |__/\\____/_/ /_/ /_/_/  |_\\__, /\\___/_/ /_/\\__/  
                              /____/                  
[/bold magenta]
[dim]v4.2 - AI Development Assistant[/dim]
[cyan]Tip: Ctrl+Z ile Zen Modunu deneyin![/cyan]
"""
        chat = self.query_one("#chat-scroll")
        chat.mount(Static(banner, classes="system-msg"))
        self._add_system_message("AtomAgent hazır! 🚀")
        
        self._show_model_info()
        self._update_session_info()
        
        # Sidebar referansı ve aktif session ayarla
        try:
            self.session_sidebar = self.query_one("#session-sidebar", SessionSidebar)
            if self.current_session:
                self.session_sidebar.set_active_session(self.current_session.id)
        except:
            pass
        
        # Debug widget'larını referansla
        try:
            self.debug_log = self.query_one("#debug-log", DebugLogWidget)
            self.agent_state = self.query_one("#agent-state", AgentStateWidget)
            self.progress_tracker = self.query_one("#task-progress", TaskProgressWidget)
            self.tool_activity = self.query_one("#tool-activity", ToolActivityWidget)
            self._log_debug("info", "AtomAgent başlatıldı")
            # Model bilgilerini güncelle
            if self.agent_state:
                self.agent_state.update_models()
        except:
            pass

    def get_commands(self, query: str = "") -> list[DiscoveryHit]:
        """Command Palette için komutları döndür"""
        yield from super().get_commands(query)
        
        # Tema komutları Command Palette'den kaldırıldı (Kullanıcı isteği)
        # Sadece :theme komutu ile değiştirilebilir

    def action_set_theme(self, theme_name: str) -> None:
        """Temayı değiştir"""
        try:
            theme_name = theme_name.lower()
            logger.info(f"Changing theme to: {theme_name}")
            
            if theme_name not in THEMES:
                self.notify(f"Tema bulunamadı: {theme_name}", severity="error")
                return

            variables = get_theme_variables(theme_name)
            
            # CSS değişkenlerini güncelle - Textual otomatik olarak yeniden boyayacaktır
            self.stylesheet.set_variables(variables)
            
            # refresh_css() çağrısını kaldırıyoruz çünkü değişkenler kaybolabiliyor
            # self.refresh_css() 
            
            self._add_system_message(f"Tema değiştirildi: {theme_name}")
            self.notify(f"Tema değiştirildi: {theme_name}", severity="information")
            
        except Exception as e:
            logger.error(f"Error changing theme: {e}")
            self.notify(f"Tema değiştirme hatası: {e}", severity="error")

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
        
        if user_input.lower() == ":stop":
            self._stop_agent()
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
        
        if user_input.lower() == ":reset" or user_input.lower() == ":resetall":
            from core.providers import reset_api_key_index
            from tools.agents import clear_agent_cache
            # Tüm index'leri sıfırla
            reset_api_key_index()
            # Model manager'ı sıfırla (primary'ye dön)
            model_manager.reset_to_primary()
            model_manager.clear_cache()
            clear_agent_cache()
            # Agent'ı yeniden oluştur
            self.agent_executor, _, self.system_prompt = get_agent_executor()
            self._add_system_message("Tüm provider'lar sıfırlandı, primary modellere dönüldü")
            self._show_model_info()
            return
        
        if user_input.lower() == ":copy":
            self._copy_to_clipboard(self._last_ai_response)
            return
        
        if user_input.lower() == ":memory":
            self._show_memory_status()
            return
        
        if user_input.lower() == ":clear" or user_input.lower() == ":clearmemory":
            from tools.memory import clear_memory
            clear_memory.invoke({})
            self._add_system_message("Hafıza temizlendi")
            return
        
        if user_input.lower() == ":debug":
            self.action_toggle_debug()
            return
        
        if user_input.lower() == ":tools" or user_input.lower() == ":toolfactory":
            self.query_one("#right-tabs", TabbedContent).active = "tab-tools"
            return
        
        if user_input.lower() == ":sandbox":
            self.query_one("#right-tabs", TabbedContent).active = "tab-sandbox"
            return
        
        # Session komutları
        if user_input.lower() == ":history" or user_input.lower() == ":sessions":
            self.action_show_history()
            return
        
        if user_input.lower() == ":new" or user_input.lower() == ":newsession":
            self.action_new_session()
            return
        
        if user_input.lower().startswith(":rename "):
            new_title = user_input[8:].strip()
            if new_title and self.current_session:
                session_manager.update_session(self.current_session.id, title=new_title)
                self.current_session = session_manager.get_session(self.current_session.id)
                self._update_session_info()
                self._add_system_message(f"Session yeniden adlandırıldı: {new_title}")
            return
        
        if user_input.lower().startswith(":theme"):
            parts = user_input.split()
            if len(parts) > 1:
                theme_name = parts[1]
                self.action_set_theme(theme_name)
            else:
                self._add_system_message("Kullanım: :theme [gruvbox|dracula|nord]")
            return

        if user_input.lower() == ":export":
            self._export_current_session()
            return

        chat = self.query_one("#chat-scroll")
        user_text = self.chat_handler.create_user_message(user_input)
        await chat.mount(Static(user_text, classes="user-msg"))
        chat.scroll_end()

        self.message_history.append(HumanMessage(content=user_input))
        
        # Mesajı session'a kaydet
        self._save_message_to_session("human", user_input)
        
        # İlk mesajsa otomatik başlık oluştur
        if self.current_session and self.current_session.message_count == 1:
            session_manager.auto_title(self.current_session.id)
            self.current_session = session_manager.get_session(self.current_session.id)
            self._update_session_info()
            # Sidebar'ı güncelle (yeni başlık için)
            if self.session_sidebar:
                self.session_sidebar.refresh_sessions()
        
        self.run_worker(self._run_agent(user_input), exclusive=True)
    
    def _show_help(self):
        """Yardım mesajını göster"""
        help_text = """[bold cyan]Özel Komutlar:[/bold cyan]
  :model       - Model ayarları ve seçimi
  :fallback    - Yedek model (fallback) yapılandırması
  :theme [ad]  - Temayı değiştir (örn: :theme dracula)
  :keys        - API key kullanım durumu
  :resetkeys   - API key indekslerini sıfırla
  :reset       - Tüm provider'ları sıfırla
  :stop        - Çalışan agent'ı durdur
  :copy        - Son AI yanıtını panoya kopyala
  :memory      - Hafıza durumunu göster
  :clear       - Hafızayı temizle
  :tools       - Tool Factory panelini aç
  :sandbox     - Sandbox panelini aç
  :help        - Bu yardım mesajı
  
[bold magenta]Session Komutları:[/bold magenta]
  :history     - Konuşma geçmişi (Ctrl+H)
  :new         - Yeni session başlat (Ctrl+N)
  :rename [ad] - Aktif session'ı yeniden adlandır
  :export      - Session'ı JSON olarak dışa aktar
  
[bold cyan]Kısayollar:[/bold cyan]
  Ctrl+C       - Çıkış
  Ctrl+Z       - Zen Modu (Tam ekran chat)
  Ctrl+L       - Chat temizle
  Ctrl+S       - Dosya kaydet (Editör)
  F5           - Dosya çalıştır (Editör)
  Ctrl+R       - Dosyaları yenile
  Ctrl+B       - Yan panelleri aç/kapat
  
[bold cyan]Özellikler:[/bold cyan]
  • [green]Session Management[/green] - Konuşmalar otomatik kaydedilir
  • [green]Kod Highlighting[/green] - Renkli kod blokları
  • [green]Memory Sistemi[/green] - Uzun süreli hafıza ve RAG
  • [green]Tool Factory[/green] - Kendi araçlarınızı oluşturun
  • [green]Sandbox[/green] - Güvenli kod çalıştırma ortamı"""
        
        chat = self.query_one("#chat-scroll")
        chat.mount(Static(help_text, classes="system-msg"))
    
    def _export_current_session(self):
        """Aktif session'ı export et"""
        if not self.current_session:
            self._add_system_message("Aktif session yok")
            return
        
        import json
        import os
        
        data = session_manager.export_session(self.current_session.id)
        if data:
            filename = f"session_export_{self.current_session.id}.json"
            filepath = os.path.join(config.workspace.base_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._add_system_message(f"✓ Export edildi: {filename}")
            self.notify(f"Export: {filename}", severity="information")
        else:
            self._add_system_message("Export başarısız")
            self.notify("Export başarısız", severity="error")
    
    def _show_memory_status(self):
        """Hafıza durumunu göster"""
        from tools.memory import get_memory_stats
        
        stats = get_memory_stats.invoke({})
        chat = self.query_one("#chat-scroll")
        chat.mount(Static(stats, classes="system-msg"))
    
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
        from core.providers import is_rate_limit_error, is_fallback_needed, handle_rate_limit
        from tools.agents import clear_agent_cache
        from tools.memory import get_persistent_context
        
        # Agent çalışıyor flag'ini set et
        self._agent_running = True
        self._stop_requested = False
        
        chat = self.query_one("#chat-scroll")
        dashboard = self.query_one("#dashboard-view")
        # Dashboard is now inside 'tab-monitor'
        self.query_one("#right-tabs", TabbedContent).active = "tab-monitor"

        ai_response = Static(self.chat_handler.create_thinking_message(), classes="ai-msg")
        await chat.mount(ai_response)

        final_text = ""
        max_retries = 10  # Tüm fallback'leri deneyebilmek için

        try:
            # Kalıcı hafızadaki bilgileri system prompt'a ekle
            system_prompt_with_memory = self.system_prompt
            persistent_ctx = get_persistent_context()
            if persistent_ctx:
                system_prompt_with_memory = self.system_prompt + "\n\n" + persistent_ctx
            
            messages = [SystemMessage(content=system_prompt_with_memory)] + self.message_history
            thread_config = get_thread_config(self.thread_id)
            thread_config["recursion_limit"] = 100  # Sınırsız gibi - karmaşık görevler için

            self._update_status("⚙️ Çalışıyor...", "yellow")
            
            # Debug: Agent durumunu güncelle
            if self.agent_state:
                self.agent_state.set_thinking(user_input[:50])
            if self.progress_tracker:
                self.progress_tracker.start_task(user_input[:50])
            self._log_debug("info", f"Görev başladı: {user_input[:50]}...")

            async for event in self.agent_executor.astream_events(
                {"messages": messages},
                config=thread_config,
                version="v1"
            ):
                # Stop kontrolü
                if self._stop_requested:
                    self._log_debug("warning", "Agent kullanıcı tarafından durduruldu")
                    final_text += "\n\n[Kullanıcı tarafından durduruldu]"
                    break
                
                kind = event["event"]

                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        final_text = await self.chat_handler.process_stream_chunk(
                            chunk.content, final_text, ai_response, chat
                        )

                elif kind == "on_tool_start":
                    # Stop kontrolü - tool başlamadan önce
                    if self._stop_requested:
                        break
                    
                    tool_name = event['name']
                    await self.chat_handler.handle_tool_start(
                        tool_name, event['run_id'],
                        dashboard, self.loading_widgets, self.tool_handler
                    )
                    # Debug: Tool başladı
                    if self.tool_activity:
                        self.tool_activity.add_activity(tool_name, "running")
                    if self.agent_state:
                        self.agent_state.set_working(tool_name)
                        self.agent_state.increment_tools()
                    if self.progress_tracker:
                        self.progress_tracker.increment_step(f"Tool: {tool_name}")
                    self._log_debug("info", f"Tool başladı: {tool_name}")

                elif kind == "on_tool_end":
                    tool_name = event['name']
                    output = str(event['data'].get('output', ''))
                    await self.chat_handler.handle_tool_end(
                        tool_name, event['run_id'], output,
                        dashboard, self.loading_widgets, self.tool_handler
                    )
                    # Debug: Tool bitti
                    if self.tool_activity:
                        status = "error" if "error" in output.lower() or "hata" in output.lower() else "success"
                        self.tool_activity.update_activity(tool_name, status)
                    self._log_debug("success" if "error" not in output.lower() else "warning", f"Tool bitti: {tool_name}")

            self.chat_handler.finalize_response(final_text, ai_response)
            self._last_ai_response = final_text  # Son yanıtı sakla
            
            # AI yanıtını session'a kaydet
            self._save_message_to_session("ai", final_text)
            self._update_session_info()
            
            # Debug: Görev tamamlandı
            if self.agent_state:
                self.agent_state.set_idle()
            if self.progress_tracker:
                if self._stop_requested:
                    self.progress_tracker.complete_task("Durduruldu")
                else:
                    self.progress_tracker.complete_task("Tamamlandı")
            
            if self._stop_requested:
                self._log_debug("warning", "Görev durduruldu")
                self._update_status("⏹ Durduruldu", "yellow")
            else:
                self._log_debug("success", "Görev tamamlandı")

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
            self._log_debug("error", f"Hata yakalandı: {str(e)[:100]}")
            
            # Fallback gerekip gerekmediğini kontrol et
            needs_fallback = is_fallback_needed(e)
            
            self._log_debug("info", f"Fallback needed: {needs_fallback}, Retry: {retry_count}/{max_retries}")
            
            # Fallback gerektiren hata kontrolü
            if needs_fallback and retry_count < max_retries:
                supervisor_config = model_manager.get_config("supervisor")
                provider = supervisor_config.provider if supervisor_config else "unknown"
                
                self._log_debug("warning", f"Rate limit/connection error for {provider}, trying fallback...")
                
                # Ollama veya API key olmayan provider için direkt fallback'e geç
                if provider == "ollama" or not handle_rate_limit(provider):
                    # Fallback provider'a geç
                    if model_manager.switch_to_fallback("supervisor"):
                        # Coder ve researcher için de fallback'e geç
                        model_manager.switch_to_fallback("coder")
                        model_manager.switch_to_fallback("researcher")
                        
                        self.notify("🔄 Yedek provider'a geçildi", severity="warning", timeout=3)
                        self._show_api_key_status()
                        self._show_model_info()
                        self._log_debug("info", "Fallback provider'a geçildi")
                        
                        # Debug panelinde model bilgilerini güncelle
                        if self.agent_state:
                            self.agent_state.update_models()
                        
                        # Cache temizle
                        model_manager.clear_cache()
                        clear_agent_cache()
                        self.agent_executor, _, self.system_prompt = get_agent_executor()
                        
                        await ai_response.remove()
                        self.run_worker(self._run_agent(user_input, retry_count + 1), exclusive=True)
                        return
                    else:
                        # Tüm fallback'ler tükendi
                        self._log_debug("error", "Tüm fallback'ler tükendi")
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
                else:
                    # API key rotasyonu başarılı
                    self.notify(f"🔄 API key değiştirildi ({retry_count + 1}/{max_retries})", severity="warning", timeout=2)
                    self._show_api_key_status()
                    
                    model_manager.clear_cache()
                    clear_agent_cache()
                    self.agent_executor, _, self.system_prompt = get_agent_executor()
                    
                    await ai_response.remove()
                    self.run_worker(self._run_agent(user_input, retry_count + 1), exclusive=True)
                    return
            
            # Hata mesajını göster
            await dashboard.mount(Static(self.chat_handler.create_error_message(e), classes="error-msg"))
            ai_response.update(Text(f"[{self.chat_handler.get_timestamp()}] Agent: Hata oluştu", style="italic red"))
            self._update_status("Error", "red")
            
            # Debug: Hata
            if self.agent_state:
                self.agent_state.set_error(str(e)[:50])
            if self.progress_tracker:
                self.progress_tracker.fail_task(str(e)[:50])
            self._log_debug("error", f"Hata: {str(e)[:100]}")
        
        finally:
            # Agent çalışma flag'lerini resetle
            self._agent_running = False
            self._stop_requested = False
            if not self._stop_requested:
                self._update_status("Ready", "dim")


def main():
    app = AtomAgentApp()
    app.run()


if __name__ == "__main__":
    main()
