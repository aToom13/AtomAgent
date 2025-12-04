/**
 * AtomAgent - Canvas Module
 * Live preview for web apps, HTML files, and GUI applications
 */

let currentUrl = '';
let currentMode = 'web'; // 'web', 'html', 'vnc'
let vncConnection = null;

let commandHistory = [];
let historyIndex = -1;

export function initCanvas() {
    setupModeSwitch();
    setupWebControls();
    setupHtmlControls();
    setupVncControls();
    setupTerminal();
    loadHtmlFiles();
}

// ==================== MODE SWITCHING ====================

function setupModeSwitch() {
    document.querySelectorAll('.canvas-mode-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            switchMode(mode);
        });
    });
}

function switchMode(mode) {
    currentMode = mode;
    
    // Update tab buttons
    document.querySelectorAll('.canvas-mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });
    
    // Show/hide controls
    document.getElementById('canvas-web-controls')?.classList.toggle('hidden', mode !== 'web');
    document.getElementById('canvas-html-controls')?.classList.toggle('hidden', mode !== 'html');
    document.getElementById('canvas-vnc-controls')?.classList.toggle('hidden', mode !== 'vnc');
    
    // Reset canvas
    resetCanvas();
    
    // Mode-specific init
    if (mode === 'html') {
        loadHtmlFiles();
    } else if (mode === 'vnc') {
        checkVncStatus();
    }
}

function resetCanvas() {
    const iframe = document.getElementById('canvas-iframe');
    const emptyState = document.getElementById('canvas-empty');
    
    if (iframe) {
        iframe.src = 'about:blank';
        iframe.classList.add('hidden');
    }
    if (emptyState) {
        emptyState.classList.remove('hidden');
    }
    
    setCanvasStatus('idle', 'Bağlantı bekleniyor...');
}

// ==================== WEB MODE ====================

function setupWebControls() {
    const urlInput = document.getElementById('canvas-url');
    const goBtn = document.getElementById('canvas-go');
    const refreshBtn = document.getElementById('canvas-refresh');
    const openExternalBtn = document.getElementById('canvas-open-external');
    const portSelect = document.getElementById('canvas-port-select');
    
    goBtn?.addEventListener('click', () => loadWebUrl());
    urlInput?.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadWebUrl();
    });
    refreshBtn?.addEventListener('click', () => refreshCanvas());
    openExternalBtn?.addEventListener('click', () => openExternal());
    
    portSelect?.addEventListener('change', () => {
        const port = portSelect.value;
        if (port && urlInput) {
            urlInput.value = `localhost:${port}`;
            loadWebUrl();
        }
    });
}

export function loadWebUrl(url = null) {
    if (currentMode !== 'web') switchMode('web');
    
    const urlInput = document.getElementById('canvas-url');
    const targetUrl = url || urlInput?.value?.trim();
    if (!targetUrl) return;
    
    let fullUrl = targetUrl;
    if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
        fullUrl = `http://${targetUrl}`;
    }
    
    currentUrl = fullUrl;
    if (urlInput) urlInput.value = targetUrl;
    
    loadInIframe(fullUrl);
}

export function loadUrl(url) {
    loadWebUrl(url);
}

// ==================== HTML MODE ====================

function setupHtmlControls() {
    const loadBtn = document.getElementById('canvas-load-html');
    const select = document.getElementById('canvas-html-select');
    
    loadBtn?.addEventListener('click', () => {
        const file = select?.value;
        if (file) loadHtmlFile(file);
    });
    
    select?.addEventListener('change', () => {
        const file = select.value;
        if (file) loadHtmlFile(file);
    });
}

