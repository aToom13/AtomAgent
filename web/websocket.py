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

# Attachment storage directory - workspace içinde uploads klasörü
UPLOADS_DIR = os.path.join(config.workspace.base_dir, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


async def process_attachments(content: str, attachments: List[dict]) -> str:
    """
    Process attachments and add them to the message content.
    Files are saved to workspace/uploads folder for agent access.
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
            
            # Save to workspace/uploads folder
            file_path = os.path.join(UPLOADS_DIR, name)
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # Relative path for agent
            relative_path = f"uploads/{name}"
            
            # Build attachment info for agent
            if att_type == "image":
                attachment_info.append(f"[Resim eklendi: {name}]")
                attachment_info.append(f"Dosya yolu: {relative_path}")
                attachment_info.append(f"Bu resmi analiz etmek için analyze_image('{relative_path}', 'Bu resimde ne var?') kullan.")
            elif att_type == "audio":
                attachment_info.append(f"[Ses dosyası eklendi: {name}]")
                attachment_info.append(f"Dosya yolu: {relative_path}")
                attachment_info.append(f"Bu ses dosyasını transkript etmek için transcribe_audio('{relative_path}') kullan.")
            elif att_type == "code":
                # Read code content for inline display
                try:
                    code_content = file_data.decode("utf-8")[:3000]
                    ext = os.path.splitext(name)[1].lstrip('.')
                    attachment_info.append(f"[Kod dosyası: {name}]\n```{ext}\n{code_content}\n```")
                except:
                    attachment_info.append(f"[Kod dosyası eklendi: {name}] - Dosya yolu: {relative_path}")
            else:
                # Try to read text content for documents
                try:
                    text_content = file_data.decode("utf-8")[:3000]
                    attachment_info.append(f"[Dosya: {name}]\nİçerik:\n{text_content}")
                except:
                    attachment_info.append(f"[Dosya eklendi: {name}] - Dosya yolu: {relative_path}")
                    attachment_info.append(f"Bu dosyayı okumak için read_file('{relative_path}') kullan.")
            
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

# Active tasks for each client - for cancellation
import asyncio
active_tasks: Dict[str, asyncio.Task] = {}


async def handle_chat(websocket: WebSocket, client_id: str):
    """WebSocket chat handler"""
    await manager.connect(websocket, client_id)
    state.set_stop_flag(client_id, False)

    try:
        while True:
            data = await websocket.receive_json()
            logger.info(f"[WS] Received data: {data.get('type')}")
            print(f"[WS DEBUG] Received: {data}")

            if data.get("type") == "message":
                content = data.get("content", "")
                session_id = data.get("session_id")
                attachments = data.get("attachments", [])
                agent_id = data.get("agent", "supervisor")
                agent_name = data.get("agent_name", "Supervisor")

                # Cancel any existing task for this client
                if client_id in active_tasks:
                    old_task = active_tasks[client_id]
                    if not old_task.done():
                        old_task.cancel()
                        try:
                            await old_task
                        except asyncio.CancelledError:
                            pass

                # Reset stop flag
                state.set_stop_flag(client_id, False)
                
                # Log agent info
                logger.info(f"Message routed to agent: {agent_name} ({agent_id})")

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
                
                # Create task and track it
                task = asyncio.create_task(stream_response(client_id, session_id, processed_content))
                active_tasks[client_id] = task
                
                try:
                    await task
                except asyncio.CancelledError:
                    logger.info(f"Task cancelled for {client_id}")
                finally:
                    active_tasks.pop(client_id, None)

            elif data.get("type") == "stop":
                state.set_stop_flag(client_id, True)
                logger.info(f"Stop requested for {client_id}")
                
                # Cancel the active task
                if client_id in active_tasks:
                    task = active_tasks[client_id]
                    if not task.done():
                        task.cancel()
                        logger.info(f"Task cancelled for {client_id}")
                
                await manager.send_message(client_id, {
                    "type": "stopped",
                    "message": "Agent durduruldu"
                })
                await manager.send_message(client_id, {
                    "type": "stream_end",
                    "session_id": "stopped"
                })
                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "ready",
                    "message": "Hazır"
                })

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        state.clear_stop_flag(client_id)
        active_tasks.pop(client_id, None)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)
        state.clear_stop_flag(client_id)
        active_tasks.pop(client_id, None)


async def stream_response(client_id: str, session_id: str, user_message: str, retry_count: int = 0):
    """Agent yanıtını stream et - fallback destekli"""
    from langchain_core.messages import HumanMessage
    import asyncio

    print(f"[STREAM DEBUG] Starting stream_response for {client_id}")
    logger.info(f"[STREAM] Starting for {client_id}, message: {user_message[:50]}...")

    # Toplam API key sayısı + fallback provider sayısı kadar retry hakkı
    MAX_RETRIES = 20

    try:
        # Check if already cancelled
        if state.get_stop_flag(client_id):
            logger.info(f"Stream cancelled before start for {client_id}")
            return
        # Aktif model bilgisini gönder - sadece status bar
        current_provider, current_model = model_manager.get_current_provider_info("supervisor")
        print(f"[STREAM DEBUG] Using model: {current_provider}/{current_model}")
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

        try:
            async for event in agent.astream_events(
                {"messages": [HumanMessage(content=user_message)]},
                config=thread_config,
                version="v2"
            ):
                # Check stop flag - her event'te kontrol et
                if state.get_stop_flag(client_id):
                    logger.info(f"Stopping stream for {client_id}")
                    return  # Fonksiyondan tamamen çık

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
                        
                        # Sunucu başlatma komutlarını algıla ve Canvas'a bildir
                        server_patterns = [
                            ("python", ["flask run", "uvicorn", "python -m http.server", "streamlit run", "gradio", "manage.py runserver"]),
                            ("node", ["npm start", "npm run dev", "yarn start", "yarn dev", "node server", "npx serve"]),
                        ]
                        
                        tool_input = event.get("data", {}).get("input", {})
                        cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
                        cmd_lower = cmd.lower()
                        
                        for server_type, patterns in server_patterns:
                            for pattern in patterns:
                                if pattern in cmd_lower:
                                    # Port'u bulmaya çalış
                                    import re
                                    port_match = re.search(r':(\d{4,5})|--port[= ](\d+)|-p[= ]?(\d+)', cmd)
                                    port = 8000  # default
                                    if port_match:
                                        port = int(port_match.group(1) or port_match.group(2) or port_match.group(3))
                                    elif "5000" in cmd:
                                        port = 5000
                                    elif "3000" in cmd:
                                        port = 3000
                                    elif "8080" in cmd:
                                        port = 8080
                                    elif "8501" in cmd:  # streamlit default
                                        port = 8501
                                    
                                    await manager.send_message(client_id, {
                                        "type": "server_started",
                                        "port": port,
                                        "server_type": server_type,
                                        "command": cmd[:200]
                                    })
                                    break

                        # GUI uygulama başlatma algıla (pygame, tkinter, etc.)
                        gui_patterns = ["pygame", "tkinter", "pyqt", "pyside", "kivy", "wxpython"]
                        if any(pattern in cmd_lower for pattern in gui_patterns):
                            await manager.send_message(client_id, {
                                "type": "gui_started",
                                "command": cmd[:200]
                            })
                    
                    # write_file ile HTML dosyası oluşturulduğunu algıla
                    if tool_name == "write_file":
                        tool_input = event.get("data", {}).get("input", {})
                        file_path = tool_input.get("path", "") if isinstance(tool_input, dict) else ""
                        if file_path.endswith('.html') or file_path.endswith('.htm'):
                            await manager.send_message(client_id, {
                                "type": "html_created",
                                "path": file_path
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
                        
        except asyncio.CancelledError:
            logger.info(f"Stream cancelled for {client_id}")
            return  # Task cancelled, just return

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
        from core.providers import handle_rate_limit, is_rate_limit_error, get_api_key_info
        
        error_str = str(e)
        logger.error(f"Stream error (retry {retry_count}): {error_str}")

        if is_fallback_needed(e) and retry_count < MAX_RETRIES:
            current_provider, current_model = model_manager.get_current_provider_info("supervisor")
            logger.info(f"Fallback needed for {current_provider}/{current_model}")
            
            # Önce aynı provider içinde API key rotation dene
            if is_rate_limit_error(e):
                key_info = get_api_key_info(current_provider)
                logger.info(f"API key info for {current_provider}: {key_info}")
                
                if handle_rate_limit(current_provider):
                    new_key_info = get_api_key_info(current_provider)
                    logger.info(f"Rotated API key for {current_provider}: {new_key_info['current']}/{new_key_info['total']}")
                    
                    await manager.send_message(client_id, {
                        "type": "status",
                        "status": "switching",
                        "message": f"API key değiştiriliyor ({new_key_info['current']}/{new_key_info['total']})...",
                        "model": f"{current_provider}/{current_model}"
                    })
                    
                    # Cache'i temizle ve yeni key ile agent oluştur
                    model_manager.clear_cache("supervisor")
                    state.update_agent()
                    await stream_response(client_id, session_id, user_message, retry_count + 1)
                    return
            
            # API key rotation başarısızsa (veya rate limit değilse), farklı provider'a geç
            switched = model_manager.switch_to_fallback("supervisor")
            
            if switched:
                new_provider, new_model = model_manager.get_current_provider_info("supervisor")
                logger.info(f"Switched to fallback: {new_provider}/{new_model}")

                await manager.send_message(client_id, {
                    "type": "status",
                    "status": "switching",
                    "message": f"Provider değiştiriliyor: {new_provider}/{new_model}",
                    "model": f"{new_provider}/{new_model}"
                })

                state.update_agent()
                await stream_response(client_id, session_id, user_message, retry_count + 1)
                return
            else:
                logger.error("No more fallbacks available")
                await manager.send_message(client_id, {
                    "type": "error",
                    "message": "Tüm provider'lar ve API key'ler tükendi."
                })
        else:
            await manager.send_message(client_id, {"type": "error", "message": error_str})
