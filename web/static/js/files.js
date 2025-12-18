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

// Helper to get icon class based on extension
function getFileIcon(filename, isDir) {
    if (isDir) return { icon: '📁', class: 'folder' };
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'py': { icon: '🐍', class: 'py' },
        'html': { icon: '🌐', class: 'html' },
        'css': { icon: '🎨', class: 'css' },
        'js': { icon: '📜', class: 'js' },
        'json': { icon: '🔧', class: 'json' },
        'md': { icon: '📝', class: 'md' },
        'txt': { icon: '📄', class: 'file' }
    };
    return icons[ext] || { icon: '📄', class: 'file' };
}

export function renderFileTree(items, currentPath, source = 'workspace') {
    const elements = getElements();
    const loadFn = source === 'docker' ? 'loadDockerFiles' : 'loadWorkspaceFiles';
    const openFn = source === 'docker' ? 'openDockerFile' : 'openFile';

    // Sort: Folders first, then files
    items.sort((a, b) => {
        if (a.is_dir === b.is_dir) return a.name.localeCompare(b.name);
        return a.is_dir ? -1 : 1;
    });

    elements.fileTree.innerHTML = items.map(item => {
        const iconData = getFileIcon(item.name, item.is_dir);
        return `
        <div class="file-item" 
             onclick="window.AtomAgent.${item.is_dir ? loadFn : openFn}('${item.path}')">
            <span class="file-icon ${iconData.class}">${iconData.icon}</span>
            <span class="file-name">${escapeHtml(item.name)}</span>
        </div>
    `}).join('');

    if (currentPath && currentPath !== '/' && currentPath !== '/home/agent') {
        const parentPath = currentPath.split('/').slice(0, -1).join('/') || (source === 'docker' ? '/home/agent' : '');
        elements.fileTree.innerHTML = `
            <div class="file-item" onclick="window.AtomAgent.${loadFn}('${parentPath}')">
                <span class="file-icon folder">📂</span>
                <span class="file-name">..</span>
            </div>
        ` + elements.fileTree.innerHTML;
    }
}

export async function openFile(path) {
    const elements = getElements();

    try {
        const response = await fetch(`/api/workspace/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        // v2.0 Update: Use Modal editor
        if (window.showEditorModal) {
            window.showEditorModal(path);
            // Wait for modal to render then set content
            setTimeout(() => {
                const editor = document.getElementById('code-editor');
                if (editor) {
                    editor.value = data.content;
                    editor.dataset.path = path;
                    editor.dataset.source = 'workspace';
                    document.getElementById('save-file-btn').disabled = false;
                }
            }, 50);
        } else {
            // Fallback (should not happen with project.js loaded)
            elements.codeEditor.value = data.content;
            elements.editorFilename.textContent = path;
            // switchTab('editor'); // Removed
        }
    } catch (error) {
        console.error('Failed to open file:', error);
        alert('Dosya açılamadı: ' + path);
    }
}

export async function openDockerFile(path) {
    const elements = getElements();

    try {
        const response = await fetch(`/api/docker/file?path=${encodeURIComponent(path)}`);
        const data = await response.json();

        // v2.0 Update: Use Modal editor
        if (window.showEditorModal) {
            window.showEditorModal(`🐳 ${path}`);
            setTimeout(() => {
                const editor = document.getElementById('code-editor');
                if (editor) {
                    editor.value = data.content;
                    editor.dataset.path = path;
                    editor.dataset.source = 'docker';
                    document.getElementById('save-file-btn').disabled = true; // Read only
                }
            }, 50);
        }
    } catch (error) {
        console.error('Failed to open docker file:', error);
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

export function setupFileTabs() {
    document.querySelectorAll('.file-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.file-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const fileTree = document.getElementById('file-tree');
            const memoryPanel = document.getElementById('memory-panel');

            state.fileSource = tab.dataset.source;

            if (state.fileSource === 'memory') {
                // Hafıza panelini göster, dosya ağacını gizle
                if (fileTree) fileTree.classList.add('hidden');
                if (memoryPanel) memoryPanel.classList.remove('hidden');
            } else {
                // Dosya ağacını göster, hafıza panelini gizle
                if (fileTree) fileTree.classList.remove('hidden');
                if (memoryPanel) memoryPanel.classList.add('hidden');

                if (state.fileSource === 'docker') {
                    loadDockerFiles();
                } else {
                    loadWorkspaceFiles();
                }
            }
        });
    });
}
