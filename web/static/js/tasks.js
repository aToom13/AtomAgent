/**
 * AtomAgent - Tasks Panel
 * Görev takibi ve yönetimi
 */

import { escapeHtml, formatDate } from './utils.js';

// Görev listesi
const tasks = [];
let taskIdCounter = 0;

// Görev durumları
const TASK_STATUS = {
    pending: { label: 'Bekliyor', icon: '⏳', color: 'warning' },
    running: { label: 'Çalışıyor', icon: '🔄', color: 'primary' },
    completed: { label: 'Tamamlandı', icon: '✅', color: 'success' },
    failed: { label: 'Başarısız', icon: '❌', color: 'error' },
    cancelled: { label: 'İptal', icon: '🚫', color: 'muted' }
};

export function createTask(title, description = '') {
    const task = {
        id: ++taskIdCounter,
        title: title,
        description: description,
        status: 'pending',
        progress: 0,
        steps: [],
        createdAt: new Date(),
        startedAt: null,
        completedAt: null,
        error: null
    };
    
    tasks.unshift(task);
    renderTasksPanel();
    
    return task.id;
}

export function updateTaskStatus(taskId, status, progress = null) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    task.status = status;
    
    if (progress !== null) {
        task.progress = Math.min(100, Math.max(0, progress));
    }
    
    if (status === 'running' && !task.startedAt) {
        task.startedAt = new Date();
    }
    
    if (status === 'completed' || status === 'failed') {
        task.completedAt = new Date();
        task.progress = status === 'completed' ? 100 : task.progress;
    }
    
    renderTasksPanel();
}

export function addTaskStep(taskId, step) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    task.steps.push({
        text: step,
        timestamp: new Date()
    });
    
    renderTasksPanel();
}

export function setTaskError(taskId, error) {
    const task = tasks.find(t => t.id === taskId);
    if (!task) return;
    
    task.error = error;
    task.status = 'failed';
    task.completedAt = new Date();
    
    renderTasksPanel();
}

export function renderTasksPanel() {
    const container = document.getElementById('tasks-list');
    if (!container) return;
    
    if (tasks.length === 0) {
        container.innerHTML = `
            <div class="tasks-empty">
                <div class="tasks-empty-icon">📋</div>
                <p>Aktif görev yok</p>
                <p class="tasks-hint">Agent'a bir görev verdiğinizde burada takip edebilirsiniz</p>
            </div>
        `;
        return;
    }
    
    // İstatistikler
    const stats = getTaskStats();
    
    container.innerHTML = `
        <div class="tasks-stats">
            <div class="stat-item">
                <span class="stat-value">${stats.total}</span>
                <span class="stat-label">Toplam</span>
            </div>
            <div class="stat-item running">
                <span class="stat-value">${stats.running}</span>
                <span class="stat-label">Çalışıyor</span>
            </div>
            <div class="stat-item completed">
                <span class="stat-value">${stats.completed}</span>
                <span class="stat-label">Tamamlandı</span>
            </div>
        </div>
        
        <div class="tasks-list-items">
            ${tasks.map(task => renderTaskItem(task)).join('')}
        </div>
        
        ${tasks.length > 0 ? `
            <div class="tasks-actions">
                <button class="small-btn" onclick="window.AtomAgent.clearCompletedTasks()">
                    Tamamlananları Temizle
                </button>
            </div>
        ` : ''}
    `;
}

function renderTaskItem(task) {
    const status = TASK_STATUS[task.status];
    const duration = task.startedAt ? formatDuration(task.completedAt || new Date(), task.startedAt) : '';
    
    return `
        <div class="task-item ${task.status}" data-id="${task.id}">
            <div class="task-header">
                <span class="task-status-icon">${status.icon}</span>
                <span class="task-title">${escapeHtml(task.title)}</span>
                <span class="task-time">${duration}</span>
            </div>
            
            ${task.description ? `
                <div class="task-description">${escapeHtml(task.description)}</div>
            ` : ''}
            
            ${task.status === 'running' ? `
                <div class="task-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${task.progress}%"></div>
                    </div>
                    <span class="progress-text">${task.progress}%</span>
                </div>
            ` : ''}
            
            ${task.steps.length > 0 ? `
                <div class="task-steps">
                    ${task.steps.slice(-3).map(step => `
                        <div class="task-step">
                            <span class="step-time">${formatTime(step.timestamp)}</span>
                            <span class="step-text">${escapeHtml(step.text)}</span>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${task.error ? `
                <div class="task-error">
                    <span class="error-icon">⚠️</span>
                    <span class="error-text">${escapeHtml(task.error)}</span>
                </div>
            ` : ''}
        </div>
    `;
}

function getTaskStats() {
    return {
        total: tasks.length,
        pending: tasks.filter(t => t.status === 'pending').length,
        running: tasks.filter(t => t.status === 'running').length,
        completed: tasks.filter(t => t.status === 'completed').length,
        failed: tasks.filter(t => t.status === 'failed').length
    };
}

function formatDuration(end, start) {
    const ms = new Date(end) - new Date(start);
    if (ms < 1000) return '<1s';
    if (ms < 60000) return `${Math.floor(ms / 1000)}s`;
    if (ms < 3600000) return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`;
    return `${Math.floor(ms / 3600000)}h ${Math.floor((ms % 3600000) / 60000)}m`;
}

function formatTime(date) {
    return new Date(date).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function clearCompletedTasks() {
    const remaining = tasks.filter(t => t.status === 'running' || t.status === 'pending');
    tasks.length = 0;
    tasks.push(...remaining);
    renderTasksPanel();
}

export function clearAllTasks() {
    tasks.length = 0;
    renderTasksPanel();
}

export function getActiveTasks() {
    return tasks.filter(t => t.status === 'running' || t.status === 'pending');
}

export function getTasks() {
    return [...tasks];
}

// Mesajdan otomatik görev oluştur
export function createTaskFromMessage(message) {
    // Basit görev tespiti
    const taskPatterns = [
        /(?:yap|oluştur|ekle|düzenle|sil|güncelle|kur|başlat|durdur)\s+(.+)/i,
        /(.+)\s+(?:yap|oluştur|ekle)/i
    ];
    
    for (const pattern of taskPatterns) {
        const match = message.match(pattern);
        if (match) {
            return createTask(match[1].substring(0, 50), message);
        }
    }
    
    // Genel görev
    return createTask(message.substring(0, 50), message);
}
