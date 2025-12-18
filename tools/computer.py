"""
Computer Use Tools
Interact with the computer using mouse, keyboard, and screen.
Supports: pyautogui, mss (if available)
"""
import base64
import os
import io
from langchain_core.tools import tool
from utils.logger import get_logger

logger = get_logger()

# Try to import dependencies
try:
    import pyautogui
    import mss
    HAS_GUI_DEPS = True
except ImportError:
    HAS_GUI_DEPS = False

@tool
def computer_screenshot() -> str:
    """
    Take a screenshot of the current screen.
    Returns:
        Path to the saved screenshot or base64 data description.
    """
    logger.info("Taking screenshot...")
    
    filename = f"screenshot_{int(time.time())}.png"
    filepath = os.path.join(os.getcwd(), "uploads", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if HAS_GUI_DEPS:
        try:
            with mss.mss() as sct:
                sct.shot(output=filepath)
            return f"Screenshot saved to: {filepath} (View in Preview tab)"
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return f"Error taking screenshot: {e}"
    else:
        # Mock for headless / missing deps
        return "Screenshot capability not available (missing dependencies). Simulated screenshot taken."

@tool
def computer_click(x: int, y: int, click_type: str = "left") -> str:
    """
    Click mouse at (x, y).
    Args:
        x: X coordinate
        y: Y coordinate
        click_type: "left", "right", "double"
    """
    if HAS_GUI_DEPS:
        try:
            pyautogui.click(x=x, y=y, button=click_type.replace("double", "left"))
            if click_type == "double":
                pyautogui.click(x=x, y=y)
            return f"Clicked {click_type} at ({x}, {y})"
        except Exception as e:
            return f"Click failed: {e}"
    else:
        return f"[MOCK] Clicked {click_type} at ({x}, {y})"

@tool
def computer_type(text: str) -> str:
    """
    Type text using keyboard.
    Args:
        text: Text to type
    """
    if HAS_GUI_DEPS:
        try:
            pyautogui.write(text)
            return f"Typed: {text}"
        except Exception as e:
            return f"Type failed: {e}"
    else:
        return f"[MOCK] Typed: {text}"

@tool
def start_vnc_session() -> str:
    """
    Start a VNC session in the Docker sandbox.
    This starts the X server, VNC, and noVNC for browser viewing.
    Returns:
        VNC status and connection info
    """
    import subprocess
    import os
    
    DOCKER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docker")
    
    try:
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", "name=atomagent-sandbox"],
            capture_output=True, text=True, timeout=5
        )
        if not result.stdout.strip():
            return "❌ Sandbox is not running. Use sandbox_start first."
        
        # Start VNC (script handles if already running)
        subprocess.run(
            ["docker", "exec", "atomagent-sandbox", "bash", "-c", 
             "/home/agent/start-vnc.sh"],
            capture_output=True, text=True, timeout=30, cwd=DOCKER_DIR
        )
        
        return "✓ VNC Session Started. Connect at http://localhost:16080/vnc.html (View in Preview tab)"
        
    except subprocess.TimeoutExpired:
        return "⚠️ VNC start timed out, but may still be running."
    except Exception as e:
        return f"❌ Error starting VNC: {str(e)}"

import time

