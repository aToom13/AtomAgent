"""Docker/Sandbox API Routes"""
import subprocess
from fastapi import APIRouter, HTTPException
from typing import Optional

from utils.logger import get_logger

router = APIRouter(prefix="/api/docker", tags=["docker"])
logger = get_logger()

CONTAINER_NAME = "atomagent-sandbox"


def get_container_status():
    """Docker container durumunu kontrol et"""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={CONTAINER_NAME}"],
            capture_output=True, text=True, timeout=5
        )
        container_id = result.stdout.strip()
        return {"running": bool(container_id), "container_id": container_id}
    except Exception as e:
        logger.error(f"Docker status check failed: {e}")
        return {"running": False, "error": str(e)}


def exec_in_container(command: str, timeout: int = 30):
    """Container içinde komut çalıştır"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "bash", "-c", command],
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/status")
async def docker_status():
    """Docker container durumu"""
    return get_container_status()


@router.get("/files")
async def list_docker_files(path: str = "/home/agent"):
    """Docker container içindeki dosyaları listele"""
    status = get_container_status()
    if not status.get("running"):
        raise HTTPException(status_code=503, detail="Container not running")
    
    result = exec_in_container(f'ls -la "{path}" 2>/dev/null')
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "Failed"))
    
    items = []
    lines = result["stdout"].strip().split("\n")[1:]  # Skip total line
    
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 9:
            name = " ".join(parts[8:])
            if name in [".", ".."]:
                continue
            is_dir = parts[0].startswith("d")
            size = int(parts[4]) if not is_dir else 0
            items.append({
                "name": name,
                "path": f"{path}/{name}".replace("//", "/"),
                "is_dir": is_dir,
                "size": size
            })
    
    return {"items": sorted(items, key=lambda x: (not x["is_dir"], x["name"]))}


@router.get("/file")
async def read_docker_file(path: str):
    """Docker container içindeki dosyayı oku"""
    status = get_container_status()
    if not status.get("running"):
        raise HTTPException(status_code=503, detail="Container not running")
    
    result = exec_in_container(f'cat "{path}"')
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("stderr", "Failed"))
    
    return {"content": result["stdout"], "path": path}


@router.post("/exec")
async def exec_command(command: str, timeout: int = 30):
    """Docker container içinde komut çalıştır"""
    status = get_container_status()
    if not status.get("running"):
        raise HTTPException(status_code=503, detail="Container not running")
    
    result = exec_in_container(command, timeout)
    return result
