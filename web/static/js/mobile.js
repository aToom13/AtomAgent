/**
 * Mobile UI Manager - AtomAgent
 * Touch-friendly interface with bottom sheet drawers
 */

class MobileUI {
    constructor() {
        this.isMobile = window.innerWidth <= 768;
        this.activeDrawer = null;
        this.touchStartY = 0;
        this.drawerStartY = 0;
        
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
        console.log('[Mobile] Initializing mobile UI');
        this.createMobileNav();
        this.createDrawers();
        this.createFAB();
        this.setupTouchHandlers();
        document.body.classList.add('mobile-nav-visible');
    }
    
    cleanup() {
        console.log('[Mobile] Cleaning up mobile UI');
        document.querySelectorAll('.mobile-nav, .mobile-drawer, .drawer-backdrop, .mobile-fab').forEach(el => el.remove());
        document.body.classList.remove('mobile-nav-visible');
    }
    
    createMobileNav() {
        // Remove existing nav if any
        document.querySelector('.mobile-nav')?.remove();
        
        const nav = document.createElement('nav');
        nav.className = 'mobile-nav';
        nav.innerHTML = `
            <button class="mobile-nav-btn active" data-action="chat">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                </svg>
                <span>Chat</span>
            </button>
            <button class="mobile-nav-btn" data-action="sessions">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    <path d="M8 9h8M8 13h6"/>
                </svg>
                <span>Geçmiş</span>
            </button>
            <button class="mobile-nav-btn" data-action="tools">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
                </svg>
                <span>Araçlar</span>
            </button>
            <button class="mobile-nav-btn" data-action="settings">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="3"/>
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
                </svg>
                <span>Ayarlar</span>
            </button>
        `;
        
        document.body.appendChild(nav);
        
        // Event listeners
        nav.querySelectorAll('.mobile-nav-btn').forEach(btn => {
            btn.addEventListener('click', () => this.handleNavClick(btn));
        });
    }
    
    createDrawers() {
        // Backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'drawer-backdrop';
        backdrop.addEventListener('click', () => this.closeDrawer());
        document.body.appendChild(backdrop);
        
        // Sessions Drawer
        this.createDrawer('sessions', 'Sohbetler', this.getSessionsContent());
        
        // Tools Drawer
        this.createDrawer('tools', 'Araçlar', this.getToolsContent());
        
        // Settings Drawer
        this.createDrawer('settings', 'Ayarlar', this.getSettingsContent());
    }
    
    createDrawer(id, title, content) {
        const drawer = document.createElement('div');
        drawer.id = `${id}-drawer`;
        drawer.className = 'mobile-drawer';
        drawer.innerHTML = `
            <div class="drawer-handle"></div>
            <div class="drawer-header">
                <h3>${title}</h3>
                <button class="drawer-close">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
            <div class="drawer-content">${content}</div>
        `;
        
        document.body.appendChild(drawer);
        
        // Close button
        drawer.querySelector('.drawer-close').addEventListener('click', () => this.closeDrawer());
        
        // Swipe to close
        this.setupDrawerSwipe(drawer);
    }
    
