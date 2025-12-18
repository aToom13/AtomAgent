/**
 * AtomAgent - Preview Tab (Smart Content Switcher)
 */
import { state } from './state.js';

export function initPreview() {
    setupPreviewListeners();
    // Default state check
    updatePreviewContent();
}

function getElements() {
    return {
        container: document.querySelector('.preview-container'),
        placeholder: document.getElementById('preview-placeholder'),
        frame: document.getElementById('preview-frame'),
        image: document.getElementById('preview-image'),
        vnc: document.getElementById('preview-vnc'),
        status: document.getElementById('preview-status'),
        refreshBtn: document.getElementById('preview-refresh'),
        externalBtn: document.getElementById('preview-external')
    };
}

// Global preview state
let previewState = {
    mode: 'empty', // empty, web, image, vnc
    content: null, // url, image_src, vnc_url
    timestamp: 0   // last update time
};

// Setup listeners for browser mockup controls
function setupPreviewListeners() {
    const els = getElements();

    // Device Toggles (in status bar)
    const deviceBtns = document.querySelectorAll('.preview-statusbar .device-btn');
    const contentArea = document.querySelector('.preview-content-area');

    deviceBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active class from all
            deviceBtns.forEach(b => b.classList.remove('active'));
            // Add to clicked
            btn.classList.add('active');

            // Update content area styling based on device (for responsive preview)
            const deviceType = btn.dataset.device; // desktop, tablet, mobile
            // Could add width constraints here if you want to simulate device widths
            console.log(`Device mode: ${deviceType}`);
        });
    });

    // Browser Controls
    const backBtn = document.getElementById('browser-back');
    const forwardBtn = document.getElementById('browser-forward');
    const refreshBtn = document.getElementById('browser-refresh');
    const externalBtn = document.getElementById('preview-external');
    const urlInput = document.getElementById('browser-url');

    refreshBtn?.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (els.frame && els.frame.src) {
            // Use src reload instead of contentWindow (cross-origin safe)
            const currentSrc = els.frame.src;
            els.frame.src = '';
            setTimeout(() => { els.frame.src = currentSrc; }, 100);
        }
    });

    externalBtn?.addEventListener('click', () => {
        if (previewState.content && (previewState.mode === 'web' || previewState.mode === 'image')) {
            window.open(previewState.content, '_blank');
        }
    });

    // Back/Forward (limited functionality for iframe security reasons usually, but simplistic attempt)
    backBtn?.addEventListener('click', () => {
        try { if (els.frame) els.frame.contentWindow.history.back(); } catch (e) { }
    });
    forwardBtn?.addEventListener('click', () => {
        try { if (els.frame) els.frame.contentWindow.history.forward(); } catch (e) { }
    });
}

// Public API to set content
export function setPreviewContent(type, data) {
    previewState.timestamp = Date.now();

    if (type === 'web') {
        previewState.mode = 'web';
        // Handle localhost mapping if needed (e.g. 3000 -> 13000)
        previewState.content = data.url;
        showWeb(data.url);
    } else if (type === 'image') {
        previewState.mode = 'image';
        previewState.content = data.url; // /static/... or data:image...
        showImage(data.url);
    } else if (type === 'vnc') {
        previewState.mode = 'vnc';
        previewState.content = data.url || 'ws://localhost:6080/websockify';
        showVNC(data);
    } else {
        previewState.mode = 'empty';
        showEmpty();
    }

    updateStatus();
}

function showWeb(url) {
    const els = getElements();

    // Validate URL
    if (!url || url === 'undefined' || url === '') {
        console.warn('[Preview] Invalid URL:', url);
        return;
    }

    console.log('[Preview] Showing URL:', url);

    hideAll(els);
    els.frame.classList.remove('hidden');
    els.frame.src = url;

    // Update URL bar
    const urlInput = document.getElementById('browser-url');
    if (urlInput) urlInput.value = url;

    // Register in taskbar
    addAppToTaskbar({ id: 'app_web', name: 'Web Preview', icon: '🌐', type: 'web', content: url });
}

function showImage(src) {
    const els = getElements();
    hideAll(els);
    els.image.classList.remove('hidden');
    els.image.src = src;

    // Register in taskbar
    addAppToTaskbar({ id: 'app_image', name: 'Image Viewer', icon: '🖼️', type: 'image', content: src });
}

