"""
AtomAgent UI Styles - Theme Support
"""

class Theme:
    def __init__(self, name, colors):
        self.name = name
        self.colors = colors

# Gruvbox Dark (Default)
GRUVBOX = Theme("gruvbox", {
    "bg": "#1d2021",
    "fg": "#ebdbb2",
    "panel_bg": "#282828",
    "border": "#3c3836",
    "accent": "#fe8019",
    "success": "#b8bb26",
    "error": "#fb4934",
    "warning": "#fabd2f",
    "info": "#83a598",
    "dim": "#928374",
    "highlight": "#504945"
})

# Dracula
DRACULA = Theme("dracula", {
    "bg": "#282a36",
    "fg": "#f8f8f2",
    "panel_bg": "#44475a",
    "border": "#6272a4",
    "accent": "#ff79c6",
    "success": "#50fa7b",
    "error": "#ff5555",
    "warning": "#f1fa8c",
    "info": "#8be9fd",
    "dim": "#6272a4",
    "highlight": "#44475a"
})

# Nord
NORD = Theme("nord", {
    "bg": "#2e3440",
    "fg": "#d8dee9",
    "panel_bg": "#3b4252",
    "border": "#4c566a",
    "accent": "#88c0d0",
    "success": "#a3be8c",
    "error": "#bf616a",
    "warning": "#ebcb8b",
    "info": "#81a1c1",
    "dim": "#4c566a",
    "highlight": "#434c5e"
})

# Catppuccin Mocha
CATPPUCCIN = Theme("catppuccin", {
    "bg": "#1e1e2e",
    "fg": "#cdd6f4",
    "panel_bg": "#181825",
    "border": "#313244",
    "accent": "#cba6f7",
    "success": "#a6e3a1",
    "error": "#f38ba8",
    "warning": "#f9e2af",
    "info": "#89b4fa",
    "dim": "#6c7086",
    "highlight": "#313244"
})

# Cyberpunk
CYBERPUNK = Theme("cyberpunk", {
    "bg": "#050505",
    "fg": "#00ff9f",
    "panel_bg": "#101010",
    "border": "#00ff9f",
    "accent": "#ff00ff",
    "success": "#00ff9f",
    "error": "#ff0055",
    "warning": "#fcee0a",
    "info": "#00ffff",
    "dim": "#404040",
    "highlight": "#202020"
})

# Monokai Pro
MONOKAI = Theme("monokai", {
    "bg": "#2d2a2e",
    "fg": "#fcfcfa",
    "panel_bg": "#403e41",
    "border": "#727072",
    "accent": "#ffd866",
    "success": "#a9dc76",
    "error": "#ff6188",
    "warning": "#fc9867",
    "info": "#78dce8",
    "highlight": "#5b595c"
})

THEMES = {
    "gruvbox": GRUVBOX,
    "dracula": DRACULA,
    "nord": NORD,
    "catppuccin": CATPPUCCIN,
    "cyberpunk": CYBERPUNK,
    "monokai": MONOKAI
}

# Legacy STYLES variable (kept for compatibility, not used)
STYLES = ""