    createFAB() {
        const fab = document.createElement('button');
        fab.className = 'mobile-fab';
        fab.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 5v14M5 12h14"/>
            </svg>
        `;
        fab.addEventListener('click', () => this.newChat());
        document.body.appendChild(fab);
    }
    
    handleNavClick(btn) {
        const action = btn.dataset.action;
        
        // Update active state
        document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));
        
        if (action === 'chat') {
            btn.classList.add('active');
            this.closeDrawer();
        } else {
            this.openDrawer(action);
        }
    }
    
    openDrawer(type) {
        const drawer = document.getElementById(`${type}-drawer`);
        const backdrop = document.querySelector('.drawer-backdrop');
        
        if (!drawer) return;
        
        // Update content before opening
        if (type === 'sessions') {
            drawer.querySelector('.drawer-content').innerHTML = this.getSessionsContent();
            this.bindSessionEvents(drawer);
        } else if (type === 'tools') {
            drawer.querySelector('.drawer-content').innerHTML = this.getToolsContent();
        }
        
        this.activeDrawer = drawer;
        backdrop.classList.add('visible');
        
        requestAnimationFrame(() => {
            drawer.classList.add('open');
        });
    }
    
    closeDrawer() {
        if (!this.activeDrawer) return;
        
        const backdrop = document.querySelector('.drawer-backdrop');
        this.activeDrawer.classList.remove('open');
        backdrop.classList.remove('visible');
        
        // Reset nav active state
        document.querySelectorAll('.mobile-nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelector('.mobile-nav-btn[data-action="chat"]')?.classList.add('active');
        
        this.activeDrawer = null;
    }
    
    setupDrawerSwipe(drawer) {
        const handle = drawer.querySelector('.drawer-handle');
        
        handle.addEventListener('touchstart', (e) => {
            this.touchStartY = e.touches[0].clientY;
            this.drawerStartY = drawer.getBoundingClientRect().top;
            drawer.style.transition = 'none';
        }, { passive: true });
        
        handle.addEventListener('touchmove', (e) => {
            const deltaY = e.touches[0].clientY - this.touchStartY;
            if (deltaY > 0) {
                drawer.style.transform = `translateY(${deltaY}px)`;
            }
        }, { passive: true });
        
        handle.addEventListener('touchend', (e) => {
            drawer.style.transition = '';
            const deltaY = e.changedTouches[0].clientY - this.touchStartY;
            
            if (deltaY > 100) {
                this.closeDrawer();
            } else {
                drawer.style.transform = '';
            }
        });
    }
    
    setupTouchHandlers() {
        // Prevent body scroll when drawer is open
        document.addEventListener('touchmove', (e) => {
            if (this.activeDrawer && !this.activeDrawer.contains(e.target)) {
                e.preventDefault();
            }
        }, { passive: false });
    }
    
    getSessionsContent() {
        const sessions = window.AtomAgent?.sessions || [];
        
        if (sessions.length === 0) {
            return `
                <div class="empty-state">
                    <p>Henüz sohbet yok</p>
                    <button class="small-btn primary" onclick="window.mobileUI.newChat()">Yeni Sohbet</button>
                </div>
            `;
        }
        
        return sessions.map(session => `
            <div class="mobile-session-item ${session.id === window.AtomAgent?.currentSessionId ? 'active' : ''}" 
                 data-session-id="${session.id}">
                <span class="mobile-session-icon">💬</span>
                <div class="mobile-session-info">
                    <div class="mobile-session-title">${session.title || 'Yeni Sohbet'}</div>
                    <div class="mobile-session-meta">${session.message_count || 0} mesaj</div>
                </div>
            </div>
        `).join('');
    }
    
    bindSessionEvents(drawer) {
        drawer.querySelectorAll('.mobile-session-item').forEach(item => {
            item.addEventListener('click', () => {
                const sessionId = item.dataset.sessionId;
                if (window.AtomAgent?.loadSession) {
                    window.AtomAgent.loadSession(sessionId);
                }
                this.closeDrawer();
            });
        });
    }
    
    getToolsContent() {
        const toolsList = document.getElementById('tools-list');
        if (toolsList) {
            return toolsList.innerHTML;
        }
        return `
            <div class="tools-empty">
                <div class="tools-empty-icon">🔧</div>
                <p>Henüz araç kullanılmadı</p>
            </div>
        `;
    }
    
    getSettingsContent() {
        return `
            <div class="settings-section">
                <h4>Agent</h4>
                <div class="setting-item">
                    <label>Aktif Agent</label>
                    <select id="mobile-agent-select" onchange="window.mobileUI.changeAgent(this.value)">
                        <option value="supervisor">🎯 Supervisor</option>
                        <option value="coder">👨‍💻 Coder</option>
                        <option value="researcher">🔍 Researcher</option>
                        <option value="devops">🚀 DevOps</option>
                        <option value="qa">🧪 QA</option>
                        <option value="security">🔒 Security</option>
                    </select>
                </div>
            </div>
            <div class="settings-section">
                <h4>Görünüm</h4>
                <div class="setting-item">
                    <label>
                        <input type="checkbox" id="mobile-dark-mode" checked>
                        Karanlık Mod
                    </label>
                </div>
            </div>
            <div class="settings-section">
                <button class="small-btn" onclick="document.getElementById('settings-modal').classList.remove('hidden')">
                    Tüm Ayarlar
                </button>
            </div>
        `;
    }
    
    newChat() {
        if (window.AtomAgent?.newSession) {
            window.AtomAgent.newSession();
        }
        this.closeDrawer();
    }
    
    changeAgent(agent) {
        if (window.AtomAgent?.setAgent) {
            window.AtomAgent.setAgent(agent);
        }
    }
    
    // Update tools drawer when tools are used
    updateTools() {
        const drawer = document.getElementById('tools-drawer');
        if (drawer && drawer.classList.contains('open')) {
            drawer.querySelector('.drawer-content').innerHTML = this.getToolsContent();
        }
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
