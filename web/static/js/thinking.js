/**
 * AtomAgent - Thinking/Status Functions
 */

import { state, getElements } from './state.js';
import { renderMarkdown, scrollToBottom } from './utils.js';

let currentThinkingBlock = null;
let thinkingContent = '';

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
    const elements = getElements();
    thinkingContent = '';
    
    const block = document.createElement('div');
    block.className = 'thinking-block active';
    block.innerHTML = `
        <div class="thinking-header" onclick="window.AtomAgent.toggleThinking(this)">
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
    scrollToBottom(elements.messages);
    
    // Update thinking panel
    updateThinkingPanel('');
}

export function appendThinkingToken(token) {
    if (!currentThinkingBlock) return;
    
    const elements = getElements();
    thinkingContent += token;
    const contentEl = currentThinkingBlock.querySelector('.thinking-content');
    
    if (contentEl) {
        let cleanContent = thinkingContent
            .replace(/<think>/g, '')
            .replace(/<\/think>/g, '')
            .replace(/\*\*Düşünce:\*\*/g, '')
            .replace(/\*\*Thinking:\*\*/g, '');
        
        contentEl.innerHTML = renderMarkdown(cleanContent);
    }
    
    scrollToBottom(elements.messages);
    updateThinkingPanel(thinkingContent);
}

export function endThinkingBlock() {
    if (currentThinkingBlock) {
        currentThinkingBlock.classList.remove('active');
        currentThinkingBlock.classList.add('collapsed');
        
        const titleEl = currentThinkingBlock.querySelector('.thinking-title');
        if (titleEl && thinkingContent.length > 50) {
            const summary = thinkingContent.substring(0, 50).replace(/<[^>]*>/g, '').trim() + '...';
            titleEl.textContent = summary;
        }
    }
    currentThinkingBlock = null;
    thinkingContent = '';
    
    // Close thinking panel after delay
    setTimeout(() => {
        if (state.thinkingPanelOpen) {
            toggleThinkingPanel();
        }
    }, 2000);
}

export function toggleThinking(header) {
    const block = header.parentElement;
    block.classList.toggle('collapsed');
}

// Thinking Panel
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
