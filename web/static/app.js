/**
 * AtomAgent Web UI - Main Application
 */

// State
const state = {
    currentSessionId: null,
    sessions: [],
    ws: null,
    isStreaming: false,
    settings: null,
    prompts: {},
    sidebarCollapsed: false,
    currentModelRole: 'supervisor',
    currentFallbackRole: 'supervisor',
    rightPanelWidth: 380,
    fileSource: 'workspace', // 'workspace' or 'docker'
    thinkingPanelOpen: false,
    hasReceivedContent: false // Track if we received actual content
};

// DOM Elements
const elements = {
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

// Initialize
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupEventListeners();
    await loadSessions();
    await loadSettings();
    connectWebSocket();
    loadWorkspaceFiles();
    checkDockerStatus();
}

// Event Listeners
function setupEventListeners() {
    // Sidebar toggle
    document.getElementById('toggle-sidebar').addEventListener('click', toggleSidebar);
    document.getElementById('expand-sidebar').addEventListener('click', toggleSidebar);
    
    // New chat
    document.getElementById('new-chat-btn').addEventListener('click', newChat);
    document.getElementById('new-chat-collapsed').addEventListener('click', newChat);
    
    // Settings
    document.getElementById('settings-btn').addEventListener('click', openSettings);
    document.getElementById('settings-collapsed').addEventListener('click', openSettings);
    document.getElementById('close-settings').addEventListener('click', closeSettings);
    document.querySelector('.modal-backdrop').addEventListener('click', closeSettings);
    
    // Message input
    elements.messageInput.addEventListener('keydown', handleInputKeydown);
    elements.messageInput.addEventListener('input', autoResizeTextarea);
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.stopBtn.addEventListener('click', stopGeneration);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Settings tabs
    document.querySelectorAll('.settings-tab').forEach(btn => {
        btn.addEventListener('click', () => switchSettingsTab(btn.dataset.settings));
    });
    
    // Prompt selector
    document.getElementById('prompt-select').addEventListener('change', loadPrompt);
    document.getElementById('save-prompt-btn').addEventListener('click', savePrompt);
    
    // Save file
    document.getElementById('save-file-btn').addEventListener('click', saveFile);
    
    // Model role tabs
    document.querySelectorAll('#model-role-tabs .role-tab').forEach(btn => {
        btn.addEventListener('click', () => switchModelRole(btn.dataset.role));
    });
    
    // Fallback role tabs
    document.querySelectorAll('#fallback-role-tabs .role-tab').forEach(btn => {
        btn.addEventListener('click', () => switchFallbackRole(btn.dataset.role));
    });
    
    // Add fallback button
    document.getElementById('add-fallback-btn').addEventListener('click', addFallback);
    
    // Resize handle
    setupResizeHandle();
}

// WebSocket Connection
function connectWebSocket() {
    const clientId = 'client_' + Date.now();
    const wsUrl = `ws://${window.location.host}/ws/chat/${clientId}`;
    
    state.ws = new WebSocket(wsUrl);
    
    state.ws.onopen = () => {
        console.log('WebSocket connected');
        updateStatus('Bağlandı', true);
    };
    
    state.ws.onclose = () => {
        console.log('WebSocket disconnected');
        updateStatus('Bağlantı kesildi', false);
        setTimeout(connectWebSocket, 3000);
    };
    
    state.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('Bağlantı hatası', false);
    };
    
    state.ws.onmessage = handleWebSocketMessage;
}

function handleWebSocketMessage(event) {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'session_created':
            state.currentSessionId = data.session.id;
            loadSessions();
            break;
            
        case 'stream_start':
            state.isStreaming = true;
            updateStreamingUI(true);
            createAIMessageElement();
            break;
            
        case 'token':
            appendToken(data.content);
            break;
            
        case 'tool_start':
            addToolActivity(data.tool, data.input, 'start');
            break;
            
        case 'tool_end':
            addToolActivity(data.tool, data.output, 'end');
            break;
            
        case 'stream_end':
            state.isStreaming = false;
            updateStreamingUI(false);
            finalizeAIMessage();
            loadSessions();
            break;
            
        case 'error':
            showError(data.message);
            state.isStreaming = false;
            updateStreamingUI(false);
            break;
            
        case 'stopped':
            state.isStreaming = false;
            updateStreamingUI(false);
            break;
            
        case 'system':
            showSystemMessage(data.message);
            break;
            
        case 'status':
            updateAgentStatus(data.status, data.message, data.model);
            break;
            
        case 'thinking_start':
            startThinkingBlock(data.title);
            break;
            
        case 'thinking_token':
            appendThinkingToken(data.content);
            break;
            
        case 'thinking_end':
            endThinkingBlock();
            break;
            
        case 'docker_command':
            addDockerCommand(data.command, data.status);
            break;
            
        case 'docker_output':
            addDockerOutput(data.output, data.status);
            break;
    }
}

