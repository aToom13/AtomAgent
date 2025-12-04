"""WebSocket Chat Handler"""
import os
import base64
import tempfile
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List

from core.agent import get_thread_config, get_agent_executor
from core.session_manager import session_manager
from core.providers import model_manager, is_fallback_needed
from utils.logger import get_logger
from config import config
from web import state

logger = get_logger()

# Attachment storage directory
ATTACHMENT_DIR = os.path.join(config.workspace.base_dir, ".attachments")
os.makedirs(ATTACHMENT_DIR, exist_ok=True)


async def process_attachments(content: str, attachments: List[dict]) -> str:
    """
    Process attachments and add them to the message content.
    Files are saved to sandbox shared folder for agent access.
    """
    if not attachments:
        return content
    
    attachment_info = []
    
    for att in attachments:
        try:
            name = att.get("name", "unknown")
            att_type = att.get("type", "file")
            mime_type = att.get("mimeType", "")
            data = att.get("data", "")
            
            # Decode base64 data
            if data.startswith("data:"):
                # Remove data URL prefix
                data = data.split(",", 1)[1] if "," in data else data
            
            file_data = base64.b64decode(data)
            
            # Save to shared folder (accessible by sandbox)
            shared_dir = os.path.join(config.workspace.base_dir, "..", "docker", "shared")
            os.makedirs(shared_dir, exist_ok=True)
            
            file_path = os.path.join(shared_dir, name)
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # Build attachment info for agent
            if att_type == "image":
                attachment_info.append(f"[Resim eklendi: {name}] - Dosya yolu: /home/agent/shared/{name}")
                attachment_info.append(f"Bu resmi analiz etmek için analyze_image tool'unu kullan: analyze_image('/home/agent/shared/{name}', 'Bu resimde ne var?')")
            elif att_type == "audio":
                attachment_info.append(f"[Ses dosyası eklendi: {name}] - Dosya yolu: /home/agent/shared/{name}")
                attachment_info.append(f"Bu ses dosyasını transkript etmek için transcribe_audio tool'unu kullan.")
            elif att_type == "code":
                # Read code content for inline display
                try:
                    code_content = file_data.decode("utf-8")[:2000]
                    attachment_info.append(f"[Kod dosyası eklendi: {name}]\n```\n{code_content}\n```")
                except:
                    attachment_info.append(f"[Kod dosyası eklendi: {name}] - Dosya yolu: /home/agent/shared/{name}")
            else:
                attachment_info.append(f"[Dosya eklendi: {name}] - Dosya yolu: /home/agent/shared/{name}")
            
            logger.info(f"Attachment saved: {name} -> {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to process attachment: {e}")
            attachment_info.append(f"[Dosya işlenemedi: {att.get('name', 'unknown')}]")
    
    # Combine content with attachment info
    if attachment_info:
        attachment_text = "\n\n".join(attachment_info)
        if content:
            return f"{content}\n\n---\nEkler:\n{attachment_text}"
        else:
            return f"Ekler:\n{attachment_text}"
    
    return content


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

# Stop flags for each client
stop_flags: Dict[str, bool] = {}


