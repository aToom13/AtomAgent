"""
Scheduler Service
Background job scheduler using APScheduler for reminders and scheduled tasks
"""
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from models.reminder import Reminder, reminder_store
from utils.logger import get_logger

logger = get_logger()

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None
_reminder_callback: Optional[Callable] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            timezone='Europe/Istanbul'
        )
    return _scheduler


def set_reminder_callback(callback: Callable):
    """Set callback function to be called when a reminder triggers"""
    global _reminder_callback
    _reminder_callback = callback


async def trigger_reminder(reminder_id: str):
    """Called when a reminder's scheduled time is reached"""
    logger.info(f"Reminder triggered: {reminder_id}")
    
    reminder = reminder_store.get(reminder_id)
    if not reminder:
        logger.warning(f"Reminder {reminder_id} not found")
        return
    
    # Update status
    if not reminder.is_recurring:
        reminder_store.update(reminder_id, status="triggered")
    
    # Call the callback (usually sends WebSocket notification)
    if _reminder_callback:
        await _reminder_callback(reminder)


def schedule_reminder(reminder: Reminder) -> bool:
    """Schedule a reminder job"""
    scheduler = get_scheduler()
    
    try:
        if reminder.is_recurring and reminder.cron_expression:
            # Recurring: use CronTrigger
            # Parse cron expression (minute hour day month day_of_week)
            parts = reminder.cron_expression.split()
            if len(parts) >= 5:
                trigger = CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
                scheduler.add_job(
                    trigger_reminder,
                    trigger=trigger,
                    args=[reminder.id],
                    id=reminder.id,
                    replace_existing=True
                )
                logger.info(f"Scheduled recurring reminder: {reminder.id} with cron: {reminder.cron_expression}")
                return True
        elif reminder.trigger_time:
            # One-time: use DateTrigger
            trigger = DateTrigger(run_date=reminder.trigger_time)
            scheduler.add_job(
                trigger_reminder,
                trigger=trigger,
                args=[reminder.id],
                id=reminder.id,
                replace_existing=True
            )
            logger.info(f"Scheduled one-time reminder: {reminder.id} for {reminder.trigger_time}")
            return True
    except Exception as e:
        logger.error(f"Failed to schedule reminder {reminder.id}: {e}")
    
    return False


def cancel_reminder(reminder_id: str) -> bool:
    """Cancel a scheduled reminder job"""
    scheduler = get_scheduler()
    try:
        scheduler.remove_job(reminder_id)
        logger.info(f"Cancelled reminder job: {reminder_id}")
        return True
    except Exception as e:
        logger.warning(f"Could not cancel reminder {reminder_id}: {e}")
        return False


def start_scheduler():
    """Start the scheduler and load existing reminders"""
    scheduler = get_scheduler()
    
    # Load and schedule all pending reminders
    for reminder in reminder_store.list_pending():
        schedule_reminder(reminder)
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler stopped")


def parse_time_expression(expr: str) -> Optional[datetime]:
    """
    Parse natural time expressions like:
    - "10m", "10dk", "10 dakika", "10 dakika sonra" -> 10 minutes from now
    - "1h", "1sa", "1 saat" -> 1 hour from now
    - "yarın 09:00", "yarın sabah"
    - "2 gün sonra"
    """
    import re
    
    expr = expr.lower().strip()
    now = datetime.now()
    
    # "yarın" patterns
    if "yarın" in expr:
        target_date = now + timedelta(days=1)
        # Check for specific time
        time_match = re.search(r'(\d{1,2})[:.](\d{2})', expr)
        if time_match:
            return target_date.replace(
                hour=int(time_match.group(1)), 
                minute=int(time_match.group(2)), 
                second=0, microsecond=0
            )
        elif "sabah" in expr:
            return target_date.replace(hour=8, minute=0, second=0, microsecond=0)
        elif "akşam" in expr:
            return target_date.replace(hour=20, minute=0, second=0, microsecond=0)
        elif "öğle" in expr:
            return target_date.replace(hour=13, minute=0, second=0, microsecond=0)
        else:
            # Default to tomorrow same time if generic "yarın"
            return target_date
            
    # Relative days: "2 gün sonra", "3 gun sonra"
    day_match = re.search(r'(\d+)\s*g[uü]n\s*sonra', expr)
    if day_match:
        days = int(day_match.group(1))
        return now + timedelta(days=days)

    # Patterns: number + unit
    patterns = [
        (r'(\d+)\s*(dk|dakika|min|m)', 'minutes'),
        (r'(\d+)\s*(sa|saat|hour|h)', 'hours'),
        (r'(\d+)\s*(sn|saniye|sec|s)', 'seconds'),
    ]
    
    for pattern, unit in patterns:
        match = re.search(pattern, expr)
        if match:
            value = int(match.group(1))
            if unit == 'minutes':
                return now + timedelta(minutes=value)
            elif unit == 'hours':
                return now + timedelta(hours=value)
            elif unit == 'seconds':
                return now + timedelta(seconds=value)
    
    # Try parsing HH:MM directly (assumes today/tomorrow logic could be added)
    time_match = re.search(r'^(\d{1,2})[:.](\d{2})$', expr)
    if time_match:
        target = now.replace(
            hour=int(time_match.group(1)), 
            minute=int(time_match.group(2)), 
            second=0, microsecond=0
        )
        if target < now:
            # If time passed, assume tomorrow
            target += timedelta(days=1)
        return target
            
    return None


def parse_cron_expression(expr: str) -> Optional[str]:
    """
    Parse natural cron expressions like:
    - "her sabah", "her gün 8'de" -> "0 8 * * *"
    - "her saat" -> "0 * * * *"
    - "haftaiçi" -> "0 9 * * 1-5"
    """
    expr = expr.lower().strip()
    
    cron_map = {
        "her sabah": "0 8 * * *",
        "her gün": "0 9 * * *",
        "her saat": "0 * * * *",
        "haftaiçi": "0 9 * * 1-5",
        "her pazartesi": "0 9 * * 1",
        "her cuma": "0 9 * * 5",
    }
    
    for key, cron in cron_map.items():
        if key in expr:
            return cron
    
    # Check if it looks like a cron expression already
    import re
    if re.match(r'[\d\*]+\s+[\d\*]+\s+[\d\*]+\s+[\d\*]+\s+[\d\*\-]+', expr):
        return expr
    
    return None