function showSystemMessage(message) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = message;
    elements.messages.appendChild(div);
    scrollToBottom();
}

// Agent Status Bar
function updateAgentStatus(status, message, model) {
    const statusBar = document.getElementById('agent-status-bar');
    const statusText = document.getElementById('status-text');
    const statusModel = document.getElementById('status-model');
    
    if (status === 'ready') {
        statusBar.classList.add('hidden');
        return;
    }
    
    statusBar.classList.remove('hidden');
    statusBar.className = 'agent-status-bar ' + status;
    statusText.textContent = message;
    
    if (model) {
        statusModel.textContent = model;
        statusModel.style.display = 'block';
    }
}

// Thinking Block
let currentThinkingBlock = null;
let thinkingContent = '';

function startThinkingBlock(title) {
    thinkingContent = '';
    
    const block = document.createElement('div');
    block.className = 'thinking-block active';
    block.innerHTML = `
        <div class="thinking-header" onclick="toggleThinking(this)">
            <span class="thinking-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
            </span>
            <span class="thinking-title">${title || 'Düşünüyor...'}</span>
            <span class="thinking-toggle">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </span>
        </div>
        <div class="thinking-content"></div>
    `;
    
    currentThinkingBlock = block;
    elements.messages.appendChild(block);
    scrollToBottom();
}

function appendThinkingToken(token) {
    if (!currentThinkingBlock) return;
    
    thinkingContent += token;
    const contentEl = currentThinkingBlock.querySelector('.thinking-content');
    if (contentEl) {
        // Clean up thinking tags
        let cleanContent = thinkingContent
            .replace(/<think>/g, '')
            .replace(/<\/think>/g, '')
            .replace(/\*\*Düşünce:\*\*/g, '')
            .replace(/\*\*Thinking:\*\*/g, '');
        
        contentEl.innerHTML = renderMarkdown(cleanContent);
    }
    scrollToBottom();
}

function endThinkingBlock() {
    if (currentThinkingBlock) {
        currentThinkingBlock.classList.remove('active');
        // Auto-collapse after ending
        currentThinkingBlock.classList.add('collapsed');
        
        // Update title with summary
        const titleEl = currentThinkingBlock.querySelector('.thinking-title');
        if (titleEl && thinkingContent.length > 50) {
            const summary = thinkingContent.substring(0, 50).replace(/<[^>]*>/g, '').trim() + '...';
            titleEl.textContent = summary;
        }
    }
    currentThinkingBlock = null;
    thinkingContent = '';
}

function toggleThinking(header) {
    const block = header.parentElement;
    block.classList.toggle('collapsed');
}

// Sessions
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions?limit=50');
        const data = await response.json();
        state.sessions = data.sessions;
        renderSessions();
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

function renderSessions() {
    elements.sessionsList.innerHTML = state.sessions.map(session => `
        <div class="session-item ${session.id === state.currentSessionId ? 'active' : ''}" 
             data-id="${session.id}">
            <div class="session-info" onclick="loadSession('${session.id}')">
                <div class="session-title">${escapeHtml(session.title)}</div>
                <div class="session-meta">${session.message_count} mesaj • ${formatDate(session.updated_at)}</div>
            </div>
            <button class="session-delete" onclick="deleteSession('${session.id}', event)" title="Sil">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
            </button>
        </div>
    `).join('');
}

