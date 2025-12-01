IDE_CSS = """
    Screen {
        background: #1e1e1e;
        color: #cccccc;
        layout: horizontal;
    }

    /* --- Left Panel: Sidebar --- */
    #sidebar {
        width: 20%;
        height: 100%;
        background: #252526;
        border-right: solid #1e1e1e;
        dock: left;
    }

    #sidebar-header {
        background: #252526;
        color: #bbbbbb;
        padding: 1;
        text-style: bold;
        border-bottom: solid #1e1e1e;
    }

    DirectoryTree {
        background: #252526;
        color: #cccccc;
        border: none;
    }

    /* --- Right Panel: AI Chat --- */
    #ai-panel {
        width: 25%;
        height: 100%;
        background: #252526;
        border-left: solid #1e1e1e;
        dock: right;
        layout: vertical;
    }

    #ai-header {
        background: #252526;
        color: #bbbbbb;
        padding: 1;
        text-style: bold;
        border-bottom: solid #1e1e1e;
        text-align: center;
    }

    #chat-scroll {
        height: 1fr;
        padding: 1;
        overflow-y: auto;
        background: #252526;
    }

    #user-input {
        dock: bottom;
        height: 3;
        background: #3c3c3c;
        border: solid #007acc;
        color: #ffffff;
        margin: 1;
    }

    .user-msg {
        color: #4ec9b0;
        text-style: bold;
        margin-top: 1;
    }

    .ai-msg {
        color: #ce9178;
        margin-bottom: 1;
    }

    /* --- Middle Container (Editor + Terminal) --- */
    #middle-container {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }

    /* --- Editor Area --- */
    #editor-area {
        height: 1fr;
        background: #1e1e1e;
        layout: vertical;
    }

    #editor-header {
        width: 100%;
        background: #2d2d2d;
        color: #cccccc;
        padding: 0 1;
        border-bottom: solid #1e1e1e;
    }

    TextArea {
        width: 100%;
        height: 1fr;
        background: #1e1e1e;
        color: #d4d4d4;
        border: none;
    }
    
    TextArea > .text-area--cursor-line {
        background: #2d2d2d;
    }

    TextArea > .text-area--gutter {
        background: #1e1e1e;
        color: #858585;
        border-right: solid #444444;
    }

    /* --- Terminal Panel --- */
    #terminal-panel {
        height: 25%;
        background: #000000;
        border-top: solid #444444;
        layout: vertical;
    }

    #terminal-header {
        background: #1e1e1e;
        color: #cccccc;
        padding: 0 1;
        text-style: bold;
        border-bottom: solid #444444;
    }

    RichLog {
        background: #000000;
        color: #cccccc;
        height: 1fr;
        overflow-y: auto;
        padding: 1;
    }
"""
