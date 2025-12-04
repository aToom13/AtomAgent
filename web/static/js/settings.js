/**
 * AtomAgent - Settings Management
 */

import { state, getElements } from './state.js';
import { escapeHtml, showNotification } from './utils.js';

export async function loadSettings() {
    try {
        const [settingsRes, promptsRes, providersRes] = await Promise.all([
            fetch('/api/settings'),
            fetch('/api/prompts'),
            fetch('/api/providers')
        ]);
        
        state.settings = await settingsRes.json();
        state.prompts = (await promptsRes.json()).prompts;
        state.providers = (await providersRes.json()).providers;
        
        renderModelConfigs();
        renderFallbackConfigs();
        renderCommands();
        renderAPIStatus();
        loadPrompt();
        populateProviderDropdown('new-fallback-provider');
    } catch (error) {
        console.error('Failed to load settings:', error);
    }
}

export function renderModelConfigs() {
    const container = document.getElementById('model-configs');
    if (!container) return;
    
    const role = state.currentModelRole;
    const config = state.settings?.models?.[role] || {};
    
    container.innerHTML = `
        <div class="model-config-single">
            <div class="config-row">
                <label>Provider</label>
                <select id="provider-${role}" onchange="window.AtomAgent.updateModel('${role}')">
                    ${(state.providers || []).map(p => `
                        <option value="${p.id}" ${p.id === config.provider ? 'selected' : ''}>${p.name}</option>
                    `).join('')}
                </select>
            </div>
            <div class="config-row">
                <label>Model</label>
                <input type="text" id="model-${role}" value="${config.model || ''}" 
                       placeholder="Model adı" onchange="window.AtomAgent.updateModel('${role}')">
            </div>
            <div class="config-row">
                <label>Temperature</label>
                <input type="number" id="temp-${role}" value="${config.temperature || 0}" 
                       min="0" max="2" step="0.1" onchange="window.AtomAgent.updateModel('${role}')">
            </div>
            ${config.current_provider ? `
                <div class="current-info">
                    <strong>Aktif:</strong> ${config.current_provider}/${config.current_model || 'N/A'}
                </div>
            ` : ''}
        </div>
    `;
    
    populateProviderDropdown('new-fallback-provider');
}

export function switchModelRole(role) {
    state.currentModelRole = role;
    
    document.querySelectorAll('#model-role-tabs .role-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#model-role-tabs [data-role="${role}"]`)?.classList.add('active');
    
    renderModelConfigs();
}

export function populateProviderDropdown(selectId) {
    const select = document.getElementById(selectId);
    if (select && state.providers) {
        select.innerHTML = state.providers.map(p => 
            `<option value="${p.id}">${p.name}</option>`
        ).join('');
    }
}

export async function updateModel(role) {
    const provider = document.getElementById(`provider-${role}`)?.value;
    const model = document.getElementById(`model-${role}`)?.value;
    const tempInput = document.getElementById(`temp-${role}`);
    const temperature = tempInput ? parseFloat(tempInput.value) : 0;
    
    try {
        await fetch('/api/settings/model', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, provider, model, temperature })
        });
        
        if (state.settings?.models?.[role]) {
            state.settings.models[role].provider = provider;
            state.settings.models[role].model = model;
            state.settings.models[role].temperature = temperature;
        }
        
        showNotification('Model güncellendi');
    } catch (error) {
        console.error('Failed to update model:', error);
        showNotification('Model güncellenemedi', 'error');
    }
}

// Fallback Functions
export function renderFallbackConfigs() {
    const container = document.getElementById('fallback-configs');
    if (!container) return;
    
    const role = state.currentFallbackRole;
    const config = state.settings?.models?.[role] || {};
    const fallbacks = config.fallbacks || [];
    
    if (fallbacks.length === 0) {
        container.innerHTML = '<div class="fallback-empty">Bu rol için fallback tanımlanmamış.</div>';
    } else {
        container.innerHTML = fallbacks.map((fb, index) => `
            <div class="fallback-item" data-index="${index}">
                <span class="fallback-order">${index + 1}</span>
                <div class="fallback-info">
                    <div class="fallback-provider">${fb.provider}</div>
                    <div class="fallback-model">${fb.model}</div>
                </div>
                <button class="fallback-delete" onclick="window.AtomAgent.deleteFallback(${index})" title="Sil">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        `).join('');
    }
}

