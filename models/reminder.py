"""
Reminder Model
Data model for reminders and scheduled tasks
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
import uuid
import json
import os

REMINDERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "reminders.json")

@dataclass
class Reminder:
    """A reminder or scheduled task"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = ""
    message: str = ""
    trigger_time: Optional[datetime] = None  # For one-time reminders
    cron_expression: Optional[str] = None    # For recurring (e.g., "0 8 * * *")
    is_recurring: bool = False
    status: Literal["pending", "triggered", "dismissed"] = "pending"
    action: Literal["notify", "run_command", "ask_agent"] = "notify"
    action_data: Optional[str] = None  # Command to run or agent prompt
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "trigger_time": self.trigger_time.isoformat() if self.trigger_time else None,
            "cron_expression": self.cron_expression,
            "is_recurring": self.is_recurring,
            "status": self.status,
            "action": self.action,
            "action_data": self.action_data,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Reminder":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            title=data.get("title", ""),
            message=data.get("message", ""),
            trigger_time=datetime.fromisoformat(data["trigger_time"]) if data.get("trigger_time") else None,
            cron_expression=data.get("cron_expression"),
            is_recurring=data.get("is_recurring", False),
            status=data.get("status", "pending"),
            action=data.get("action", "notify"),
            action_data=data.get("action_data"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )
    
    def time_remaining(self) -> Optional[int]:
        """Returns seconds remaining until trigger, or None if recurring/no trigger time"""
        if self.trigger_time and not self.is_recurring:
            delta = self.trigger_time - datetime.now()
            return max(0, int(delta.total_seconds()))
        return None


class ReminderStore:
    """Persistent storage for reminders"""
    
    def __init__(self, filepath: str = REMINDERS_FILE):
        self.filepath = filepath
        self.reminders: dict[str, Reminder] = {}
        self._ensure_dir()
        self.load()
    
    def _ensure_dir(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
    
    def load(self):
        """Load reminders from file"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    data = json.load(f)
                    self.reminders = {
                        r["id"]: Reminder.from_dict(r) for r in data
                    }
            except (json.JSONDecodeError, KeyError):
                self.reminders = {}
    
    def save(self):
        """Save reminders to file"""
        with open(self.filepath, "w") as f:
            json.dump([r.to_dict() for r in self.reminders.values()], f, indent=2)
    
    def add(self, reminder: Reminder) -> Reminder:
        """Add a new reminder"""
        self.reminders[reminder.id] = reminder
        self.save()
        return reminder
    
    def get(self, reminder_id: str) -> Optional[Reminder]:
        """Get reminder by ID"""
        return self.reminders.get(reminder_id)
    
    def delete(self, reminder_id: str) -> bool:
        """Delete a reminder"""
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            self.save()
            return True
        return False
    
    def update(self, reminder_id: str, **updates) -> Optional[Reminder]:
        """Update a reminder"""
        if reminder_id in self.reminders:
            reminder = self.reminders[reminder_id]
            for key, value in updates.items():
                if hasattr(reminder, key):
                    setattr(reminder, key, value)
            self.save()
            return reminder
        return None
    
    def list_pending(self) -> list[Reminder]:
        """List all pending reminders"""
        return [r for r in self.reminders.values() if r.status == "pending"]
    
    def list_all(self) -> list[Reminder]:
        """List all reminders"""
        return list(self.reminders.values())


# Global store instance
reminder_store = ReminderStore()
