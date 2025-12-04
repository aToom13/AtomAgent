/**
 * AtomAgent - Attachment Handler
 * Dosya, resim, ses ekleme ve yönetimi
 */

import { state } from './state.js';

// Attachment state
let attachments = [];
let attachMenuOpen = false;

export function initAttachments() {
    const attachBtn = document.getElementById('attach-btn');
    const attachMenu = document.getElementById('attach-menu');
    const imageInput = document.getElementById('image-input');
    const audioInput = document.getElementById('audio-input');
    const fileInput = document.getElementById('file-input');
    const codeInput = document.getElementById('code-input');
    
    // Toggle menu
    attachBtn?.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleAttachMenu();
    });
    
    // Close menu on outside click
    document.addEventListener('click', (e) => {
        if (attachMenuOpen && !attachMenu?.contains(e.target)) {
            closeAttachMenu();
        }
    });
    
    // Attach options
    document.querySelectorAll('.attach-option').forEach(option => {
        option.addEventListener('click', () => {
            const type = option.dataset.type;
            handleAttachOption(type);
            closeAttachMenu();
        });
    });
    
    // File input handlers
    imageInput?.addEventListener('change', (e) => handleFileSelect(e, 'image'));
    audioInput?.addEventListener('change', (e) => handleFileSelect(e, 'audio'));
    fileInput?.addEventListener('change', (e) => handleFileSelect(e, 'file'));
    codeInput?.addEventListener('change', (e) => handleFileSelect(e, 'code'));
    
    // Drag & drop
    initDragDrop();
}

function toggleAttachMenu() {
    const menu = document.getElementById('attach-menu');
    attachMenuOpen = !attachMenuOpen;
    menu?.classList.toggle('hidden', !attachMenuOpen);
}

function closeAttachMenu() {
    const menu = document.getElementById('attach-menu');
    attachMenuOpen = false;
    menu?.classList.add('hidden');
}

function handleAttachOption(type) {
    switch (type) {
        case 'image':
            document.getElementById('image-input')?.click();
            break;
        case 'audio':
            document.getElementById('audio-input')?.click();
            break;
        case 'file':
            document.getElementById('file-input')?.click();
            break;
        case 'code':
            document.getElementById('code-input')?.click();
            break;
    }
}

async function handleFileSelect(event, type) {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    
    for (const file of files) {
        await addAttachment(file, type);
    }
    
    // Reset input
    event.target.value = '';
}

async function addAttachment(file, type) {
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
        alert('Dosya boyutu 10MB\'dan büyük olamaz.');
        return;
    }
    
    // Determine type if not specified
    if (!type) {
        if (file.type.startsWith('image/')) type = 'image';
        else if (file.type.startsWith('audio/')) type = 'audio';
        else if (isCodeFile(file.name)) type = 'code';
        else type = 'file';
    }
    
    // Read file
    const reader = new FileReader();
    
    reader.onload = async (e) => {
        const attachment = {
            id: Date.now() + Math.random(),
            name: file.name,
            size: file.size,
            type: type,
            mimeType: file.type,
            data: e.target.result
        };
        
        // For images, create thumbnail
        if (type === 'image') {
            attachment.thumbnail = e.target.result;
        }
        
        attachments.push(attachment);
        renderAttachmentPreview();
    };
    
    if (type === 'image') {
        reader.readAsDataURL(file);
    } else {
        reader.readAsDataURL(file);
    }
}

function isCodeFile(filename) {
    const codeExtensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.yaml', '.yml', '.md', '.txt', '.sh', '.sql', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.rb', '.php'];
    return codeExtensions.some(ext => filename.toLowerCase().endsWith(ext));
}

function renderAttachmentPreview() {
    const preview = document.getElementById('attachment-preview');
    if (!preview) return;
    
    if (attachments.length === 0) {
        preview.classList.add('hidden');
        preview.innerHTML = '';
        return;
    }
    
    preview.classList.remove('hidden');
    preview.innerHTML = attachments.map(att => {
        const icon = getAttachmentIcon(att.type);
        const size = formatFileSize(att.size);
        
        if (att.type === 'image' && att.thumbnail) {
            return `
                <div class="attachment-item image-preview" data-id="${att.id}">
                    <img src="${att.thumbnail}" alt="${att.name}">
                    <div class="attachment-info">
                        <span class="attachment-name">${att.name}</span>
                        <span class="attachment-size">${size}</span>
                    </div>
                    <button class="attachment-remove" onclick="window.AtomAgent.removeAttachment(${att.id})">×</button>
                </div>
            `;
        }
        
        if (att.type === 'audio') {
            return `
                <div class="attachment-item audio-preview" data-id="${att.id}">
                    <div class="audio-icon">🎵</div>
                    <div class="attachment-info">
                        <span class="attachment-name">${att.name}</span>
                        <span class="attachment-size">${size}</span>
                    </div>
                    <button class="attachment-remove" onclick="window.AtomAgent.removeAttachment(${att.id})">×</button>
                </div>
            `;
        }
        
        return `
            <div class="attachment-item" data-id="${att.id}">
                <span class="attachment-icon">${icon}</span>
                <span class="attachment-name">${att.name}</span>
                <span class="attachment-size">${size}</span>
                <button class="attachment-remove" onclick="window.AtomAgent.removeAttachment(${att.id})">×</button>
            </div>
        `;
    }).join('');
}

function getAttachmentIcon(type) {
    switch (type) {
        case 'image': return '🖼️';
        case 'audio': return '🎵';
        case 'code': return '📝';
        default: return '📎';
    }
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

export function removeAttachment(id) {
    attachments = attachments.filter(a => a.id !== id);
    renderAttachmentPreview();
}

export function getAttachments() {
    return [...attachments];
}

export function clearAttachments() {
    attachments = [];
    renderAttachmentPreview();
}

export function hasAttachments() {
    return attachments.length > 0;
}

// Drag & Drop
function initDragDrop() {
    const chatArea = document.getElementById('chat-area');
    if (!chatArea) return;
    
    let dragCounter = 0;
    
    chatArea.addEventListener('dragenter', (e) => {
        e.preventDefault();
        dragCounter++;
        showDragOverlay();
    });
    
    chatArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            hideDragOverlay();
        }
    });
    
    chatArea.addEventListener('dragover', (e) => {
        e.preventDefault();
    });
    
    chatArea.addEventListener('drop', async (e) => {
        e.preventDefault();
        dragCounter = 0;
        hideDragOverlay();
        
        const files = e.dataTransfer.files;
        for (const file of files) {
            await addAttachment(file);
        }
    });
}

function showDragOverlay() {
    let overlay = document.querySelector('.drag-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'drag-overlay';
        overlay.innerHTML = `
            <div class="drag-overlay-content">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                </svg>
                <p>Dosyayı buraya bırakın</p>
            </div>
        `;
        document.getElementById('chat-area')?.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}

function hideDragOverlay() {
    const overlay = document.querySelector('.drag-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}
