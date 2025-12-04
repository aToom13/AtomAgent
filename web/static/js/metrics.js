/**
 * AtomAgent - Metrics & Progress Panel
 * Real-time metrikler ve ilerleme takibi
 */

import { state } from './state.js';

// Metrics state
state.metrics = {
    tokensUsed: 0,
    tokensLimit: 200000,
    sessionDuration: 0,
    messagesCount: 0,
    toolCalls: 0,
    successRate: 100,
    errors: 0,
    startTime: null
};

let metricsInterval = null;

/**
 * Metrikleri başlat
 */
export function initMetrics() {
    state.metrics.startTime = Date.now();
    startDurationTimer();
    renderMetricsPanel();
}

/**
 * Süre sayacını başlat
 */
function startDurationTimer() {
    if (metricsInterval) clearInterval(metricsInterval);
    
    metricsInterval = setInterval(() => {
        if (state.metrics.startTime) {
            state.metrics.sessionDuration = Math.floor((Date.now() - state.metrics.startTime) / 1000);
            updateDurationDisplay();
        }
    }, 1000);
}

/**
 * Token kullanımını güncelle
 */
export function updateTokenUsage(used, limit = 200000) {
    state.metrics.tokensUsed = used;
    state.metrics.tokensLimit = limit;
    updateTokenDisplay();
}

/**
 * Mesaj sayısını artır
 */
export function incrementMessages() {
    state.metrics.messagesCount++;
    renderMetricsPanel();
}

/**
 * Tool çağrısı sayısını artır
 */
export function incrementToolCalls() {
    state.metrics.toolCalls++;
    renderMetricsPanel();
}

/**
 * Hata sayısını artır
 */
export function incrementErrors() {
    state.metrics.errors++;
    updateSuccessRate();
    renderMetricsPanel();
}

/**
 * Başarı oranını güncelle
 */
function updateSuccessRate() {
    const total = state.metrics.toolCalls + state.metrics.messagesCount;
    if (total > 0) {
        state.metrics.successRate = Math.round(((total - state.metrics.errors) / total) * 100);
    }
}

/**
 * Metrics panelini render et
 */
export function renderMetricsPanel() {
    const container = document.getElementById('metrics-panel');
    if (!container) return;
    
    const { tokensUsed, tokensLimit, sessionDuration, messagesCount, toolCalls, successRate } = state.metrics;
    const tokenPercent = Math.round((tokensUsed / tokensLimit) * 100);
    const tokenColor = tokenPercent > 80 ? 'var(--accent-error)' : tokenPercent > 60 ? 'var(--accent-warning)' : 'var(--accent-success)';
    
    container.innerHTML = `
        <div class="metrics-header">
            <span class="metrics-icon">📊</span>
            <span>Metrikler</span>
        </div>
        
        <div class="metrics-grid">
            <!-- Token Usage -->
            <div class="metric-card">
                <div class="metric-label">Token Kullanımı</div>
                <div class="metric-value">
                    <span class="metric-number">${formatNumber(tokensUsed)}</span>
                    <span class="metric-unit">/ ${formatNumber(tokensLimit)}</span>
                </div>
                <div class="metric-bar">
                    <div class="metric-bar-fill" style="width: ${tokenPercent}%; background: ${tokenColor}"></div>
                </div>
            </div>
            
            <!-- Session Duration -->
            <div class="metric-card">
                <div class="metric-label">Süre</div>
                <div class="metric-value">
                    <span class="metric-number" id="duration-display">${formatDuration(sessionDuration)}</span>
                </div>
            </div>
            
            <!-- Messages -->
            <div class="metric-card">
                <div class="metric-label">Mesajlar</div>
                <div class="metric-value">
                    <span class="metric-number">${messagesCount}</span>
                </div>
            </div>
            
            <!-- Tool Calls -->
            <div class="metric-card">
                <div class="metric-label">Tool Çağrıları</div>
                <div class="metric-value">
                    <span class="metric-number">${toolCalls}</span>
                </div>
            </div>
            
            <!-- Success Rate -->
            <div class="metric-card full-width">
                <div class="metric-label">Başarı Oranı</div>
                <div class="metric-value">
                    <span class="metric-number success">${successRate}%</span>
                </div>
                <div class="metric-bar">
                    <div class="metric-bar-fill success" style="width: ${successRate}%"></div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Sadece süre gösterimini güncelle
 */
function updateDurationDisplay() {
    const el = document.getElementById('duration-display');
    if (el) {
        el.textContent = formatDuration(state.metrics.sessionDuration);
    }
}

/**
 * Sadece token gösterimini güncelle
 */
function updateTokenDisplay() {
    const container = document.getElementById('metrics-panel');
    if (!container) return;
    
    const tokenCard = container.querySelector('.metric-card:first-child');
    if (tokenCard) {
        const { tokensUsed, tokensLimit } = state.metrics;
        const tokenPercent = Math.round((tokensUsed / tokensLimit) * 100);
        const tokenColor = tokenPercent > 80 ? 'var(--accent-error)' : tokenPercent > 60 ? 'var(--accent-warning)' : 'var(--accent-success)';
        
        tokenCard.querySelector('.metric-number').textContent = formatNumber(tokensUsed);
        tokenCard.querySelector('.metric-bar-fill').style.width = `${tokenPercent}%`;
        tokenCard.querySelector('.metric-bar-fill').style.background = tokenColor;
    }
}

/**
 * Compact metrics bar (header için)
 */
export function renderCompactMetrics() {
    const container = document.getElementById('compact-metrics');
    if (!container) return;
    
    const { tokensUsed, tokensLimit, sessionDuration } = state.metrics;
    const tokenPercent = Math.round((tokensUsed / tokensLimit) * 100);
    
    container.innerHTML = `
        <div class="compact-metric">
            <span class="compact-icon">🔤</span>
            <span class="compact-value">${formatNumber(tokensUsed)}</span>
            <div class="compact-bar">
                <div class="compact-bar-fill" style="width: ${tokenPercent}%"></div>
            </div>
        </div>
        <div class="compact-metric">
            <span class="compact-icon">⏱️</span>
            <span class="compact-value" id="compact-duration">${formatDuration(sessionDuration)}</span>
        </div>
    `;
}

/**
 * Sayı formatla
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

/**
 * Süre formatla
 */
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Metrikleri sıfırla
 */
export function resetMetrics() {
    state.metrics = {
        tokensUsed: 0,
        tokensLimit: 200000,
        sessionDuration: 0,
        messagesCount: 0,
        toolCalls: 0,
        successRate: 100,
        errors: 0,
        startTime: Date.now()
    };
    renderMetricsPanel();
    renderCompactMetrics();
}

/**
 * WebSocket'ten gelen metric güncellemelerini işle
 */
export function handleMetricsUpdate(data) {
    if (data.tokens) {
        updateTokenUsage(data.tokens.used, data.tokens.limit);
    }
    if (data.toolCall) {
        incrementToolCalls();
    }
    if (data.error) {
        incrementErrors();
    }
}

// Export for window
window.AtomAgent = window.AtomAgent || {};
Object.assign(window.AtomAgent, {
    resetMetrics
});