async function loadHtmlFiles() {
    const select = document.getElementById('canvas-html-select');
    if (!select) return;
    
    try {
        // Workspace'den HTML dosyalarını al
        const response = await fetch('/api/workspace/files?path=.');
        const data = await response.json();
        
        // HTML dosyalarını filtrele (recursive)
        const htmlFiles = findHtmlFiles(data.items || [], '');
        
        select.innerHTML = '<option value="">HTML dosyası seç...</option>';
        htmlFiles.forEach(file => {
            const option = document.createElement('option');
            option.value = file;
            option.textContent = file;
            select.appendChild(option);
        });
        
        // Docker'dan da HTML dosyalarını al
        try {
            const dockerResponse = await fetch('/api/docker/files?path=/home/agent/shared');
            const dockerData = await dockerResponse.json();
            const dockerHtmlFiles = findHtmlFilesSimple(dockerData.items || [], '/home/agent/shared');
            
            if (dockerHtmlFiles.length > 0) {
                const optgroup = document.createElement('optgroup');
                optgroup.label = '🐳 Docker';
                dockerHtmlFiles.forEach(file => {
                    const option = document.createElement('option');
                    option.value = `docker:${file}`;
                    option.textContent = file.replace('/home/agent/shared/', '');
                    optgroup.appendChild(option);
                });
                select.appendChild(optgroup);
            }
        } catch (e) {
            // Docker not running, ignore
        }
    } catch (e) {
        console.error('Failed to load HTML files:', e);
    }
}

function findHtmlFiles(items, prefix) {
    let files = [];
    for (const item of items) {
        const path = prefix ? `${prefix}/${item.name}` : item.name;
        if (item.name.endsWith('.html') || item.name.endsWith('.htm')) {
            files.push(path);
        }
    }
    return files;
}

function findHtmlFilesSimple(items, prefix) {
    return items
        .filter(item => !item.is_dir && (item.name.endsWith('.html') || item.name.endsWith('.htm')))
        .map(item => item.path || `${prefix}/${item.name}`);
}

async function loadHtmlFile(filePath) {
    if (currentMode !== 'html') switchMode('html');
    
    setCanvasStatus('loading', 'HTML yükleniyor...');
    
    try {
        let content;
        
        if (filePath.startsWith('docker:')) {
            // Docker'dan oku
            const dockerPath = filePath.replace('docker:', '');
            const response = await fetch(`/api/docker/file?path=${encodeURIComponent(dockerPath)}`);
            const data = await response.json();
            content = data.content;
        } else {
            // Workspace'den oku
            const response = await fetch(`/api/workspace/file?path=${encodeURIComponent(filePath)}`);
            const data = await response.json();
            content = data.content;
        }
        
        // HTML'i iframe'de göster
        displayHtmlContent(content, filePath);
        
    } catch (e) {
        console.error('Failed to load HTML file:', e);
        setCanvasStatus('error', 'Dosya yüklenemedi');
    }
}

function displayHtmlContent(htmlContent, filename) {
    const iframe = document.getElementById('canvas-iframe');
    const emptyState = document.getElementById('canvas-empty');
    
    if (!iframe) return;
    
    // Base tag ekle (relative path'ler için)
    const baseDir = filename.includes('/') ? filename.substring(0, filename.lastIndexOf('/') + 1) : '';
    const baseTag = `<base href="/api/workspace/raw/${baseDir}">`;
    
    // HTML'i düzenle
    let modifiedHtml = htmlContent;
    if (!htmlContent.includes('<base')) {
        if (htmlContent.includes('<head>')) {
            modifiedHtml = htmlContent.replace('<head>', `<head>${baseTag}`);
        } else if (htmlContent.includes('<html>')) {
            modifiedHtml = htmlContent.replace('<html>', `<html><head>${baseTag}</head>`);
        }
    }
    
    // Blob URL oluştur
    const blob = new Blob([modifiedHtml], { type: 'text/html' });
    const blobUrl = URL.createObjectURL(blob);
    
    currentUrl = blobUrl;
    
    if (emptyState) emptyState.classList.add('hidden');
    iframe.classList.remove('hidden');
    iframe.src = blobUrl;
    
    iframe.onload = () => {
        setCanvasStatus('connected', `Yüklendi: ${filename}`);
    };
    
    highlightCanvasTab();
}

// ==================== VNC MODE (GUI Apps) ====================

function setupVncControls() {
    const connectBtn = document.getElementById('canvas-vnc-connect');
    const fullscreenBtn = document.getElementById('canvas-vnc-fullscreen');
    
    connectBtn?.addEventListener('click', () => connectVnc());
    fullscreenBtn?.addEventListener('click', () => toggleVncFullscreen());
}

