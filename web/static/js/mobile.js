/**
 * Mobile UI Manager - AtomAgent
 * Full functionality with Canvas support
 */

class MobileUI {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.leftPanelOpen = false;
        this.rightPanelOpen = false;
        this.initialized = false;
        
        if (this.isMobile) {
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => setTimeout(() => this.init(), 300));
            } else {
                setTimeout(() => this.init(), 300);
            }
        }
        
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
        this.createAgentDropdown();
        this.setupEventListeners();
        this.setupObservers();
        
        // Initial sync after app loads
        setTimeout(() => {
            this.updateSessionsList();
            this.updateAgentSelector();
            this.syncAllPanels();
        }, 1000);
        
        this.initialized = true;
    }
    
    cleanup() {
        console.log('[Mobile] Cleaning up mobile UI');
        document.querySelectorAll('.mobile-header, .mobile-panel, .mobile-panel-backdrop, .mobile-agent-dropdown').forEach(el => el.remove());
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
    }
    
    createLeftPanel() {
        document.getElementById('mobile-sessions-panel')?.remove();
        
        const panel = document.createElement('div');
        panel.id = 'mobile-sessions-panel';
        panel.className = 'mobile-panel left';
        panel.innerHTML = `
            <div class="mobile-panel-header">
                <h3>💬 Sohbetler</h3>
                <button class="mobile-panel-close" id="close-left-panel">✕</button>
            </div>
            <div class="mobile-panel-content">
                <button class="mobile-new-chat-btn" id="mobile-new-chat-btn">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M12 5v14M5 12h14"/>
                    </svg>
                    Yeni Sohbet
                </button>
                <div id="mobile-sessions-list" class="mobile-sessions-list"></div>
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
                <button class="mobile-panel-close" id="close-right-panel">✕</button>
            </div>
            <div class="mobile-panel-tabs">
                <button class="mobile-panel-tab active" data-tab="tools">🔧</button>
                <button class="mobile-panel-tab" data-tab="browser">🌐</button>
                <button class="mobile-panel-tab" data-tab="canvas">🖥️</button>
                <button class="mobile-panel-tab" data-tab="docker">🐳</button>
                <button class="mobile-panel-tab" data-tab="files">📁</button>
                <button class="mobile-panel-tab" data-tab="settings">⚙️</button>
            </div>
            <div class="mobile-panel-body">
                <!-- Tools Tab -->
                <div id="mobile-tab-tools" class="mobile-panel-tab-content active">
                    <div id="mobile-tools-list"></div>
                </div>
                
                <!-- Browser Tab -->
                <div id="mobile-tab-browser" class="mobile-panel-tab-content">
                    <div id="mobile-browser-content"></div>
                </div>
                
                <!-- Canvas Tab -->
                <div id="mobile-tab-canvas" class="mobile-panel-tab-content">
                    <div class="mobile-canvas-controls">
                        <div class="mobile-canvas-url-bar">
                            <input type="text" id="mobile-canvas-url" placeholder="localhost:8000" value="localhost:8000">
                            <button id="mobile-canvas-go" class="mobile-small-btn">→</button>
                        </div>
                        <div class="mobile-canvas-actions">
                            <button id="mobile-canvas-refresh" class="mobile-small-btn">↻</button>
                            <button id="mobile-canvas-open" class="mobile-small-btn">↗</button>
                        </div>
                    </div>
                    <div class="mobile-canvas-status" id="mobile-canvas-status">
                        <span>○</span> Bağlantı bekleniyor
                    </div>
                    <div class="mobile-canvas-frame">
                        <iframe id="mobile-canvas-iframe" src="about:blank"></iframe>
                    </div>
                </div>
                
                <!-- Docker Tab -->
                <div id="mobile-tab-docker" class="mobile-panel-tab-content">
                    <div id="mobile-docker-status" class="mobile-docker-status"></div>
                    <div id="mobile-docker-output" class="mobile-docker-output"></div>
                </div>
                
                <!-- Files Tab -->
                <div id="mobile-tab-files" class="mobile-panel-tab-content">
                    <div id="mobile-file-tree"></div>
                </div>
                
                <!-- Settings Tab -->
                <div id="mobile-tab-settings" class="mobile-panel-tab-content">
                    <div class="mobile-settings-section">
                        <h4>Genel</h4>
                        <button class="mobile-settings-btn" id="mobile-open-full-settings">
                            ⚙️ Tüm Ayarları Aç
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(panel);
    }
    
    createBackdrop() {
        document.querySelector('.mobile-panel-backdrop')?.remove();
        
        const backdrop = document.createElement('div');
        backdrop.className = 'mobile-panel-backdrop';
        backdrop.id = 'mobile-backdrop';
        document.body.appendChild(backdrop);
    }
    
    createAgentDropdown() {
        document.getElementById('mobile-agent-dropdown')?.remove();
        
        const agents = [
            { id: 'supervisor', name: 'Supervisor', icon: '🎯', desc: 'Genel koordinasyon' },
            { id: 'coder', name: 'Coder', icon: '👨‍💻', desc: 'Kod yazma' },
            { id: 'researcher', name: 'Researcher', icon: '🔍', desc: 'Araştırma' },
            { id: 'devops', name: 'DevOps', icon: '🚀', desc: 'Deployment' },
            { id: 'qa', name: 'QA', icon: '🧪', desc: 'Test' },
            { id: 'security', name: 'Security', icon: '🔒', desc: 'Güvenlik' },
            { id: 'uiux', name: 'UI/UX', icon: '🎨', desc: 'Tasarım' },
            { id: 'data', name: 'Data', icon: '📊', desc: 'Veri analizi' },
            { id: 'api', name: 'API', icon: '🔌', desc: 'API geliştirme' }
        ];
        
        const dropdown = document.createElement('div');
        dropdown.id = 'mobile-agent-dropdown';
        dropdown.className = 'mobile-agent-dropdown hidden';
        dropdown.innerHTML = agents.map(a => `
            <div class="mobile-agent-option" data-agent="${a.id}">
                <span class="agent-option-icon">${a.icon}</span>
                <div class="agent-option-info">
                    <span class="agent-option-name">${a.name}</span>
                    <span class="agent-option-desc">${a.desc}</span>
                </div>
            </div>
        `).join('');
        
        document.body.appendChild(dropdown);
    }
    
    setupEventListeners() {
        // Menu buttons
        document.getElementById('mobile-left-menu-btn')?.addEventListener('click', () => this.openLeftPanel());
        document.getElementById('mobile-right-menu-btn')?.addEventListener('click', () => this.openRightPanel());
        
        // Close buttons
        document.getElementById('close-left-panel')?.addEventListener('click', () => this.closeLeftPanel());
        document.getElementById('close-right-panel')?.addEventListener('click', () => this.closeRightPanel());
        
        // Backdrop
        document.getElementById('mobile-backdrop')?.addEventListener('click', () => this.closeAllPanels());
        
        // New chat
        document.getElementById('mobile-new-chat-btn')?.addEventListener('click', () => this.newChat());
        
        // Agent selector
        document.getElementById('mobile-agent-selector')?.addEventListener('click', () => this.toggleAgentDropdown());
        
        // Agent options
        document.querySelectorAll('.mobile-agent-option').forEach(opt => {
            opt.addEventListener('click', () => this.selectAgent(opt.dataset.agent));
        });
        
        // Panel tabs
        document.querySelectorAll('.mobile-panel-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        
        // Full settings
        document.getElementById('mobile-open-full-settings')?.addEventListener('click', () => {
            document.getElementById('settings-modal')?.classList.remove('hidden');
            this.closeRightPanel();
        });
        
        // Canvas controls
        document.getElementById('mobile-canvas-go')?.addEventListener('click', () => this.loadCanvasUrl());
        document.getElementById('mobile-canvas-refresh')?.addEventListener('click', () => this.refreshCanvas());
        document.getElementById('mobile-canvas-open')?.addEventListener('click', () => this.openCanvasExternal());
        
        // Swipe gestures
        this.setupSwipeGestures();
    }
    
    setupObservers() {
        // Watch tools list
        const toolsList = document.getElementById('tools-list');
        if (toolsList) {
            new MutationObserver(() => this.syncToolsList()).observe(toolsList, { childList: true, subtree: true, characterData: true });
        }
        
        // Watch browser content
        const browserContent = document.getElementById('browser-content');
        if (browserContent) {
            new MutationObserver(() => this.syncBrowserContent()).observe(browserContent, { childList: true, subtree: true });
        }
        
        // Watch docker output
        const dockerOutput = document.getElementById('docker-output');
        if (dockerOutput) {
            new MutationObserver(() => this.syncDockerOutput()).observe(dockerOutput, { childList: true, subtree: true });
        }
        
        // Watch file tree
        const fileTree = document.getElementById('file-tree');
        if (fileTree) {
            new MutationObserver(() => this.syncFileTree()).observe(fileTree, { childList: true, subtree: true });
        }
        
        // Watch canvas status
        const canvasStatus = document.getElementById('canvas-status');
        if (canvasStatus) {
            new MutationObserver(() => this.syncCanvasStatus()).observe(canvasStatus, { childList: true, subtree: true, characterData: true });
        }
        
        // Watch sessions list for changes
        const sessionsList = document.getElementById('sessions-list');
        if (sessionsList) {
            new MutationObserver(() => this.updateSessionsList()).observe(sessionsList, { childList: true, subtree: true });
        }
    }
    
    setupSwipeGestures() {
        let startX = 0, startY = 0;
        
        document.addEventListener('touchstart', e => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        }, { passive: true });
        
        document.addEventListener('touchend', e => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            const dx = endX - startX;
            const dy = endY - startY;
            
            if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 60) {
                if (dx > 0 && startX < 40 && !this.leftPanelOpen && !this.rightPanelOpen) {
                    this.openLeftPanel();
                } else if (dx < 0 && startX > window.innerWidth - 40 && !this.leftPanelOpen && !this.rightPanelOpen) {
                    this.openRightPanel();
                } else if (dx < 0 && this.leftPanelOpen) {
                    this.closeLeftPanel();
                } else if (dx > 0 && this.rightPanelOpen) {
                    this.closeRightPanel();
                }
            }
        }, { passive: true });
    }
    
    // Panel controls
    openLeftPanel() {
        this.closeRightPanel();
        this.closeAgentDropdown();
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
        this.closeAgentDropdown();
        this.syncAllPanels();
        
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
            
            // Call main app function
            if (window.AtomAgent?.setActiveAgent) {
                window.AtomAgent.setActiveAgent(agentId, agent.name);
            }
        }
        
        this.closeAgentDropdown();
    }
    
    updateAgentSelector() {
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
        
        // Sync content when switching
        if (tabName === 'tools') this.syncToolsList();
        if (tabName === 'browser') this.syncBrowserContent();
        if (tabName === 'docker') this.syncDockerOutput();
        if (tabName === 'files') this.syncFileTree();
        if (tabName === 'canvas') this.syncCanvasStatus();
    }
    
    // Sync functions
    syncAllPanels() {
        this.syncToolsList();
        this.syncBrowserContent();
        this.syncDockerOutput();
        this.syncFileTree();
        this.syncCanvasStatus();
    }
    
    syncToolsList() {
        const mobile = document.getElementById('mobile-tools-list');
        const desktop = document.getElementById('tools-list');
        
        if (mobile && desktop) {
            mobile.innerHTML = desktop.innerHTML;
        }
    }
    
    syncBrowserContent() {
        const mobile = document.getElementById('mobile-browser-content');
        const desktop = document.getElementById('browser-content');
        
        if (mobile && desktop) {
            mobile.innerHTML = desktop.innerHTML;
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
    
    syncFileTree() {
        const mobile = document.getElementById('mobile-file-tree');
        const desktop = document.getElementById('file-tree');
        
        if (mobile && desktop) {
            mobile.innerHTML = desktop.innerHTML;
        }
    }
    
    syncCanvasStatus() {
        const mobileStatus = document.getElementById('mobile-canvas-status');
        const desktopStatus = document.getElementById('canvas-status');
        
        if (mobileStatus && desktopStatus) {
            mobileStatus.innerHTML = desktopStatus.innerHTML;
        }
        
        // Sync iframe src
        const mobileIframe = document.getElementById('mobile-canvas-iframe');
        const desktopIframe = document.getElementById('canvas-iframe');
        
        if (mobileIframe && desktopIframe && desktopIframe.src !== 'about:blank') {
            if (mobileIframe.src !== desktopIframe.src) {
                mobileIframe.src = desktopIframe.src;
            }
        }
    }
    
    // Sessions
    updateSessionsList() {
        const container = document.getElementById('mobile-sessions-list');
        if (!container) return;
        
        // Try to get sessions from desktop list
        const desktopList = document.getElementById('sessions-list');
        if (desktopList && desktopList.children.length > 0) {
            // Clone desktop sessions
            container.innerHTML = '';
            Array.from(desktopList.children).forEach(item => {
                const sessionId = item.dataset.id;
                const title = item.querySelector('.session-title')?.textContent || 'Yeni Sohbet';
                const meta = item.querySelector('.session-meta')?.textContent || '';
                const isActive = item.classList.contains('active');
                
                const mobileItem = document.createElement('div');
                mobileItem.className = `mobile-session-item ${isActive ? 'active' : ''}`;
                mobileItem.dataset.sessionId = sessionId;
                mobileItem.innerHTML = `
                    <span class="mobile-session-icon">💬</span>
                    <div class="mobile-session-info">
                        <div class="mobile-session-title">${this.escapeHtml(title)}</div>
                        <div class="mobile-session-meta">${this.escapeHtml(meta)}</div>
                    </div>
                    <button class="mobile-session-delete" data-id="${sessionId}">🗑️</button>
                `;
                
                // Click to load
                mobileItem.querySelector('.mobile-session-info').addEventListener('click', () => {
                    this.loadSession(sessionId);
                });
                
                // Delete button
                mobileItem.querySelector('.mobile-session-delete').addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.deleteSession(sessionId);
                });
                
                container.appendChild(mobileItem);
            });
        } else {
            container.innerHTML = '<p class="mobile-empty-text">Henüz sohbet yok</p>';
        }
    }
    
    // Actions
    newChat() {
        if (window.AtomAgent?.newChat) {
            window.AtomAgent.newChat();
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
            window.AtomAgent.deleteSession(sessionId, { stopPropagation: () => {} });
        }
    }
    
    // Canvas
    loadCanvasUrl() {
        const input = document.getElementById('mobile-canvas-url');
        const iframe = document.getElementById('mobile-canvas-iframe');
        
        if (input && iframe) {
            let url = input.value.trim();
            if (!url.startsWith('http')) {
                url = 'http://' + url;
            }
            iframe.src = url;
            
            // Also update desktop
            const desktopInput = document.getElementById('canvas-url');
            const desktopIframe = document.getElementById('canvas-iframe');
            if (desktopInput) desktopInput.value = input.value;
            if (desktopIframe) desktopIframe.src = url;
        }
    }
    
    refreshCanvas() {
        const iframe = document.getElementById('mobile-canvas-iframe');
        if (iframe && iframe.src !== 'about:blank') {
            iframe.src = iframe.src;
        }
    }
    
    openCanvasExternal() {
        const iframe = document.getElementById('mobile-canvas-iframe');
        if (iframe && iframe.src !== 'about:blank') {
            window.open(iframe.src, '_blank');
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
}

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.mobileUI = new MobileUI();
    });
} else {
    window.mobileUI = new MobileUI();
}
