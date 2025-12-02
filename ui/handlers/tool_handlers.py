"""
Tool Output Handlers - Dashboard'da tool çıktılarını gösterir
"""
import json
from rich.text import Text
from textual.widgets import Static, DirectoryTree, TabbedContent

from utils.logger import get_logger

logger = get_logger()

# Tool status mapping
TOOL_STATUS_MAP = {
    "call_coder": ("🔧 Coder", "green"),
    "call_researcher": ("🔍 Researcher", "cyan"),
    "create_plan": ("📋 Plan", "yellow"),
    "get_next_todo_step": ("📋 Todo", "yellow"),
    "mark_todo_done": ("✅ Todo Done", "green"),
    "get_current_todo": ("📋 Todo", "yellow"),
    "search_codebase": ("🧠 RAG Search", "magenta"),
    "refresh_memory": ("🧠 Memory Refresh", "magenta"),
    "lint_and_fix": ("✨ Code Polish", "magenta"),
    "check_syntax": ("🔍 Syntax Check", "yellow"),
    # Git tools
    "git_init": ("📦 Git Init", "blue"),
    "git_status": ("📊 Git Status", "blue"),
    "git_add": ("➕ Git Add", "blue"),
    "git_commit": ("💾 Git Commit", "green"),
    "git_log": ("📜 Git Log", "blue"),
    "git_diff": ("📝 Git Diff", "blue"),
    "git_branch": ("🌿 Git Branch", "blue"),
    "git_stash": ("📦 Git Stash", "blue"),
    "git_reset": ("⏪ Git Reset", "yellow"),
    # Test tools
    "run_tests": ("🧪 Tests", "cyan"),
    "run_single_test": ("🧪 Test", "cyan"),
    "create_test_file": ("📝 Create Test", "cyan"),
    "list_tests": ("📋 List Tests", "cyan"),
    "test_coverage": ("📊 Coverage", "cyan"),
    "run_unittest": ("🧪 Unittest", "cyan"),
}


