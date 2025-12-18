"""
Reminders Tool
Agent tools for creating and managing reminders and scheduled tasks
"""
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

from models.reminder import Reminder, reminder_store
from core.scheduler import schedule_reminder, cancel_reminder, parse_time_expression, parse_cron_expression
from utils.logger import get_logger

logger = get_logger()


@tool
def create_reminder(
    title: str,
    time_or_cron: str,
    message: str = "",
    action: str = "notify"
) -> str:
    """
    Bir hatırlatıcı veya zamanlı görev oluşturur.
    
    Args:
        title: Hatırlatıcı başlığı (örn: "Fırını kapat", "Hava Durumu")
        time_or_cron: Zaman ifadesi:
            - Tek seferlik: "10dk", "1sa", "30sn", "5m", "2h"
            - Tekrarlayan: "her sabah", "her saat", "haftaiçi" veya cron format "0 8 * * *"
        message: Hatırlatıcı mesajı (ne yapılacak)
        action: Aksiyon tipi:
            - "notify": Sadece bildirim göster (varsayılan)
            - "ask_agent": Agent'a mesajı gönder ve yanıt al
            - "run_command": Komutu sandbox'ta çalıştır
    
    Returns:
        Başarı mesajı ve hatırlatıcı ID'si
    
    Örnekler:
        create_reminder("Fırını kapat", "10dk", "Fırını kapatma zamanı!")
        create_reminder("Hava Durumu", "her sabah", "Bugünün hava durumunu getir", "ask_agent")
    """
    # Determine if recurring or one-time
    cron_expr = parse_cron_expression(time_or_cron)
    trigger_time = parse_time_expression(time_or_cron)
    
    is_recurring = cron_expr is not None
    
    if not cron_expr and not trigger_time:
        return f"❌ Zaman ifadesi anlaşılamadı: '{time_or_cron}'. Örnek: '10dk', '1sa', 'her sabah'"
    
    # Create reminder
    reminder = Reminder(
        title=title,
        message=message or title,
        trigger_time=trigger_time,
        cron_expression=cron_expr,
        is_recurring=is_recurring,
        action=action,
        action_data=message if action in ["ask_agent", "run_command"] else None
    )
    
    # Save and schedule
    reminder_store.add(reminder)
    scheduled = schedule_reminder(reminder)
    
    if not scheduled:
        reminder_store.delete(reminder.id)
        return "❌ Hatırlatıcı zamanlanamadı. Lütfen zaman formatını kontrol edin."
    
    if is_recurring:
        return f"✅ Tekrarlayan görev oluşturuldu: '{title}' (ID: {reminder.id})\n📅 Zamanlama: {cron_expr}"
    else:
        remaining = reminder.time_remaining()
        minutes = remaining // 60
        seconds = remaining % 60
        return f"✅ Hatırlatıcı oluşturuldu: '{title}' (ID: {reminder.id})\n⏱️ {minutes} dakika {seconds} saniye sonra"


@tool
def list_reminders() -> str:
    """
    Aktif hatırlatıcıları listeler.
    
    Returns:
        Aktif hatırlatıcıların listesi
    """
    reminders = reminder_store.list_pending()
    
    if not reminders:
        return "📋 Aktif hatırlatıcı yok."
    
    lines = ["📋 Aktif Hatırlatıcılar:"]
    for r in reminders:
        if r.is_recurring:
            lines.append(f"🔄 [{r.id}] {r.title} - {r.cron_expression}")
        else:
            remaining = r.time_remaining()
            if remaining is not None:
                mins = remaining // 60
                secs = remaining % 60
                lines.append(f"🔔 [{r.id}] {r.title} - {mins}dk {secs}sn kaldı")
            else:
                lines.append(f"🔔 [{r.id}] {r.title}")
    
    return "\n".join(lines)


@tool
def cancel_reminder_tool(reminder_id: str) -> str:
    """
    Bir hatırlatıcıyı iptal eder.
    
    Args:
        reminder_id: İptal edilecek hatırlatıcının ID'si
    
    Returns:
        Başarı veya hata mesajı
    """
    reminder = reminder_store.get(reminder_id)
    if not reminder:
        return f"❌ Hatırlatıcı bulunamadı: {reminder_id}"
    
    cancel_reminder(reminder_id)
    reminder_store.delete(reminder_id)
    
    return f"✅ Hatırlatıcı iptal edildi: '{reminder.title}'"


@tool
def dismiss_reminder(reminder_id: str) -> str:
    """
    Tetiklenmiş bir hatırlatıcıyı kapatır (dismiss).
    
    Args:
        reminder_id: Kapatılacak hatırlatıcının ID'si
    
    Returns:
        Başarı mesajı
    """
    reminder = reminder_store.get(reminder_id)
    if not reminder:
        return f"❌ Hatırlatıcı bulunamadı: {reminder_id}"
    
    reminder_store.update(reminder_id, status="dismissed")
    return f"✅ Hatırlatıcı kapatıldı: '{reminder.title}'"
