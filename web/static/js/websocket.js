/**
 * AtomAgent - WebSocket Handler
 */

import { state, getElements } from './state.js';
import { updateStatus, updateStreamingUI } from './ui.js';
import { createAIMessageElement, appendToken, finalizeAIMessage, addToolActivity, showError, showSystemMessage } from './chat.js';
import { loadSessions } from './sessions.js';
import { updateAgentStatus } from './thinking.js';
import { addDockerCommand, addDockerOutput } from './docker.js';
import { addToolStart, addToolEnd } from './tools.js';
import { addBrowserStart, addBrowserResult } from './browser.js';
import { updateTaskStatus, addTaskStep, handleTodoUpdate as handleTaskTodoUpdate } from './tasks.js';
import { handleTodoUpdate } from './todos.js';
import { handleMemoryUpdate } from './memory.js';
import { handleCanvasMessage, handleServerStart, handleHtmlCreated, handleGuiAppStart } from './canvas.js';

export function connectWebSocket() {
    const clientId = 'client_' + Date.now();
    // Use wss:// for HTTPS (ngrok, production), ws:// for HTTP (localhost)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/chat/${clientId}`;
    
    console.log('[WS] Connecting to:', wsUrl);
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
            addToolStart(data.tool, data.input);
            break;
            
        case 'tool_end':
            addToolActivity(data.tool, data.output, 'end');
            addToolEnd(data.tool, data.output);
            
            // Todo tool'larını tasks paneline gönder
            const todoTools = ['update_todo_list', 'mark_todo_done', 'get_current_todo', 'add_todo_item', 'get_next_todo_step'];
            if (todoTools.includes(data.tool)) {
                handleTaskTodoUpdate(data.tool, data.output);
            }
            break;
            
        // v2.0 - Todo updates
        case 'todo_update':
            handleTodoUpdate(data);
            break;
            
        // v2.0 - Memory updates
        case 'memory_update':
            handleMemoryUpdate(data);
            break;
            
        case 'browser_start':
            addBrowserStart(data.tool, data.url);
            break;
            
        case 'browser_result':
            addBrowserResult(data.tool, data.content);
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
            finalizeAIMessage();
            break;
            
        case 'system':
            showSystemMessage(data.message);
            break;
            
        case 'status':
            updateAgentStatus(data.status, data.message, data.model);
            break;
            
        // Thinking artık sadece status bar'da gösteriliyor
        case 'thinking_start':
        case 'thinking_token':
        case 'thinking_end':
            // Artık kullanılmıyor - status bar yeterli
            break;
            
        case 'docker_command':
            addDockerCommand(data.command, data.status);
            break;
            
        case 'docker_output':
            addDockerOutput(data.output, data.status);
            break;
            
        // Canvas - Live Preview
        case 'server_started':
            handleServerStart(data.port, data.server_type);
            break;
            
        case 'canvas_url':
            handleCanvasMessage(data);
            break;
            
        case 'html_created':
            handleHtmlCreated(data.path);
            break;
            
        case 'gui_started':
            handleGuiAppStart();
            break;
    }
}
