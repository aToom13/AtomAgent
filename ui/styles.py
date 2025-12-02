"""
AtomAgent UI Styles - Modern Gruvbox Theme
"""

APP_CSS = """
    Screen {
        background: #1d2021;
        color: #ebdbb2;
    }

    /* === MAIN LAYOUT === */
    #main-container {
        layout: horizontal;
        height: 100%;
    }

    /* === LEFT SIDEBAR (Sessions + Workspace) === */
    #left-sidebar {
        width: 28;
        height: 100%;
        background: #1d2021;
        border-right: solid #3c3836;
    }
    
    #left-tabs {
        height: 100%;
    }
    
    #session-sidebar {
        width: 100%;
        height: 100%;
        background: #1d2021;
        padding: 0;
        margin: 0;
        border: none;
    }
    
    #session-sidebar #sidebar-header {
        display: none;
    }
    
    #session-sidebar #sidebar-footer {
        display: none;
    }

    /* === LEFT PANEL - CHAT === */
    #left-panel {
        width: 1fr;
        height: 100%;
        background: #1d2021;
        border-right: solid #3c3836;
    }

    #chat-header {
        height: 3;
        background: #282828;
        color: #fe8019;
        text-align: center;
        text-style: bold;
        padding: 1;
        border-bottom: solid #3c3836;
    }

    #chat-scroll {
        height: 1fr;
        padding: 1 2;
        background: #1d2021;
    }

    /* Chat Messages */
    .user-msg {
        background: #3c3836;
        color: #83a598;
        padding: 1;
        margin: 1 0;
        border-left: thick #458588;
    }

    .ai-msg {
        background: #282828;
        color: #ebdbb2;
        padding: 1;
        margin: 1 0;
        border-left: thick #b8bb26;
    }

    .system-msg {
        color: #928374;
        text-style: italic;
        padding: 0 1;
        margin: 1 0;
    }

    /* Status Bar */
    #status-bar {
        height: 1;
        background: #3c3836;
        color: #ebdbb2;
        padding: 0 1;
        text-align: left;
    }

    /* Status Container - Normal ve Permission modları */
    #status-container {
        height: auto;
        background: #3c3836;
        padding: 0 1;
    }

    #perm-text {
        color: #fabd2f;
        padding: 0 1;
    }

    #perm-buttons {
        height: auto;
        layout: horizontal;
        padding: 0 1;
    }

    #perm-buttons Button {
        margin: 0 1;
        min-width: 10;
        height: 1;
    }

    /* Input Area */
    #input-container {
        height: auto;
        padding: 1;
        background: #282828;
        border-top: solid #3c3836;
    }

    #user-input {
        background: #3c3836;
        color: #ebdbb2;
        border: tall #504945;
        padding: 0 1;
        height: 3;
    }

    #user-input:focus {
        border: tall #fe8019;
    }

    /* === RIGHT PANEL - DASHBOARD === */
    #right-panel {
        width: 45;
        height: 100%;
        background: #282828;
    }

    /* Tabs */
    TabbedContent {
        height: 100%;
    }

    Tabs {
        background: #1d2021;
        color: #a89984;
    }

    Tab {
        background: #1d2021;
        color: #a89984;
        padding: 0 2;
    }

    Tab:hover {
        background: #3c3836;
        color: #ebdbb2;
    }

    Tab.-active {
        background: #3c3836;
        color: #fe8019;
        text-style: bold;
    }

    TabPane {
        height: 100%;
        padding: 0;
    }

    ContentSwitcher {
        height: 1fr;
    }

    /* === DASHBOARD VIEW === */
    #dashboard-view {
        height: 1fr;
        padding: 1;
        background: #282828;
    }

    /* Tool Output Cards */
    .tool-card {
        background: #3c3836;
        border: solid #504945;
        padding: 1;
        margin: 0 0 1 0;
    }

    .tool-card-header {
        color: #fe8019;
        text-style: bold;
        margin-bottom: 1;
    }

    .search-card {
        background: #32302f;
        border: solid #458588;
        padding: 1;
        margin: 0 0 1 0;
    }

    .neofetch-output {
        background: #1d2021;
        border: solid #98971a;
        padding: 1;
        margin: 0 0 1 0;
    }

    .loading-card {
        background: #32302f;
        border: dashed #d79921;
        color: #d79921;
        padding: 1;
        margin: 0 0 1 0;
        text-align: center;
    }

    .success-msg {
        color: #b8bb26;
        padding: 0 1;
    }

    .error-msg {
        color: #fb4934;
        padding: 0 1;
    }

    .info-msg {
        color: #83a598;
        padding: 0 1;
    }

    /* === WORKSPACE TREE === */
    #workspace-container {
        height: 100%;
        background: #282828;
        overflow-y: auto;
    }

    .tree-label {
        height: 2;
        background: #3c3836;
        padding: 0 1;
        text-style: bold;
        margin-top: 1;
    }
    
    .tree-label:first-child {
        margin-top: 0;
    }

    #workspace-header {
        height: 3;
        background: #3c3836;
        color: #b8bb26;
        text-align: center;
        text-style: bold;
        padding: 1;
    }

    DirectoryTree {
        background: #282828;
        color: #ebdbb2;
        padding: 0 1;
        height: auto;
        max-height: 50%;
    }
    
    #sandbox-tree {
        border-top: solid #504945;
    }

    DirectoryTree > .directory-tree--folder {
        color: #fabd2f;
    }

    DirectoryTree > .directory-tree--file {
        color: #ebdbb2;
    }

    DirectoryTree:focus > .directory-tree--cursor {
        background: #3c3836;
    }

    /* === TODO PANEL === */
    #todo-scroll {
        height: 1fr;
        background: #282828;
        padding: 1;
    }

    #todo-area {
        height: auto;
        background: #282828;
        color: #ebdbb2;
        padding: 1;
    }

    /* === EDITOR === */
    #editor-container {
        height: 100%;
        background: #1d2021;
    }

    #editor-header {
        height: 3;
        background: #3c3836;
        color: #8ec07c;
        padding: 1;
        text-style: bold;
        border-bottom: solid #504945;
    }

    #code-editor {
        height: 1fr;
        background: #1d2021;
        color: #ebdbb2;
    }

    TextArea > .text-area--cursor-line {
        background: #32302f;
    }

    TextArea > .text-area--gutter {
        background: #282828;
        color: #665c54;
        padding-right: 1;
    }

    TextArea > .text-area--cursor {
        background: #fe8019;
        color: #1d2021;
    }

    /* === STATUS BAR === */
    #status-bar {
        height: 1;
        background: #3c3836;
        color: #a89984;
        padding: 0 1;
    }

    .status-item {
        margin-right: 2;
    }

    /* === FOOTER === */
    Footer {
        background: #1d2021;
        color: #928374;
    }

    Footer > .footer--key {
        background: #3c3836;
        color: #fe8019;
    }

    Footer > .footer--description {
        color: #a89984;
    }

    /* === SCROLLBARS === */
    VerticalScroll > .scrollbar {
        background: #3c3836;
    }

    VerticalScroll > .scrollbar--bar {
        background: #665c54;
    }

    VerticalScroll > .scrollbar--bar:hover {
        background: #928374;
    }

    /* === DEBUG PANEL === */
    #debug-container {
        height: 100%;
        background: #1d2021;
        padding: 1;
    }

    #agent-state {
        height: auto;
        background: #282828;
        border: solid #3c3836;
        padding: 1;
        margin-bottom: 1;
    }

    #task-progress {
        height: auto;
        background: #282828;
        border: solid #3c3836;
        padding: 1;
        margin-bottom: 1;
    }

    #tool-activity {
        height: auto;
        max-height: 10;
        background: #282828;
        border: solid #3c3836;
        padding: 1;
        margin-bottom: 1;
    }

    #debug-log {
        height: 1fr;
        background: #1d2021;
        border: solid #3c3836;
        padding: 1;
    }

    RichLog {
        background: #1d2021;
        color: #ebdbb2;
        scrollbar-background: #3c3836;
        scrollbar-color: #665c54;
    }

    /* === CODE HIGHLIGHTING === */
    .code-block {
        background: #1d2021;
        border: solid #504945;
        padding: 1;
        margin: 1 0;
    }

    .code-keyword {
        color: #fb4934;
        text-style: bold;
    }

    .code-string {
        color: #b8bb26;
    }

    .code-comment {
        color: #928374;
        text-style: italic;
    }

    .code-number {
        color: #d3869b;
    }

    .code-function {
        color: #8ec07c;
    }
"""
