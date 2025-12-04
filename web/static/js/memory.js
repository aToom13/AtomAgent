/**
 * AtomAgent - Memory Management System
 * Kalıcı hafıza ve kullanıcı tercihleri
 */

import { state } from './state.js';

// Memory state
state.memories = [];
state.memoryTags = new Set();

/**
 * Hafıza ekle
 */
export function addMemory(memory) {
    const newMemory = {
        id: memory.id || `mem_${Date.now()}`,
        title: memory.title,
        content: memory.content,
        tags: memory.tags || [],
        type: memory.type || 'general', // user_preference, project_info, learned, context
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
    };
    
    state.memories.unshift(newMemory);
    memory.tags.forEach(tag => state.memoryTags.add(tag));
    
    renderMemoryPanel();
    showMemoryNotification('added', newMemory.title);
    
    return newMemory;
}

/**
 * Hafıza güncelle
 */
export function updateMemory(memoryId, updates) {
    const memory = state.memories.find(m => m.id === memoryId);
    if (memory) {
        Object.assign(memory, updates, { updatedAt: new Date().toISOString() });
        if (updates.tags) {
            updates.tags.forEach(tag => state.memoryTags.add(tag));
        }
        renderMemoryPanel();
    }
    return memory;
}

/**
 * Hafıza sil
 */
export function deleteMemory(memoryId) {
    const index = state.memories.findIndex(m => m.id === memoryId);
    if (index !== -1) {
        state.memories.splice(index, 1);
        renderMemoryPanel();
    }
}

/**
 * Hafızada ara
 */
export function searchMemories(query, tags = []) {
    let results = state.memories;
    
    if (query) {
        const lowerQuery = query.toLowerCase();
        results = results.filter(m => 
            m.title.toLowerCase().includes(lowerQuery) ||
            m.content.toLowerCase().includes(lowerQuery)
        );
    }
    
    if (tags.length > 0) {
        results = results.filter(m => 
            tags.some(tag => m.tags.includes(tag))
        );
    }
    
    return results;
}

/**
 * Memory panelini render et
 */