def get_theme_variables(theme_name="gruvbox"):
    """Tema değişkenlerini dict olarak döndür"""
    theme = THEMES.get(theme_name, GRUVBOX)
    c = theme.colors
    
    # Temel değişkenler
    vars = {k: str(v) for k, v in c.items()}
    
    # Textual standart değişkenleri için mapping
    vars.update({
        "background": c["bg"],
        "foreground": c["fg"],
        "surface": c["panel_bg"],
        "panel": c["panel_bg"],
        "boost": c["highlight"],
        "primary": c["accent"],
        "secondary": c["info"],
        "accent": c["accent"],
        "error": c["error"],
        "success": c["success"],
        "warning": c["warning"],
        
        # Scrollbar variables
        "scrollbar-background": c["bg"],
        "scrollbar-background-hover": c["panel_bg"],
        "scrollbar-background-active": c["highlight"],
        "scrollbar": c["highlight"],
        "scrollbar-hover": c["accent"],
        "scrollbar-active": c["success"],
        "scrollbar-corner-color": c["bg"],
        
        # Link variables
        "link-background": "transparent",
        "link-background-hover": c["highlight"],
        "link-color": c["accent"],
        "link-color-hover": c["accent"],
        "link-style": "underline",
        "link-style-hover": "underline bold",
        
        # Text variables
        "text-disabled": c["dim"],
        "text-muted": c["dim"],
        
        # Footer variables
        "footer-background": c["bg"],
        "footer-foreground": c["dim"],
        "footer-key-foreground": c["accent"],
        "footer-key-background": c["highlight"],
        "footer-item-background": c["bg"],
        "footer-description-foreground": c["dim"],
        "footer-description-background": c["bg"],
        
        # Block variables
        "block-hover-background": c["highlight"],
        "block-cursor-text-style": "bold",
        "block-cursor-foreground": c["accent"],
        "block-cursor-background": c["highlight"],
        "block-cursor-blur-foreground": c["fg"],
        "block-cursor-blur-background": c["panel_bg"],
        "block-selection-background": c["highlight"],
        "block-selection-text-style": "bold",
        
        # Text Context Colors
        "text": c["fg"],
        "text-primary": c["fg"],
        "text-pr": c["fg"],
        "text-secondary": c["dim"],
        "text-success": c["success"],
        "text-warning": c["warning"],
        "text-warn": c["warning"],
        "text-error": c["error"],
        "text-accent": c["accent"],
        "text-disabled": c["dim"],
        "text-d": c["dim"],
        
        # Muted Backgrounds
        "primary-muted": c["panel_bg"],
        "secondary-muted": c["panel_bg"],
        "success-muted": c["panel_bg"],
        "warning-muted": c["panel_bg"],
        "error-muted": c["panel_bg"],
        "accent-muted": c["panel_bg"],
        
        # Input variables
        "input-background": c["highlight"],
        "input-foreground": c["fg"],
        "input-border": c["dim"],
        "input-border-focus": c["accent"],
        "input-cursor-background": c["fg"],
        "input-cursor-foreground": c["bg"],
        "input-cursor-text-style": "reverse",
        "input-selection-background": c["highlight"],
        "input-placeholder-color": c["dim"],
        
        # Button variables
        "button-focus-text-style": "bold",
        "button-foreground": c["fg"],
        "button-color-foreground": c["fg"],
        
        # Border variables
        "border-blurred": c["dim"],
        
        # Block Cursor Blurred
        "block-cursor-blurred-background": c["panel_bg"],
        "block-cursor-blurred-foreground": c["dim"],
        "block-cursor-blurred-text-style": "none",
        
        # Darken variants (mapping to base or dim for now)
        "surface-darken-1": c["bg"],
        "panel-darken-1": c["bg"],
        "panel-darken-2": c["bg"],
        "error-darken-1": c["error"],
        "error-darken-2": c["error"],
        "error-darken-3": c["error"],
        "success-darken-1": c["success"],
        "success-darken-2": c["success"],
        "success-darken-3": c["success"],
        "warning-darken-1": c["warning"],
        "warning-darken-2": c["warning"],
        "warning-darken-3": c["warning"],
        "accent-darken-1": c["accent"],
        "accent-darken-2": c["accent"],
        "accent-darken-3": c["accent"],
        "primary-darken-1": c["accent"],
        "primary-darken-2": c["accent"],
        "primary-darken-3": c["accent"],
        "secondary-darken-1": c["info"],
        "secondary-darken-2": c["info"],
        "secondary-darken-3": c["info"],
        "foreground-darken-1": c["dim"],
        "foreground-darken-2": c["dim"],
        "foreground-darken-3": c["dim"],
        "background-darken-1": c["bg"],
        "background-darken-2": c["bg"],
        "background-darken-3": c["bg"],
        
        "background-darken-3": c["bg"],
        
        # Lighten variants
        "primary-lighten-1": c["accent"],
        "primary-lighten-2": c["accent"],
        "primary-lighten-3": c["accent"],
        "secondary-lighten-1": c["info"],
        "secondary-lighten-2": c["info"],
        "secondary-lighten-3": c["info"],
        "accent-lighten-1": c["accent"],
        "accent-lighten-2": c["accent"],
        "accent-lighten-3": c["accent"],
        "success-lighten-1": c["success"],
        "success-lighten-2": c["success"],
        "success-lighten-3": c["success"],
        "error-lighten-1": c["error"],
        "error-lighten-2": c["error"],
        "error-lighten-3": c["error"],
        "warning-lighten-1": c["warning"],
        "warning-lighten-2": c["warning"],
        "warning-lighten-3": c["warning"],
        "background-lighten-1": c["bg"],
        "background-lighten-2": c["bg"],
        "background-lighten-3": c["bg"],
        "foreground-lighten-1": c["fg"],
        "foreground-lighten-2": c["fg"],
        "foreground-lighten-3": c["fg"],
        "surface-lighten-1": c["panel_bg"],
        "surface-lighten-2": c["panel_bg"],
        "surface-lighten-3": c["panel_bg"],
        "panel-lighten-1": c["panel_bg"],
        "panel-lighten-2": c["panel_bg"],
        "panel-lighten-3": c["panel_bg"],
        "panel-bg": c["panel_bg"],
        
        # Markdown variables
        "markdown-h1-background": c["panel_bg"],
        "markdown-h1-color": c["accent"],
        "markdown-h1-text-style": "bold underline",
        "markdown-h2-background": "transparent",
        "markdown-h2-color": c["accent"],
        "markdown-h2-text-style": "bold",
        "markdown-h3-background": "transparent",
        "markdown-h3-color": c["fg"],
        "markdown-h3-text-style": "bold",
        "markdown-h4-background": "transparent",
        "markdown-h4-color": c["fg"],
        "markdown-h4-text-style": "underline",
        "markdown-h5-background": "transparent",
        "markdown-h5-color": c["dim"],
        "markdown-h5-text-style": "italic",
        "markdown-h6-background": "transparent",
        "markdown-h6-color": c["dim"],
        "markdown-h6-text-style": "italic",
    })
    
    return vars



