"""UI Widgets Package"""
from ui.widgets.model_selector import ModelSelectorModal, apply_saved_settings
from ui.widgets.fallback_selector import FallbackSelectorModal
from ui.widgets.progress_tracker import TaskProgressWidget, ToolActivityWidget
from ui.widgets.debug_panel import DebugLogWidget, AgentStateWidget, MemoryUsageWidget
from ui.widgets.code_highlighter import (
    parse_message_with_code, 
    highlight_code, 
    detect_language,
    simple_highlight,
    CodeBlockWidget
)
from ui.widgets.session_widgets import (
    SessionBrowserModal,
    SessionInfoWidget,
    RenameSessionModal,
    SessionListItem
)
from ui.widgets.session_sidebar import SessionSidebar, SessionItem
from ui.widgets.sandbox_panel import SandboxPanel
from ui.widgets.tool_factory_panel import ToolFactoryPanel, ToolItem

__all__ = [
    "ModelSelectorModal", 
    "apply_saved_settings", 
    "FallbackSelectorModal",
    "TaskProgressWidget",
    "ToolActivityWidget",
    "DebugLogWidget",
    "AgentStateWidget",
    "MemoryUsageWidget",
    "parse_message_with_code",
    "highlight_code",
    "detect_language",
    "simple_highlight",
    "CodeBlockWidget",
    # Session widgets
    "SessionBrowserModal",
    "SessionInfoWidget",
    "RenameSessionModal",
    "SessionListItem",
    "SessionSidebar",
    "SessionItem",
    "SandboxPanel",
    # Tool Factory
    "ToolFactoryPanel",
    "ToolItem"
]
