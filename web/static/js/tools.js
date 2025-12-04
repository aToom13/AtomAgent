/**
 * AtomAgent - Tools Panel
 * Kullanılan araçları gerçek zamanlı gösterir
 */

import { escapeHtml } from './utils.js';

// Tool kullanım geçmişi
const toolHistory = [];
const MAX_HISTORY = 50;

// Tool kategorileri
const TOOL_CATEGORIES = {
    sandbox: {
        name: 'Sandbox',
        icon: '🐳',
        tools: ['sandbox_shell', 'sandbox_start', 'sandbox_stop', 'sandbox_upload', 'sandbox_download', 'sandbox_status']
    },
    files: {
        name: 'Dosyalar',
        icon: '📁',
        tools: ['read_file', 'write_file', 'list_directory', 'create_directory', 'delete_file']
    },
    web: {
        name: 'Web',
        icon: '🌐',
        tools: ['web_search', 'browse_url', 'scrape_page', 'web_browse']
    },
    git: {
        name: 'Git',
        icon: '📦',
        tools: ['git_status', 'git_commit', 'git_push', 'git_pull', 'git_diff']
    },
    code: {
        name: 'Kod',
        icon: '💻',
        tools: ['execute_python', 'run_tests', 'lint_code', 'format_code']
    },
    memory: {
        name: 'Hafıza',
        icon: '🧠',
        tools: ['remember', 'recall', 'forget', 'list_memories']
    }
};

// Aktif tool
let activeToolId = null;

export function addToolStart(toolName, input) {
    const toolId = 'tool-' + Date.now();
    activeToolId = toolId;
    
    const entry = {
        id: toolId,
        tool: toolName,
        input: input,
        output: null,
        status: 'running',
        startTime: new Date(),
        endTime: null,
        duration: null
    };
    
    toolHistory.unshift(entry);
    
    // Limit history
    if (toolHistory.length > MAX_HISTORY) {
        toolHistory.pop();
    }
    
    renderToolsPanel();
    highlightToolsTab();
    
    return toolId;
}

export function addToolEnd(toolName, output) {
    // Aktif tool'u bul ve güncelle
    const entry = toolHistory.find(t => t.tool === toolName && t.status === 'running');
    
    if (entry) {
        entry.output = output;
        entry.status = 'completed';
        entry.endTime = new Date();
        entry.duration = entry.endTime - entry.startTime;
    }
    
    activeToolId = null;
    renderToolsPanel();
}

export function renderToolsPanel() {
    const container = document.getElementById('tools-list');
    if (!container) return;
    
    if (toolHistory.length === 0) {
        container.innerHTML = `
            <div class="tools-empty">
                <div class="tools-empty-icon">🔧</div>
                <p>Henüz araç kullanılmadı</p>
                <p class="tools-hint">Agent çalışmaya başladığında kullanılan araçlar burada görünecek</p>
            </div>
        `;
        return;
    }
    
    // Kategorilere göre grupla
    const stats = getToolStats();
    
    container.innerHTML = `
        <div class="tools-stats">
            <div class="stat-item">
                <span class="stat-value">${toolHistory.length}</span>
                <span class="stat-label">Toplam</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${stats.running}</span>
                <span class="stat-label">Çalışıyor</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">${formatDuration(stats.totalDuration)}</span>
                <span class="stat-label">Süre</span>
            </div>
        </div>
        
        <div class="tools-history">
            ${toolHistory.map(entry => renderToolEntry(entry)).join('')}
        </div>
    `;
}

function renderToolEntry(entry) {
    const category = getToolCategory(entry.tool);
    const icon = category ? TOOL_CATEGORIES[category].icon : '🔧';
    const statusClass = entry.status === 'running' ? 'running' : 'completed';
    const duration = entry.duration ? formatDuration(entry.duration) : '...';
    
    return `
        <div class="tool-entry ${statusClass}" data-id="${entry.id}">
            <div class="tool-header">
                <span class="tool-icon">${icon}</span>
                <span class="tool-name">${escapeHtml(entry.tool)}</span>
                <span class="tool-duration">${duration}</span>
                <span class="tool-status-dot ${statusClass}"></span>
            </div>
            ${entry.input ? `
                <div class="tool-input">
                    <span class="tool-label">Input:</span>
                    <code>${escapeHtml(truncate(entry.input, 100))}</code>
                </div>
            ` : ''}
            ${entry.output ? `
                <div class="tool-output">
                    <span class="tool-label">Output:</span>
                    <code>${escapeHtml(truncate(entry.output, 150))}</code>
                </div>
            ` : ''}
        </div>
    `;
}

function getToolCategory(toolName) {
    for (const [category, data] of Object.entries(TOOL_CATEGORIES)) {
        if (data.tools.includes(toolName)) {
            return category;
        }
    }
    return null;
}

function getToolStats() {
    let running = 0;
    let totalDuration = 0;
    
    for (const entry of toolHistory) {
        if (entry.status === 'running') running++;
        if (entry.duration) totalDuration += entry.duration;
    }
    
    return { running, totalDuration };
}

function formatDuration(ms) {
    if (!ms) return '0ms';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
}

function truncate(str, maxLen) {
    if (!str) return '';
    str = String(str);
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function highlightToolsTab() {
    const toolsTab = document.querySelector('[data-tab="tools"]');
    if (toolsTab && !toolsTab.classList.contains('active')) {
        toolsTab.classList.add('has-activity');
        setTimeout(() => toolsTab.classList.remove('has-activity'), 3000);
    }
}

export function clearToolHistory() {
    toolHistory.length = 0;
    renderToolsPanel();
}

export function getToolHistory() {
    return [...toolHistory];
}
