"""WebSocket Chat Handler"""
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict

from core.agent import get_thread_config, get_agent_executor
from core.session_manager import session_manager
from core.providers import model_manager, is_fallback_needed
from utils.logger import get_logger
from web import state

logger = get_logger()


class ConnectionManager:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")
    
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")
    
    async def send_message(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)


manager = ConnectionManager()


async def handle_chat(websocket: WebSocket, client_id: str):
    """WebSocket chat handler"""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "message":
                content = data.get("content", "")
                session_id = data.get("session_id")
                
                if not session_id:
                    session = session_manager.create_session()
                    session_id = session.id
                    await manager.send_message(client_id, {
                        "type": "session_created",
                        "session": session.to_dict()
                    })
                
                session_manager.add_message(session_id, "human", content)
                await stream_response(client_id, session_id, content)
            
            elif data.get("type") == "stop":
                await manager.send_message(client_id, {
                    "type": "stopped",
                    "message": "Agent stopped"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)


async def stream_response(client_id: str, session_id: str, user_message: str, retry_count: int = 0):
    """Agent yanıtını stream et - fallback destekli"""
    from langchain_core.messages import HumanMessage
    
    MAX_RETRIES = 5
    current_thinking = ""
    in_thinking = False
    
    try:
        # Aktif model bilgisini gönder
        current_provider, current_model = model_manager.get_current_provider_info("supervisor")
        await manager.send_message(client_id, {
            "type": "status",
            "status": "thinking",
            "message": f"Düşünüyor...",
            "model": f"{current_provider}/{current_model}"
        })
        
        await manager.send_message(client_id, {
            "type": "stream_start",
            "session_id": session_id
        })
        
        thread_config = get_thread_config(session_id)
        full_response = ""
        agent = state.get_agent()
        
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=user_message)]},
            config=thread_config,
            version="v2"
        ):
            kind = event.get("event")
            
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    
                    # Thinking block detection (<think> tags veya reasoning)
                    if "<think>" in token or "**Düşünce:" in token or "**Thinking:" in token:
                        in_thinking = True
                        await manager.send_message(client_id, {
                            "type": "thinking_start",
                            "title": "Düşünüyor..."
                        })
                    
                    if in_thinking:
                        current_thinking += token
                        await manager.send_message(client_id, {
                            "type": "thinking_token",
                            "content": token
                        })
                        
                        if "</think>" in token or (in_thinking and token.strip().endswith("**")):
                            in_thinking = False
                            await manager.send_message(client_id, {
                                "type": "thinking_end"
                            })
                    else:
                        full_response += token
                        await manager.send_message(client_id, {"type": "token", "content": token})
            
            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = str(event.get("data", {}).get("input", ""))
                
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "tool",
                    "message": f"🔧 {tool_name} çalıştırılıyor..."
                })
                await manager.send_message(client_id, {
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": tool_input[:200]
                })
                
                # Docker/sandbox komutlarını Docker sekmesine gönder
                if tool_name in ["execute_command", "run_command", "shell", "bash", "terminal"]:
                    await manager.send_message(client_id, {
                        "type": "docker_command",
                        "command": tool_input[:500],
                        "status": "running"
                    })
            
            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                tool_output = str(event.get("data", {}).get("output", ""))
                
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "thinking",
                    "message": "Yanıt hazırlanıyor..."
                })
                await manager.send_message(client_id, {
                    "type": "tool_end",
                    "tool": tool_name,
                    "output": tool_output[:500]
                })
                
                # Docker/sandbox komut çıktısını Docker sekmesine gönder
                if tool_name in ["execute_command", "run_command", "shell", "bash", "terminal"]:
                    await manager.send_message(client_id, {
                        "type": "docker_output",
                        "output": tool_output[:2000],
                        "status": "completed"
                    })
        
        if full_response:
            session_manager.add_message(session_id, "ai", full_response)
            session = session_manager.get_session(session_id)
            if session and session.message_count <= 2:
                session_manager.auto_title(session_id)
        
        await manager.send_message(client_id, {
            "type": "status",
            "status": "ready",
            "message": "Hazır"
        })
        await manager.send_message(client_id, {"type": "stream_end", "session_id": session_id})
    
    except Exception as e:
        error_str = str(e)
        logger.error(f"Stream error: {error_str}")
        
        if is_fallback_needed(e) and retry_count < MAX_RETRIES:
            switched = model_manager.switch_to_fallback("supervisor")
            
            if switched:
                new_provider, new_model = model_manager.get_current_provider_info("supervisor")
                logger.info(f"Switched to fallback: {new_provider}/{new_model}")
                
                # Sadece status bar'da göster, chat'e mesaj ekleme
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "switching",
                    "message": f"Model değiştiriliyor: {new_model}",
                    "model": f"{new_provider}/{new_model}"
                })
                
                state.update_agent()
                await stream_response(client_id, session_id, user_message, retry_count + 1)
                return
            else:
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Tüm provider'lar tükendi."
                })
        else:
            await manager.send_message(client_id, {"type": "error", "message": error_str})