/**
 * AtomAgent - UI Helper Functions
 */

import { state, getElements } from './state.js';

export function toggleSidebar() {
    const elements = getElements();
    state.sidebarCollapsed = !state.sidebarCollapsed;
    
    if (state.sidebarCollapsed) {
        elements.sidebar.classList.add('hidden');
        elements.sidebarCollapsed.classList.remove('hidden');
    } else {
        elements.sidebar.classList.remove('hidden');
        elements.sidebarCollapsed.classList.add('hidden');
    }
}

export function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`tab-${tabName}`)?.classList.add('active');
}

export function updateStatus(text, connected) {
    const elements = getElements();
    const statusDot = elements.chatStatus.querySelector('.status-dot');
    const statusText = elements.chatStatus.querySelector('span:last-child');
    
    statusText.textContent = text;
    statusDot.style.background = connected ? 'var(--accent-success)' : 'var(--accent-error)';
}

export function updateStreamingUI(streaming) {
    const elements = getElements();
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
        
        if (statusBar) {
            statusBar.classList.add('hidden');
        }
    }
}

export function setupResizeHandle() {
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
    
    // Touch support
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
