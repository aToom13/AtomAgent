from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Container
from textual.widgets import Header, Footer, Input, Markdown, Label, Static, DirectoryTree, TextArea, RichLog
from textual.binding import Binding
from rich.text import Text
from langchain_core.messages import HumanMessage, SystemMessage
from core.agent import get_agent_executor
from ui.ide_styles import IDE_CSS
import json
import os

# Workspace Directory
WORKSPACE_DIR = os.path.abspath("atom_workspace")

class AtomIDE(App):
    CSS = IDE_CSS

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+d", "toggle_dark", "Toggle Dark Mode"),
        Binding("ctrl+s", "save_file", "Save File"),
        Binding("f5", "run_active_file", "Run File"),
    ]

    def __init__(self):
        super().__init__()
        self.title = "AtomIDE Pro"
        
        # Initialize Agent
        self.agent_executor, self.memory, self.system_prompt = get_agent_executor()
        self.current_file_path = None

    def compose(self) -> ComposeResult:
        # Left Panel: Sidebar
        with Vertical(id="sidebar"):
            yield Label("EXPLORER", id="sidebar-header")
            yield DirectoryTree(WORKSPACE_DIR, id="workspace-tree")

        # Middle Container: Editor + Terminal
        with Vertical(id="middle-container"):
            # Top: Editor
            with Vertical(id="editor-area"):
                yield Label("[No File Opened]", id="editor-header")
                yield TextArea(language="python", show_line_numbers=True, id="code-editor")
            
            # Bottom: Terminal
            with Vertical(id="terminal-panel"):
                yield Label("TERMINAL / OUTPUT", id="terminal-header")
                yield RichLog(id="terminal-log", highlight=True, markup=True)

        # Right Panel: AI Chat
        with Vertical(id="ai-panel"):
            yield Label("AI ASSISTANT", id="ai-header")
            yield Vertical(id="chat-scroll", classes="chat-container") # Using Vertical for scrollable container
            yield Input(placeholder="Ask AI...", id="user-input")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#user-input").focus()
        terminal = self.query_one("#terminal-log", RichLog)
        terminal.write("[bold green]System Initialized.[/bold green]")
        terminal.write(f"[dim]Workspace: {WORKSPACE_DIR}[/dim]")
        
        # Initial Chat Message
        chat_container = self.query_one("#chat-scroll")
        chat_container.mount(Markdown("**AGENT:** Ready to help! 🚀", classes="ai-msg"))

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Called when a file is selected in the DirectoryTree."""
        event.stop()
        file_path = event.path
        
        if not os.path.isfile(file_path):
            return

        self.current_file_path = file_path
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Detect language
            ext = os.path.splitext(file_path)[1].lower()
            language = "python"
            if ext == ".md": language = "markdown"
            elif ext == ".json": language = "json"
            elif ext in [".html", ".htm"]: language = "html"
            elif ext == ".css": language = "css"
            elif ext == ".js": language = "javascript"
            
            # Update Editor Header
            self.query_one("#editor-header").update(f"📄 {os.path.basename(file_path)}")
            
            # Update Editor
            editor = self.query_one("#code-editor", TextArea)
            editor.text = content
            editor.language = language
            editor.cursor_location = (0, 0)
            editor.focus()
            
        except Exception as e:
            self.notify(f"Error opening file: {e}", severity="error")

    def action_save_file(self) -> None:
        """Saves the current file."""
        if not self.current_file_path:
            return
            
        try:
            editor = self.query_one("#code-editor", TextArea)
            content = editor.text
            
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.notify(f"Saved: {os.path.basename(self.current_file_path)}")
            
        except Exception as e:
            self.notify(f"Error saving file: {e}", severity="error")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        user_input = message.value
        if not user_input.strip():
            return

        # Clear input
        self.query_one("#user-input").value = ""
        
        # Display User Message in Chat
        chat_container = self.query_one("#chat-scroll")
        await chat_container.mount(Markdown(f"**USER:** {user_input}", classes="user-msg"))
        
        # Start Agent Worker
        self.run_worker(self.run_agent(user_input), exclusive=True)

    def action_run_active_file(self) -> None:
        """Runs the currently active file."""
        if not self.current_file_path:
            self.notify("No file open to run!", severity="warning")
            return
            
        terminal = self.query_one("#terminal-log", RichLog)
        filename = os.path.basename(self.current_file_path)
        ext = os.path.splitext(filename)[1].lower()
        
        command = ""
        if ext == ".py":
            command = f"python {filename}"
        elif ext == ".js":
            command = f"node {filename}"
        else:
            self.notify(f"Cannot run {ext} files directly.", severity="warning")
            return
            
        terminal.write(f"[bold yellow]>> Executing: {filename}...[/bold yellow]")
        
        # Execute using subprocess (Blocking for simplicity in this version, 
        # ideally should be async or worker for long running tasks)
        import subprocess
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=WORKSPACE_DIR, 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.stdout:
                terminal.write(f"[green]{result.stdout}[/green]")
            if result.stderr:
                terminal.write(f"[red]{result.stderr}[/red]")
                
        except Exception as e:
            terminal.write(f"[bold red]Execution Error: {e}[/bold red]")

    # ... (on_input_submitted remains same)

    async def run_agent(self, user_input: str):
        chat_container = self.query_one("#chat-scroll")
        terminal = self.query_one("#terminal-log", RichLog)
        
        # Agent Thinking Message
        ai_response_md = Markdown("**AGENT:** [blink]Thinking...[/blink]", classes="ai-msg")
        await chat_container.mount(ai_response_md)
        
        final_text = ""
        
        try:
            memory_vars = self.memory.load_memory_variables({})
            history_messages = memory_vars.get("history", [])
            messages = [SystemMessage(content=self.system_prompt)] + history_messages + [HumanMessage(content=user_input)]
            
            terminal.write(f"[dim]🚀 Process started: {user_input[:50]}...[/dim]")

            async for event in self.agent_executor.astream_events(
                {"messages": messages},
                version="v1"
            ):
                kind = event["event"]
                
                if kind == "on_chat_model_stream":
                    # Filter out Supervisor's JSON output
                    metadata = event.get('metadata', {})
                    if metadata.get('langgraph_node') == "Supervisor":
                        continue
                        
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        if not final_text:
                            ai_response_md.update(f"**AGENT:** ")
                        final_text += chunk.content
                        ai_response_md.update(f"**AGENT:** {final_text} █")
                
                elif kind == "on_tool_start":
                    tool_name = event['name']
                    
                    # Try to get agent name from metadata
                    metadata = event.get('metadata', {})
                    agent_name = metadata.get('langgraph_node', '')
                    log_prefix = f"[{agent_name}] " if agent_name else ""

                    terminal.write(f"[bold cyan]▶️ Tool Start:[/bold cyan] {log_prefix}{tool_name}")
                    if not final_text:
                        ai_response_md.update(f"**AGENT:** [⚙️ {log_prefix}Running {tool_name}...]")

                elif kind == "on_tool_end":
                    tool_name = event['name']
                    output = str(event['data'].get('output'))
                    
                    # Special handling for run_terminal_command
                    if tool_name == "run_terminal_command":
                        terminal.write(f"[bold green]✓ Execution Result:[/bold green]")
                        terminal.write(output) # Write full output to terminal
                        if not final_text:
                             ai_response_md.update(f"**AGENT:** [Command executed. Check terminal for output.]")
                    
                    # Special handling for visit_webpage
                    elif tool_name == "visit_webpage":
                        # Extract URL from event input if available, otherwise just show success
                        input_data = event.get('data', {}).get('input', {})
                        url = input_data.get('url', 'URL') if isinstance(input_data, dict) else 'URL'
                        terminal.write(f"[bold cyan]🌐 Site Ziyaret Edildi:[/bold cyan] {url}")
                        terminal.write(f"[dim]Content Length: {len(output)} chars[/dim]")
                        
                    else:
                        terminal.write(f"[bold green]✓ Tool End:[/bold green] {tool_name}")
                        terminal.write(f"[dim]{output[:200]}...[/dim]") # Truncate others
                    
                    if tool_name in ["write_file", "delete_file", "create_directory"]:
                        self.query_one("#workspace-tree").reload()

            if not final_text:
                final_text = "[Done]"
            ai_response_md.update(f"**AGENT:** {final_text}")
            
            self.memory.save_context({"input": user_input}, {"output": final_text})
            
        except Exception as e:
            terminal.write(f"[bold red]CRITICAL ERROR:[/bold red] {str(e)}")
            ai_response_md.update(f"**AGENT:** Error occurred. Check terminal.")

if __name__ == "__main__":
    app = AtomIDE()
    app.run()
