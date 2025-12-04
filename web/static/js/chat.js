/**
 * AtomAgent - Chat Functions
 */

import { state, getElements } from './state.js';
import { escapeHtml, renderMarkdown, highlightCode, scrollToBottom } from './utils.js';

let currentAIMessage = null;
let currentAIContent = '';

export function sendMessage() {
    const elements = getElements();
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
    scrollToBottom(elements.messages);
}

export function addUserMessage(content) {
    const elements = getElements();
    const div = document.createElement('div');
    div.className = 'message user';
    div.innerHTML = escapeHtml(content).replace(/\n/g, '<br>');
    elements.messages.appendChild(div);
    scrollToBottom(elements.messages);
}

export function addAIMessage(content) {
    const elements = getElements();
    const div = document.createElement('div');
    div.className = 'message ai';
    div.innerHTML = renderMarkdown(content);
    elements.messages.appendChild(div);
    highlightCode();
    scrollToBottom(elements.messages);
}

export function createAIMessageElement() {
    const elements = getElements();
    currentAIContent = '';
    state.hasReceivedContent = false;
    currentAIMessage = document.createElement('div');
    currentAIMessage.className = 'message ai pending';
    currentAIMessage.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    elements.messages.appendChild(currentAIMessage);
    scrollToBottom(elements.messages);
}

export function appendToken(token) {
    if (!currentAIMessage) return;
    
    const elements = getElements();
    
    // Mark that we received actual content
    if (!state.hasReceivedContent && token.trim()) {
        state.hasReceivedContent = true;
        currentAIMessage.classList.remove('pending');
    }
    
    currentAIContent += token;
    currentAIMessage.innerHTML = renderMarkdown(currentAIContent);
    scrollToBottom(elements.messages);
}

export function finalizeAIMessage() {
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

export function addToolActivity(toolName, content, type) {
    const elements = getElements();
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
    
    scrollToBottom(elements.messages);
}

export function showError(message) {
    const elements = getElements();
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = '❌ Hata: ' + message;
    elements.messages.appendChild(div);
    scrollToBottom(elements.messages);
}

export function showSystemMessage(message) {
    const elements = getElements();
    const div = document.createElement('div');
    div.className = 'message system';
    div.textContent = message;
    elements.messages.appendChild(div);
    scrollToBottom(elements.messages);
}

export function stopGeneration() {
    if (state.ws && state.isStreaming) {
        state.ws.send(JSON.stringify({ type: 'stop' }));
    }
}

export function autoResizeTextarea() {
    const elements = getElements();
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 150) + 'px';
}

export function handleInputKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}
