"""
Reminders API Routes
CRUD endpoints for reminders and scheduled tasks
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.reminder import Reminder, reminder_store
from core.scheduler import schedule_reminder, cancel_reminder, parse_time_expression, parse_cron_expression

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderCreate(BaseModel):
    title: str
    time_or_cron: str
    message: str = ""
    action: str = "notify"


class ReminderResponse(BaseModel):
    id: str
    title: str
    message: str
    trigger_time: Optional[str]
    cron_expression: Optional[str]
    is_recurring: bool
    status: str
    action: str
    time_remaining: Optional[int]
    created_at: str


@router.get("")
async def list_reminders():
    """List all reminders"""
    reminders = reminder_store.list_all()
    return [
        ReminderResponse(
            id=r.id,
            title=r.title,
            message=r.message,
            trigger_time=r.trigger_time.isoformat() if r.trigger_time else None,
            cron_expression=r.cron_expression,
            is_recurring=r.is_recurring,
            status=r.status,
            action=r.action,
            time_remaining=r.time_remaining(),
            created_at=r.created_at.isoformat()
        )
        for r in reminders
    ]


@router.post("")
async def create_reminder_endpoint(data: ReminderCreate):
    """Create a new reminder"""
    # Parse time
    cron_expr = parse_cron_expression(data.time_or_cron)
    trigger_time = parse_time_expression(data.time_or_cron)
    
    is_recurring = cron_expr is not None
    
    if not cron_expr and not trigger_time:
        raise HTTPException(400, f"Invalid time expression: {data.time_or_cron}")
    
    reminder = Reminder(
        title=data.title,
        message=data.message or data.title,
        trigger_time=trigger_time,
        cron_expression=cron_expr,
        is_recurring=is_recurring,
        action=data.action,
        action_data=data.message if data.action in ["ask_agent", "run_command"] else None
    )
    
    reminder_store.add(reminder)
    scheduled = schedule_reminder(reminder)
    
    if not scheduled:
        reminder_store.delete(reminder.id)
        raise HTTPException(500, "Failed to schedule reminder")
    
    return {
        "id": reminder.id,
        "title": reminder.title,
        "is_recurring": reminder.is_recurring,
        "time_remaining": reminder.time_remaining()
    }


@router.delete("/{reminder_id}")
async def delete_reminder_endpoint(reminder_id: str):
    """Delete a reminder"""
    reminder = reminder_store.get(reminder_id)
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    
    cancel_reminder(reminder_id)
    reminder_store.delete(reminder_id)
    
    return {"success": True, "id": reminder_id}


@router.put("/{reminder_id}/dismiss")
async def dismiss_reminder_endpoint(reminder_id: str):
    """Dismiss a triggered reminder"""
    reminder = reminder_store.get(reminder_id)
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    
    reminder_store.update(reminder_id, status="dismissed")
    
    return {"success": True, "id": reminder_id, "status": "dismissed"}


@router.get("/{reminder_id}")
async def get_reminder_endpoint(reminder_id: str):
    """Get a specific reminder"""
    reminder = reminder_store.get(reminder_id)
    if not reminder:
        raise HTTPException(404, "Reminder not found")
    
    return ReminderResponse(
        id=reminder.id,
        title=reminder.title,
        message=reminder.message,
        trigger_time=reminder.trigger_time.isoformat() if reminder.trigger_time else None,
        cron_expression=reminder.cron_expression,
        is_recurring=reminder.is_recurring,
        status=reminder.status,
        action=reminder.action,
        time_remaining=reminder.time_remaining(),
        created_at=reminder.created_at.isoformat()
    )
