"""
Tool Factory Panel - Custom tool yönetimi UI
Agent'ın oluşturduğu tool'ları görüntüle ve yönet
"""
from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Static, Button, Label, TextArea, Input
from textual.widget import Widget
from textual.message import Message
from datetime import datetime

from tools.tool_factory import (
    get_tool_list, _tool_registry, _load_registry,
    delete_tool as delete_tool_func, get_tool_code as get_tool_code_func,
    test_tool as test_tool_func, _custom_tools
)
from utils.logger import get_logger

logger = get_logger()


class ToolItem(Widget):
    """Tek bir custom tool kartı"""
    
    DEFAULT_CSS = """
    ToolItem {
        height: auto;
        margin: 1 0;
        padding: 1;
        background: $surface;
        border: solid $primary-lighten-2;
    }
    
    ToolItem:hover {
        background: $surface-lighten-1;
    }
    
    ToolItem .tool-header {
        height: 1;
    }
    
    ToolItem .tool-name {
        color: $success;
        text-style: bold;
    }
    
    ToolItem .tool-desc {
        color: $text-muted;
        margin-top: 1;
    }
    
    ToolItem .tool-meta {
        color: $text-disabled;
        margin-top: 1;
    }
    
    ToolItem .tool-actions {
        height: 3;
        margin-top: 1;
    }
    
    ToolItem .tool-actions Button {
        min-width: 8;
        margin-right: 1;
    }
    """
    
    class ViewCode(Message):
        """Tool kodunu görüntüle"""
        def __init__(self, tool_name: str):
            self.tool_name = tool_name
            super().__init__()
    
    class TestTool(Message):
        """Tool'u test et"""
        def __init__(self, tool_name: str):
            self.tool_name = tool_name
            super().__init__()
    
    class DeleteTool(Message):
        """Tool'u sil"""
        def __init__(self, tool_name: str):
            self.tool_name = tool_name
            super().__init__()
    
    def __init__(self, tool_info: dict, **kwargs):
        super().__init__(**kwargs)
        self.tool_info = tool_info
        self.tool_name = tool_info.get("name", "unknown")
    
    def compose(self) -> ComposeResult:
        name = self.tool_info.get("name", "unknown")
        desc = self.tool_info.get("description", "")[:60]
        created = self.tool_info.get("created_at", "")
        enabled = self.tool_info.get("enabled", True)
        
        # Tarih formatla
        try:
            dt = datetime.fromisoformat(created)
            date_str = dt.strftime("%d %b %H:%M")
        except:
            date_str = "?"
        
        status = "✅" if enabled else "⏸️"
        
        with Vertical():
            yield Static(f"{status} [bold green]{name}[/bold green]", classes="tool-name")
            yield Static(f"[dim]{desc}[/dim]", classes="tool-desc")
            yield Static(f"[dim]Oluşturulma: {date_str}[/dim]", classes="tool-meta")
            
            with Horizontal(classes="tool-actions"):
                yield Button("📝 Kod", id=f"view-{name}", variant="default")
                yield Button("🧪 Test", id=f"test-{name}", variant="primary")
                yield Button("🗑️", id=f"del-{name}", variant="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        event.stop()
        btn_id = event.button.id or ""
        
        if btn_id.startswith("view-"):
            self.post_message(self.ViewCode(self.tool_name))
        elif btn_id.startswith("test-"):
            self.post_message(self.TestTool(self.tool_name))
        elif btn_id.startswith("del-"):
            self.post_message(self.DeleteTool(self.tool_name))


class ToolFactoryPanel(Widget):
    """Tool Factory ana paneli"""
    
    DEFAULT_CSS = """
    ToolFactoryPanel {
        height: 100%;
        padding: 1;
    }
    
    ToolFactoryPanel #tf-header {
        height: 3;
        background: $primary-darken-2;
        padding: 1;
        margin-bottom: 1;
    }
    
    ToolFactoryPanel #tf-stats {
        height: 2;
        margin-bottom: 1;
    }
    
    ToolFactoryPanel #tf-tools-scroll {
        height: 1fr;
        border: solid $primary-lighten-3;
    }
    
    ToolFactoryPanel #tf-empty {
        text-align: center;
        padding: 3;
        color: $text-muted;
    }
    
    ToolFactoryPanel #tf-code-view {
        height: auto;
        max-height: 20;
        margin-top: 1;
        padding: 1;
        background: $surface;
        border: solid $secondary;
        display: none;
    }
    
    ToolFactoryPanel #tf-code-view.visible {
        display: block;
    }
    
    ToolFactoryPanel #tf-test-area {
        height: auto;
        margin-top: 1;
        padding: 1;
        background: $surface;
        border: solid $warning;
        display: none;
    }
    
    ToolFactoryPanel #tf-test-area.visible {
        display: block;
    }
    
    ToolFactoryPanel #tf-test-input {
        margin: 1 0;
    }
    
    ToolFactoryPanel #tf-test-result {
        margin-top: 1;
        padding: 1;
        background: $surface-darken-1;
    }
    
    ToolFactoryPanel .tf-actions {
        height: 3;
        margin-top: 1;
    }
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_test_tool = None
        self._current_code_tool = None
    
    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("[bold cyan]🔧 Tool Factory[/bold cyan]\n[dim]Agent'ın oluşturduğu custom tool'lar[/dim]", id="tf-header")
            yield Static("", id="tf-stats")
            
            yield VerticalScroll(id="tf-tools-scroll")
            
            # Kod görüntüleme alanı
            with Vertical(id="tf-code-view"):
                yield Static("", id="tf-code-title")
                yield TextArea(id="tf-code-area", read_only=True, language="python", show_line_numbers=True)
                with Horizontal(classes="tf-actions"):
                    yield Button("Kapat", id="tf-close-code", variant="default")
            
            # Test alanı
            with Vertical(id="tf-test-area"):
                yield Static("", id="tf-test-title")
                yield Input(placeholder='JSON input: {"param": "value"}', id="tf-test-input")
                with Horizontal(classes="tf-actions"):
                    yield Button("▶️ Çalıştır", id="tf-run-test", variant="success")
                    yield Button("Kapat", id="tf-close-test", variant="default")
                yield Static("", id="tf-test-result")
            
            with Horizontal(classes="tf-actions"):
                yield Button("🔄 Yenile", id="tf-refresh", variant="primary")
    
    def on_mount(self) -> None:
        self.refresh_tools()
    
    def refresh_tools(self) -> None:
        """Tool listesini yenile"""
        tools = get_tool_list()
        scroll = self.query_one("#tf-tools-scroll", VerticalScroll)
        scroll.remove_children()
        
        # Stats güncelle
        loaded = len(_custom_tools)
        total = len(tools)
        stats = self.query_one("#tf-stats", Static)
        stats.update(f"[cyan]Toplam:[/cyan] {total} tool | [green]Yüklü:[/green] {loaded}")
        
        if not tools:
            scroll.mount(Static(
                "[dim]Henüz custom tool yok.\n\n"
                "Agent'a 'create_tool' kullanarak\n"
                "yeni tool oluşturmasını söyleyin.[/dim]",
                id="tf-empty"
            ))
            return
        
        for tool_info in tools:
            scroll.mount(ToolItem(tool_info))
    
    def on_tool_item_view_code(self, event: ToolItem.ViewCode) -> None:
        """Tool kodunu göster"""
        event.stop()
        self._current_code_tool = event.tool_name
        
        # Kodu al
        _load_registry()
        if event.tool_name in _tool_registry:
            code = _tool_registry[event.tool_name].get("code", "# Kod bulunamadı")
            desc = _tool_registry[event.tool_name].get("description", "")
        else:
            code = "# Tool bulunamadı"
            desc = ""
        
        # UI güncelle
        self.query_one("#tf-code-title", Static).update(
            f"[bold cyan]📝 {event.tool_name}[/bold cyan]\n[dim]{desc}[/dim]"
        )
        self.query_one("#tf-code-area", TextArea).text = code
        self.query_one("#tf-code-view").add_class("visible")
        self.query_one("#tf-test-area").remove_class("visible")
    
    def on_tool_item_test_tool(self, event: ToolItem.TestTool) -> None:
        """Tool test alanını aç"""
        event.stop()
        self._current_test_tool = event.tool_name
        
        self.query_one("#tf-test-title", Static).update(
            f"[bold yellow]🧪 Test: {event.tool_name}[/bold yellow]"
        )
        self.query_one("#tf-test-input", Input).value = ""
        self.query_one("#tf-test-result", Static).update("")
        self.query_one("#tf-test-area").add_class("visible")
        self.query_one("#tf-code-view").remove_class("visible")
        self.query_one("#tf-test-input", Input).focus()
    
    def on_tool_item_delete_tool(self, event: ToolItem.DeleteTool) -> None:
        """Tool'u sil"""
        event.stop()
        result = delete_tool_func.invoke({"name": event.tool_name})
        self.app.notify(result, severity="information", timeout=3)
        self.refresh_tools()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        
        if btn_id == "tf-refresh":
            self.refresh_tools()
            self.app.notify("Tool listesi yenilendi", timeout=2)
        
        elif btn_id == "tf-close-code":
            self.query_one("#tf-code-view").remove_class("visible")
            self._current_code_tool = None
        
        elif btn_id == "tf-close-test":
            self.query_one("#tf-test-area").remove_class("visible")
            self._current_test_tool = None
        
        elif btn_id == "tf-run-test":
            self._run_test()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Test input'unda Enter basıldığında"""
        if event.input.id == "tf-test-input":
            self._run_test()
    
    def _run_test(self) -> None:
        """Test'i çalıştır"""
        if not self._current_test_tool:
            return
        
        test_input = self.query_one("#tf-test-input", Input).value.strip()
        if not test_input:
            test_input = "{}"
        
        result = test_tool_func.invoke({
            "name": self._current_test_tool,
            "test_input": test_input
        })
        
        self.query_one("#tf-test-result", Static).update(result)