# CSS Kuralları (Değişken tanımları olmadan)
BASE_CSS = """
    Screen {
        background: $bg;
        color: $fg;
    }

    /* === MAIN LAYOUT === */
    #main-container {
        layout: horizontal;
        height: 100%;
    }

    /* === LEFT SIDEBAR === */
    #left-sidebar {
        width: 35;
        height: 100%;
        background: $bg;
        border-right: solid $border;
    }
    
    #sidebar-header-label, #right-header-label {
        height: 3;
        background: $panel-bg;
        color: $accent;
        text-align: center;
        text-style: bold;
        padding: 1;
        border-bottom: solid $border;
    }

    .section-label {
        height: 2;
        background: $highlight;
        padding: 0 1;
        text-style: bold;
        margin-top: 1;
        color: $accent;
    }

    .info-box {
        padding: 1;
        background: $panel-bg;
        border: solid $dim;
        color: $fg;
        margin: 0 1;
    }
    
    #left-tabs {
        height: 1fr;
    }
    
    #session-sidebar {
        width: 100%;
        height: 100%;
        background: $bg;
        padding: 0;
        margin: 0;
        border: none;
    }

    /* === LEFT PANEL - CHAT === */
    #left-panel {
        width: 1fr;
        height: 100%;
        background: $bg;
        border-right: solid $border;
    }

    #chat-header {
        height: 3;
        background: $panel-bg;
        color: $accent;
        text-align: center;
        text-style: bold;
        padding: 1;
        border-bottom: solid $border;
    }

    #chat-scroll {
        height: 1fr;
        padding: 1 2;
        background: $bg;
    }

    /* Chat Messages */
    .user-msg {
        background: $highlight;
        color: $info;
        padding: 1;
        margin: 1 0;
        border-left: thick $info;
    }

    .ai-msg {
        background: $panel-bg;
        color: $fg;
        padding: 1;
        margin: 1 0;
        border-left: thick $success;
    }

    .system-msg {
        color: $dim;
        text-style: italic;
        padding: 0 1;
        margin: 1 0;
    }

    /* Status Bar */
    #status-bar {
        height: 1;
        background: $highlight;
        color: $fg;
        padding: 0 1;
        text-align: left;
    }
    
    #status-container {
        height: auto;
        background: $highlight;
        padding: 0 1;
    }

    #input-container {
        height: auto;
        padding: 1;
        background: $panel-bg;
        border-top: solid $border;
    }

    #user-input {
        background: $highlight;
        color: $fg;
        border: tall $highlight;
        padding: 0 1;
        height: 3;
        width: 1fr;
    }

    #user-input:focus {
        border: tall $accent;
    }
    
    .stop-btn {
        width: 5;
        min-width: 5;
        height: 3;
        margin-left: 1;
    }

    /* === RIGHT PANEL === */
    #right-panel {
        width: 45;
        height: 100%;
        background: $panel-bg;
    }

    /* === TABS === */
    Tabs {
        background: $bg;
        color: $dim;
        height: 3;
        dock: top;
        padding: 0 1;
    }

    Tab {
        background: $bg;
        color: $dim;
        padding: 0 2;
        height: 3;
        border-top: none;
        border-left: none;
        border-right: none;
        border-bottom: thick transparent;
        content-align: center middle;
    }

    Tab:hover {
        background: $panel-bg;
        color: $fg;
        border-bottom: thick $highlight;
    }

    Tab.-active {
        background: $bg;
        color: $accent;
        text-style: bold;
        border-bottom: thick $accent;
    }
    
    /* Remove underline from active tab content */
    Tab.-active .underline--bar {
        color: $accent;
    }

    /* === DASHBOARD === */
    #dashboard-view {
        height: 1fr;
        padding: 1;
        background: $panel-bg;
    }

    .tool-card {
        background: $highlight;
        border: solid $highlight;
        padding: 1;
        margin: 0 0 1 0;
    }

    /* === WORKSPACE === */
    #workspace-container {
        height: 100%;
        background: $panel-bg;
        overflow-y: auto;
    }

    .tree-label {
        height: 2;
        background: $highlight;
        padding: 0 1;
        text-style: bold;
        margin-top: 1;
    }

    DirectoryTree {
        background: $panel-bg;
        color: $fg;
        padding: 0 1;
        height: auto;
        max-height: 50%;
    }
    
    SandboxTree {
        background: $panel-bg;
        color: $fg;
        padding: 0 1;
        height: auto;
        max-height: 50%;
    }

    DirectoryTree > .directory-tree--folder {
        color: $warning;
    }

    DirectoryTree > .directory-tree--file {
        color: $fg;
    }

    /* === EDITOR === */
    #editor-container {
        height: 100%;
        background: $bg;
    }

    #editor-toolbar {
        height: 3;
        background: $panel-bg;
        border-bottom: solid $border;
        align: left middle;
        padding: 0 1;
    }

    #editor-header {
        height: 1;
        background: transparent;
        color: $info;
        text-style: bold;
        border: none;
        width: 1fr;
        padding: 0;
    }
    
    .small-btn {
        min-width: 8;
        height: 1;
        margin-left: 1;
        border: none;
    }

    #code-editor {
        height: 1fr;
        background: $bg;
        color: $fg;
    }
    
    /* === FOOTER === */
    Footer {
        background: $bg;
        color: $dim;
    }

    Footer > .footer--key {
        background: $highlight;
        color: $accent;
    }

    /* === SESSION SIDEBAR WIDGETS === */
    /* === SESSION SIDEBAR WIDGETS === */
    SessionSidebar {
        width: 100%;
        height: 100%;
        background: $bg;
        border-right: solid $border;
        padding: 0;
        margin: 0;
    }
    
    TabbedContent {
        height: 100%;
        background: $bg;
    }
    
    ContentSwitcher {
        height: 1fr;
        background: $bg;
    }
    
    TabPane {
        height: 100%;
        padding: 0;
        background: $bg;
    }

    Tree {
        background: $panel-bg;
        color: $fg;
        padding: 0 1;
        height: auto;
        max-height: 50%;
    }
    
    #sidebar-header {
        height: 3;
        background: $panel-bg;
        color: $accent;
        text-align: center;
        text-style: bold;
        padding: 1;
        border-bottom: solid $border;
        margin: 0;
    }
    
    #sidebar-actions {
        height: auto;
        padding: 1;
        background: $panel-bg;
        border-bottom: solid $border;
    }
    
    #sidebar-actions Button {
        width: 100%;
        margin: 0;
    }
    
    #btn-new-session {
        background: $success;
        color: $bg;
    }
    
    #btn-new-session:hover {
        background: $success;
        opacity: 80%;
    }
    
    #session-list-scroll {
        height: 1fr;
        padding: 1;
        background: $bg;
    }
    
    #session-list {
        height: auto;
    }
    
    #sidebar-footer {
        height: auto;
        padding: 1;
        background: $panel-bg;
        border-top: solid $border;
        text-align: center;
    }
    
    .no-sessions {
        color: $dim;
        text-align: center;
        padding: 2;
    }

    SessionItem {
        height: auto;
        padding: 1;
        margin: 0 0 1 0;
        background: $highlight;
        border-left: thick transparent;
    }
    
    SessionItem:hover {
        background: $highlight;
        border-left: thick $accent;
        opacity: 90%;
    }
    
    SessionItem.active {
        background: $highlight;
        border-left: thick $success;
    }
    
    SessionItem .session-title {
        color: $fg;
        height: auto;
        width: 1fr;
    }
    
    SessionItem .session-meta {
        color: $dim;
        height: auto;
    }
    
    SessionItem .session-row {
        height: auto;
        width: 100%;
        align: left middle;
    }
    
    SessionItem .btn-delete {
        width: 3;
        min-width: 3;
        max-width: 3;
        height: 1;
        background: $highlight;
        color: $dim;
        border: none;
        padding: 0;
        margin: 0;
        text-align: center;
    }
    
    SessionItem .btn-delete:hover {
        color: $error;
        background: $highlight;
    }
    
    SessionItem .btn-delete:focus {
        color: $error;
    }

    /* === SANDBOX PANEL === */
    SandboxPanel {
        height: 100%;
        background: $bg;
        padding: 1;
    }
    
    #sandbox-header {
        height: 3;
        background: $panel-bg;
        padding: 1;
        border-bottom: solid $border;
    }
    
    #sandbox-title {
        color: $accent;
        text-style: bold;
    }
    
    #sandbox-status-indicator {
        color: $dim;
    }
    
    #sandbox-controls {
        height: auto;
        padding: 1;
        background: $panel-bg;
        border-bottom: solid $border;
    }
    
    #sandbox-controls Button {
        margin-right: 1;
        min-width: 12;
    }
    
    #btn-sandbox-start {
        background: $success;
        color: $bg;
    }
    
    #btn-sandbox-stop {
        background: $error;
        color: $fg;
    }
    
    #btn-sandbox-clear {
        background: $info;
        color: $fg;
    }
    
    #terminal-container {
        height: 1fr;
        padding: 0;
    }
    
    #sandbox-terminal {
        height: 1fr;
        background: #0d0d0d;
        color: $fg;
        padding: 1;
        border: solid $border;
    }
    
    #sandbox-footer {
        height: auto;
        padding: 1;
        background: $panel-bg;
        border-top: solid $border;
        color: $dim;
    }

    SandboxTerminal {
        height: 1fr;
        background: $bg;
        border: solid $border;
        padding: 1;
    }

    /* === MODEL SELECTOR MODAL === */
    ModelSelectorModal {
        align: center middle;
    }
    
    #model-modal {
        width: 75;
        height: 85%;
        max-height: 50;
        background: $panel-bg;
        border: solid $accent;
        padding: 0;
    }
    
    #model-modal-header {
        height: 3;
        background: $bg;
        border-bottom: solid $border;
        padding: 0 1;
    }
    
    #model-modal-title {
        width: 1fr;
        content-align: left middle;
        text-style: bold;
        color: $accent;
    }
    
    #model-modal-header #btn-close {
        width: 5;
        min-width: 5;
    }
    
    #model-modal-info {
        height: 3;
        padding: 1;
        text-align: center;
        border-bottom: solid $border;
    }
    
    #model-list {
        height: 1fr;
        padding: 1;
        scrollbar-gutter: stable;
    }
    
    .model-card {
        background: $bg;
        border: solid $border;
        margin-bottom: 1;
        padding: 1;
        height: auto;
    }
    
    .model-card-secondary {
        border: dashed $dim;
    }
    
    .model-card-header {
        height: 3;
        margin-bottom: 1;
    }
    
    .model-card-title {
        width: 1fr;
        text-style: bold;
        color: $fg;
        content-align: left middle;
    }
    
    .model-card-status {
        width: auto;
        color: $dim;
        content-align: right middle;
    }
    
    .model-card-row {
        height: 3;
        margin-bottom: 1;
    }
    
    .model-label {
        width: 12;
        content-align: left middle;
        color: $dim;
    }
    
    .model-select {
        width: 1fr;
    }
    
    .model-input {
        width: 1fr;
    }
    
    .model-card-actions {
        height: 3;
        margin-top: 1;
    }
    
    .test-btn {
        width: 12;
    }
    
    .test-result {
        width: 1fr;
        content-align: left middle;
        padding-left: 1;
        color: $info;
    }
    
    .section-divider {
        height: 3;
        text-align: center;
        color: $dim;
        content-align: center middle;
        margin: 1 0;
    }
    
    #model-modal-footer {
        height: 4;
        align: center middle;
        border-top: solid $border;
        padding: 1;
        background: $bg;
    }
    
    #model-modal-footer Button {
        margin: 0 1;
        min-width: 12;
    }

    /* === FALLBACK SELECTOR MODAL === */
    FallbackSelectorModal {
        align: center middle;
    }
    
    #fallback-modal {
        width: 80;
        height: 85%;
        max-height: 50;
        background: $panel-bg;
        border: solid $warning;
        padding: 0;
    }
    
    #fallback-modal-header {
        height: 3;
        background: $bg;
        border-bottom: solid $border;
        padding: 0 1;
    }
    
    #fallback-modal-title {
        width: 1fr;
        content-align: left middle;
        text-style: bold;
        color: $warning;
    }
    
    #fallback-modal-header #btn-close {
        width: 5;
        min-width: 5;
    }
    
    #fallback-modal-info {
        height: 3;
        padding: 1;
        text-align: center;
        border-bottom: solid $border;
    }
    
    #fallback-list {
        height: 1fr;
        padding: 1;
        scrollbar-gutter: stable;
    }
    
    .fallback-card {
        background: $bg;
        border: solid $border;
        margin-bottom: 1;
        padding: 1;
        height: auto;
    }
    
    .fallback-card-header {
        height: 3;
        margin-bottom: 1;
        border-bottom: dashed $dim;
        padding-bottom: 1;
    }
    
    .fallback-card-title {
        width: auto;
        text-style: bold;
        color: $fg;
        margin-right: 2;
        content-align: left middle;
    }
    
    .fallback-primary-info {
        width: 1fr;
        content-align: right middle;
    }
    
    .fallback-row {
        height: 3;
        margin-bottom: 1;
    }
    
    .fallback-index {
        width: 4;
        content-align: center middle;
        color: $accent;
        text-style: bold;
    }
    
    .fallback-select {
        width: 22;
        margin-right: 1;
    }
    
    .fallback-input {
        width: 1fr;
    }
    
    #fallback-modal-footer {
        height: 4;
        align: center middle;
        border-top: solid $border;
        padding: 1;
        background: $bg;
    }
    
    #fallback-modal-footer Button {
        margin: 0 1;
        min-width: 10;
    }

    /* === MONITOR & TOOLS PANELS === */
    #monitor-scroll {
        height: 1fr;
        padding: 1;
        scrollbar-gutter: stable;
    }
    
    #tool-factory-panel {
        height: 1fr;
        overflow-y: auto;
    }
    
    #tf-tools-scroll {
        height: 1fr;
        min-height: 10;
        scrollbar-gutter: stable;
    }
    
    TabPane {
        height: 1fr;
        overflow: auto;
    }
"""



def get_css(theme_name="gruvbox"):
    """Full CSS string (variables + rules)"""
    vars = get_theme_variables(theme_name)
    
    var_lines = []
    for k, v in vars.items():
        var_lines.append(f"    ${k}: {v};")
    
    return "\n".join(var_lines) + "\n" + BASE_CSS

# Default CSS for backward compatibility
APP_CSS = get_css("gruvbox")
