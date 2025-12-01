import os
import re
from langchain_core.tools import tool
from config import config
from utils.logger import get_logger

WORKSPACE_DIR = config.workspace.base_dir
TODO_FILE = os.path.join(WORKSPACE_DIR, "todo.md")
logger = get_logger()


@tool
def update_todo_list(content: str) -> str:
    """
    Updates the Todo List / Plan.
    Accepts a Markdown string (e.g., "- [ ] Task 1").
    Saves it to 'todo.md' in the workspace.
    """
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(TODO_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info("Todo updated")
        return content
    except Exception as e:
        logger.error(f"Todo error: {e}")
        return f"Error: {e}"


@tool
def mark_todo_done(step_keyword: str) -> str:
    """
    Marks a todo step as completed [x].
    Call this AFTER completing each step in the plan.
    
    Args:
        step_keyword: A word or phrase from the step to mark (e.g., "Araştır", "pygame", "test")
    
    Returns:
        Updated todo content or error message
    """
    logger.info(f"Marking todo step: {step_keyword}")
    
    try:
        if not os.path.exists(TODO_FILE):
            return "Todo dosyası yok - önce create_plan kullan"
        
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        updated = False
        marked_line = ""
        
        for i, line in enumerate(lines):
            # Keyword'ü içeren ve henüz işaretlenmemiş satırı bul
            if step_keyword.lower() in line.lower() and "[ ]" in line:
                lines[i] = line.replace("[ ]", "[x]")
                updated = True
                marked_line = lines[i].strip()
                logger.info(f"Todo step marked: {marked_line}")
                break  # Sadece ilk eşleşeni işaretle
        
        if updated:
            new_content = "\n".join(lines)
            with open(TODO_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            return f"✓ Tamamlandı: {marked_line}"
        else:
            return f"'{step_keyword}' içeren tamamlanmamış adım bulunamadı"
        
    except Exception as e:
        logger.error(f"Mark todo error: {e}")
        return f"Error: {e}"


@tool
def get_current_todo() -> str:
    """
    Returns the current todo list.
    Use this to see what steps need to be done.
    
    Returns:
        Current todo content in markdown format
    """
    try:
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                content = f.read()
            if content.strip():
                return content
            return "Todo listesi boş"
        return "Todo dosyası yok - create_plan ile plan oluştur"
    except Exception as e:
        return f"Error: {e}"


@tool
def get_next_todo_step() -> str:
    """
    Returns the next uncompleted step from the todo list.
    Use this to know what to do next.
    
    Returns:
        Next step to complete or "All done" message
    """
    try:
        if not os.path.exists(TODO_FILE):
            return "Todo dosyası yok"
        
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        for line in content.split("\n"):
            if "[ ]" in line:  # Tamamlanmamış adım
                # Satırı temizle
                step = line.strip()
                step = re.sub(r'^-\s*\[\s*\]\s*', '', step)  # "- [ ] " kısmını kaldır
                return f"Sıradaki adım: {step}"
        
        return "✓ Tüm adımlar tamamlandı!"
        
    except Exception as e:
        return f"Error: {e}"


# Legacy function for internal use
def mark_todo_step(keyword: str, completed: bool = True) -> str:
    """Internal function - use mark_todo_done tool instead"""
    try:
        if not os.path.exists(TODO_FILE):
            return "Todo dosyası yok"
        
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = content.split("\n")
        updated = False
        
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                if completed and "[ ]" in line:
                    lines[i] = line.replace("[ ]", "[x]")
                    updated = True
                    logger.info(f"Todo step marked: {keyword}")
                    break
        
        if updated:
            new_content = "\n".join(lines)
            with open(TODO_FILE, "w", encoding="utf-8") as f:
                f.write(new_content)
            return new_content
        
        return content
        
    except Exception as e:
        logger.error(f"Mark todo error: {e}")
        return f"Error: {e}"


def get_todo_content() -> str:
    """Todo içeriğini döndürür - UI için"""
    try:
        if os.path.exists(TODO_FILE):
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                return f.read()
        return ""
    except:
        return ""