export function renderMemoryPanel() {
    const container = document.getElementById('memory-panel');
    if (!container) return;
    
    const typeIcons = {
        user_preference: '👤',
        project_info: '📁',
        learned: '💡',
        context: '📝',
        general: '🧠'
    };
    
    let html = `
        <div class="memory-header">
            <div class="memory-title">
                <span class="memory-icon">🧠</span>
                <span>Hafıza</span>
                <span class="memory-count">${state.memories.length}</span>
            </div>
            <button class="icon-btn small" onclick="window.AtomAgent.openAddMemoryModal()" title="Hafıza Ekle">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 5v14M5 12h14"/>
                </svg>
            </button>
        </div>
        
        <div class="memory-search">
            <input type="text" id="memory-search-input" placeholder="Hafızada ara..." oninput="window.AtomAgent.filterMemories()">
        </div>
        
        <div class="memory-tags">
            ${Array.from(state.memoryTags).map(tag => `
                <button class="memory-tag" data-tag="${tag}" onclick="window.AtomAgent.toggleMemoryTag('${tag}')">
                    ${tag}
                </button>
            `).join('')}
        </div>
        
        <div class="memory-list">
    `;
    
    if (state.memories.length === 0) {
        html += `
            <div class="memory-empty">
                <div class="memory-empty-icon">🧠</div>
                <p>Hafıza boş</p>
                <p class="memory-hint">Agent önemli bilgileri burada saklayacak</p>
            </div>
        `;
    } else {
        for (const memory of state.memories) {
            html += `
                <div class="memory-item" data-id="${memory.id}">
                    <div class="memory-item-header">
                        <span class="memory-type-icon">${typeIcons[memory.type] || '🧠'}</span>
                        <span class="memory-item-title">${escapeHtml(memory.title)}</span>
                        <button class="memory-delete-btn" onclick="window.AtomAgent.deleteMemory('${memory.id}')" title="Sil">×</button>
                    </div>
                    <div class="memory-item-content">${escapeHtml(memory.content)}</div>
                    ${memory.tags.length > 0 ? `
                        <div class="memory-item-tags">
                            ${memory.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
}

/**
 * Hafıza filtreleme
 */
export function filterMemories() {
    const query = document.getElementById('memory-search-input')?.value || '';
    const activeTags = Array.from(document.querySelectorAll('.memory-tag.active')).map(el => el.dataset.tag);
    
    const results = searchMemories(query, activeTags);
    
    document.querySelectorAll('.memory-item').forEach(el => {
        const memoryId = el.dataset.id;
        const isVisible = results.some(m => m.id === memoryId);
        el.style.display = isVisible ? 'block' : 'none';
    });
}

/**
 * Tag toggle
 */
export function toggleMemoryTag(tag) {
    const btn = document.querySelector(`.memory-tag[data-tag="${tag}"]`);
    if (btn) {
        btn.classList.toggle('active');
        filterMemories();
    }
}

/**
 * Hafıza ekleme modalı
 */
export function openAddMemoryModal() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'add-memory-modal';
    modal.innerHTML = `
        <div class="modal-backdrop" onclick="window.AtomAgent.closeAddMemoryModal()"></div>
        <div class="modal-content small-modal">
            <div class="modal-header">
                <h3>🧠 Hafıza Ekle</h3>
                <button class="icon-btn" onclick="window.AtomAgent.closeAddMemoryModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Başlık</label>
                    <input type="text" id="new-memory-title" placeholder="Hafıza başlığı">
                </div>
                <div class="form-group">
                    <label>İçerik</label>
                    <textarea id="new-memory-content" rows="4" placeholder="Hafıza içeriği"></textarea>
                </div>
                <div class="form-group">
                    <label>Etiketler (virgülle ayır)</label>
                    <input type="text" id="new-memory-tags" placeholder="user, preference, project">
                </div>
                <div class="form-group">
                    <label>Tür</label>
                    <select id="new-memory-type">
                        <option value="general">Genel</option>
                        <option value="user_preference">Kullanıcı Tercihi</option>
                        <option value="project_info">Proje Bilgisi</option>
                        <option value="learned">Öğrenilen</option>
                        <option value="context">Bağlam</option>
                    </select>
                </div>
            </div>
            <div class="modal-footer">
                <button class="small-btn" onclick="window.AtomAgent.closeAddMemoryModal()">İptal</button>
                <button class="small-btn primary" onclick="window.AtomAgent.saveNewMemory()">Kaydet</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

/**
 * Modal kapat
 */
export function closeAddMemoryModal() {
    document.getElementById('add-memory-modal')?.remove();
}

/**
 * Yeni hafıza kaydet
 */
export function saveNewMemory() {
    const title = document.getElementById('new-memory-title')?.value.trim();
    const content = document.getElementById('new-memory-content')?.value.trim();
    const tagsStr = document.getElementById('new-memory-tags')?.value.trim();
    const type = document.getElementById('new-memory-type')?.value;
    
    if (!title || !content) {
        alert('Başlık ve içerik gerekli');
        return;
    }
    
    const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(t => t) : [];
    
    addMemory({ title, content, tags, type });
    closeAddMemoryModal();
}

/**
 * Bildirim göster
 */
function showMemoryNotification(action, title) {
    const notification = document.createElement('div');
    notification.className = 'memory-notification';
    notification.innerHTML = `
        <span class="memory-icon">🧠</span>
        <span>Hafıza ${action === 'added' ? 'eklendi' : 'güncellendi'}: ${title}</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

/**
 * WebSocket'ten gelen memory güncellemelerini işle
 */
export function handleMemoryUpdate(data) {
    switch (data.action) {
        case 'add':
            addMemory(data.memory);
            break;
        case 'update':
            updateMemory(data.memoryId, data.updates);
            break;
        case 'delete':
            deleteMemory(data.memoryId);
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
    deleteMemory,
    filterMemories,
    toggleMemoryTag,
    openAddMemoryModal,
    closeAddMemoryModal,
    saveNewMemory
});