async function loadSession(sessionId) {
    state.currentSessionId = sessionId;
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}/messages`);
        const data = await response.json();
        
        elements.messages.innerHTML = '';
        
        data.messages.forEach(msg => {
            if (msg.role === 'human') {
                addUserMessage(msg.content);
            } else if (msg.role === 'ai') {
                addAIMessage(msg.content);
            }
        });
        
        renderSessions();
        scrollToBottom();
    } catch (error) {
        console.error('Failed to load session:', error);
    }
}

async function deleteSession(sessionId, event) {
    event.stopPropagation();
    
    if (!confirm('Bu sohbeti silmek istediğinizden emin misiniz?')) return;
    
    try {
        await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
        
        if (state.currentSessionId === sessionId) {
            state.currentSessionId = null;
            elements.messages.innerHTML = getWelcomeMessage();
        }
        
        await loadSessions();
    } catch (error) {
        console.error('Failed to delete session:', error);
    }
}

function newChat() {
    state.currentSessionId = null;
    elements.messages.innerHTML = getWelcomeMessage();
    elements.messageInput.focus();
    renderSessions();
}

function getWelcomeMessage() {
    return `
        <div class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <h2>AtomAgent'a Hoş Geldiniz</h2>
            <p>AI destekli geliştirme asistanınız hazır. Bir soru sorun veya görev verin.</p>
        </div>
    `;
}

// Messages
function sendMessage() {
    const content = elements.messageInput.value.trim();
    if (!content || state.isStreaming) return;
    
    // Clear welcome message
    const welcome = elements.messages.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    // Add user message
    addUserMessage(content);
    
    // Send via WebSocket
    state.ws.send(JSON.stringify({
        type: 'message',
        content: content,
        session_id: state.currentSessionId
    }));
    
    // Clear input
    elements.messageInput.value = '';
    autoResizeTextarea();
    scrollToBottom();
}

function addUserMessage(content) {
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = escapeHtml(content).replace(/\n/g, '<br>');
    elements.messages.appendChild(div);
    scrollToBottom();
}

function addAIMessage(content) {
    const div = document.createElement('div');
    div.className = 'message ai';
    div.innerHTML = renderMarkdown(content);
    elements.messages.appendChild(div);
    highlightCode();
    scrollToBottom();
}

let currentAIMessage = null;
let currentAIContent = '';

function createAIMessageElement() {
    currentAIContent = '';
    state.hasReceivedContent = false;
    currentAIMessage = document.createElement('div');
    currentAIMessage.className = 'message ai pending';
    currentAIMessage.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    elements.messages.appendChild(currentAIMessage);
    scrollToBottom();
}

function appendToken(token) {
    if (!currentAIMessage) return;
    
    // Mark that we received actual content
    if (!state.hasReceivedContent && token.trim()) {
        state.hasReceivedContent = true;
        currentAIMessage.classList.remove('pending');
    }
    
    currentAIContent += token;
    currentAIMessage.innerHTML = renderMarkdown(currentAIContent);
    scrollToBottom();
}

function finalizeAIMessage() {
    // Remove empty messages (API retry cases)
    if (currentAIMessage && !state.hasReceivedContent) {
        currentAIMessage.remove();
    } else if (currentAIMessage && currentAIContent) {
        currentAIMessage.classList.remove('pending');
        currentAIMessage.innerHTML = renderMarkdown(currentAIContent);
        highlightCode();
    }
    currentAIMessage = null;
    currentAIContent = '';
    state.hasReceivedContent = false;
}

function addToolActivity(toolName, content, type) {
    const div = document.createElement('div');
    div.className = 'tool-activity';
    
    if (type === 'start') {
        div.innerHTML = `
            <span class="tool-name">🔧 ${escapeHtml(toolName)}</span>
            <div class="tool-output">${escapeHtml(content.substring(0, 200))}${content.length > 200 ? '...' : ''}</div>
        `;
    } else {
        div.innerHTML = `
            <span class="tool-name">✅ ${escapeHtml(toolName)}</span>
            <div class="tool-output">${escapeHtml(content.substring(0, 500))}${content.length > 500 ? '...' : ''}</div>
        `;
    }
    
    // Add to terminal
    const terminalLine = document.createElement('div');
    terminalLine.className = 'terminal-line';
    terminalLine.innerHTML = `<span class="info">[${toolName}]</span> <span>${escapeHtml(content.substring(0, 200))}</span>`;
    elements.terminalOutput.appendChild(terminalLine);
    elements.terminalOutput.scrollTop = elements.terminalOutput.scrollHeight;
    
    // Add to messages if streaming
    if (currentAIMessage) {
        elements.messages.insertBefore(div, currentAIMessage);
    }
    
    scrollToBottom();
}

function showError(message) {
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = '❌ Hata: ' + message;
    elements.messages.appendChild(div);
    scrollToBottom();
}

function stopGeneration() {
    if (state.ws && state.isStreaming) {
        state.ws.send(JSON.stringify({ type: 'stop' }));
    }
}

// Settings
async function loadSettings() {
    try {
        const [settingsRes, promptsRes, providersRes] = await Promise.all([
            fetch('/api/settings'),
            fetch('/api/prompts'),
            fetch('/api/providers')
        ]);
        
        state.settings = await settingsRes.json();
        state.prompts = (await promptsRes.json()).prompts;
        state.providers = (await providersRes.json()).providers;
        
        renderModelConfigs();
        renderFallbackConfigs();
        renderCommands();
        renderAPIStatus();
        loadPrompt();
        populateProviderDropdown('new-fallback-provider');
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

function renderModelConfigs() {
    const container = document.getElementById('model-configs');
    const role = state.currentModelRole;
    const config = state.settings.models[role] || {};
    
    container.innerHTML = `
        <div class="model-config-single">
            <div class="config-row">
                <label>Provider</label>
                <select id="provider-${role}" onchange="updateModel('${role}')">
                    ${state.providers.map(p => `
                        <option value="${p.id}" ${p.id === config.provider ? 'selected' : ''}>${p.name}</option>
                    `).join('')}
                </select>
            </div>
            <div class="config-row">
                <label>Model</label>
                <input type="text" id="model-${role}" value="${config.model || ''}" 
                       placeholder="Model adı" onchange="updateModel('${role}')">
            </div>
            <div class="config-row">
                <label>Temperature</label>
                <input type="number" id="temp-${role}" value="${config.temperature || 0}" 
                       min="0" max="2" step="0.1" onchange="updateModel('${role}')">
            </div>
            ${config.current_provider ? `
                <div class="current-info">
                    <strong>Aktif:</strong> ${config.current_provider}/${config.current_model || 'N/A'}
                </div>
            ` : ''}
        </div>
    `;
    
    // Provider dropdown'ı doldur
    populateProviderDropdown('new-fallback-provider');
}

function switchModelRole(role) {
    state.currentModelRole = role;
    
    // Tab'ları güncelle
    document.querySelectorAll('#model-role-tabs .role-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#model-role-tabs [data-role="${role}"]`).classList.add('active');
    
    renderModelConfigs();
}