async def handle_chat(websocket: WebSocket, client_id: str):
    """WebSocket chat handler"""
    await manager.connect(websocket, client_id)
    stop_flags[client_id] = False

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "message":
                content = data.get("content", "")
                session_id = data.get("session_id")
                attachments = data.get("attachments", [])

                # Reset stop flag
                stop_flags[client_id] = False

                if not session_id:
                    session = session_manager.create_session()
                    session_id = session.id
                    await manager.send_message(client_id, {
                        "type": "session_created",
                        "session": session.to_dict()
                    })

                # Process attachments
                processed_content = content
                if attachments:
                    processed_content = await process_attachments(content, attachments)

                session_manager.add_message(session_id, "human", content)
                await stream_response(client_id, session_id, processed_content)

            elif data.get("type") == "stop":
                stop_flags[client_id] = True
                logger.info(f"Stop requested for {client_id}")
                await manager.send_message(client_id, {
                    "type": "stopped",
                    "message": "Agent durduruldu"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        stop_flags.pop(client_id, None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)
        stop_flags.pop(client_id, None)


async def stream_response(client_id: str, session_id: str, user_message: str, retry_count: int = 0):
    """Agent yanıtını stream et - fallback destekli"""
    from langchain_core.messages import HumanMessage

    MAX_RETRIES = 5

    try:
        # Aktif model bilgisini gönder - sadece status bar
        current_provider, current_model = model_manager.get_current_provider_info("supervisor")
        await manager.send_message(client_id, {
            "type": "status",
            "status": "thinking",
            "message": "🧠 Düşünüyor...",
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
            # Check stop flag
            if stop_flags.get(client_id, False):
                logger.info(f"Stopping stream for {client_id}")
                break

            kind = event.get("event")

            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    token = chunk.content
                    full_response += token
                    await manager.send_message(client_id, {"type": "token", "content": token})

            elif kind == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = event.get("data", {}).get("input", {})
                tool_input_str = str(tool_input)

                # Status bar güncelle
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "tool",
                    "message": f"🔧 {tool_name} çalıştırılıyor..."
                })

                # Tools paneline gönder
                await manager.send_message(client_id, {
                    "type": "tool_start",
                    "tool": tool_name,
                    "input": tool_input_str[:500]
                })

                # Sandbox/Docker komutlarını Docker sekmesine gönder
                sandbox_tools = ["sandbox_shell", "sandbox_start", "sandbox_stop", "sandbox_upload", "sandbox_download"]
                if tool_name in sandbox_tools:
                    cmd = tool_input.get("command", tool_input_str) if isinstance(tool_input, dict) else tool_input_str
                    await manager.send_message(client_id, {
                        "type": "docker_command",
                        "tool": tool_name,
                        "command": str(cmd)[:500],
                        "status": "running"
                    })

                # Web araçlarını browser sekmesine gönder
                web_tools = ["web_search", "browse_url", "scrape_page", "web_browse"]
                if tool_name in web_tools:
                    url = tool_input.get("url", tool_input.get("query", "")) if isinstance(tool_input, dict) else ""
                    await manager.send_message(client_id, {
                        "type": "browser_start",
                        "tool": tool_name,
                        "url": str(url)[:500],
                        "status": "loading"
                    })

            elif kind == "on_tool_end":
                tool_name = event.get("name", "unknown")
                tool_output = str(event.get("data", {}).get("output", ""))

                # Status bar güncelle
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "thinking",
                    "message": "💭 Yanıt hazırlanıyor..."
                })

                # Tools paneline gönder
                await manager.send_message(client_id, {
                    "type": "tool_end",
                    "tool": tool_name,
                    "output": tool_output[:500]
                })

                # Sandbox/Docker komut çıktısını Docker sekmesine gönder
                sandbox_tools = ["sandbox_shell", "sandbox_start", "sandbox_stop", "sandbox_upload", "sandbox_download"]
                if tool_name in sandbox_tools:
                    await manager.send_message(client_id, {
                        "type": "docker_output",
                        "tool": tool_name,
                        "output": tool_output[:2000],
                        "status": "completed"
                    })

                # Web araçları çıktısını browser sekmesine gönder
                web_tools = ["web_search", "browse_url", "scrape_page", "web_browse"]
                if tool_name in web_tools:
                    await manager.send_message(client_id, {
                        "type": "browser_result",
                        "tool": tool_name,
                        "content": tool_output[:3000],
                        "status": "loaded"
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
        from core.providers import handle_rate_limit, is_rate_limit_error
        
        error_str = str(e)
        logger.error(f"Stream error: {error_str}")

        if is_fallback_needed(e) and retry_count < MAX_RETRIES:
            current_provider, _ = model_manager.get_current_provider_info("supervisor")
            
            # Önce aynı provider içinde API key rotation dene
            if is_rate_limit_error(e) and handle_rate_limit(current_provider):
                logger.info(f"Rotated API key for {current_provider}")
                
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "switching",
                    "message": f"API key değiştiriliyor...",
                    "model": f"{current_provider}"
                })
                
                # Cache'i temizle ve yeni key ile agent oluştur
                model_manager.clear_cache("supervisor")
                state.update_agent()
                await stream_response(client_id, session_id, user_message, retry_count + 1)
                return
            
            # API key rotation başarısızsa, farklı provider'a geç
            switched = model_manager.switch_to_fallback("supervisor")

            if switched:
                new_provider, new_model = model_manager.get_current_provider_info("supervisor")
                logger.info(f"Switched to fallback: {new_provider}/{new_model}")

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
                    "message": "Tüm provider'lar ve API key'ler tükendi."
                })
        else:
            await manager.send_message(client_id, {"type": "error", "message": error_str})
