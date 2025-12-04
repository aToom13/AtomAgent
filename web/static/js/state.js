/**
 * AtomAgent - Global State Management
 */

export const state = {
    currentSessionId: null,
    sessions: [],
    ws: null,
    isStreaming: false,
    settings: null,
    prompts: {},
    providers: [],
    sidebarCollapsed: false,
    currentModelRole: 'supervisor',
    currentFallbackRole: 'supervisor',
    rightPanelWidth: 380,
    fileSource: 'workspace',
    thinkingPanelOpen: false,
    hasReceivedContent: false,
    
    // v2.0 - Agent System
    activeAgent: 'supervisor',
    autoRouting: true,
    
    // v2.0 - Todos
    todos: [],
    todoStats: { total: 0, completed: 0, inProgress: 0, pending: 0 },
    
    // v2.0 - Memory
    memories: [],
    memoryTags: new Set()
};

// DOM Elements - lazy loaded
let _elements = null;

export function getElements() {
    if (!_elements) {
        _elements = {
            sidebar: document.getElementById('sidebar'),
            sidebarCollapsed: document.getElementById('sidebar-collapsed'),
            sessionsList: document.getElementById('sessions-list'),
            messages: document.getElementById('messages'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            stopBtn: document.getElementById('stop-btn'),
            chatStatus: document.getElementById('chat-status'),
            settingsModal: document.getElementById('settings-modal'),
            terminalOutput: document.getElementById('terminal-output'),
            fileTree: document.getElementById('file-tree'),
            codeEditor: document.getElementById('code-editor'),
            editorFilename: document.getElementById('editor-filename')
        };
    }
    return _elements;
}
