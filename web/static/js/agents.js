/**
 * AtomAgent - Agent Management System
 * Otomatik agent routing ve manuel seçim
 */

import { state } from './state.js';

// Agent tanımları
export const AGENTS = {
    supervisor: {
        id: 'supervisor',
        name: 'Supervisor',
        icon: '🎯',
        color: '#3b82f6',
        description: 'Master koordinatör - tüm agent\'ları yönetir',
        keywords: ['planla', 'organize', 'yönet', 'koordine', 'proje', 'genel'],
        isDefault: true
    },
    coder: {
        id: 'coder',
        name: 'Coder',
        icon: '👨‍💻',
        color: '#22c55e',
        description: 'Kod geliştirme uzmanı',
        keywords: ['kod', 'yaz', 'fonksiyon', 'class', 'bug', 'fix', 'refactor', 'implement', 'geliştir', 'oluştur', 'ekle', 'düzelt', 'python', 'javascript', 'react', 'api']
    },
    researcher: {
        id: 'researcher',
        name: 'Researcher',
        icon: '🔍',
        color: '#f59e0b',
        description: 'Araştırma ve bilgi toplama',
        keywords: ['araştır', 'bul', 'ara', 'öğren', 'nedir', 'nasıl', 'karşılaştır', 'analiz', 'dokümantasyon', 'best practice']
    },
    devops: {
        id: 'devops',
        name: 'DevOps',
        icon: '🚀',
        color: '#8b5cf6',
        description: 'CI/CD, deployment, altyapı',
        keywords: ['deploy', 'docker', 'kubernetes', 'ci/cd', 'pipeline', 'server', 'aws', 'cloud', 'nginx', 'terraform']
    },
    qa: {
        id: 'qa',
        name: 'QA',
        icon: '🧪',
        color: '#ec4899',
        description: 'Test ve kalite güvencesi',
        keywords: ['test', 'pytest', 'jest', 'unit test', 'integration', 'coverage', 'bug', 'hata', 'kalite']
    },
    security: {
        id: 'security',
        name: 'Security',
        icon: '🔒',
        color: '#ef4444',
        description: 'Güvenlik analizi ve denetimi',
        keywords: ['güvenlik', 'security', 'vulnerability', 'owasp', 'authentication', 'authorization', 'şifre', 'token', 'jwt']
    },
    uiux: {
        id: 'uiux',
        name: 'UI/UX',
        icon: '🎨',
        color: '#06b6d4',
        description: 'Arayüz tasarımı ve kullanıcı deneyimi',
        keywords: ['tasarım', 'design', 'ui', 'ux', 'css', 'style', 'responsive', 'component', 'button', 'form', 'layout']
    },
    data: {
        id: 'data',
        name: 'Data',
        icon: '📊',
        color: '#14b8a6',
        description: 'Veri analizi ve ML',
        keywords: ['veri', 'data', 'analiz', 'ml', 'machine learning', 'pandas', 'numpy', 'grafik', 'chart', 'visualization']
    },
    api: {
        id: 'api',
        name: 'API',
        icon: '🔌',
        color: '#f97316',
        description: 'API tasarımı ve entegrasyon',
        keywords: ['api', 'rest', 'graphql', 'endpoint', 'swagger', 'openapi', 'entegrasyon', 'webhook']
    }
};

// Aktif agent
state.activeAgent = 'supervisor';
state.autoRouting = true;

/**
 * Mesaja göre en uygun agent'ı belirle
 */
export function detectAgent(message) {
    if (!state.autoRouting) {
        return state.activeAgent;
    }
    
    const lowerMessage = message.toLowerCase();
    let bestMatch = { agent: 'supervisor', score: 0 };
    
    for (const [agentId, agent] of Object.entries(AGENTS)) {
        if (agent.isDefault) continue;
        
        let score = 0;
        for (const keyword of agent.keywords) {
            if (lowerMessage.includes(keyword.toLowerCase())) {
                score += keyword.length; // Daha uzun keyword = daha spesifik
            }
        }
        
        if (score > bestMatch.score) {
            bestMatch = { agent: agentId, score };
        }
    }
    
    // Minimum skor eşiği
    return bestMatch.score >= 3 ? bestMatch.agent : 'supervisor';
}

/**
 * Agent'ı manuel olarak değiştir
 */
export function setActiveAgent(agentId) {
    if (AGENTS[agentId]) {
        state.activeAgent = agentId;
        state.autoRouting = false;
        updateAgentUI();
        return true;
    }
    return false;
}

/**
 * Otomatik routing'i aç/kapat
 */
export function toggleAutoRouting(enabled = true) {
    state.autoRouting = enabled;
    if (enabled) {
        state.activeAgent = 'supervisor';
    }
    updateAgentUI();
}

/**
 * Agent UI'ını güncelle
 */
