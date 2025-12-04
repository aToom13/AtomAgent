/**
 * AtomAgent - Tasks Panel
 * Görev takibi ve yönetimi - Todo entegrasyonu
 */

import { escapeHtml, formatDate } from './utils.js';

// Görev listesi
const tasks = [];
let taskIdCounter = 0;

// Todo items from agent
let todoItems = [];

// Görev durumları
const TASK_STATUS = {
    pending: { label: 'Bekliyor', icon: '⏳', color: 'warning' },
    running: { label: 'Çalışıyor', icon: '🔄', color: 'primary' },
    completed: { label: 'Tamamlandı', icon: '✅', color: 'success' },
    failed: { label: 'Başarısız', icon: '❌', color: 'error' },
    cancelled: { label: 'İptal', icon: '🚫', color: 'muted' }
};

// Todo tool'larından gelen verileri işle
export function handleTodoUpdate(toolName, output) {
    if (toolName === 'update_todo_list' || toolName === 'get_current_todo') {
        parseTodoContent(output);
    } else if (toolName === 'mark_todo_done') {
        // Bir adım tamamlandı - todo'yu güncelle
        if (output.includes('✓')) {
            const match = output.match(/Tamamlandı:\s*(.+)/);
            if (match) {
                markTodoItemDone(match[1]);
            }
        }
    } else if (toolName === 'add_todo_item') {
        // Yeni todo eklendi
        parseTodoContent(output);
    }
    renderTasksPanel();
}

function parseTodoContent(content) {
    if (!content) return;
    
    // Markdown todo formatını parse et
    const lines = content.split('\n');
    todoItems = [];
    
    for (const line of lines) {
        const trimmed = line.trim();
        
        // "- [ ] Task" veya "- [x] Task" formatı
        const todoMatch = trimmed.match(/^-\s*\[([ x])\]\s*(.+)$/i);
        if (todoMatch) {
            todoItems.push({
                id: todoItems.length + 1,
                text: todoMatch[2].trim(),
                completed: todoMatch[1].toLowerCase() === 'x',
                timestamp: new Date()
            });
        }
    }
}

function markTodoItemDone(text) {
    const item = todoItems.find(t => t.text.toLowerCase().includes(text.toLowerCase()));
    if (item) {
        item.completed = true;
    }
}

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
    
    const hasTodos = todoItems.length > 0;
    const hasTasks = tasks.length > 0;
    
    if (!hasTodos && !hasTasks) {
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
    const todoStats = getTodoStats();
    const taskStats = getTaskStats();
    
    let html = '';
    
    // Todo listesi varsa göster
    if (hasTodos) {
        html += `
            <div class="todo-section">
                <div class="section-header">
                    <h4>📝 Todo Listesi</h4>
                    <span class="todo-progress">${todoStats.completed}/${todoStats.total}</span>
                </div>
                <div class="todo-progress-bar">
                    <div class="progress-fill" style="width: ${todoStats.percent}%"></div>
                </div>
                <div class="todo-items">
                    ${todoItems.map(item => renderTodoItem(item)).join('')}
                </div>
            </div>
        `;
    }
    
    // Task listesi varsa göster
    if (hasTasks) {
        html += `
            <div class="tasks-section">
                <div class="section-header">
                    <h4>🔧 Aktif Görevler</h4>
                </div>
                <div class="tasks-stats">
                    <div class="stat-item">
                        <span class="stat-value">${taskStats.total}</span>
                        <span class="stat-label">Toplam</span>
                    </div>
                    <div class="stat-item running">
                        <span class="stat-value">${taskStats.running}</span>
                        <span class="stat-label">Çalışıyor</span>
                    </div>
                    <div class="stat-item completed">
                        <span class="stat-value">${taskStats.completed}</span>
                        <span class="stat-label">Tamamlandı</span>
                    </div>
                </div>
                <div class="tasks-list-items">
                    ${tasks.map(task => renderTaskItem(task)).join('')}
                </div>
            </div>
        `;
    }
    
    // Temizle butonu
    if (hasTodos || hasTasks) {
        html += `
            <div class="tasks-actions">
                <button class="small-btn" onclick="window.AtomAgent.clearCompletedTasks()">
                    Tamamlananları Temizle
                </button>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function renderTodoItem(item) {
    const statusClass = item.completed ? 'completed' : 'pending';
    const icon = item.completed ? '✅' : '⬜';
    
    return `
        <div class="todo-item ${statusClass}">
            <span class="todo-checkbox">${icon}</span>
            <span class="todo-text">${escapeHtml(item.text)}</span>
        </div>
    `;
}

function getTodoStats() {
    const total = todoItems.length;
    const completed = todoItems.filter(t => t.completed).length;
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { total, completed, percent };
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
