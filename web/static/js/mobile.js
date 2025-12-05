/**
 * Mobile UI Manager - AtomAgent
 * Minimal hamburger menu design
 */

class MobileUI {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.leftPanelOpen = false;
        this.rightPanelOpen = false;
        this.initialized = false;
        
        if (this.isMobile) {
            this.init();
        }
        
        // Re-check on resize
        window.addEventListener('resize', () => {
            const wasMobile = this.isMobile;
            this.isMobile = window.innerWidth <= 768;
            
            if (this.isMobile && !wasMobile) {
                this.init();
            } else if (!this.isMobile && wasMobile) {
                this.cleanup();
            }
        });
    }
    
    init() {
        if (this.initialized) return;
        console.log('[Mobile] Initializing mobile UI');
        
        this.createMobileHeader();
        this.createPanels();
        this.createBackdrop();
        this.setupEventListeners();
        
        this.initialized = true;
    }
    
    cleanup() {
        console.log('[Mobile] Cleaning up mobile UI');
        document.querySelectorAll('.mobile-header, .mobile-panel, .mobile-panel-backdrop').forEach(el => el.remove());
        this.initialized = false;
    }
    
    createMobileHeader() {
        // Remove existing
        document.querySelector('.mobile-header')?.remove();
        
        const header = document.createElement('div');
        header.className = 'mobile-header';
        header.innerHTML = `
            <button class="mobile-header-btn" id="mobile-left-menu-btn" title="Sohbetler">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 12h18M3 6h18M3 18h18"/>
                </svg>
            </button>
            
            <div class="mobile-agent-selector" id="mobile-agent-selector">
                <span class="agent-icon">🎯</span>
                <span class="agent-name">Supervisor</span>
                <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </div>
            
            <button class="mobile-header-btn" id="mobile-right-menu-btn" title="Araçlar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="1"/>
                    <circle cx="12" cy="5" r="1"/>
                    <circle cx="12" cy="19" r="1"/>
                </svg>
            </button>
        `;
        
        // Insert at the beginning of chat-area
        const chatArea = document.getElementById('chat-area');
        if (chatArea) {
            chatArea.insertBefore(header, chatArea.firstChild);
        }
    }
    
    createPanels() {
        // Left Panel - Sessions
        this.createLeftPanel();
        
        // Right Panel - Tools & Settings
        this.createRightPanel();
    }
    
    createLeftPanel() {
        document.getElementById('mobile-sessions-panel')?.remove();
        
        const panel = document.createElement('div');
        panel.id = 'mobile-sessions-panel';
        panel.className = 'mobile-panel left';
        panel.innerHTML = `
            <div class="mobile-panel-header">
                <h3>💬 Sohbetler</h3>
                <button class="mobile-panel-close" onclick="window.mobileUI.closeLeftPanel()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="mobile-panel-content">
                <button class="mobile-new-chat-btn" onclick="window.mobileUI.newChat()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 5v14M5 12h14"/>
                    </svg>
                    Yeni Sohbet
                </button>
                <div id="mobile-sessions-list"></div>
            </div>
        `;
        
        document.body.appendChild(panel);
    }
    
    createRightPanel() {
        document.getElementById('mobile-tools-panel')?.remove();
        
        const panel = document.createElement('div');
        panel.id = 'mobile-tools-panel';
        panel.className = 'mobile-panel right';
        panel.innerHTML = `
            <div class="mobile-panel-header">
                <h3>⚡ Panel</h3>
                <button class="mobile-panel-close" onclick="window.mobileUI.closeRightPanel()">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="mobile-panel-tabs">
                <button class="mobile-panel-tab active" data-tab="tools" onclick="window.mobileUI.switchTab('tools')">🔧 Araçlar</button>
                <button class="mobile-panel-tab" data-tab="files" onclick="window.mobileUI.switchTab('files')">📁 Dosyalar</button>
                <button class="mobile-panel-tab" data-tab="settings" onclick="window.mobileUI.switchTab('settings')">⚙️ Ayarlar</button>
            </div>
            <div class="mobile-panel-content">
                <div id="mobile-tab-tools" class="mobile-panel-tab-content active">
                    <div class="mobile-tools-empty">
                        <div class="mobile-tools-empty-icon">🔧</div>
                        <p>Henüz araç kullanılmadı</p>
                    </div>
                </div>
                <div id="mobile-tab-files" class="mobile-panel-tab-content">
                    <div class="mobile-tools-empty">
                        <div class="mobile-tools-empty-icon">📁</div>
                        <p>Dosya yönetimi</p>
                    </div>
                </div>
                <div id="mobile-tab-settings" class="mobile-panel-tab-content">
                    ${this.getSettingsContent()}
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
    }
    
    createBackdrop() {
        document.querySelector('.mobile-panel-backdrop')?.remove();
        
        const backdrop = document.createElement('div');
        backdrop.className = 'mobile-panel-backdrop';
        backdrop.addEventListener('click', () => this.closeAllPanels());
        document.body.appendChild(backdrop);
    }
    
    setupEventListeners() {
        // Left menu button
        document.getElementById('mobile-left-menu-btn')?.addEventListener('click', () => {
            this.openLeftPanel();
        });
        
        // Right menu button
        document.getElementById('mobile-right-menu-btn')?.addEventListener('click', () => {
            this.openRightPanel();
        });
        
        // Agent selector
        document.getElementById('mobile-agent-selector')?.addEventListener('click', () => {
            this.toggleAgentDropdown();
        });
        
        // Swipe gestures
        this.setupSwipeGestures();
    }
    
    setupSwipeGestures() {
        let touchStartX = 0;
        let touchStartY = 0;
        
        document.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchend', (e) => {
            const touchEndX = e.changedTouches[0].clientX;
            const touchEndY = e.changedTouches[0].clientY;
            const deltaX = touchEndX - touchStartX;
            const deltaY = touchEndY - touchStartY;
            
            // Only horizontal swipes
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
                if (deltaX > 0 && touchStartX < 30) {
                    // Swipe right from left edge
                    this.openLeftPanel();
                } else if (deltaX < 0 && touchStartX > window.innerWidth - 30) {
                    // Swipe left from right edge
                    this.openRightPanel();
                } else if (deltaX < 0 && this.leftPanelOpen) {
                    // Swipe left to close left panel
                    this.closeLeftPanel();
                } else if (deltaX > 0 && this.rightPanelOpen) {
                    // Swipe right to close right panel
                    this.closeRightPanel();
                }
            }
        }, { passive: true });
    }
    
    openLeftPanel() {
        this.closeRightPanel();
        this.updateSessionsList();
        
        const panel = document.getElementById('mobile-sessions-panel');
        const backdrop = document.querySelector('.mobile-panel-backdrop');
        
        panel?.classList.add('open');
        backdrop?.classList.add('visible');
        this.leftPanelOpen = true;
    }
    
    closeLeftPanel() {
        const panel = document.getElementById('mobile-sessions-panel');
        const backdrop = document.querySelector('.mobile-panel-backdrop');
        
        panel?.classList.remove('open');
        if (!this.rightPanelOpen) {
            backdrop?.classList.remove('visible');
        }
        this.leftPanelOpen = false;
    }
    
    openRightPanel() {
        this.closeLeftPanel();
        this.updateToolsList();
        
        const panel = document.getElementById('mobile-tools-panel');
        const backdrop = document.querySelector('.mobile-panel-backdrop');
        
        panel?.classList.add('open');
        backdrop?.classList.add('visible');
        this.rightPanelOpen = true;
    }
    
    closeRightPanel() {
        const panel = document.getElementById('mobile-tools-panel');
        const backdrop = document.querySelector('.mobile-panel-backdrop');
        
        panel?.classList.remove('open');
        if (!this.leftPanelOpen) {
            backdrop?.classList.remove('visible');
        }
        this.rightPanelOpen = false;
    }
    
    closeAllPanels() {
        this.closeLeftPanel();
        this.closeRightPanel();
    }
    
    toggleAgentDropdown() {
        const selector = document.getElementById('mobile-agent-selector');
        const dropdown = document.getElementById('agent-dropdown');
        
        if (dropdown) {
            dropdown.classList.toggle('hidden');
            selector?.classList.toggle('open');
        }
        
        // Use existing agent dropdown if available
        if (window.AtomAgent?.toggleAgentDropdown) {
            window.AtomAgent.toggleAgentDropdown();
        }
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.mobile-panel-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        // Update tab content
        document.querySelectorAll('.mobile-panel-tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `mobile-tab-${tabName}`);
        });
    }
    
    updateSessionsList() {
        const container = document.getElementById('mobile-sessions-list');
        if (!container) return;
        
        const sessions = window.AtomAgent?.sessions || [];
        const currentId = window.AtomAgent?.currentSessionId;
        
        if (sessions.length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 16px;">Henüz sohbet yok</p>';
            return;
        }
        
        container.innerHTML = sessions.map(session => `
            <div class="mobile-session-item ${session.id === currentId ? 'active' : ''}" 
                 data-session-id="${session.id}"
                 onclick="window.mobileUI.loadSession('${session.id}')">
                <span class="mobile-session-icon">💬</span>
                <div class="mobile-session-info">
                    <div class="mobile-session-title">${this.escapeHtml(session.title || 'Yeni Sohbet')}</div>
                    <div class="mobile-session-meta">${session.message_count || 0} mesaj</div>
                </div>
                <button class="mobile-session-delete" onclick="event.stopPropagation(); window.mobileUI.deleteSession('${session.id}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                </button>
            </div>
        `).join('');
    }
    
    updateToolsList() {
        const container = document.getElementById('mobile-tab-tools');
        if (!container) return;
        
        // Get tools from desktop tools list
        const desktopTools = document.getElementById('tools-list');
        if (desktopTools && !desktopTools.querySelector('.tools-empty')) {
            container.innerHTML = `<div class="mobile-tools-list">${desktopTools.innerHTML}</div>`;
        } else {
            container.innerHTML = `
                <div class="mobile-tools-empty">
                    <div class="mobile-tools-empty-icon">🔧</div>
                    <p>Henüz araç kullanılmadı</p>
                </div>
            `;
        }
    }
    
    getSettingsContent() {
        return `
            <div class="mobile-settings-section">
                <h4>Agent</h4>
                <div class="mobile-setting-item" onclick="window.mobileUI.toggleAgentDropdown()">
                    <span class="mobile-setting-label">Aktif Agent</span>
                    <span class="mobile-setting-value" id="mobile-current-agent">Supervisor</span>
                </div>
            </div>
            <div class="mobile-settings-section">
                <h4>Genel</h4>
                <div class="mobile-setting-item" onclick="document.getElementById('settings-modal')?.classList.remove('hidden'); window.mobileUI.closeRightPanel();">
                    <span class="mobile-setting-label">Tüm Ayarlar</span>
                    <span class="mobile-setting-value">→</span>
                </div>
            </div>
        `;
    }
    
    newChat() {
        if (window.AtomAgent?.newSession) {
            window.AtomAgent.newSession();
        }
        this.closeLeftPanel();
    }
    
    loadSession(sessionId) {
        if (window.AtomAgent?.loadSession) {
            window.AtomAgent.loadSession(sessionId);
        }
        this.closeLeftPanel();
    }
    
    deleteSession(sessionId) {
        if (window.AtomAgent?.deleteSession) {
            window.AtomAgent.deleteSession(sessionId);
        }
    }
    
    updateAgentDisplay(agentName, agentIcon) {
        const selector = document.getElementById('mobile-agent-selector');
        if (selector) {
            selector.querySelector('.agent-icon').textContent = agentIcon || '🎯';
            selector.querySelector('.agent-name').textContent = agentName || 'Supervisor';
        }
        
        const settingValue = document.getElementById('mobile-current-agent');
        if (settingValue) {
            settingValue.textContent = agentName || 'Supervisor';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileUI = new MobileUI();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileUI;
}