function showVNC(data) {
    const els = getElements();
    hideAll(els);
    els.vnc.classList.remove('hidden');

    // Use iframe to connect to noVNC
    const vncPort = data.port || 16080;
    const vncUrl = `http://localhost:${vncPort}/vnc.html?autoconnect=true&resize=scale&reconnect=true`;

    // Create or update iframe inside VNC container
    let vncFrame = els.vnc.querySelector('iframe');
    if (!vncFrame) {
        vncFrame = document.createElement('iframe');
        vncFrame.style.cssText = 'width:100%; height:100%; border:none;';
        els.vnc.appendChild(vncFrame);
    }
    vncFrame.src = vncUrl;

    // Update URL bar
    const urlInput = document.getElementById('browser-url');
    if (urlInput) urlInput.value = `VNC: localhost:${vncPort}`;

    // Register in taskbar
    addAppToTaskbar({ id: 'app_vnc', name: 'VNC Desktop', icon: '🖥️', type: 'vnc', content: vncUrl });
}

function showEmpty() {
    const els = getElements();
    hideAll(els);
    els.placeholder.classList.remove('hidden');
}

function hideAll(els) {
    els.placeholder.classList.add('hidden');
    els.frame.classList.add('hidden');
    els.image.classList.add('hidden');
    els.vnc.classList.add('hidden');
}

function updateStatus() {
    const els = getElements();
    if (previewState.mode === 'web') {
        els.status.textContent = `🌐 ${previewState.content}`;
    } else if (previewState.mode === 'image') {
        els.status.textContent = `🖼️ Görsel Önizleme`;
    } else if (previewState.mode === 'vnc') {
        els.status.textContent = `🖥️ Masaüstü (VNC)`;
    } else {
        els.status.textContent = 'Hazır';
    }
}

// Auto-detect update
function updatePreviewContent() {
    // Check state or last known active content
    if (previewState.mode === 'empty') {
        showEmpty();
    }
}

// === LIVE TERMINAL OVERLAY ===
let terminalOverlayLines = [];
let terminalUserClosed = false; // Track if user explicitly closed the terminal
const MAX_TERMINAL_LINES = 100;

function getTerminalElements() {
    return {
        overlay: document.getElementById('preview-terminal-overlay'),
        output: document.getElementById('terminal-overlay-output'),
        status: document.querySelector('.terminal-overlay-header .terminal-status'),
        toggleBtn: document.getElementById('terminal-overlay-toggle')
    };
}

export function showTerminalOverlay() {
    // Don't auto-show if user explicitly closed it
    if (terminalUserClosed) return;

    const els = getTerminalElements();
    if (els.overlay) {
        els.overlay.classList.add('active');
        els.overlay.classList.remove('minimized');
    }
}

export function hideTerminalOverlay() {
    const els = getTerminalElements();
    if (els.overlay) {
        els.overlay.classList.remove('active');
    }
}

// User explicitly closes terminal (from close button)
export function closeTerminalOverlay() {
    terminalUserClosed = true;
    hideTerminalOverlay();
}

// Reset user-closed state (call when new session/chat starts)
export function resetTerminalUserClosed() {
    terminalUserClosed = false;
}

export function appendTerminalOutput(text, type = 'output') {
    const els = getTerminalElements();
    if (!els.output || !text) return;

    // Show overlay
    showTerminalOverlay();

    // Split by newlines and add each line
    const lines = text.split('\n');
    lines.forEach(line => {
        if (line.trim()) {
            const lineEl = document.createElement('div');
            lineEl.className = `line ${type}`;
            lineEl.textContent = line;
            els.output.appendChild(lineEl);
            terminalOverlayLines.push(lineEl);
        }
    });

    // Limit lines
    while (terminalOverlayLines.length > MAX_TERMINAL_LINES) {
        const oldLine = terminalOverlayLines.shift();
        oldLine?.remove();
    }

    // Auto-scroll
    els.output.scrollTop = els.output.scrollHeight;
}

export function setTerminalStatus(status, isRunning = true) {
    const els = getTerminalElements();
    if (els.status) {
        els.status.textContent = isRunning ? `▶ ${status}` : `✓ ${status}`;
        els.status.style.color = isRunning ? '#4ec9b0' : '#888';
    }
}

export function clearTerminalOverlay() {
    const els = getTerminalElements();
    if (els.output) {
        els.output.innerHTML = '';
        terminalOverlayLines = [];
    }
}

