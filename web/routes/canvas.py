"""Canvas API Routes - Live Preview"""
import subprocess
import socket
from fastapi import APIRouter, HTTPException
from typing import Optional

from utils.logger import get_logger

router = APIRouter(prefix="/api/canvas", tags=["canvas"])
logger = get_logger()

CONTAINER_NAME = "atomagent-sandbox"


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def get_container_port_mapping(container_port: int) -> Optional[int]:
    """Get host port mapped to container port"""
    try:
        result = subprocess.run(
            ["docker", "port", CONTAINER_NAME, str(container_port)],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            # Output format: 0.0.0.0:8000 or :::8000
            mapping = result.stdout.strip().split(":")[-1]
            return int(mapping)
    except Exception as e:
        logger.error(f"Failed to get port mapping: {e}")
    return None


@router.get("/check-port")
async def check_port(port: int, host: str = "localhost"):
    """Check if a port is available/listening"""
    is_open = is_port_open(host, port)
    return {
        "port": port,
        "host": host,
        "available": is_open
    }


@router.get("/container-ports")
async def get_container_ports():
    """Get all exposed ports from the container"""
    try:
        result = subprocess.run(
            ["docker", "port", CONTAINER_NAME],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode != 0:
            return {"ports": [], "error": "Container not running"}
        
        ports = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Format: 8000/tcp -> 0.0.0.0:8000
                parts = line.split(" -> ")
                if len(parts) == 2:
                    container_port = parts[0].split("/")[0]
                    host_port = parts[1].split(":")[-1]
                    ports.append({
                        "container": int(container_port),
                        "host": int(host_port)
                    })
        
        return {"ports": ports}
    except Exception as e:
        logger.error(f"Failed to get container ports: {e}")
        return {"ports": [], "error": str(e)}


@router.get("/proxy/{port:int}/{path:path}")
async def proxy_request(port: int, path: str = ""):
    """
    Proxy requests to container port.
    This helps with CORS issues when embedding in iframe.
    """
    import httpx
    
    try:
        url = f"http://localhost:{port}/{path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            return {
                "status": response.status_code,
                "content": response.text[:10000],  # Limit response size
                "headers": dict(response.headers)
            }
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/start-server")
async def start_server(command: str, port: int = 8000, workdir: str = "/home/agent/shared"):
    """Start a server in the container"""
    try:
        # Run command in background
        full_cmd = f"cd {workdir} && nohup {command} > /tmp/server.log 2>&1 &"
        result = subprocess.run(
            ["docker", "exec", "-d", CONTAINER_NAME, "bash", "-c", full_cmd],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            return {
                "success": True,
                "port": port,
                "message": f"Server started on port {port}"
            }
        else:
            return {
                "success": False,
                "error": result.stderr
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-server")
async def stop_server(port: int):
    """Stop a server running on specified port"""
    try:
        # Find and kill process on port
        kill_cmd = f"fuser -k {port}/tcp 2>/dev/null || true"
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", kill_cmd],
            capture_output=True, text=True, timeout=10
        )
        
        return {
            "success": True,
            "message": f"Stopped server on port {port}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/vnc-status")
async def vnc_status():
    """Check if VNC/noVNC is available in the container"""
    try:
        # Check if X11 display is running
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", "pgrep -x Xvfb || pgrep -x Xvnc"],
            capture_output=True, text=True, timeout=5
        )
        
        x11_running = result.returncode == 0
        
        # Check if noVNC is running
        novnc_result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", "pgrep -f novnc || pgrep -f websockify"],
            capture_output=True, text=True, timeout=5
        )
        
        novnc_running = novnc_result.returncode == 0
        
        return {
            "running": x11_running,
            "novnc": novnc_running,
            "vnc_port": 5900,
            "novnc_port": 6080
        }
    except Exception as e:
        return {"running": False, "error": str(e)}


@router.post("/start-vnc")
async def start_vnc():
    """Start VNC server in the container for GUI apps"""
    try:
        # Start Xvfb (virtual framebuffer)
        xvfb_cmd = "Xvfb :99 -screen 0 1280x720x24 &"
        subprocess.run(
            ["docker", "exec", "-d", CONTAINER_NAME, "bash", "-c", xvfb_cmd],
            capture_output=True, text=True, timeout=10
        )
        
        # Set DISPLAY
        subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", "echo 'export DISPLAY=:99' >> ~/.bashrc"],
            capture_output=True, text=True, timeout=5
        )
        
        # Start x11vnc
        vnc_cmd = "x11vnc -display :99 -forever -shared -rfbport 5900 &"
        subprocess.run(
            ["docker", "exec", "-d", CONTAINER_NAME, "bash", "-c", vnc_cmd],
            capture_output=True, text=True, timeout=10
        )
        
        # Start noVNC (web-based VNC client)
        novnc_cmd = "websockify --web=/usr/share/novnc 6080 localhost:5900 &"
        subprocess.run(
            ["docker", "exec", "-d", CONTAINER_NAME, "bash", "-c", novnc_cmd],
            capture_output=True, text=True, timeout=10
        )
        
        return {
            "success": True,
            "message": "VNC started",
            "vnc_port": 5900,
            "novnc_port": 6080,
            "url": "http://localhost:6080/vnc.html"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop-vnc")
async def stop_vnc():
    """Stop VNC server"""
    try:
        subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", "pkill -f x11vnc; pkill -f Xvfb; pkill -f websockify"],
            capture_output=True, text=True, timeout=10
        )
        return {"success": True, "message": "VNC stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