async function checkVncStatus() {
    const statusEl = document.getElementById('vnc-status');
    
    try {
        const response = await fetch('/api/canvas/vnc-status');
        const data = await response.json();
        
        if (data.running) {
            statusEl.textContent = '● VNC Hazır';
            statusEl.className = 'vnc-status connected';
        } else {
            statusEl.textContent = '○ VNC Kapalı';
            statusEl.className = 'vnc-status disconnected';
        }
    } catch (e) {
        statusEl.textContent = '○ VNC Bağlantısı Yok';
        statusEl.className = 'vnc-status disconnected';
    }
}

async function connectVnc() {
    if (currentMode !== 'vnc') switchMode('vnc');
    
    setCanvasStatus('loading', 'VNC başlatılıyor...');
    
    try {
        // Önce VNC durumunu kontrol et
        const statusResponse = await fetch('/api/canvas/vnc-status');
        const statusData = await statusResponse.json();
        
        // VNC çalışmıyorsa başlat
        if (!statusData.running || !statusData.novnc) {
            setCanvasStatus('loading', 'VNC sunucusu başlatılıyor...');
            
            const startResponse = await fetch('/api/canvas/start-vnc', { method: 'POST' });
            const startData = await startResponse.json();
            
            if (!startData.success) {
                setCanvasStatus('error', 'VNC başlatılamadı');
                showVncError('VNC sunucusu başlatılamadı. Docker container çalışıyor mu?');
                return;
            }
            
            // VNC'nin başlaması için bekle
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // noVNC iframe ile bağlan (host port: 16080 -> container port: 6080)
        const vncPort = 16080;
        const vncUrl = `http://localhost:${vncPort}/vnc.html?autoconnect=true&resize=scale&reconnect=true`;
        
        setCanvasStatus('loading', 'noVNC bağlanıyor...');
        loadInIframe(vncUrl);
        
        // Status güncelle
        const statusEl = document.getElementById('vnc-status');
        if (statusEl) {
            statusEl.textContent = '● VNC Bağlı';
            statusEl.className = 'vnc-status connected';
        }
        
    } catch (e) {
        console.error('VNC connection error:', e);
        setCanvasStatus('error', 'VNC bağlantı hatası');
        showVncError('VNC bağlantısı kurulamadı: ' + e.message);
    }
}

function showVncError(message) {
    const emptyState = document.getElementById('canvas-empty');
    const iframe = document.getElementById('canvas-iframe');
    
    if (iframe) iframe.classList.add('hidden');
    if (emptyState) {
        emptyState.classList.remove('hidden');
        emptyState.innerHTML = `
            <div class="canvas-empty-icon">❌</div>
            <h3>VNC Bağlantı Hatası</h3>
            <p>${message}</p>
            <div class="canvas-hints" style="margin-top: 16px;">
                <p>💡 Çözüm adımları:</p>
                <ul>
                    <li>Docker container'ın çalıştığından emin olun</li>
                    <li>Container'ı yeniden başlatın: <code>docker-compose down && docker-compose up -d --build</code></li>
                    <li>VNC paketlerinin kurulu olduğundan emin olun</li>
                </ul>
            </div>
            <button onclick="window.AtomAgent.retryCanvas()" class="small-btn" style="margin-top: 12px;">
                Tekrar Dene
            </button>
        `;
    }
}

function toggleVncFullscreen() {
    const container = document.getElementById('canvas-container');
    if (document.fullscreenElement) {
        document.exitFullscreen();
    } else {
        container?.requestFullscreen();
    }
}

// ==================== COMMON FUNCTIONS ====================

function loadInIframe(url) {
    const iframe = document.getElementById('canvas-iframe');
    const emptyState = document.getElementById('canvas-empty');
    const container = document.getElementById('canvas-container');
    
    if (!iframe) return;
    
    currentUrl = url;
    setCanvasStatus('loading', 'Yükleniyor...');
    
    if (emptyState) emptyState.classList.add('hidden');
    iframe.classList.remove('hidden');
    
    showLoading(container);
    iframe.src = url;
    
    iframe.onload = () => {
        hideLoading(container);
        setCanvasStatus('connected', 'Bağlandı');
    };
    
    iframe.onerror = () => {
        hideLoading(container);
        setCanvasStatus('error', 'Bağlantı hatası');
    };
    
    // Timeout
    setTimeout(() => {
        hideLoading(container);
        if (iframe.src === url) {
            setCanvasStatus('connected', 'Yüklendi');
        }
    }, 10000);
    
    highlightCanvasTab();
}

export function refreshCanvas() {
    const iframe = document.getElementById('canvas-iframe');
    if (iframe && currentUrl) {
        if (currentUrl.startsWith('blob:')) {
            // HTML mode - reload from select
            const select = document.getElementById('canvas-html-select');
            if (select?.value) loadHtmlFile(select.value);
        } else {
            iframe.src = currentUrl;
        }
    }
}

export function openExternal() {
    if (currentUrl && !currentUrl.startsWith('blob:')) {
        window.open(currentUrl, '_blank');
    }
}

function setCanvasStatus(status, text) {
    const statusEl = document.getElementById('canvas-status');
    const statusText = document.getElementById('canvas-status-text');
    const statusIcon = statusEl?.querySelector('.canvas-status-icon');
    
    if (statusEl) statusEl.className = `canvas-status ${status}`;
    if (statusText) statusText.textContent = text;
    
    if (statusIcon) {
        const icons = { connected: '●', loading: '◐', error: '○', idle: '○' };
        statusIcon.textContent = icons[status] || '○';
    }
}

function showLoading(container) {
    hideLoading(container);
    const loading = document.createElement('div');
    loading.className = 'canvas-loading';
    loading.innerHTML = '<div class="canvas-loading-spinner"></div>';
    container?.appendChild(loading);
}

function hideLoading(container) {
    container?.querySelector('.canvas-loading')?.remove();
}

export function highlightCanvasTab() {
    const canvasTab = document.querySelector('[data-tab="canvas"]');
    if (canvasTab && !canvasTab.classList.contains('active')) {
        canvasTab.classList.add('has-activity');
        setTimeout(() => canvasTab.classList.remove('has-activity'), 3000);
    }
}

// ==================== EXTERNAL TRIGGERS ====================

export function handleServerStart(port, type = 'web') {
    const urlInput = document.getElementById('canvas-url');
    if (urlInput) urlInput.value = `localhost:${port}`;
    
    setTimeout(() => {
        switchMode('web');
        loadWebUrl(`localhost:${port}`);
        
        // Canvas tab'ına geç
        document.querySelector('[data-tab="canvas"]')?.click();
    }, 2000);
}

export function handleHtmlCreated(filePath) {
    // Agent HTML dosyası oluşturduğunda
    setTimeout(() => {
        switchMode('html');
        loadHtmlFiles().then(() => {
            const select = document.getElementById('canvas-html-select');
            if (select) {
                select.value = filePath;
                loadHtmlFile(filePath);
            }
        });
        document.querySelector('[data-tab="canvas"]')?.click();
    }, 1000);
}

export function handleGuiAppStart() {
    // Agent GUI uygulaması başlattığında
    setTimeout(() => {
        switchMode('vnc');
        connectVnc();
        document.querySelector('[data-tab="canvas"]')?.click();
    }, 2000);
}

export function handleCanvasMessage(message) {
    if (message.type === 'server_started') {
        handleServerStart(message.port, message.server_type);
    } else if (message.type === 'canvas_url') {
        loadWebUrl(message.url);
    } else if (message.type === 'html_created') {
        handleHtmlCreated(message.path);
    } else if (message.type === 'gui_started') {
        handleGuiAppStart();
    }
}

export function retryCanvas() {
    if (currentUrl) {
        if (currentMode === 'web') loadWebUrl(currentUrl);
        else if (currentMode === 'vnc') connectVnc();
    }
}

// ==================== INTERACTIVE TERMINAL ====================

function setupTerminal() {
    const input = document.getElementById('canvas-terminal-input');
    const runBtn = document.getElementById('canvas-terminal-run');
    const clearBtn = document.getElementById('canvas-terminal-clear');
    const toggleBtn = document.getElementById('canvas-terminal-toggle');
    const header = document.querySelector('.canvas-terminal-header');
    const resizeHandle = document.getElementById('canvas-terminal-resize');
    
    // Enter ile komut çalıştır
    input?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            runTerminalCommand();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            navigateHistory(-1);
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            navigateHistory(1);
        }
    });
    
    runBtn?.addEventListener('click', runTerminalCommand);
    clearBtn?.addEventListener('click', clearTerminal);
    toggleBtn?.addEventListener('click', toggleTerminal);
    header?.addEventListener('dblclick', toggleTerminal);
    
    // Resize handle
    setupTerminalResize(resizeHandle);
}