function populateProviderDropdown(selectId) {
    const select = document.getElementById(selectId);
    if (select && state.providers) {
        select.innerHTML = state.providers.map(p => 
            `<option value="${p.id}">${p.name}</option>`
        ).join('');
    }
}

async function updateModel(role) {
    const provider = document.getElementById(`provider-${role}`).value;
    const model = document.getElementById(`model-${role}`).value;
    const tempInput = document.getElementById(`temp-${role}`);
    const temperature = tempInput ? parseFloat(tempInput.value) : 0;
    
    try {
        await fetch('/api/settings/model', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, provider, model, temperature })
        });
        
        // State'i güncelle
        if (state.settings.models[role]) {
            state.settings.models[role].provider = provider;
            state.settings.models[role].model = model;
            state.settings.models[role].temperature = temperature;
        }
        
        showNotification('Model güncellendi');
    } catch (error) {
        console.error('Failed to update model:', error);
        showNotification('Model güncellenemedi', 'error');
    }
}

// Fallback Functions
function renderFallbackConfigs() {
    const container = document.getElementById('fallback-configs');
    const role = state.currentFallbackRole;
    const config = state.settings.models[role] || {};
    const fallbacks = config.fallbacks || [];
    
    if (fallbacks.length === 0) {
        container.innerHTML = '<div class="fallback-empty">Bu rol için fallback tanımlanmamış.</div>';
    } else {
        container.innerHTML = fallbacks.map((fb, index) => `
            <div class="fallback-item" data-index="${index}">
                <span class="fallback-order">${index + 1}</span>
                <div class="fallback-info">
                    <div class="fallback-provider">${fb.provider}</div>
                    <div class="fallback-model">${fb.model}</div>
                </div>
                <button class="fallback-delete" onclick="deleteFallback(${index})" title="Sil">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `).join('');
    }
}

