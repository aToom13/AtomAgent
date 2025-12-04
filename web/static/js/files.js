/**
 * AtomAgent - File Management
 */

import { state, getElements } from './state.js';
import { escapeHtml, showNotification } from './utils.js';
import { switchTab } from './ui.js';

export async function loadWorkspaceFiles(path = '') {
    const elements = getElements();
    
    try {
        const response = await fetch(`/api/workspace/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        renderFileTree(data.items, path, 'workspace');
    } catch (error) {
        console.error('Failed to load files:', error);
        elements.fileTree.innerHTML = '<div class="file-error">Dosyalar yüklenemedi</div>';
    }
}

export async function loadDockerFiles(path = '/home/agent') {
    const elements = getElements();
    
    try {
        const response = await fetch(`/api/docker/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        renderFileTree(data.items || [], path, 'docker');
    } catch (error) {
        elements.fileTree.innerHTML = '<div class="file-error">Docker dosyaları yüklenemedi</div>';
    }
}

export function renderFileTree(items, currentPath, source = 'workspace') {
    const elements = getElements();
    const loadFn = source === 'docker' ? 'loadDockerFiles' : 'loadWorkspaceFiles';
    const openFn = source === 'docker' ? 'openDockerFile' : 'openFile';
    
    elements.fileTree.innerHTML = items.map(item => `
        <div class="file-item ${item.is_dir ? 'folder' : 'file'}" 
             onclick="window.AtomAgent.${item.is_dir ? loadFn : openFn}('${item.path}')">
            ${item.is_dir ? '📁' : '📄'} ${escapeHtml(item.name)}
        </div>
    `).join('');
    
    if (currentPath && currentPath !== '/' && currentPath !== '/home/agent') {
        const parentPath = currentPath.split('/').slice(0, -1).join('/') || (source === 'docker' ? '/home/agent' : '');
        elements.fileTree.innerHTML = `
            <div class="file-item folder" onclick="window.AtomAgent.${loadFn}('${parentPath}')">
                📁 ..
            </div>
        ` + elements.fileTree.innerHTML;
    }
}

export async function openFile(path) {
    const elements = getElements();
    
    try {
        const response = await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        elements.codeEditor.value = data.content;
        elements.editorFilename.textContent = path;
        elements.codeEditor.dataset.path = path;
        elements.codeEditor.dataset.source = 'workspace';
        document.getElementById('save-file-btn').disabled = false;
        
        switchTab('editor');
    } catch (error) {
        console.error('Failed to open file:', error);
        showNotification('Dosya açılamadı', 'error');
    }
}

export async function openDockerFile(path) {
    const elements = getElements();
    
    try {
        const response = await fetch(`/api/docker/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        
        elements.codeEditor.value = data.content;
        elements.editorFilename.textContent = `🐳 ${path}`;
        elements.codeEditor.dataset.path = path;
        elements.codeEditor.dataset.source = 'docker';
        document.getElementById('save-file-btn').disabled = true;
        
        switchTab('editor');
    } catch (error) {
        console.error('Failed to open docker file:', error);
        showNotification('Docker dosyası açılamadı', 'error');
    }
}

export async function saveFile() {
    const elements = getElements();
    const path = elements.codeEditor.dataset.path;
    const content = elements.codeEditor.value;
    const source = elements.codeEditor.dataset.source;
    
    if (!path || source === 'docker') return;
    
    try {
        await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        
        showNotification('Dosya kaydedildi');
    } catch (error) {
        console.error('Failed to save file:', error);
        showNotification('Dosya kaydedilemedi', 'error');
    }
}

export async function loadUploads() {
    const elements = getElements();
    
    try {
        const response = await fetch('/api/workspace/files?path=uploads');
        const data = await response.json();
        
        if (!data.items || data.items.length === 0) {
            elements.fileTree.innerHTML = `
                <div class="file-empty">
                    <div class="file-empty-icon">📤</div>
                    <p>Henüz yüklenen dosya yok</p>
                    <p class="file-hint">Dosya eklemek için chat'teki 📎 butonunu kullanın</p>
                </div>
            `;
            return;
        }
        
        renderFileTree(data.items, 'uploads', 'workspace');
    } catch (error) {
        console.error('Failed to load uploads:', error);
        elements.fileTree.innerHTML = '<div class="file-error">Uploads yüklenemedi</div>';
    }
}

export function setupFileTabs() {
    document.querySelectorAll('.file-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.file-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            state.fileSource = tab.dataset.source;
            if (state.fileSource === 'docker') {
                loadDockerFiles();
            } else if (state.fileSource === 'uploads') {
                loadUploads();
            } else {
                loadWorkspaceFiles();
            }
        });
    });
}