function setupTerminalResize(handle) {
    if (!handle) return;
    
    let startY, startHeight;
    const terminal = document.getElementById('canvas-terminal');
    
    handle.addEventListener('mousedown', (e) => {
        startY = e.clientY;
        startHeight = terminal.offsetHeight;
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
    });
    
    function onMouseMove(e) {
        const delta = startY - e.clientY;
        const newHeight = Math.max(100, Math.min(startHeight + delta, window.innerHeight * 0.7));
        terminal.style.height = newHeight + 'px';
    }
    
    function onMouseUp() {
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
    }
}

async function runTerminalCommand() {
    const input = document.getElementById('canvas-terminal-input');
    const command = input?.value?.trim();
    
    if (!command) return;
    
    // Komutu history'e ekle
    commandHistory.push(command);
    historyIndex = commandHistory.length;
    
    // Input'u temizle
    input.value = '';
    
    // Komutu terminale yaz
    addTerminalLine(command, 'command');
    
    try {
        // Docker'da komutu çalıştır
        const response = await fetch('/api/docker/exec', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, timeout: 30 })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // stdout ve stderr'i göster
            if (data.stdout && data.stdout.trim()) {
                addTerminalLine(data.stdout.trim(), 'output');
            }
            if (data.stderr && data.stderr.trim()) {
                // stderr her zaman error değil, warning de olabilir
                const isError = data.returncode !== 0;
                addTerminalLine(data.stderr.trim(), isError ? 'error' : 'output');
            }
            // Hiç çıktı yoksa
            if (!data.stdout?.trim() && !data.stderr?.trim()) {
                // Sessiz başarı - bir şey yazmaya gerek yok
            }
        } else {
            addTerminalLine(data.error || 'Komut çalıştırılamadı', 'error');
        }
    } catch (e) {
        addTerminalLine(`Hata: ${e.message}`, 'error');
    }
    
    // Scroll to bottom
    scrollTerminalToBottom();
}