function switchFallbackRole(role) {
    state.currentFallbackRole = role;
    
    // Tab'ları güncelle
    document.querySelectorAll('#fallback-role-tabs .role-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#fallback-role-tabs [data-role="${role}"]`).classList.add('active');
    
    renderFallbackConfigs();
}

async function addFallback() {
    const provider = document.getElementById('new-fallback-provider').value;
    const model = document.getElementById('new-fallback-model').value.trim();
    const role = state.currentFallbackRole;
    
    if (!model) {
        showNotification('Model adı gerekli', 'error');
        return;
    }
    
    try {
        // Mevcut fallback'leri al ve yenisini ekle
        const config = state.settings.models[role] || {};
        const fallbacks = [...(config.fallbacks || []), { provider, model }];
        
        await fetch('/api/settings/fallback', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, fallbacks })
        });
        
        // State'i güncelle
        if (!state.settings.models[role]) {
            state.settings.models[role] = {};
        }
        state.settings.models[role].fallbacks = fallbacks;
        
        // Input'u temizle
        document.getElementById('new-fallback-model').value = '';
        
        renderFallbackConfigs();
        showNotification('Fallback eklendi');
    } catch (error) {
        console.error('Failed to add fallback:', error);
        showNotification('Fallback eklenemedi', 'error');
    }
}

async function deleteFallback(index) {
    const role = state.currentFallbackRole;
    
    try {
        await fetch(`/api/settings/fallback/${role}/${index}`, {
            method: 'DELETE'
        });
        
        // State'i güncelle
        if (state.settings.models[role] && state.settings.models[role].fallbacks) {
            state.settings.models[role].fallbacks.splice(index, 1);
        }
        
        renderFallbackConfigs();
        showNotification('Fallback silindi');
    } catch (error) {
        console.error('Failed to delete fallback:', error);
        showNotification('Fallback silinemedi', 'error');
    }
}

function renderCommands() {
    const container = document.getElementById('allowed-commands');
    const commands = state.settings.allowed_commands || [];
    
    container.innerHTML = commands.map(cmd => `
        <span class="command-tag">
            ${escapeHtml(cmd)}
            <button onclick="removeCommand('${escapeHtml(cmd)}')">&times;</button>
        </span>
    `).join('');
}

function renderAPIStatus() {
    const container = document.getElementById('api-status');
    
    container.innerHTML = state.providers.map(p => `
        <div class="api-item">
            <span class="provider-name">${p.name}</span>
            <span class="status-badge ${p.has_api_key ? 'active' : 'inactive'}">
                ${p.has_api_key ? `${p.api_key_count} key aktif` : 'Key yok'}
            </span>
        </div>
    `).join('');
}

async function loadPrompt() {
    const promptName = document.getElementById('prompt-select').value;
    const content = state.prompts[promptName] || '';
    document.getElementById('prompt-editor').value = content;
}

