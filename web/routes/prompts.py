"""Prompts API Routes"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")


class PromptUpdate(BaseModel):
    content: str


@router.get("")
async def get_prompts():
    """Sistem promptlarını getir"""
    prompts = {}
    for filename in ["supervisor.txt", "coder.txt", "researcher.txt", "planner.txt"]:
        filepath = os.path.join(PROMPTS_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                prompts[filename.replace(".txt", "")] = f.read()
    return {"prompts": prompts}


@router.put("/{prompt_name}")
async def update_prompt(prompt_name: str, data: PromptUpdate):
    """Prompt güncelle"""
    filepath = os.path.join(PROMPTS_DIR, f"{prompt_name}.txt")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Prompt not found")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(data.content)
    return {"success": True}
