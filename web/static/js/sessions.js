/**
 * AtomAgent - Session Management
 */

import { state, getElements } from './state.js';
import { escapeHtml, formatDate, scrollToBottom } from './utils.js';
import { addUserMessage, addAIMessage } from './chat.js';

export async function loadSessions() {
    try {
        const response = await fetch('/api/sessions?limit=50');
        const data = await response.json();
        state.sessions = data.sessions;
        renderSessions();
    } catch (error) {
        console.error('Failed to load sessions:', error);
    }
}

export function renderSessions() {
    const elements = getElements();
    elements.sessionsList.innerHTML = state.sessions.map(session => `
        <div class="session-item ${session.id === state.currentSessionId ? 'active' : ''}" 
             data-id="${session.id}">
            <div class="session-info" onclick="window.AtomAgent.loadSession('${session.id}')">
                <div class="session-title">${escapeHtml(session.title)}</div>
                <div class="session-meta">${session.message_count} mesaj • ${formatDate(session.updated_at)}</div>
            </div>
            <button class="session-delete" onclick="window.AtomAgent.deleteSession('${session.id}', event)" title="Sil">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
            </button>
        </div>
    `).join('');
}

export async function loadSession(sessionId) {
    const elements = getElements();
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
        scrollToBottom(elements.messages);
    } catch (error) {
        console.error('Failed to load session:', error);
    }
}

// Pending delete session
let pendingDeleteSessionId = null;

export function deleteSession(sessionId, event) {
    event.stopPropagation();
    pendingDeleteSessionId = sessionId;
    showDeleteConfirmModal();
}

export async function confirmDeleteSession() {
    if (!pendingDeleteSessionId) return;
    
    const sessionId = pendingDeleteSessionId;
    const elements = getElements();
    
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
    
    hideDeleteConfirmModal();
    pendingDeleteSessionId = null;
}

export function cancelDeleteSession() {
    hideDeleteConfirmModal();
    pendingDeleteSessionId = null;
}

function showDeleteConfirmModal() {
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
        modal.classList.remove('hidden');
    }
}

function hideDeleteConfirmModal() {
    const modal = document.getElementById('delete-confirm-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

export function newChat() {
    const elements = getElements();
    state.currentSessionId = null;
    elements.messages.innerHTML = getWelcomeMessage();
    elements.messageInput.focus();
    renderSessions();
}

export function getWelcomeMessage() {
    return `
        <div class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <h2>AtomAgent'a Hoş Geldiniz</h2>
            <p>AI destekli geliştirme asistanınız hazır. Bir soru sorun veya görev verin.</p>
        </div>
    `;
}
