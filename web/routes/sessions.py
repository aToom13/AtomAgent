"""Session API Routes"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from core.session_manager import session_manager

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class SessionCreate(BaseModel):
    title: Optional[str] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None


@router.get("")
async def list_sessions(limit: int = 20, offset: int = 0):
    """Session listesi"""
    sessions = session_manager.list_sessions(limit=limit, offset=offset)
    return {"sessions": [s.to_dict() for s in sessions]}


@router.post("")
async def create_session(data: SessionCreate):
    """Yeni session oluştur"""
    session = session_manager.create_session(title=data.title)
    return session.to_dict()


@router.get("/{session_id}")
async def get_session(session_id: str):
    """Session detayı"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.put("/{session_id}")
async def update_session(session_id: str, data: SessionUpdate):
    """Session güncelle"""
    success = session_manager.update_session(
        session_id, title=data.title, summary=data.summary, tags=data.tags
    )
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Session sil"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}


@router.get("/{session_id}/messages")
async def get_messages(session_id: str, limit: int = 100):
    """Session mesajları"""
    messages = session_manager.get_messages(session_id, limit=limit)
    return {"messages": [m.to_dict() for m in messages]}
