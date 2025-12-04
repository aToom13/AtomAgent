/**
 * AtomAgent - Thinking/Status Functions
 * Sadece status bar ve thinking panel - chat'e element eklenmez
 */

import { state } from './state.js';
import { renderMarkdown } from './utils.js';

let thinkingContent = '';
let isThinkingActive = false;

export function updateAgentStatus(status, message, model) {
    const statusBar = document.getElementById('agent-status-bar');
    const statusText = document.getElementById('status-text');
    const statusModel = document.getElementById('status-model');
    
    if (status === 'ready') {
        statusBar?.classList.add('hidden');
        return;
    }
    
    statusBar?.classList.remove('hidden');
    if (statusBar) statusBar.className = 'agent-status-bar ' + status;
    if (statusText) statusText.textContent = message;
    
    if (model && statusModel) {
        statusModel.textContent = model;
        statusModel.style.display = 'block';
    }
}

export function startThinkingBlock(title) {
    // Chat'e element ekleme - sadece status bar ve panel kullan
    thinkingContent = '';
    isThinkingActive = true;
    
    // Status bar'ı güncelle
    const statusText = document.getElementById('status-text');
    if (statusText) {
        statusText.textContent = title || '🧠 Düşünüyor...';
    }
    
    // Thinking panel'i aç ve içeriği temizle
    const panel = document.getElementById('thinking-panel');
    const panelContent = document.getElementById('thinking-panel-content');
    
    if (panel) {
        panel.classList.remove('hidden');
        state.thinkingPanelOpen = true;
    }
    
    if (panelContent) {
        panelContent.innerHTML = `<p class="thinking-active">💭 ${title || 'Düşünüyor...'}</p>`;
    }
}

export function appendThinkingToken(token) {
    if (!isThinkingActive) return;
    
    thinkingContent += token;
    
    // Sadece thinking panel'i güncelle
    const panelContent = document.getElementById('thinking-panel-content');
    if (panelContent) {
        let cleanContent = thinkingContent
            .replace(/<think>/g, '')
            .replace(/<\/think>/g, '')
            .replace(/\*\*Düşünce:\*\*/g, '')
            .replace(/\*\*Thinking:\*\*/g, '');
        
        panelContent.innerHTML = renderMarkdown(cleanContent);
    }
}

export function endThinkingBlock() {
    isThinkingActive = false;
    
    // Thinking panel'i kapat (2 saniye sonra)
    setTimeout(() => {
        const panel = document.getElementById('thinking-panel');
        if (panel && state.thinkingPanelOpen) {
            panel.classList.add('hidden');
            state.thinkingPanelOpen = false;
        }
    }, 1500);
    
    thinkingContent = '';
}

export function toggleThinking(header) {
    // Artık kullanılmıyor - eski chat block'ları için
}

// Thinking Panel toggle
export function toggleThinkingPanel() {
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

export function updateThinkingPanel(content) {
    const panelContent = document.getElementById('thinking-panel-content');
    if (!panelContent) return;
    
    if (content) {
        panelContent.innerHTML = renderMarkdown(content);
    } else {
        panelContent.innerHTML = '<p class="thinking-placeholder">Agent düşünmeye başladığında burada göreceksiniz...</p>';
    }
}

export function getThinkingContent() {
    return thinkingContent;
}
