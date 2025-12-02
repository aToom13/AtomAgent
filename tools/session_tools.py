"""
Session Tools - Agent'ın session yönetimi için kullanabileceği tool'lar
"""
from langchain_core.tools import tool
from core.session_manager import session_manager
from utils.logger import get_logger

logger = get_logger()


@tool
def list_recent_sessions(limit: int = 10) -> str:
    """
    Son konuşma oturumlarını listeler.
    
    Args:
        limit: Listelenecek maksimum session sayısı (varsayılan 10)
    
    Returns:
        Session listesi
    """
    sessions = session_manager.list_sessions(limit=limit)
    
    if not sessions:
        return "Henüz kaydedilmiş konuşma yok."
    
    lines = [f"📚 Son {len(sessions)} Konuşma:\n"]
    
    for i, session in enumerate(sessions, 1):
        lines.append(f"{i}. {session.title[:40]}")
        lines.append(f"   ID: {session.id}")
        lines.append(f"   Mesaj: {session.message_count} • {session.updated_at[:10]}")
        lines.append("")
    
    return "\n".join(lines)


@tool
def search_conversations(query: str) -> str:
    """
    Geçmiş konuşmalarda arama yapar.
    
    Args:
        query: Aranacak kelime veya cümle
    
    Returns:
        Eşleşen konuşmalar
    """
    sessions = session_manager.search_sessions(query, limit=10)
    
    if not sessions:
        return f"'{query}' için sonuç bulunamadı."
    
    lines = [f"🔍 '{query}' için {len(sessions)} sonuç:\n"]
    
    for session in sessions:
        lines.append(f"• {session.title[:50]}")
        lines.append(f"  ID: {session.id} • {session.message_count} mesaj")
        if session.summary:
            lines.append(f"  Özet: {session.summary[:100]}...")
        lines.append("")
    
    return "\n".join(lines)


@tool
def get_session_summary(session_id: str) -> str:
    """
    Belirli bir session'ın özetini ve son mesajlarını getirir.
    
    Args:
        session_id: Session ID
    
    Returns:
        Session özeti ve son mesajlar
    """
    session = session_manager.get_session(session_id)
    
    if not session:
        return f"Session bulunamadı: {session_id}"
    
    messages = session_manager.get_recent_messages(session_id, count=5)
    
    lines = [
        f"📝 Session: {session.title}",
        f"ID: {session.id}",
        f"Oluşturulma: {session.created_at}",
        f"Mesaj sayısı: {session.message_count}",
        ""
    ]
    
    if session.summary:
        lines.append(f"Özet: {session.summary}")
        lines.append("")
    
    if messages:
        lines.append("Son mesajlar:")
        for msg in messages:
            role_icon = "👤" if msg.role == "human" else "🤖"
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            lines.append(f"  {role_icon} {content}")
    
    return "\n".join(lines)


@tool
def get_session_stats() -> str:
    """
    Genel session istatistiklerini döndürür.
    
    Returns:
        İstatistikler
    """
    stats = session_manager.get_stats()
    
    return f"""📊 Session İstatistikleri:
• Toplam konuşma: {stats['total_sessions']}
• Toplam mesaj: {stats['total_messages']}
• Veritabanı: {stats['db_path']}"""
