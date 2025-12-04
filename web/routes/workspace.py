"""Workspace API Routes"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import config

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


class FileContent(BaseModel):
    content: str


@router.get("/files")
async def list_workspace_files(path: str = ""):
    """Workspace dosyalarını listele"""
    base_path = config.workspace.base_dir
    full_path = os.path.join(base_path, path) if path else base_path
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Path not found")
    
    items = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            items.append({
                "name": item,
                "path": os.path.join(path, item) if path else item,
                "is_dir": os.path.isdir(item_path),
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0
            })
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return {"items": sorted(items, key=lambda x: (not x["is_dir"], x["name"]))}


@router.get("/file")
async def read_file(path: str):
    """Dosya içeriğini oku"""
    full_path = os.path.join(config.workspace.base_dir, path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=400, detail="Not a file")
    
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return {"content": f.read(), "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/file")
async def write_file(path: str, data: FileContent):
    """Dosyaya yaz"""
    full_path = os.path.join(config.workspace.base_dir, path)
    
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(data.content)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/raw/{path:path}")
async def get_raw_file(path: str):
    """
    Dosyayı raw olarak döndür (CSS, JS, resimler için).
    HTML içindeki relative path'ler için kullanılır.
    """
    from fastapi.responses import FileResponse
    import mimetypes
    
    full_path = os.path.join(config.workspace.base_dir, path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=400, detail="Not a file")
    
    # MIME type belirle
    mime_type, _ = mimetypes.guess_type(full_path)
    if not mime_type:
        mime_type = "application/octet-stream"
    
    return FileResponse(full_path, media_type=mime_type)
