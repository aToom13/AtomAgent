"""
Session Sidebar - Sol tarafta geçmiş sohbetleri gösteren panel
"""
from textual.app import ComposeResult
from textual.containers import Vertical, VerticalScroll, Horizontal
from textual.widgets import Button, Static, Label
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from rich.text import Text
from datetime import datetime

from core.session_manager import session_manager, Session
from utils.logger import get_logger

logger = get_logger()


class SessionItem(Vertical):
    """Tek bir session item'ı"""
    
    # Styles moved to ui/styles.py
    
    class Selected(Message):
        """Session seçildiğinde gönderilen mesaj"""
        def __init__(self, session: Session):
            self.session = session
            super().__init__()
    
    class DeleteRequested(Message):
        """Session silinmek istendiğinde gönderilen mesaj"""
        def __init__(self, session: Session):
            self.session = session
            super().__init__()
    
    def __init__(self, session: Session, is_active: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.session = session
        self.is_active = is_active
    
    def compose(self) -> ComposeResult:
        # Başlığı kısalt
        title = self.session.title[:18]
        if len(self.session.title) > 18:
            title += "..."
        
        # Tarihi formatla
        try:
            dt = datetime.fromisoformat(self.session.updated_at)
            date_str = dt.strftime("%d/%m %H:%M")
        except:
            date_str = "?"
        
        # Basit layout - tek satırda başlık ve silme butonu
        with Horizontal(classes="session-row"):
            yield Static(f"[bold]{title}[/bold]", classes="session-title")
            yield Button("✕", classes="btn-delete", id=f"del-{self.session.id}")
        yield Static(f"[dim]{date_str} • {self.session.message_count} msg[/dim]", classes="session-meta")
    
    def on_mount(self) -> None:
        if self.is_active:
            self.add_class("active")
    
    def on_click(self, event) -> None:
        """Tıklandığında session'ı seç (delete butonu hariç)"""
        # Delete butonuna tıklandıysa seçme
        if hasattr(event, 'widget') and isinstance(event.widget, Button):
            return
        self.post_message(self.Selected(self.session))
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Delete butonuna tıklandığında"""
        if event.button.has_class("btn-delete"):
            event.stop()
            self.post_message(self.DeleteRequested(self.session))


class SessionSidebar(Vertical):
    """Session sidebar widget'ı"""
    
    # Styles moved to ui/styles.py
    
    # Reactive: aktif session ID
    active_session_id = reactive("")
    
    class SessionSelected(Message):
        """Session seçildiğinde parent'a gönderilen mesaj"""
        def __init__(self, session: Session):
            self.session = session
            super().__init__()
    
    class NewSessionRequested(Message):
        """Yeni session istendiğinde gönderilen mesaj"""
        pass
    
    class SessionDeleted(Message):
        """Session silindiğinde parent'a gönderilen mesaj"""
        def __init__(self, session_id: str):
            self.session_id = session_id
            super().__init__()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sessions: list[Session] = []
    
    def compose(self) -> ComposeResult:
        yield Label("📚 Sohbetler", id="sidebar-header")
        
        with Vertical(id="sidebar-actions"):
            yield Button("+ Yeni Sohbet", id="btn-new-session", variant="success")
        
        with VerticalScroll(id="session-list-scroll"):
            yield Vertical(id="session-list")
        
        yield Static("[dim]Ctrl+H: Tüm geçmiş[/dim]", id="sidebar-footer")
    
    def on_mount(self) -> None:
        logger.info("SessionSidebar on_mount called")
        # Widget'lar tam mount olduktan sonra refresh yap
        self.call_after_refresh(self.refresh_sessions)
    
    def refresh_sessions(self, limit: int = 15):
        """Session listesini yenile"""
        self.sessions = session_manager.list_sessions(limit=limit)
        logger.info(f"Sidebar refresh: {len(self.sessions)} sessions loaded")
        self._render_sessions()
    
    def _render_sessions(self):
        """Session'ları render et"""
        logger.info(f"_render_sessions called with {len(self.sessions)} sessions")
        
        try:
            session_list = self.query_one("#session-list", Vertical)
        except Exception as e:
            logger.error(f"Cannot find #session-list: {e}")
            return
        
        session_list.remove_children()
        
        if not self.sessions:
            logger.info("Sidebar render: No sessions to display")
            session_list.mount(Static("[dim]Henüz sohbet yok[/dim]", classes="no-sessions"))
            return
        
        logger.info(f"Sidebar render: Rendering {len(self.sessions)} sessions")
        for i, session in enumerate(self.sessions):
            is_active = session.id == self.active_session_id
            logger.info(f"  [{i}] {session.id}: {session.title[:20]}")
            item = SessionItem(session, is_active=is_active)
            session_list.mount(item)
    
    def set_active_session(self, session_id: str, refresh: bool = True):
        """Aktif session'ı ayarla"""
        self.active_session_id = session_id
        if refresh:
            self.refresh_sessions()
        else:
            self._render_sessions()
    
    def on_session_item_selected(self, event: SessionItem.Selected) -> None:
        """Session item seçildiğinde"""
        event.stop()
        self.post_message(self.SessionSelected(event.session))
    
    def on_session_item_delete_requested(self, event: SessionItem.DeleteRequested) -> None:
        """Session silme isteği geldiğinde"""
        event.stop()
        session = event.session
        
        # Aktif session silinmeye çalışılıyorsa uyar
        if session.id == self.active_session_id:
            self.app.notify("Aktif session silinemez!", severity="warning", timeout=2)
            return
        
        # Session'ı sil
        if session_manager.delete_session(session.id):
            self.app.notify(f"Silindi: {session.title[:20]}", severity="information", timeout=2)
            self.post_message(self.SessionDeleted(session.id))
            self.refresh_sessions()
        else:
            self.app.notify("Silinemedi!", severity="error", timeout=2)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Buton tıklandığında"""
        if event.button.id == "btn-new-session":
            event.stop()
            self.post_message(self.NewSessionRequested())
    
    def watch_active_session_id(self, new_id: str) -> None:
        """Aktif session değiştiğinde"""
        # Tüm item'ların active class'ını güncelle
        for item in self.query(SessionItem):
            if item.session.id == new_id:
                item.add_class("active")
            else:
                item.remove_class("active")