async function savePrompt() {
    const promptName = document.getElementById('prompt-select').value;
    const content = document.getElementById('prompt-editor').value;
    
    try {
        await fetch(`/api/prompts/${promptName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        state.prompts[promptName] = content;
        showNotification('Prompt kaydedildi');
    } catch (error) {
        console.error('Failed to save prompt:', error);
        showNotification('Prompt kaydedilemedi', 'error');
    }
}

function openSettings() {
    elements.settingsModal.classList.remove('hidden');
}

function closeSettings() {
    elements.settingsModal.classList.add('hidden');
}

function switchSettingsTab(tabName) {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-settings="${tabName}"]`).classList.add('active');
    document.getElementById(`settings-${tabName}`).classList.add('active');
    
    // Fallback tab'ına geçildiğinde render et
    if (tabName === 'fallbacks') {
        renderFallbackConfigs();
        populateProviderDropdown('new-fallback-provider');
    }
}

// Workspace Files
async function loadWorkspaceFiles(path = '') {
    try {
        const response = await fetch(`/api/workspace/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        renderFileTree(data.items, path, 'workspace');
    } catch (error) {
        console.error('Failed to load files:', error);
        elements.fileTree.innerHTML = '<div class="file-error">Dosyalar yüklenemedi</div>';
    }
}

function renderFileTree(items, currentPath, source = 'workspace') {
    const loadFn = source === 'docker' ? 'loadDockerFiles' : 'loadWorkspaceFiles';
    const openFn = source === 'docker' ? 'openDockerFile' : 'openFile';
    
    elements.fileTree.innerHTML = items.map(item => `
        <div class="file-item ${item.is_dir ? 'folder' : 'file'}" 
             onclick="${item.is_dir ? `${loadFn}('${item.path}')` : `${openFn}('${item.path}')`}">
            ${item.is_dir ? '📁' : '📄'} ${escapeHtml(item.name)}
        </div>
    `).join('');
    
    if (currentPath && currentPath !== '/' && currentPath !== '/home/agent') {
        const parentPath = currentPath.split('/').slice(0, -1).join('/') || (source === 'docker' ? '/home/agent' : '');
        elements.fileTree.innerHTML = `
            <div class="file-item folder" onclick="${loadFn}('${parentPath}')">
                📁 ..
            </div>
        ` + elements.fileTree.innerHTML;
    }
}

async function openFile(path) {
    try {
        const response = await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        elements.codeEditor.value = data.content;
        elements.editorFilename.textContent = path;
        elements.codeEditor.dataset.path = path;
        document.getElementById('save-file-btn').disabled = false;
        
        switchTab('editor');
    } catch (error) {
        console.error('Failed to open file:', error);
    }
}

async function saveFile() {
    const path = elements.codeEditor.dataset.path;
    const content = elements.codeEditor.value;
    
    if (!path) return;
    
    try {
        await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        showNotification('Dosya kaydedildi');
    } catch (error) {
        console.error('Failed to save file:', error);
        showNotification('Dosya kaydedilemedi', 'error');
    }
}

// UI Helpers
function toggleSidebar() {
    state.sidebarCollapsed = !state.sidebarCollapsed;
    
    if (state.sidebarCollapsed) {
        elements.sidebar.classList.add('hidden');
        elements.sidebarCollapsed.classList.remove('hidden');
    } else {
        elements.sidebar.classList.remove('hidden');
        elements.sidebarCollapsed.classList.add('hidden');
    }
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

function updateStatus(text, connected) {
    const statusDot = elements.chatStatus.querySelector('.status-dot');
    const statusText = elements.chatStatus.querySelector('span:last-child');
    
    statusText.textContent = text;
    statusDot.style.background = connected ? 'var(--accent-success)' : 'var(--accent-error)';
}

function updateStreamingUI(streaming) {
    const statusBar = document.getElementById('agent-status-bar');
    
    if (streaming) {
        elements.sendBtn.classList.add('hidden');
        elements.stopBtn.classList.remove('hidden');
        elements.messageInput.disabled = true;
        elements.chatStatus.querySelector('.status-dot').classList.add('loading');
        elements.chatStatus.querySelector('span:last-child').textContent = 'Yanıt yazılıyor...';
    } else {
        elements.sendBtn.classList.remove('hidden');
        elements.stopBtn.classList.add('hidden');
        elements.messageInput.disabled = false;
        elements.chatStatus.querySelector('.status-dot').classList.remove('loading');
        elements.chatStatus.querySelector('span:last-child').textContent = 'Hazır';
        elements.messageInput.focus();
        
        // Hide status bar when done
        if (statusBar) {
            statusBar.classList.add('hidden');
        }
    }
}

function handleInputKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 150) + 'px';
}

function scrollToBottom() {
    elements.messages.scrollTop = elements.messages.scrollHeight;
}

function showNotification(message, type = 'success') {
    // Simple notification - could be enhanced
    console.log(`[${type}] ${message}`);
}

// Utilities
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Az önce';
    if (diff < 3600000) return Math.floor(diff / 60000) + ' dk önce';
    if (diff < 86400000) return Math.floor(diff / 3600000) + ' saat önce';
    if (diff < 604800000) return Math.floor(diff / 86400000) + ' gün önce';
    
    return date.toLocaleDateString('tr-TR');
}

function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            highlight: function(code, lang) {
                if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return code;
            },
            breaks: true
        });
        return marked.parse(text);
    }
    return escapeHtml(text).replace(/\n/g, '<br>');
}

function highlightCode() {
    if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
    }
}

// Resize Handle
function setupResizeHandle() {
    const resizeHandle = document.getElementById('resize-handle');
    const rightPanel = document.getElementById('right-panel');
    
    if (!resizeHandle || !rightPanel) return;
    
    let isResizing = false;
    let startX = 0;
    let startWidth = 0;
    
    resizeHandle.addEventListener('mousedown', (e) => {
        isResizing = true;
        startX = e.clientX;
        startWidth = rightPanel.offsetWidth;
        resizeHandle.classList.add('dragging');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const diff = startX - e.clientX;
        const newWidth = Math.min(Math.max(startWidth + diff, 250), 800);
        
        rightPanel.style.width = newWidth + 'px';
        rightPanel.style.minWidth = newWidth + 'px';
        state.rightPanelWidth = newWidth;
    });
    
    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            resizeHandle.classList.remove('dragging');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
    
    // Touch support for mobile
    resizeHandle.addEventListener('touchstart', (e) => {
        isResizing = true;
        startX = e.touches[0].clientX;
        startWidth = rightPanel.offsetWidth;
        resizeHandle.classList.add('dragging');
        e.preventDefault();
    });
    
    document.addEventListener('touchmove', (e) => {
        if (!isResizing) return;
        
        const diff = startX - e.touches[0].clientX;
        const newWidth = Math.min(Math.max(startWidth + diff, 250), 800);
        
        rightPanel.style.width = newWidth + 'px';
        rightPanel.style.minWidth = newWidth + 'px';
        state.rightPanelWidth = newWidth;
    });
    
    document.addEventListener('touchend', () => {
        if (isResizing) {
            isResizing = false;
            resizeHandle.classList.remove('dragging');
        }
    });
}

// === DOCKER FUNCTIONS ===

async function checkDockerStatus() {
    const indicator = document.getElementById('docker-indicator');
    const statusText = document.getElementById('docker-status-text');
    
    if (!indicator || !statusText) return;
    
    indicator.className = 'docker-indicator loading';
    statusText.textContent = 'Bağlantı kontrol ediliyor...';
    
    try {
        const response = await fetch('/api/docker/status');
        const data = await response.json();
        
        if (data.running) {
            indicator.className = 'docker-indicator online';
            statusText.textContent = `Container çalışıyor: ${data.container_id || 'sandbox'}`;
        } else {
            indicator.className = 'docker-indicator offline';
            statusText.textContent = 'Container çalışmıyor';
        }
    } catch (error) {
        indicator.className = 'docker-indicator offline';
        statusText.textContent = 'Docker bağlantısı yok';
    }
}

function addDockerLog(command, output, isError = false) {
    const dockerOutput = document.getElementById('docker-output');
    if (!dockerOutput) return;
    
    const time = new Date().toLocaleTimeString('tr-TR');
    const line = document.createElement('div');
    line.className = 'docker-line';
    line.innerHTML = `
        <span class="docker-time">[${time}]</span>
        <span class="docker-cmd">$ ${escapeHtml(command)}</span>
        <div class="${isError ? 'docker-error' : 'docker-output-text'}">${escapeHtml(output)}</div>
    `;
    dockerOutput.appendChild(line);
    dockerOutput.scrollTop = dockerOutput.scrollHeight;
}

// Docker command tracking
let currentDockerCommand = null;

function addDockerCommand(command, status) {
    const dockerOutput = document.getElementById('docker-output');
    if (!dockerOutput) return;
    
    const time = new Date().toLocaleTimeString('tr-TR');
    const line = document.createElement('div');
    line.className = 'docker-line running';
    line.id = 'docker-cmd-' + Date.now();
    line.innerHTML = `
        <span class="docker-time">[${time}]</span>
        <span class="docker-cmd">$ ${escapeHtml(command)}</span>
        <div class="docker-status">⏳ Çalışıyor...</div>
    `;
    dockerOutput.appendChild(line);
    dockerOutput.scrollTop = dockerOutput.scrollHeight;
    currentDockerCommand = line;
    
    // Auto-switch to Docker tab if not visible
    highlightDockerTab();
}

function addDockerOutput(output, status) {
    const dockerOutput = document.getElementById('docker-output');
    if (!dockerOutput) return;
    
    if (currentDockerCommand) {
        const statusEl = currentDockerCommand.querySelector('.docker-status');
        if (statusEl) {
            const isError = output.toLowerCase().includes('error') || output.toLowerCase().includes('failed');
            statusEl.className = isError ? 'docker-error' : 'docker-output-text';
            statusEl.innerHTML = escapeHtml(output).replace(/\n/g, '<br>');
        }
        currentDockerCommand.classList.remove('running');
        currentDockerCommand = null;
    } else {
        // Standalone output
        const time = new Date().toLocaleTimeString('tr-TR');
        const line = document.createElement('div');
        line.className = 'docker-line';
        const isError = output.toLowerCase().includes('error') || output.toLowerCase().includes('failed');
        line.innerHTML = `
            <span class="docker-time">[${time}]</span>
            <div class="${isError ? 'docker-error' : 'docker-output-text'}">${escapeHtml(output).replace(/\n/g, '<br>')}</div>
        `;
        dockerOutput.appendChild(line);
    }
    
    dockerOutput.scrollTop = dockerOutput.scrollHeight;
}

function highlightDockerTab() {
    const dockerTab = document.querySelector('[data-tab="docker"]');
    if (dockerTab && !dockerTab.classList.contains('active')) {
        dockerTab.classList.add('has-activity');
        setTimeout(() => dockerTab.classList.remove('has-activity'), 3000);
    }
}

// === FILE TABS (Workspace/Docker) ===

function setupFileTabs() {
    document.querySelectorAll('.file-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.file-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            state.fileSource = tab.dataset.source;
            if (state.fileSource === 'docker') {
                loadDockerFiles();
            } else {
                loadWorkspaceFiles();
            }
        });
    });
}

async function loadDockerFiles(path = '/home/agent') {
    try {
        const response = await fetch(`/api/docker/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        renderFileTree(data.items || [], path, 'docker');
    } catch (error) {
        elements.fileTree.innerHTML = '<div class="file-error">Docker dosyaları yüklenemedi</div>';
    }
}

async function openDockerFile(path) {
    try {
        const response = await fetch(`/api/docker/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        elements.codeEditor.value = data.content;
        elements.editorFilename.textContent = `🐳 ${path}`;
        elements.codeEditor.dataset.path = path;
        elements.codeEditor.dataset.source = 'docker';
        document.getElementById('save-file-btn').disabled = true; // Docker dosyaları read-only
        
        switchTab('editor');
    } catch (error) {
        console.error('Failed to open docker file:', error);
        showNotification('Docker dosyası açılamadı', 'error');
    }
}

// === THINKING PANEL ===

let thinkingPanelContent = '';

function toggleThinkingPanel() {
    const panel = document.getElementById('thinking-panel');
    const statusBar = document.getElementById('agent-status-bar');
    
    if (!panel) return;
    
    state.thinkingPanelOpen = !state.thinkingPanelOpen;
    
    if (state.thinkingPanelOpen) {
        panel.classList.remove('hidden');
        statusBar?.classList.add('expanded');
    } else {
        panel.classList.add('hidden');
        statusBar?.classList.remove('expanded');
    }
}

function updateThinkingPanel(content) {
    const panelContent = document.getElementById('thinking-panel-content');
    if (!panelContent) return;
    
    thinkingPanelContent = content;
    panelContent.innerHTML = renderMarkdown(content);
}

function clearThinkingPanel() {
    thinkingPanelContent = '';
    const panelContent = document.getElementById('thinking-panel-content');
    if (panelContent) {
        panelContent.innerHTML = '<p class="thinking-placeholder">Agent düşünmeye başladığında burada göreceksiniz...</p>';
    }
}

// Update existing functions to use thinking panel
const originalAppendThinkingToken = appendThinkingToken;
appendThinkingToken = function(token) {
    originalAppendThinkingToken(token);
    // Also update thinking panel
    updateThinkingPanel(thinkingContent);
};

const originalEndThinkingBlock = endThinkingBlock;
endThinkingBlock = function() {
    originalEndThinkingBlock();
    // Close thinking panel after a delay
    setTimeout(() => {
        if (state.thinkingPanelOpen) {
            toggleThinkingPanel();
        }
    }, 2000);
};

// Initialize file tabs on load
document.addEventListener('DOMContentLoaded', () => {
    setupFileTabs();
    
    // Docker refresh button
    const refreshBtn = document.getElementById('docker-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', checkDockerStatus);
    }
});