function addTerminalLine(text, type = 'output') {
    const output = document.getElementById('canvas-terminal-output');
    if (!output) return;
    
    const lines = text.split('\n');
    lines.forEach(line => {
        if (line.trim() || type === 'command') {
            const div = document.createElement('div');
            div.className = `terminal-line ${type}`;
            div.textContent = line;
            output.appendChild(div);
        }
    });
    
    scrollTerminalToBottom();
}

function scrollTerminalToBottom() {
    const output = document.getElementById('canvas-terminal-output');
    if (output) {
        output.scrollTop = output.scrollHeight;
    }
}

function clearTerminal() {
    const output = document.getElementById('canvas-terminal-output');
    if (output) {
        output.innerHTML = '<div class="terminal-line system">Terminal temizlendi.</div>';
    }
}

function toggleTerminal() {
    const terminal = document.getElementById('canvas-terminal');
    const toggleBtn = document.getElementById('canvas-terminal-toggle');
    
    if (terminal) {
        terminal.classList.toggle('collapsed');
        if (toggleBtn) {
            toggleBtn.textContent = terminal.classList.contains('collapsed') ? '▲' : '▼';
        }
    }
}

function navigateHistory(direction) {
    const input = document.getElementById('canvas-terminal-input');
    if (!input || commandHistory.length === 0) return;
    
    historyIndex += direction;
    
    if (historyIndex < 0) {
        historyIndex = 0;
    } else if (historyIndex >= commandHistory.length) {
        historyIndex = commandHistory.length;
        input.value = '';
        return;
    }
    
    input.value = commandHistory[historyIndex] || '';
}

// Export terminal functions
export function terminalExec(command) {
    const input = document.getElementById('canvas-terminal-input');
    if (input) {
        input.value = command;
        runTerminalCommand();
    }
}

export { clearTerminal, addTerminalLine };
