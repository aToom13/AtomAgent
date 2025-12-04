/**
 * AtomAgent - Browser Panel
 * Web araması ve tarayıcı aktivitelerini gösterir
 */

import { escapeHtml, renderMarkdown } from './utils.js';

// Browser geçmişi
const browserHistory = [];
const MAX_HISTORY = 30;

// Aktif sayfa
let activePage = null;

export function addBrowserStart(tool, url) {
    const pageId = 'page-' + Date.now();
    
    const entry = {
        id: pageId,
        tool: tool,
        url: url,
        title: url,
        content: null,
        status: 'loading',
        startTime: new Date(),
        endTime: null
    };
    
    activePage = entry;
    browserHistory.unshift(entry);
    
    if (browserHistory.length > MAX_HISTORY) {
        browserHistory.pop();
    }
    
    renderBrowserPanel();
    highlightBrowserTab();
    
    return pageId;
}

export function addBrowserResult(tool, content) {
    if (activePage && activePage.tool === tool) {
        activePage.content = content;
        activePage.status = 'loaded';
        activePage.endTime = new Date();
        
        // URL'den title çıkar
        if (content) {
            const titleMatch = content.match(/<title>([^<]+)<\/title>/i);
            if (titleMatch) {
                activePage.title = titleMatch[1];
            }
        }
    }
    
    activePage = null;
    renderBrowserPanel();
}

export function renderBrowserPanel() {
    const container = document.getElementById('browser-content');
    if (!container) return;
    
    if (browserHistory.length === 0) {
        container.innerHTML = `
            <div class="browser-empty">
                <div class="browser-empty-icon">🌐</div>
                <p>Web aktivitesi yok</p>
                <p class="browser-hint">Agent web araması yaptığında sonuçlar burada görünecek</p>
            </div>
        `;
        return;
    }
    
    // Aktif sayfa varsa göster
    const current = browserHistory[0];
    
    container.innerHTML = `
        <div class="browser-current">
            <div class="browser-url-bar">
                <span class="browser-status ${current.status}">
                    ${current.status === 'loading' ? '⏳' : '✓'}
                </span>
                <span class="browser-url">${escapeHtml(current.url || current.tool)}</span>
                <span class="browser-tool">${escapeHtml(current.tool)}</span>
            </div>
            
            <div class="browser-viewport">
                ${current.status === 'loading' ? `
                    <div class="browser-loading">
                        <div class="loading-spinner"></div>
                        <p>Sayfa yükleniyor...</p>
                    </div>
                ` : `
                    <div class="browser-result">
                        ${formatBrowserContent(current.content, current.tool)}
                    </div>
                `}
            </div>
        </div>
        
        ${browserHistory.length > 1 ? `
            <div class="browser-history">
                <h4>Geçmiş</h4>
                <div class="history-list">
                    ${browserHistory.slice(1, 10).map(entry => `
                        <div class="history-item" onclick="window.AtomAgent.showBrowserEntry('${entry.id}')">
                            <span class="history-icon">${getToolIcon(entry.tool)}</span>
                            <span class="history-title">${escapeHtml(truncate(entry.title || entry.url, 40))}</span>
                            <span class="history-time">${formatTime(entry.startTime)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : ''}
    `;
}

function formatBrowserContent(content, tool) {
    if (!content) return '<p class="no-content">İçerik yok</p>';
    
    // Web search sonuçları için özel format
    if (tool === 'web_search') {
        return formatSearchResults(content);
    }
    
    // HTML içerik için basitleştirilmiş görünüm
    if (content.includes('<html') || content.includes('<body')) {
        return `<div class="html-preview">${sanitizeHtml(content)}</div>`;
    }
    
    // Markdown veya düz metin
    if (content.includes('##') || content.includes('**')) {
        return `<div class="markdown-content">${renderMarkdown(content)}</div>`;
    }
    
    return `<pre class="text-content">${escapeHtml(content)}</pre>`;
}

function formatSearchResults(content) {
    // Arama sonuçlarını parse et
    const lines = content.split('\n').filter(l => l.trim());
    let html = '<div class="search-results">';
    
    let currentResult = null;
    
    for (const line of lines) {
        if (line.startsWith('##') || line.startsWith('**')) {
            if (currentResult) {
                html += '</div>';
            }
            currentResult = line.replace(/[#*]/g, '').trim();
            html += `<div class="search-result"><h4>${escapeHtml(currentResult)}</h4>`;
        } else if (line.startsWith('http')) {
            html += `<a href="${escapeHtml(line)}" target="_blank" class="result-url">${escapeHtml(line)}</a>`;
        } else if (line.trim()) {
            html += `<p>${escapeHtml(line)}</p>`;
        }
    }
    
    if (currentResult) {
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

function sanitizeHtml(html) {
    // Basit HTML sanitization - script ve style kaldır
    return html
        .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
        .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
        .replace(/<link[^>]*>/gi, '')
        .replace(/on\w+="[^"]*"/gi, '')
        .replace(/on\w+='[^']*'/gi, '');
}

function getToolIcon(tool) {
    const icons = {
        'web_search': '🔍',
        'browse_url': '🌐',
        'scrape_page': '📄',
        'web_browse': '🖥️'
    };
    return icons[tool] || '🌐';
}

function truncate(str, maxLen) {
    if (!str) return '';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function formatTime(date) {
    if (!date) return '';
    return new Date(date).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' });
}

function highlightBrowserTab() {
    const browserTab = document.querySelector('[data-tab="browser"]');
    if (browserTab && !browserTab.classList.contains('active')) {
        browserTab.classList.add('has-activity');
        setTimeout(() => browserTab.classList.remove('has-activity'), 3000);
    }
}

export function showBrowserEntry(entryId) {
    const entry = browserHistory.find(e => e.id === entryId);
    if (entry) {
        // Entry'yi en üste taşı
        const index = browserHistory.indexOf(entry);
        if (index > 0) {
            browserHistory.splice(index, 1);
            browserHistory.unshift(entry);
        }
        renderBrowserPanel();
    }
}

export function clearBrowserHistory() {
    browserHistory.length = 0;
    activePage = null;
    renderBrowserPanel();
}

export function getBrowserHistory() {
    return [...browserHistory];
}