export function updateAgentUI() {
    const agent = AGENTS[state.activeAgent];
    
    // Header'daki aktif agent göstergesi
    const indicator = document.getElementById('active-agent-indicator');
    if (indicator) {
        indicator.innerHTML = `
            <span class="agent-icon" style="background: ${agent.color}20; color: ${agent.color}">${agent.icon}</span>
            <span class="agent-name">${agent.name}</span>
            ${state.autoRouting ? '<span class="auto-badge">AUTO</span>' : ''}
            <svg class="dropdown-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
            </svg>
        `;
    }
    
    // Agent dropdown'daki aktif durumu güncelle
    document.querySelectorAll('.agent-dropdown-option').forEach(el => {
        el.classList.toggle('active', el.dataset.agent === state.activeAgent);
    });
    
    // Settings sayfasındaki ayarları güncelle
    const settingsAutoRouting = document.getElementById('settings-auto-routing');
    if (settingsAutoRouting) {
        settingsAutoRouting.checked = state.autoRouting;
    }
    
    const settingsDefaultAgent = document.getElementById('settings-default-agent');
    if (settingsDefaultAgent) {
        settingsDefaultAgent.value = state.activeAgent;
    }
}

/**
 * Agent dropdown menüsünü aç/kapat
 */
export function toggleAgentDropdown() {
    const dropdown = document.getElementById('agent-dropdown');
    if (!dropdown) return;
    
    const isHidden = dropdown.classList.contains('hidden');
    
    if (isHidden) {
        renderAgentDropdown();
        dropdown.classList.remove('hidden');
        
        // Dışarı tıklayınca kapat
        setTimeout(() => {
            document.addEventListener('click', closeAgentDropdownOnClickOutside);
        }, 10);
    } else {
        dropdown.classList.add('hidden');
        document.removeEventListener('click', closeAgentDropdownOnClickOutside);
    }
}

function closeAgentDropdownOnClickOutside(e) {
    const dropdown = document.getElementById('agent-dropdown');
    const indicator = document.getElementById('active-agent-indicator');
    
    if (dropdown && !dropdown.contains(e.target) && !indicator.contains(e.target)) {
        dropdown.classList.add('hidden');
        document.removeEventListener('click', closeAgentDropdownOnClickOutside);
    }
}

/**
 * Agent dropdown menüsünü render et
 */
export function renderAgentDropdown() {
    const dropdown = document.getElementById('agent-dropdown');
    if (!dropdown) return;
    
    let html = `
        <div class="agent-dropdown-header">
            <label class="auto-routing-toggle">
                <input type="checkbox" id="dropdown-auto-routing" ${state.autoRouting ? 'checked' : ''}>
                <span>Otomatik Routing</span>
            </label>
        </div>
        <div class="agent-dropdown-list">
    `;
    
    for (const [agentId, agent] of Object.entries(AGENTS)) {
        html += `
            <button class="agent-dropdown-option ${state.activeAgent === agentId ? 'active' : ''}" 
                    data-agent="${agentId}"
                    style="--agent-color: ${agent.color}">
                <span class="agent-icon">${agent.icon}</span>
                <div class="agent-info">
                    <span class="agent-name">${agent.name}</span>
                    <span class="agent-desc">${agent.description}</span>
                </div>
            </button>
        `;
    }
    
    html += '</div>';
    dropdown.innerHTML = html;
    
    // Event listeners
    dropdown.querySelectorAll('.agent-dropdown-option').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            setActiveAgent(btn.dataset.agent);
            dropdown.classList.add('hidden');
        });
    });
    
    document.getElementById('dropdown-auto-routing')?.addEventListener('change', (e) => {
        e.stopPropagation();
        toggleAutoRouting(e.target.checked);
    });
}

/**
 * Agent seçim panelini render et (artık kullanılmıyor, dropdown kullanılıyor)
 */
export function renderAgentSelector() {
    // Dropdown kullanıldığı için bu fonksiyon artık boş
    // Sadece settings sayfasındaki agent listesini render et
    renderAgentListInSettings();
}

/**
 * Settings sayfasındaki agent listesini render et
 */
export function renderAgentListInSettings() {
    const container = document.getElementById('agent-list');
    if (!container) return;
    
    let html = '';
    
    for (const [agentId, agent] of Object.entries(AGENTS)) {
        html += `
            <div class="agent-list-item" style="--agent-color: ${agent.color}">
                <span class="agent-icon">${agent.icon}</span>
                <div class="agent-info">
                    <span class="agent-name">${agent.name}</span>
                    <span class="agent-desc">${agent.description}</span>
                </div>
                <span class="agent-keywords">${agent.keywords.slice(0, 3).join(', ')}...</span>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

/**
 * Mesaj gönderilmeden önce agent routing yap
 */
export function routeMessage(message) {
    const detectedAgent = detectAgent(message);
    
    if (state.autoRouting && detectedAgent !== state.activeAgent) {
        state.activeAgent = detectedAgent;
        updateAgentUI();
        
        // Kullanıcıya bildir
        showAgentSwitch(detectedAgent);
    }
    
    return state.activeAgent;
}

/**
 * Agent değişikliği bildirimi göster
 */
function showAgentSwitch(agentId) {
    const agent = AGENTS[agentId];
    const notification = document.createElement('div');
    notification.className = 'agent-switch-notification';
    notification.innerHTML = `
        <span class="agent-icon" style="color: ${agent.color}">${agent.icon}</span>
        <span>${agent.name} agent'ına yönlendirildi</span>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

/**
 * Aktif agent bilgisini al
 */
export function getActiveAgent() {
    return AGENTS[state.activeAgent];
}
