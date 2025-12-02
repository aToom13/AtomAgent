"""
Session Management UI Widgets
"""
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.widgets import Button, Static, Input, Label, ListView, ListItem
from textual.binding import Binding
from rich.text import Text
from datetime import datetime

from core.session_manager import session_manager, Session
from utils.logger import get_logger

logger = get_logger()


class SessionListItem(ListItem):
    """Session list item widget"""
    
    def __init__(self, session: Session):
        super().__init__()
        self.session = session
    
    def compose(self) -> ComposeResult:
        # Format date
        try:
            dt = datetime.fromisoformat(self.session.updated_at)
            date_str = dt.strftime("%d/%m %H:%M")
        except:
            date_str = "?"
        
        # Truncate title
        title = self.session.title[:40]
        if len(self.session.title) > 40:
            title += "..."
        
        yield Static(
            f"[bold]{title}[/bold]\n"
            f"[dim]{date_str} • {self.session.message_count} mesaj[/dim]",
            classes="session-item-content"
        )


class SessionBrowserModal(ModalScreen):
    """Session tarayıcı modal'ı"""
    
    CSS = """
    SessionBrowserModal {
        align: center middle;
    }
    
    #session-browser-container {
        width: 70;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #session-browser-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding-bottom: 1;
    }
    
    #session-search {
        margin-bottom: 1;
    }
    
    #session-list-scroll {
        height: 18;
        border: solid $primary-darken-2;
        margin-bottom: 1;
    }
    
    .session-item-content {
        padding: 0 1;
    }
    
    #session-buttons {
        height: 3;
        align: center middle;
    }
    
    #session-buttons Button {
        margin: 0 1;
    }
    
    #session-stats {
        text-align: center;
        color: $text-muted;
    }
    
    ListView > ListItem {
        padding: 0;
    }
    
    ListView > ListItem:hover {
        background: $primary-darken-3;
    }
    
    ListView > ListItem.-selected {
        background: $primary-darken-2;
    }
    """
    
    BINDINGS = [
        Binding("escape", "cancel", "İptal"),
        Binding("enter", "select", "Seç"),
        Binding("delete", "delete", "Sil"),
    ]
    
    def __init__(self, callback=None):
        super().__init__()
        self.callback = callback
        self.sessions: list[Session] = []
        self.selected_session: Session = None
    
    def compose(self) -> ComposeResult:
        with Vertical(id="session-browser-container"):
            yield Label("📚 Konuşma Geçmişi", id="session-browser-title")
            yield Input(placeholder="Ara...", id="session-search")
            
            with VerticalScroll(id="session-list-scroll"):
                yield ListView(id="session-list")
            
            yield Static("", id="session-stats")
            
            with Horizontal(id="session-buttons"):
                yield Button("Aç", id="btn-open", variant="primary")
                yield Button("Sil", id="btn-delete", variant="error")
                yield Button("Export", id="btn-export", variant="default")
                yield Button("İptal", id="btn-cancel", variant="default")
    
    def on_mount(self) -> None:
        self._load_sessions()
        self._update_stats()
    
    def _load_sessions(self, query: str = None):
        """Session listesini yükle"""
        list_view = self.query_one("#session-list", ListView)
        list_view.clear()
        
        if query:
            self.sessions = session_manager.search_sessions(query, limit=50)
        else:
            self.sessions = session_manager.list_sessions(limit=50)
        
        for session in self.sessions:
            list_view.append(SessionListItem(session))
    
    def _update_stats(self):
        """İstatistikleri güncelle"""
        stats = session_manager.get_stats()
        self.query_one("#session-stats", Static).update(
            f"[dim]Toplam: {stats['total_sessions']} konuşma, {stats['total_messages']} mesaj[/dim]"
        )
    
    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "session-search":
            query = event.value.strip()
            self._load_sessions(query if query else None)
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, SessionListItem):
            self.selected_session = event.item.session
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(None)
        
        elif event.button.id == "btn-open":
            self._open_selected()
        
        elif event.button.id == "btn-delete":
            self._delete_selected()
        
        elif event.button.id == "btn-export":
            self._export_selected()
    
    def _open_selected(self):
        """Seçili session'ı aç"""
        list_view = self.query_one("#session-list", ListView)
        
        if list_view.highlighted_child and isinstance(list_view.highlighted_child, SessionListItem):
            self.selected_session = list_view.highlighted_child.session
        
        if self.selected_session:
            self.dismiss(self.selected_session)
        else:
            self.notify("Bir konuşma seçin", severity="warning")
    
    def _delete_selected(self):
        """Seçili session'ı sil"""
        list_view = self.query_one("#session-list", ListView)
        
        if list_view.highlighted_child and isinstance(list_view.highlighted_child, SessionListItem):
            session = list_view.highlighted_child.session
            
            if session_manager.delete_session(session.id):
                self.notify(f"Silindi: {session.title[:30]}", severity="information")
                self._load_sessions()
                self._update_stats()
            else:
                self.notify("Silinemedi", severity="error")
    
    def _export_selected(self):
        """Seçili session'ı export et"""
        list_view = self.query_one("#session-list", ListView)
        
        if list_view.highlighted_child and isinstance(list_view.highlighted_child, SessionListItem):
            session = list_view.highlighted_child.session
            
            import json
            import os
            from config import config
            
            data = session_manager.export_session(session.id)
            if data:
                filename = f"session_export_{session.id}.json"
                filepath = os.path.join(config.workspace.base_dir, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                self.notify(f"Export: {filename}", severity="information")
            else:
                self.notify("Export başarısız", severity="error")
    
    def action_cancel(self) -> None:
        self.dismiss(None)
    
    def action_select(self) -> None:
        self._open_selected()
    
    def action_delete(self) -> None:
        self._delete_selected()


class SessionInfoWidget(Static):
    """Aktif session bilgisi widget'ı"""
    
    DEFAULT_CSS = """
    SessionInfoWidget {
        height: auto;
        padding: 1;
        background: $surface;
        border: solid $primary-darken-2;
        margin-bottom: 1;
    }
    """
    
    def __init__(self, session: Session = None, **kwargs):
        super().__init__(**kwargs)
        self.session = session
    
    def update_session(self, session: Session):
        """Session bilgisini güncelle"""
        self.session = session
        self._refresh_display()
    
    def _refresh_display(self):
        if not self.session:
            self.update("[dim]Session yok[/dim]")
            return
        
        try:
            dt = datetime.fromisoformat(self.session.created_at)
            date_str = dt.strftime("%d %b %Y %H:%M")
        except:
            date_str = "?"
        
        self.update(
            f"[bold cyan]📝 {self.session.title[:35]}[/bold cyan]\n"
            f"[dim]ID: {self.session.id}[/dim]\n"
            f"[dim]Oluşturulma: {date_str}[/dim]\n"
            f"[dim]Mesaj: {self.session.message_count}[/dim]"
        )
    
    def on_mount(self) -> None:
        self._refresh_display()


class RenameSessionModal(ModalScreen):
    """Session yeniden adlandırma modal'ı"""
    
    CSS = """
    RenameSessionModal {
        align: center middle;
    }
    
    #rename-container {
        width: 50;
        height: 12;
        background: $surface;
        border: thick $primary;
        padding: 1 2;
    }
    
    #rename-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #rename-input {
        margin-bottom: 1;
    }
    
    #rename-buttons {
        height: 3;
        align: center middle;
    }
    
    #rename-buttons Button {
        margin: 0 1;
    }
    """
    
    def __init__(self, session: Session, callback=None):
        super().__init__()
        self.session = session
        self.callback = callback
    
    def compose(self) -> ComposeResult:
        with Vertical(id="rename-container"):
            yield Label("✏️ Konuşmayı Yeniden Adlandır", id="rename-title")
            yield Input(value=self.session.title, id="rename-input")
            
            with Horizontal(id="rename-buttons"):
                yield Button("Kaydet", id="btn-save", variant="primary")
                yield Button("İptal", id="btn-cancel", variant="default")
    
    def on_mount(self) -> None:
        self.query_one("#rename-input", Input).focus()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
        
        elif event.button.id == "btn-save":
            new_title = self.query_one("#rename-input", Input).value.strip()
            if new_title:
                session_manager.update_session(self.session.id, title=new_title)
                self.dismiss(True)
            else:
                self.notify("Başlık boş olamaz", severity="warning")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        new_title = event.value.strip()
        if new_title:
            session_manager.update_session(self.session.id, title=new_title)
            self.dismiss(True)
