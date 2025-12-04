/**
 * AtomAgent - WebSocket Handler
 */

import { state, getElements } from './state.js';
import { updateStatus, updateStreamingUI } from './ui.js';
import { createAIMessageElement, appendToken, finalizeAIMessage, addToolActivity, showError, showSystemMessage } from './chat.js';
import { loadSessions } from './sessions.js';
import { updateAgentStatus, startThinkingBlock, appendThinkingToken, endThinkingBlock } from './thinking.js';
import { addDockerCommand, addDockerOutput } from './docker.js';

export function connectWebSocket() {
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