// Setup toggle button
document.addEventListener('DOMContentLoaded', () => {
    const toggleBtn = document.getElementById('terminal-overlay-toggle');
    const closeBtn = document.getElementById('terminal-overlay-close');
    const overlay = document.getElementById('preview-terminal-overlay');

    toggleBtn?.addEventListener('click', () => {
        if (overlay) {
            overlay.classList.toggle('minimized');
            toggleBtn.textContent = overlay.classList.contains('minimized') ? '+' : '−';
        }
    });

    // Close button - sets user-closed state
    closeBtn?.addEventListener('click', () => {
        closeTerminalOverlay();
    });

    // Setup window controls
    setupWindowControls();
});

// === WINDOW CONTROLS & TASKBAR ===
let openApps = []; // { id, name, icon, type, minimized, content }
let isFullscreen = false;

function setupWindowControls() {
    const windowControls = document.getElementById('preview-window-controls');
    if (!windowControls) return;

    windowControls.querySelectorAll('.window-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const action = e.target.dataset.action;
            handleWindowAction(action);
        });
    });
}

function handleWindowAction(action) {
    const contentArea = document.querySelector('.preview-content-area');
    const windowControls = document.getElementById('preview-window-controls');

    switch (action) {
        case 'close':
            // Hide current content, remove from apps
            hideAllContent();
            windowControls?.classList.add('hidden');
            removeActiveApp();
            break;
        case 'minimize':
            // Minimize to taskbar
            minimizeCurrentApp();
            break;
        case 'maximize':
            // Toggle fullscreen
            toggleFullscreen();
            break;
    }
}

function showWindowControls(appName) {
    const windowControls = document.getElementById('preview-window-controls');
    const titleEl = windowControls?.querySelector('.window-title');
    if (windowControls) {
        windowControls.classList.remove('hidden');
        if (titleEl) titleEl.textContent = appName;
    }
}

function hideWindowControls() {
    const windowControls = document.getElementById('preview-window-controls');
    windowControls?.classList.add('hidden');
}

function hideAllContent() {
    const els = getElements();
    els.placeholder?.classList.add('hidden');
    els.frame?.classList.add('hidden');
    els.image?.classList.add('hidden');
    els.vnc?.classList.add('hidden');
    showEmpty();
}

function toggleFullscreen() {
    const contentArea = document.querySelector('.preview-content-area');
    if (!contentArea) return;

    if (document.fullscreenElement) {
        document.exitFullscreen();
        isFullscreen = false;
    } else {
        contentArea.requestFullscreen();
        isFullscreen = true;
    }
}

// App management
export function addAppToTaskbar(appInfo) {
    const { id, name, icon, type } = appInfo;

    // Check if already exists
    if (openApps.find(a => a.id === id)) return;

    openApps.push({ id, name, icon, type, minimized: false });
    renderTaskbar();
    showWindowControls(name);
}

function removeActiveApp() {
    if (previewState.mode !== 'empty') {
        const appId = `app_${previewState.mode}`;
        openApps = openApps.filter(a => a.id !== appId);
        renderTaskbar();
    }
    previewState.mode = 'empty';
}

function minimizeCurrentApp() {
    const appId = `app_${previewState.mode}`;
    const app = openApps.find(a => a.id === appId);
    if (app) {
        app.minimized = true;
        renderTaskbar();
    }
    hideAllContent();
    hideWindowControls();
}

export function restoreApp(appId) {
    const app = openApps.find(a => a.id === appId);
    if (app) {
        app.minimized = false;
        renderTaskbar();
        // Restore content based on type
        if (app.type === 'web') showWeb(app.content);
        if (app.type === 'vnc') showVNC({});
        if (app.type === 'image') showImage(app.content);
        showWindowControls(app.name);
    }
}

function renderTaskbar() {
    const taskbarApps = document.getElementById('taskbar-apps');
    if (!taskbarApps) return;

    if (openApps.length === 0) {
        taskbarApps.innerHTML = '<span class="taskbar-empty">Açık uygulama yok</span>';
        return;
    }

    taskbarApps.innerHTML = openApps.map(app => `
        <button class="taskbar-app ${app.minimized ? 'minimized' : 'active'}" 
                data-app-id="${app.id}" 
                onclick="window.AtomAgent.restoreApp('${app.id}')">
            <span class="app-icon">${app.icon}</span>
            <span class="app-name">${app.name}</span>
        </button>
    `).join('');
}

// Expose to global
if (typeof window !== 'undefined') {
    window.AtomAgent = window.AtomAgent || {};
    window.AtomAgent.restoreApp = restoreApp;
}
