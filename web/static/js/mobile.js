/**
 * Mobile UI Manager - AtomAgent
 * Hamburger menu design with full functionality
 */

class MobileUI {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.leftPanelOpen = false;
        this.rightPanelOpen = false;
        this.initialized = false;
        
        if (this.isMobile) {
            // Wait for DOM and app to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.init());
            } else {
                setTimeout(() => this.init(), 100);
            }
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
        
        // Initial data load
        setTimeout(() => {
            this.updateSessionsList();
            this.updateAgentSelector();
        }, 500);
        
        this.initialized = true;
    }
    
    cleanup() {
        console.log('[Mobile] Cleaning up mobile UI');
        document.querySelectorAll('.mobile-header, .mobile-panel, .mobile-panel-backdrop').forEach(el => el.remove());
        this.initialized = false;
    }
    
    createMobileHeader() {
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
            
            <button class="mobile-header-btn" id="mobile-right-menu-btn" title="Panel">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M9 3v18"/>
                </svg>
            </button>
        `;
        
        const chatArea = document.getElementById('chat-area');
        if (chatArea) {
            chatArea.insertBefore(header, chatArea.firstChild);
        }
    }
    
    createPanels() {
        this.createLeftPanel();
        this.createRightPanel();
        this.createAgentDropdown();
    }
    
    createLeftPanel() {
        document.getElementById('mobile-sessions-panel')?.remove();
        
        const panel = document.createElement('div');
        panel.id = 'mobile-sessions-panel';
        panel.className = 'mobile-panel left';
        panel.innerHTML = `
            <div class="mobile-panel-header">
                <h3>💬 Sohbetler</h3>
                <button class="mobile-panel-close" id="close-left-panel">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="mobile-panel-content">
                <button class="mobile-new-chat-btn" id="mobile-new-chat-btn">
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
                <button class="mobile-panel-close" id="close-right-panel">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="mobile-panel-tabs">
                <button class="mobile-panel-tab active" data-tab="tools">🔧 Araçlar</button>
                <button class="mobile-panel-tab" data-tab="browser">🌐 Browser</button>
                <button class="mobile-panel-tab" data-tab="docker">🐳 Docker</button>
                <button class="mobile-panel-tab" data-tab="files">📁 Dosyalar</button>
                <button class="mobile-panel-tab" data-tab="settings">⚙️</button>
            </div>
            <div class="mobile-panel-content">
                <!-- Tools Tab -->
                <div id="mobile-tab-tools" class="mobile-panel-tab-content active">
                    <div id="mobile-tools-list" class="mobile-tools-list"></div>
                </div>
                
                <!-- Browser Tab -->
                <div id="mobile-tab-browser" class="mobile-panel-tab-content">
                    <div id="mobile-browser-content"></div>
                </div>
                
                <!-- Docker Tab -->
                <div id="mobile-tab-docker" class="mobile-panel-tab-content">
                    <div class="mobile-docker-status" id="mobile-docker-status">
                        <span class="docker-indicator">●</span>
                        <span>Docker durumu</span>
                    </div>
                    <div id="mobile-docker-output" class="mobile-docker-output"></div>
                </div>
                
                <!-- Files Tab -->
                <div id="mobile-tab-files" class="mobile-panel-tab-content">
                    <div class="mobile-file-tabs">
                        <button class="mobile-file-tab active" data-source="workspace">📁 Workspace</button>
                        <button class="mobile-file-tab" data-source="docker">🐳 Docker</button>
                    </div>
                    <div id="mobile-file-tree" class="mobile-file-tree"></div>
                </div>
                
                <!-- Settings Tab -->
                <div id="mobile-tab-settings" class="mobile-panel-tab-content">
                    <div class="mobile-settings-section">
                        <h4>Agent Ayarları</h4>
                        <div class="mobile-setting-item" id="mobile-auto-routing-setting">
                            <span class="mobile-setting-label">Otomatik Routing</span>
                            <label class="mobile-toggle">
                                <input type="checkbox" id="mobile-auto-routing" checked>
                                <span class="mobile-toggle-slider"></span>
                            </label>
                        </div>
                    </div>
                    <div class="mobile-settings-section">
                        <h4>Genel</h4>
                        <button class="mobile-settings-btn" id="mobile-open-settings">
                            ⚙️ Tüm Ayarları Aç
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
    }
    
    createAgentDropdown() {
        document.getElementById('mobile-agent-dropdown')?.remove();
        
        const dropdown = document.createElement('div');
        dropdown.id = 'mobile-agent-dropdown';
        dropdown.className = 'mobile-agent-dropdown hidden';
        
        const agents = [
            { id: 'supervisor', name: 'Supervisor', icon: '🎯', desc: 'Genel koordinasyon' },
            { id: 'coder', name: 'Coder', icon: '👨‍💻', desc: 'Kod yazma ve düzenleme' },
            { id: 'researcher', name: 'Researcher', icon: '🔍', desc: 'Araştırma ve analiz' },
            { id: 'devops', name: 'DevOps', icon: '🚀', desc: 'Deployment ve altyapı' },
            { id: 'qa', name: 'QA', icon: '🧪', desc: 'Test ve kalite' },
            { id: 'security', name: 'Security', icon: '🔒', desc: 'Güvenlik analizi' },
            { id: 'uiux', name: 'UI/UX', icon: '🎨', desc: 'Tasarım ve kullanıcı deneyimi' },
            { id: 'data', name: 'Data', icon: '📊', desc: 'Veri analizi' },
            { id: 'api', name: 'API', icon: '🔌', desc: 'API geliştirme' }
        ];
        
        dropdown.innerHTML = agents.map(agent => `
            <div class="mobile-agent-option" data-agent="${agent.id}">
                <span class="agent-option-icon">${agent.icon}</span>
                <div class="agent-option-info">
                    <span class="agent-option-name">${agent.name}</span>
                    <span class="agent-option-desc">${agent.desc}</span>
                </div>
            </div>
        `).join('');
        
        document.body.appendChild(dropdown);
    }
    
    createBackdrop() {
        document.querySelector('.mobile-panel-backdrop')?.remove();
        
        const backdrop = document.createElement('div');
        backdrop.className = 'mobile-panel-backdrop';
        backdrop.id = 'mobile-backdrop';
        document.body.appendChild(backdrop);
    }
    
    setupEventListeners() {
        // Left menu button
        document.getElementById('mobile-left-menu-btn')?.addEventListener('click', () => this.openLeftPanel());
        
        // Right menu button
        document.getElementById('mobile-right-menu-btn')?.addEventListener('click', () => this.openRightPanel());
        
        // Close buttons
        document.getElementById('close-left-panel')?.addEventListener('click', () => this.closeLeftPanel());
        document.getElementById('close-right-panel')?.addEventListener('click', () => this.closeRightPanel());
        
        // Backdrop
        document.getElementById('mobile-backdrop')?.addEventListener('click', () => this.closeAllPanels());
        
        // New chat button
        document.getElementById('mobile-new-chat-btn')?.addEventListener('click', () => this.newChat());
        
        // Agent selector
        document.getElementById('mobile-agent-selector')?.addEventListener('click', () => this.toggleAgentDropdown());
        
        // Agent options
        document.querySelectorAll('.mobile-agent-option').forEach(option => {
            option.addEventListener('click', () => this.selectAgent(option.dataset.agent));
        });
        
        // Panel tabs
        document.querySelectorAll('.mobile-panel-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        
        // File tabs
        document.querySelectorAll('.mobile-file-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchFileSource(tab.dataset.source));
        });
        
        // Open full settings
        document.getElementById('mobile-open-settings')?.addEventListener('click', () => {
            document.getElementById('settings-modal')?.classList.remove('hidden');
            this.closeRightPanel();
        });
        
        // Swipe gestures
        this.setupSwipeGestures();
        
        // Listen for tool updates from main app
        this.setupToolsObserver();
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
            
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 60) {
                if (deltaX > 0 && touchStartX < 40 && !this.leftPanelOpen && !this.rightPanelOpen) {
                    this.openLeftPanel();
                } else if (deltaX < 0 && touchStartX > window.innerWidth - 40 && !this.leftPanelOpen && !this.rightPanelOpen) {
                    this.openRightPanel();
                } else if (deltaX < 0 && this.leftPanelOpen) {
                    this.closeLeftPanel();
                } else if (deltaX > 0 && this.rightPanelOpen) {
                    this.closeRightPanel();
                }
            }
        }, { passive: true });
    }
    
    setupToolsObserver() {
        // Watch for changes in desktop tools list
        const toolsList = document.getElementById('tools-list');
        if (toolsList) {
            const observer = new MutationObserver(() => this.syncToolsList());
            observer.observe(toolsList, { childList: true, subtree: true });
        }
        
        // Watch for docker output
        const dockerOutput = document.getElementById('docker-output');
        if (dockerOutput) {
            const observer = new MutationObserver(() => this.syncDockerOutput());
            observer.observe(dockerOutput, { childList: true, subtree: true });
        }
        
        // Watch for browser content
        const browserContent = document.getElementById('browser-content');
        if (browserContent) {
            const observer = new MutationObserver(() => this.syncBrowserContent());
            observer.observe(browserContent, { childList: true, subtree: true });
        }
    }
    
    // Panel controls
    openLeftPanel() {
        this.closeRightPanel();
        this.updateSessionsList();
        
        document.getElementById('mobile-sessions-panel')?.classList.add('open');
        document.getElementById('mobile-backdrop')?.classList.add('visible');
        this.leftPanelOpen = true;
    }
    
    closeLeftPanel() {
        document.getElementById('mobile-sessions-panel')?.classList.remove('open');
        if (!this.rightPanelOpen) {
            document.getElementById('mobile-backdrop')?.classList.remove('visible');
        }
        this.leftPanelOpen = false;
    }
    
    openRightPanel() {
        this.closeLeftPanel();
        this.syncToolsList();
        this.syncDockerOutput();
        this.syncBrowserContent();
        this.syncFileTree();
        
        document.getElementById('mobile-tools-panel')?.classList.add('open');
        document.getElementById('mobile-backdrop')?.classList.add('visible');
        this.rightPanelOpen = true;
    }
    
    closeRightPanel() {
        document.getElementById('mobile-tools-panel')?.classList.remove('open');
        if (!this.leftPanelOpen) {
            document.getElementById('mobile-backdrop')?.classList.remove('visible');
        }
        this.rightPanelOpen = false;
    }
    
    closeAllPanels() {
        this.closeLeftPanel();
        this.closeRightPanel();
        this.closeAgentDropdown();
    }
    
    // Agent dropdown
    toggleAgentDropdown() {
        const dropdown = document.getElementById('mobile-agent-dropdown');
        const selector = document.getElementById('mobile-agent-selector');
        
        if (dropdown?.classList.contains('hidden')) {
            dropdown.classList.remove('hidden');
            selector?.classList.add('open');
            document.getElementById('mobile-backdrop')?.classList.add('visible');
        } else {
            this.closeAgentDropdown();
        }
    }
    
    closeAgentDropdown() {
        document.getElementById('mobile-agent-dropdown')?.classList.add('hidden');
        document.getElementById('mobile-agent-selector')?.classList.remove('open');
        if (!this.leftPanelOpen && !this.rightPanelOpen) {
            document.getElementById('mobile-backdrop')?.classList.remove('visible');
        }
    }
    
    selectAgent(agentId) {
        const agents = {
            'supervisor': { name: 'Supervisor', icon: '🎯' },
            'coder': { name: 'Coder', icon: '👨‍💻' },
            'researcher': { name: 'Researcher', icon: '🔍' },
            'devops': { name: 'DevOps', icon: '🚀' },
            'qa': { name: 'QA', icon: '🧪' },
            'security': { name: 'Security', icon: '🔒' },
            'uiux': { name: 'UI/UX', icon: '🎨' },
            'data': { name: 'Data', icon: '📊' },
            'api': { name: 'API', icon: '🔌' }
        };
        
        const agent = agents[agentId];
        if (agent) {
            // Update mobile selector
            const selector = document.getElementById('mobile-agent-selector');
            if (selector) {
                selector.querySelector('.agent-icon').textContent = agent.icon;
                selector.querySelector('.agent-name').textContent = agent.name;
            }
            
            // Update main app state
            if (window.AtomAgent?.setAgent) {
                window.AtomAgent.setAgent(agentId, agent.name);
            }
            
            // Update desktop indicator too
            const desktopIndicator = document.getElementById('active-agent-indicator');
            if (desktopIndicator) {
                desktopIndicator.querySelector('.agent-icon').textContent = agent.icon;
                desktopIndicator.querySelector('.agent-name').textContent = agent.name;
            }
        }
        
        this.closeAgentDropdown();
    }
    
    updateAgentSelector() {
        // Sync with desktop agent indicator
        const desktopIndicator = document.getElementById('active-agent-indicator');
        if (desktopIndicator) {
            const icon = desktopIndicator.querySelector('.agent-icon')?.textContent || '🎯';
            const name = desktopIndicator.querySelector('.agent-name')?.textContent || 'Supervisor';
            
            const selector = document.getElementById('mobile-agent-selector');
            if (selector) {
                selector.querySelector('.agent-icon').textContent = icon;
                selector.querySelector('.agent-name').textContent = name;
            }
        }
    }
    
    // Tab switching
    switchTab(tabName) {
        document.querySelectorAll('.mobile-panel-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        
        document.querySelectorAll('.mobile-panel-tab-content').forEach(content => {
            content.classList.toggle('active', content.id === `mobile-tab-${tabName}`);
        });
    }
    
    switchFileSource(source) {
        document.querySelectorAll('.mobile-file-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.source === source);
        });
        this.syncFileTree(source);
    }
    
    // Data sync functions
    updateSessionsList() {
        const container = document.getElementById('mobile-sessions-list');
        if (!container) return;
        
        const sessions = window.AtomAgent?.sessions || [];
        const currentId = window.AtomAgent?.currentSessionId;
        
        if (sessions.length === 0) {
            container.innerHTML = '<p class="mobile-empty-text">Henüz sohbet yok</p>';
            return;
        }
        
        container.innerHTML = sessions.map(session => `
            <div class="mobile-session-item ${session.id === currentId ? 'active' : ''}" data-session-id="${session.id}">
                <span class="mobile-session-icon">💬</span>
                <div class="mobile-session-info">
                    <div class="mobile-session-title">${this.escapeHtml(session.title || 'Yeni Sohbet')}</div>
                    <div class="mobile-session-meta">${session.message_count || 0} mesaj</div>
                </div>
                <button class="mobile-session-delete" data-delete-id="${session.id}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                    </svg>
                </button>
            </div>
        `).join('');
        
        // Add click handlers
        container.querySelectorAll('.mobile-session-item').forEach(item => {
            item.addEventListener('click', (e) => {
                if (!e.target.closest('.mobile-session-delete')) {
                    this.loadSession(item.dataset.sessionId);
                }
            });
        });
        
        container.querySelectorAll('.mobile-session-delete').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(btn.dataset.deleteId);
            });
        });
    }
    
    syncToolsList() {
        const mobileList = document.getElementById('mobile-tools-list');
        const desktopList = document.getElementById('tools-list');
        
        if (!mobileList) return;
        
        if (desktopList && !desktopList.querySelector('.tools-empty')) {
            mobileList.innerHTML = desktopList.innerHTML;
        } else {
            mobileList.innerHTML = `
                <div class="mobile-tools-empty">
                    <div class="mobile-tools-empty-icon">🔧</div>
                    <p>Henüz araç kullanılmadı</p>
                    <p class="mobile-tools-hint">Agent çalışırken araçlar burada görünecek</p>
                </div>
            `;
        }
    }
    
    syncDockerOutput() {
        const mobileOutput = document.getElementById('mobile-docker-output');
        const desktopOutput = document.getElementById('docker-output');
        const mobileStatus = document.getElementById('mobile-docker-status');
        const desktopStatus = document.getElementById('docker-status');
        
        if (mobileOutput && desktopOutput) {
            mobileOutput.innerHTML = desktopOutput.innerHTML;
        }
        
        if (mobileStatus && desktopStatus) {
            mobileStatus.innerHTML = desktopStatus.innerHTML;
        }
    }
    
    syncBrowserContent() {
        const mobileContent = document.getElementById('mobile-browser-content');
        const desktopContent = document.getElementById('browser-content');
        
        if (mobileContent && desktopContent) {
            mobileContent.innerHTML = desktopContent.innerHTML;
        }
    }
    
    syncFileTree(source = 'workspace') {
        const mobileTree = document.getElementById('mobile-file-tree');
        const desktopTree = document.getElementById('file-tree');
        
        if (mobileTree && desktopTree) {
            mobileTree.innerHTML = desktopTree.innerHTML;
        }
    }
    
    // Actions
    newChat() {
        if (window.AtomAgent?.newSession) {
            window.AtomAgent.newSession();
        }
        this.closeLeftPanel();
        this.updateSessionsList();
    }
    
    loadSession(sessionId) {
        if (window.AtomAgent?.loadSession) {
            window.AtomAgent.loadSession(sessionId);
        }
        this.closeLeftPanel();
    }
    
    deleteSession(sessionId) {
        if (confirm('Bu sohbeti silmek istediğinizden emin misiniz?')) {
            if (window.AtomAgent?.deleteSession) {
                window.AtomAgent.deleteSession(sessionId);
            }
            setTimeout(() => this.updateSessionsList(), 300);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    window.mobileUI = new MobileUI();
});

// Also try to init after a delay in case DOMContentLoaded already fired
setTimeout(() => {
    if (!window.mobileUI) {
        window.mobileUI = new MobileUI();
    }
}, 200);
