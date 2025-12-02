"""
Session Manager - Conversation History & Session Persistence
SQLite tabanlı kalıcı session storage
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from config import config
from utils.logger import get_logger

logger = get_logger()

# Database path
DB_PATH = os.path.join(config.memory.checkpoint_dir, "sessions.db")


@dataclass
class Message:
    """Tek bir mesaj"""
    role: str  # "human", "ai", "system", "tool"
    content: str
    timestamp: str
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }
    
    @staticmethod
    def from_dict(data: dict) -> "Message":
        return Message(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata")
        )


@dataclass
class Session:
    """Bir konuşma oturumu"""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
            "summary": self.summary,
            "tags": self.tags or []
        }


class SessionManager:
    """Session ve conversation history yönetimi"""
    
    def __init__(self):
        self._init_db()
    
    @contextmanager
    def _get_conn(self):
        """Thread-safe connection context manager"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_db(self):
        """Veritabanı tablolarını oluştur"""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Sessions tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    summary TEXT,
                    tags TEXT
                )
            """)
            
            # Messages tablosu
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                )
            """)
            
            # Index for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_session 
                ON messages(session_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_updated 
                ON sessions(updated_at DESC)
            """)
            
            logger.info("Session database initialized")
    
    # === SESSION OPERATIONS ===
    
    def create_session(self, session_id: str = None, title: str = None) -> Session:
        """Yeni session oluştur"""
        now = datetime.now().isoformat()
        
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not title:
            title = f"Konuşma - {datetime.now().strftime('%d %b %Y %H:%M')}"
        
        session = Session(
            id=session_id,
            title=title,
            created_at=now,
            updated_at=now,
            message_count=0
        )
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO sessions (id, title, created_at, updated_at, message_count, summary, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session.id, session.title, session.created_at, session.updated_at, 
                  session.message_count, session.summary, json.dumps(session.tags or [])))
        
        logger.info(f"Session created: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Session bilgilerini getir"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                return Session(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    message_count=row["message_count"],
                    summary=row["summary"],
                    tags=json.loads(row["tags"]) if row["tags"] else []
                )
        return None
    
    def list_sessions(self, limit: int = 20, offset: int = 0) -> List[Session]:
        """Session listesi (en son güncellenen önce)"""
        sessions = []
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions 
                ORDER BY updated_at DESC 
                LIMIT ? OFFSET ?
            """, (limit, offset))
            
            rows = cursor.fetchall()
            logger.info(f"list_sessions: Found {len(rows)} sessions in DB")
            
            for row in rows:
                sessions.append(Session(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    message_count=row["message_count"],
                    summary=row["summary"],
                    tags=json.loads(row["tags"]) if row["tags"] else []
                ))
        
        return sessions
    
    def update_session(self, session_id: str, title: str = None, 
                       summary: str = None, tags: List[str] = None) -> bool:
        """Session bilgilerini güncelle"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            updates = ["updated_at = ?"]
            values = [datetime.now().isoformat()]
            
            if title:
                updates.append("title = ?")
                values.append(title)
            if summary:
                updates.append("summary = ?")
                values.append(summary)
            if tags is not None:
                updates.append("tags = ?")
                values.append(json.dumps(tags))
            
            values.append(session_id)
            
            cursor.execute(f"""
                UPDATE sessions SET {', '.join(updates)} WHERE id = ?
            """, values)
            
            return cursor.rowcount > 0
    
    def delete_session(self, session_id: str) -> bool:
        """Session ve mesajlarını sil"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Önce mesajları sil
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            # Sonra session'ı sil
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            
            if cursor.rowcount > 0:
                logger.info(f"Session deleted: {session_id}")
                return True
        return False
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Session]:
        """Session'larda arama (title ve summary'de)"""
        sessions = []
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT s.* FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.title LIKE ? OR s.summary LIKE ? OR m.content LIKE ?
                ORDER BY s.updated_at DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", limit))
            
            for row in cursor.fetchall():
                sessions.append(Session(
                    id=row["id"],
                    title=row["title"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    message_count=row["message_count"],
                    summary=row["summary"],
                    tags=json.loads(row["tags"]) if row["tags"] else []
                ))
        
        return sessions
    
    # === MESSAGE OPERATIONS ===
    
    def add_message(self, session_id: str, role: str, content: str, 
                    metadata: Dict = None) -> Message:
        """Session'a mesaj ekle"""
        now = datetime.now().isoformat()
        
        message = Message(
            role=role,
            content=content,
            timestamp=now,
            metadata=metadata
        )
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            # Mesajı ekle
            cursor.execute("""
                INSERT INTO messages (session_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, role, content, now, json.dumps(metadata or {})))
            
            # Session'ı güncelle
            cursor.execute("""
                UPDATE sessions 
                SET updated_at = ?, message_count = message_count + 1
                WHERE id = ?
            """, (now, session_id))
        
        return message
    
    def get_messages(self, session_id: str, limit: int = 100, 
                     offset: int = 0) -> List[Message]:
        """Session mesajlarını getir"""
        messages = []
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM messages 
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (session_id, limit, offset))
            
            for row in cursor.fetchall():
                messages.append(Message(
                    role=row["role"],
                    content=row["content"],
                    timestamp=row["timestamp"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None
                ))
        
        return messages
    
    def get_recent_messages(self, session_id: str, count: int = 10) -> List[Message]:
        """Son N mesajı getir (context için)"""
        messages = []
        
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM (
                    SELECT * FROM messages 
                    WHERE session_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ) ORDER BY timestamp ASC
            """, (session_id, count))
            
            for row in cursor.fetchall():
                messages.append(Message(
                    role=row["role"],
                    content=row["content"],
                    timestamp=row["timestamp"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None
                ))
        
        return messages
    
    def clear_messages(self, session_id: str) -> bool:
        """Session mesajlarını temizle (session'ı silmeden)"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor.execute("""
                UPDATE sessions SET message_count = 0, updated_at = ? WHERE id = ?
            """, (datetime.now().isoformat(), session_id))
            
            logger.info(f"Messages cleared for session: {session_id}")
            return True
    
    # === EXPORT/IMPORT ===
    
    def export_session(self, session_id: str) -> Optional[Dict]:
        """Session'ı JSON olarak export et"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        messages = self.get_messages(session_id, limit=10000)
        
        return {
            "session": session.to_dict(),
            "messages": [m.to_dict() for m in messages],
            "exported_at": datetime.now().isoformat(),
            "version": "1.0"
        }
    
    def import_session(self, data: Dict, new_id: str = None) -> Optional[Session]:
        """JSON'dan session import et"""
        try:
            session_data = data["session"]
            messages_data = data["messages"]
            
            # Yeni ID oluştur veya kullan
            session_id = new_id or f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Session oluştur
            session = self.create_session(
                session_id=session_id,
                title=f"[İmport] {session_data['title']}"
            )
            
            # Mesajları ekle
            for msg_data in messages_data:
                self.add_message(
                    session_id=session_id,
                    role=msg_data["role"],
                    content=msg_data["content"],
                    metadata=msg_data.get("metadata")
                )
            
            # Summary ve tags'i güncelle
            self.update_session(
                session_id=session_id,
                summary=session_data.get("summary"),
                tags=session_data.get("tags")
            )
            
            logger.info(f"Session imported: {session_id}")
            return self.get_session(session_id)
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            return None
    
    # === UTILITIES ===
    
    def get_stats(self) -> Dict:
        """Genel istatistikler"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(message_count) FROM sessions")
            total = cursor.fetchone()[0] or 0
            
            return {
                "total_sessions": session_count,
                "total_messages": message_count,
                "db_path": DB_PATH
            }
    
    def auto_title(self, session_id: str) -> str:
        """İlk mesajdan otomatik başlık oluştur"""
        messages = self.get_messages(session_id, limit=1)
        
        if messages:
            first_msg = messages[0].content
            # İlk 50 karakteri al
            title = first_msg[:50].strip()
            if len(first_msg) > 50:
                title += "..."
            
            self.update_session(session_id, title=title)
            return title
        
        return "Yeni Konuşma"


# Global instance
session_manager = SessionManager()