export function switchFallbackRole(role) {
    state.currentFallbackRole = role;
    
    document.querySelectorAll('#fallback-role-tabs .role-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`#fallback-role-tabs [data-role="${role}"]`)?.classList.add('active');
    
    renderFallbackConfigs();
}

export async function addFallback() {
    const provider = document.getElementById('new-fallback-provider')?.value;
    const model = document.getElementById('new-fallback-model')?.value?.trim();
    const role = state.currentFallbackRole;
    
    if (!model) {
        showNotification('Model adı gerekli', 'error');
        return;
    }
    
    try {
        const config = state.settings?.models?.[role] || {};
        const fallbacks = [...(config.fallbacks || []), { provider, model }];
        
        await fetch('/api/settings/fallback', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role, fallbacks })
        });
        
        if (!state.settings.models[role]) {
            state.settings.models[role] = {};
        }
        state.settings.models[role].fallbacks = fallbacks;
        
        document.getElementById('new-fallback-model').value = '';
        
        renderFallbackConfigs();
        showNotification('Fallback eklendi');
    } catch (error) {
        console.error('Failed to add fallback:', error);
        showNotification('Fallback eklenemedi', 'error');
    }
}

export async function deleteFallback(index) {
    const role = state.currentFallbackRole;
    
    try {
        await fetch(`/api/settings/fallback/${role}/${index}`, {
            method: 'DELETE'
        });
        
        if (state.settings?.models?.[role]?.fallbacks) {
            state.settings.models[role].fallbacks.splice(index, 1);
        }
        
        renderFallbackConfigs();
        showNotification('Fallback silindi');
    } catch (error) {
        console.error('Failed to delete fallback:', error);
        showNotification('Fallback silinemedi', 'error');
    }
}

export function renderCommands() {
    const container = document.getElementById('allowed-commands');
    if (!container) return;
    
    const commands = state.settings?.allowed_commands || [];
    
    container.innerHTML = commands.map(cmd => `
        <span class="command-tag">
            ${escapeHtml(cmd)}
            <button onclick="window.AtomAgent.removeCommand('${escapeHtml(cmd)}')">&times;</button>
        </span>
    `).join('');
}

export function renderAPIStatus() {
    const container = document.getElementById('api-status');
    if (!container) return;
    
    container.innerHTML = (state.providers || []).map(p => `
        <div class="api-item">
            <span class="provider-name">${p.name}</span>
            <span class="status-badge ${p.has_api_key ? 'active' : 'inactive'}">
                ${p.has_api_key ? `${p.api_key_count} key aktif` : 'Key yok'}
            </span>
        </div>
    `).join('');
}

export function loadPrompt() {
    const promptSelect = document.getElementById('prompt-select');
    const promptEditor = document.getElementById('prompt-editor');
    if (!promptSelect || !promptEditor) return;
    
    const promptName = promptSelect.value;
    const content = state.prompts?.[promptName] || '';
    promptEditor.value = content;
}

export async function savePrompt() {
    const promptName = document.getElementById('prompt-select')?.value;
    const content = document.getElementById('prompt-editor')?.value;
    
    if (!promptName) return;
    
    try {
        await fetch(`/api/prompts/${promptName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        state.prompts[promptName] = content;
        showNotification('Prompt kaydedildi');
    } catch (error) {
        console.error('Failed to save prompt:', error);
        showNotification('Prompt kaydedilemedi', 'error');
    }
}

export function openSettings() {
    const elements = getElements();
    elements.settingsModal?.classList.remove('hidden');
}

export function closeSettings() {
    const elements = getElements();
    elements.settingsModal?.classList.add('hidden');
}

export function switchSettingsTab(tabName) {
    document.querySelectorAll('.settings-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.settings-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-settings="${tabName}"]`)?.classList.add('active');
    document.getElementById(`settings-${tabName}`)?.classList.add('active');
    
    if (tabName === 'fallbacks') {
        renderFallbackConfigs();
        populateProviderDropdown('new-fallback-provider');
    }
}