class ToolOutputHandler:
    """Tool çıktılarını işleyen sınıf"""
    
    def __init__(self, app):
        self.app = app
    
    def get_status(self, tool_name: str) -> tuple:
        """Tool için status ve renk döndür"""
        return TOOL_STATUS_MAP.get(tool_name, (tool_name, "white"))
    
    async def handle(self, tool_name: str, output: str, dashboard):
        """Tool çıktısını dashboard'a ekle"""
        short_output = output[:500] + "..." if len(output) > 500 else output
        
        handler_method = getattr(self, f"_handle_{tool_name}", None)
        if handler_method:
            await handler_method(output, short_output, dashboard)
        else:
            await self._handle_default(tool_name, dashboard)
        
        dashboard.scroll_end()
    
    async def _handle_call_coder(self, output: str, short_output: str, dashboard):
        self.app.query_one("#workspace-tree", DirectoryTree).reload()
        
        # Permission mesajı kontrolü (coder içinden gelebilir)
        if "PERMISSION_REQUIRED:" in output:
            perm_idx = output.find("PERMISSION_REQUIRED:")
            perm_part = output[perm_idx:]
            parts = perm_part.split(":")
            if len(parts) >= 3:
                base_cmd = parts[1]
                full_cmd = ":".join(parts[2:])
                await self.app._show_permission_dialog(base_cmd, full_cmd)
                return
        
        # Rate limit / key rotation bildirimi
        if "API key rotated" in output or "Switched to fallback" in output:
            self.app.notify("🔄 API key değiştirildi", severity="warning", timeout=3)
            # API key durumunu güncelle
            if hasattr(self.app, '_show_api_key_status'):
                self.app._show_api_key_status()
        
        text = Text()
        text.append("✓ Coder: ", style="green")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_call_researcher(self, output: str, short_output: str, dashboard):
        # Rate limit / key rotation bildirimi
        if "API key rotated" in output or "Switched to fallback" in output:
            self.app.notify("🔄 API key değiştirildi", severity="warning", timeout=3)
            if hasattr(self.app, '_show_api_key_status'):
                self.app._show_api_key_status()
        
        text = Text()
        text.append("✓ Researcher: ", style="cyan")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_create_plan(self, output: str, short_output: str, dashboard):
        await dashboard.mount(Static(Text("✓ Plan oluşturuldu", style="yellow"), classes="tool-card"))
    
    async def _handle_write_file(self, output: str, short_output: str, dashboard):
        self.app.query_one("#workspace-tree", DirectoryTree).reload()
        await dashboard.mount(Static(Text("✓ write_file", style="green"), classes="tool-card"))
    
    async def _handle_delete_file(self, output: str, short_output: str, dashboard):
        self.app.query_one("#workspace-tree", DirectoryTree).reload()
        await dashboard.mount(Static(Text("✓ delete_file", style="green"), classes="tool-card"))
    
    async def _handle_create_directory(self, output: str, short_output: str, dashboard):
        self.app.query_one("#workspace-tree", DirectoryTree).reload()
        await dashboard.mount(Static(Text("✓ create_directory", style="green"), classes="tool-card"))
    
    async def _handle_update_todo_list(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📋 Todo güncellendi", style="yellow")
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_mark_todo_done(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("✅ ", style="green")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_get_next_todo_step(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📋 ", style="yellow")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_get_current_todo(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📋 ", style="yellow")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_run_terminal_command(self, output: str, short_output: str, dashboard):
        # Permission mesajı kontrolü (sub-agent'tan gelebilir)
        if "PERMISSION_REQUIRED:" in output:
            perm_idx = output.find("PERMISSION_REQUIRED:")
            perm_part = output[perm_idx:]
            parts = perm_part.split(":")
            if len(parts) >= 3:
                base_cmd = parts[1]
                full_cmd = ":".join(parts[2:])
                await self.app._show_permission_dialog(base_cmd, full_cmd)
                return
        
        text = Text()
        text.append("Terminal: ", style="cyan")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_web_search(self, output: str, short_output: str, dashboard):
        try:
            results = json.loads(output)
            for r in results[:3]:
                title = r.get('title', '')[:50]
                text = Text()
                text.append("• ", style="blue")
                text.append(title)
                await dashboard.mount(Static(text, classes="tool-card"))
        except:
            text = Text()
            text.append("Search: ", style="blue")
            text.append(short_output)
            await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_search_codebase(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("🧠 Hafıza Tarandı: ", style="bold magenta")
        file_count = output.count("📄")
        if file_count > 0:
            text.append(f"{file_count} ilgili dosya bulundu")
        else:
            text.append(short_output[:100])
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_refresh_memory(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("🧠 Hafıza Güncellendi: ", style="bold magenta")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_lint_and_fix(self, output: str, short_output: str, dashboard):
        text = Text()
        if "successfully" in output.lower():
            text.append("✨ Code Polished: ", style="bold green")
            text.append("Kod formatlandı ve temizlendi")
        elif "error" in output.lower():
            text.append("✨ Lint Error: ", style="bold red")
            text.append(short_output)
        else:
            text.append("✨ Code Polish: ", style="bold magenta")
            text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_check_syntax(self, output: str, short_output: str, dashboard):
        text = Text()
        if "OK" in output:
            text.append("✓ Syntax OK", style="bold green")
        else:
            text.append("⚠ Syntax Error: ", style="bold red")
            text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    # Git handlers
    async def _handle_git_status(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📊 Git Status:\n", style="bold blue")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_git_commit(self, output: str, short_output: str, dashboard):
        text = Text()
        if "✓" in output:
            text.append("💾 ", style="green")
            text.append(short_output)
        else:
            text.append("Git Commit: ", style="blue")
            text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_git_log(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📜 Git Log:\n", style="bold blue")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_git_diff(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📝 Git Diff:\n", style="bold blue")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    # Test handlers
    async def _handle_run_tests(self, output: str, short_output: str, dashboard):
        text = Text()
        if "✅" in output or "passed" in output.lower():
            text.append("🧪 Tests Passed:\n", style="bold green")
        elif "❌" in output or "failed" in output.lower():
            text.append("🧪 Tests Failed:\n", style="bold red")
        else:
            text.append("🧪 Test Results:\n", style="bold cyan")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_run_single_test(self, output: str, short_output: str, dashboard):
        text = Text()
        if "✅" in output or "BAŞARILI" in output:
            text.append("✅ Test Passed\n", style="bold green")
        else:
            text.append("❌ Test Failed\n", style="bold red")
        text.append(short_output[:300])
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_create_test_file(self, output: str, short_output: str, dashboard):
        self.app.query_one("#workspace-tree", DirectoryTree).reload()
        text = Text()
        text.append("📝 ", style="cyan")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_list_tests(self, output: str, short_output: str, dashboard):
        text = Text()
        text.append("📋 Tests:\n", style="bold cyan")
        text.append(short_output)
        await dashboard.mount(Static(text, classes="tool-card"))
    
    async def _handle_default(self, tool_name: str, dashboard):
        await dashboard.mount(Static(Text(tool_name, style="dim"), classes="tool-card"))
