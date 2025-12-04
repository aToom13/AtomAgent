/**
 * AtomAgent - Status Bar Functions
 * Düşünme süreci sadece status bar'da gösteriliyor
 */

import { state } from './state.js';

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

// Eski fonksiyonlar - artık kullanılmıyor ama export ediliyor (uyumluluk için)
export function startThinkingBlock(title) {
    // Artık kullanılmıyor
}

export function appendThinkingToken(token) {
    // Artık kullanılmıyor
}

export function endThinkingBlock() {
    // Artık kullanılmıyor
}

export function toggleThinking(header) {
    // Artık kullanılmıyor
}

export function toggleThinkingPanel() {
    const panel = document.getElementById('thinking-panel');
    if (panel) {
        panel.classList.toggle('hidden');
        state.thinkingPanelOpen = !panel.classList.contains('hidden');
    }
}

export function updateThinkingPanel(content) {
    // Artık kullanılmıyor
}

export function getThinkingContent() {
    return '';
}
