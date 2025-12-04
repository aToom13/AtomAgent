/**
 * AtomAgent - Todo/Task Management System
 * Real-time görev takibi
 */

import { state } from './state.js';

// Todo state
state.todos = [];
state.todoStats = { total: 0, completed: 0, inProgress: 0, pending: 0 };

/**
 * Todo ekle
 */
export function addTodo(todo) {
    const newTodo = {
        id: todo.id || `todo_${Date.now()}`,
        title: todo.title,
        description: todo.description || '',
        status: todo.status || 'pending', // pending, in_progress, completed
        priority: todo.priority || 'medium', // low, medium, high, critical
        parentId: todo.parentId || null,
        children: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    
    if (newTodo.parentId) {
        // Alt görev olarak ekle
        const parent = findTodo(newTodo.parentId);
        if (parent) {
            parent.children.push(newTodo);
        }
    } else {
        state.todos.push(newTodo);
    }
    
    updateTodoStats();
    renderTodosPanel();
    return newTodo;
}

/**
 * Todo güncelle
 */
export function updateTodo(todoId, updates) {
    const todo = findTodo(todoId);
    if (todo) {
        Object.assign(todo, updates, { updatedAt: new Date().toISOString() });
        updateTodoStats();
        renderTodosPanel();
        
        // Animasyon için
        if (updates.status === 'completed') {
            animateTodoComplete(todoId);
        }
    }
    return todo;
}

/**
 * Todo durumunu değiştir
 */
export function setTodoStatus(todoId, status) {
    return updateTodo(todoId, { status });
}

/**
 * Todo sil
 */
export function deleteTodo(todoId) {
    // Ana listeden sil
    const index = state.todos.findIndex(t => t.id === todoId);
    if (index !== -1) {
        state.todos.splice(index, 1);
    } else {
        // Alt görevlerden sil
        for (const todo of state.todos) {
            const childIndex = todo.children.findIndex(c => c.id === todoId);
            if (childIndex !== -1) {
                todo.children.splice(childIndex, 1);
                break;
            }
        }
    }
    
    updateTodoStats();
    renderTodosPanel();
}

/**
 * Todo bul (recursive)
 */
function findTodo(todoId, todos = state.todos) {
    for (const todo of todos) {
        if (todo.id === todoId) return todo;
        if (todo.children.length > 0) {
            const found = findTodo(todoId, todo.children);
            if (found) return found;
        }
    }
    return null;
}

/**
 * İstatistikleri güncelle
 */
function updateTodoStats() {
    const stats = { total: 0, completed: 0, inProgress: 0, pending: 0 };
    
    function countTodos(todos) {
        for (const todo of todos) {
            stats.total++;
            stats[todo.status === 'in_progress' ? 'inProgress' : todo.status]++;
            if (todo.children.length > 0) {
                countTodos(todo.children);
            }
        }
    }
    
    countTodos(state.todos);
    state.todoStats = stats;
}

/**
 * Todos panelini render et
 */
export function renderTodosPanel() {
    const container = document.getElementById('todos-panel');
    if (!container) return;
    
    const { total, completed, inProgress, pending } = state.todoStats;
    const progress = total > 0 ? Math.round((completed / total) * 100) : 0;
    
    let html = `
        <div class="todos-header">
            <div class="todos-title">
                <span class="todos-icon">📋</span>
                <span>Görevler</span>
                <span class="todos-count">${completed}/${total}</span>
            </div>
            <div class="todos-actions">
                <button class="icon-btn small" onclick="window.AtomAgent.clearCompletedTodos()" title="Tamamlananları Temizle">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        </div>
        
        <div class="todos-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
            <div class="progress-stats">
                <span class="stat pending"><span class="dot"></span> ${pending} bekliyor</span>
                <span class="stat in-progress"><span class="dot"></span> ${inProgress} devam</span>
                <span class="stat completed"><span class="dot"></span> ${completed} tamamlandı</span>
            </div>
        </div>
        
        <div class="todos-list">
    `;
    
    if (state.todos.length === 0) {
        html += `
            <div class="todos-empty">
                <div class="todos-empty-icon">✨</div>
                <p>Henüz görev yok</p>
                <p class="todos-hint">Agent çalışmaya başladığında görevler burada görünecek</p>
            </div>
        `;
    } else {
        html += renderTodoItems(state.todos);
    }
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Todo item'larını render et (recursive)
 */
function renderTodoItems(todos, level = 0) {
    let html = '';
    
    for (const todo of todos) {
        const statusIcon = getStatusIcon(todo.status);
        const priorityClass = `priority-${todo.priority}`;
        const hasChildren = todo.children.length > 0;
        
        html += `
            <div class="todo-item ${todo.status} ${priorityClass}" 
                 data-id="${todo.id}" 
                 style="--level: ${level}">
                <div class="todo-main">
                    <button class="todo-status-btn" onclick="window.AtomAgent.cycleTodoStatus('${todo.id}')">
                        ${statusIcon}
                    </button>
                    <div class="todo-content">
                        <span class="todo-title">${escapeHtml(todo.title)}</span>
                        ${todo.description ? `<span class="todo-desc">${escapeHtml(todo.description)}</span>` : ''}
                    </div>
                    ${hasChildren ? `
                        <button class="todo-expand-btn" onclick="window.AtomAgent.toggleTodoChildren('${todo.id}')">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="6 9 12 15 18 9"/>
                            </svg>
                        </button>
                    ` : ''}
                </div>
                ${hasChildren ? `
                    <div class="todo-children" id="children-${todo.id}">
                        ${renderTodoItems(todo.children, level + 1)}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    return html;
}

/**
 * Durum ikonunu al
 */
function getStatusIcon(status) {
    switch (status) {
        case 'completed':
            return '<svg class="status-icon completed" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
        case 'in_progress':
            return '<svg class="status-icon in-progress" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
        default:
            return '<svg class="status-icon pending" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>';
    }
}

/**
 * Durum döngüsü
 */
export function cycleTodoStatus(todoId) {
    const todo = findTodo(todoId);
    if (!todo) return;
    
    const statusOrder = ['pending', 'in_progress', 'completed'];
    const currentIndex = statusOrder.indexOf(todo.status);
    const nextStatus = statusOrder[(currentIndex + 1) % statusOrder.length];
    
    setTodoStatus(todoId, nextStatus);
}

/**
 * Alt görevleri aç/kapat
 */
export function toggleTodoChildren(todoId) {
    const children = document.getElementById(`children-${todoId}`);
    if (children) {
        children.classList.toggle('collapsed');
    }
}

/**
 * Tamamlananları temizle
 */
export function clearCompletedTodos() {
    state.todos = state.todos.filter(t => t.status !== 'completed');
    // Alt görevleri de temizle
    for (const todo of state.todos) {
        todo.children = todo.children.filter(c => c.status !== 'completed');
    }
    updateTodoStats();
    renderTodosPanel();
}

/**
 * Tüm görevleri temizle
 */
export function clearAllTodos() {
    state.todos = [];
    updateTodoStats();
    renderTodosPanel();
}

/**
 * Tamamlama animasyonu
 */
function animateTodoComplete(todoId) {
    const element = document.querySelector(`.todo-item[data-id="${todoId}"]`);
    if (element) {
        element.classList.add('completing');
        setTimeout(() => element.classList.remove('completing'), 500);
    }
}

/**
 * WebSocket'ten gelen todo güncellemelerini işle
 */
export function handleTodoUpdate(data) {
    switch (data.action) {
        case 'add':
            addTodo(data.todo);
            break;
        case 'update':
            updateTodo(data.todoId, data.updates);
            break;
        case 'status':
            setTodoStatus(data.todoId, data.status);
            break;
        case 'delete':
            deleteTodo(data.todoId);
            break;
        case 'clear':
            clearAllTodos();
            break;
    }
}

/**
 * HTML escape
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export for window
window.AtomAgent = window.AtomAgent || {};
Object.assign(window.AtomAgent, {
    cycleTodoStatus,
    toggleTodoChildren,
    clearCompletedTodos,
    clearAllTodos
});
