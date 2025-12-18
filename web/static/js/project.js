/**
 * AtomAgent - Project Tab (Todos & Files)
 */
import { loadWorkspaceFiles, openFile } from './files.js';
import { loadReminders, createReminder } from './reminders.js';

export function initProject() {
    setupProjectListeners();
    setupResizer();

    // Initial load
    loadWorkspaceFiles();
    loadReminders();
}

function getElements() {
    return {
        todosPanel: document.getElementById('todos-panel'),
        fileTree: document.getElementById('file-tree'),
        resizer: document.getElementById('project-resizer'),
        topPane: document.querySelector('.project-pane.top'),
        bottomPane: document.querySelector('.project-pane.bottom'),
        addReminderBtn: document.getElementById('add-reminder-btn'),
        refreshFilesBtn: document.getElementById('refresh-files')
    };
}

function setupProjectListeners() {
    const els = getElements();

    els.refreshFilesBtn?.addEventListener('click', () => {
        loadWorkspaceFiles();
    });

    els.addReminderBtn?.addEventListener('click', () => {
        ensureReminderModal();
        const modal = document.getElementById('reminder-modal');
        if (modal) {
            document.getElementById('reminder-input-title').value = '';
            document.getElementById('reminder-input-time').value = '';
            modal.classList.remove('hidden');
        }
    });

    // Accordion Logic
    const accordions = document.querySelectorAll('.project-header-accordion');
    accordions.forEach(acc => {
        acc.addEventListener('click', (e) => {
            // Prevent triggering if clicked on action buttons
            if (e.target.closest('.pane-actions')) return;

            acc.classList.toggle('collapsed');
            const contentId = acc.id === 'accordion-plan' ? 'pane-plan-content' : 'pane-files-content';
            const content = document.getElementById(contentId);

            if (content) {
                if (acc.classList.contains('collapsed')) {
                    content.style.display = 'none';
                } else {
                    content.style.display = 'flex';
                }
            }
        });
    });

    // Handle file clicks (handled by files.js mainly, but ensure we have editor support)
    // If files.js tries to open #code-editor and it's missing, we need to provide a fallback or restore it.
    // For this design, let's inject a modal editor if one doesn't exist.
    ensureEditorModal();
}

function setupResizer() {
    const els = getElements();
    if (!els.resizer || !els.topPane) return;

    let isResizing = false;
    let startY = 0;
    let startHeight = 0;

    els.resizer.addEventListener('mousedown', (e) => {
        isResizing = true;
        startY = e.clientY;
        startHeight = els.topPane.offsetHeight;
        els.resizer.classList.add('active');
        document.body.style.cursor = 'row-resize';
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        const diff = e.clientY - startY;
        const newHeight = Math.max(50, startHeight + diff);
        els.topPane.style.height = `${newHeight}px`;
        els.topPane.style.flex = 'none';
    });

    document.addEventListener('mouseup', () => {
        if (isResizing) {
            isResizing = false;
            els.resizer.classList.remove('active');
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

// Editor Modal Support
function ensureEditorModal() {
    if (document.getElementById('editor-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'editor-modal';
    modal.className = 'modal hidden'; // Reuse modal styles or add new
    modal.innerHTML = `
        <div class="modal-content editor-modal-content" style="width: 80%; height: 80%; max-width: 1000px;">
            <div class="modal-header">
                <h3 id="modal-editor-filename">Dosya Düzenleyici</h3>
                <span class="close-modal">&times;</span>
            </div>
            <div class="modal-body" style="height: calc(100% - 60px); padding: 0;">
                <textarea id="code-editor" class="code-editor" style="width:100%; height:100%; resize:none; border:none; padding:10px; font-family:'JetBrains Mono'; background: var(--bg-primary); color: var(--text-primary);"></textarea>
            </div>
            <div class="modal-footer">
                <button id="save-file-btn" class="btn-primary">Kaydet</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // Close logic
    modal.querySelector('.close-modal').addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    // Override file opening to show this modal
    // Note: files.js logic needs to target #code-editor, which now exists in this modal.
    // We just need to make sure the modal becomes visible when a file is opened.
}

// Global expose for files.js to trigger visibility
window.showEditorModal = function (filename) {
    const modal = document.getElementById('editor-modal');
    if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('modal-editor-filename').textContent = filename;
    }
};
// Reminder Modal
function ensureReminderModal() {
    if (document.getElementById('reminder-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'reminder-modal';
    modal.className = 'modal hidden';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 400px;">
            <div class="modal-header">
                <h3>Yeni Hatırlatıcı</h3>
                <span class="close-modal">&times;</span>
            </div>
            <div class="modal-body">
                <div class="input-group">
                    <label>Hatırlatılacak Şey</label>
                    <input type="text" id="reminder-input-title" placeholder="Örn: Fırını kapat" class="console-input">
                </div>
                <div class="input-group" style="margin-top: 10px;">
                    <label>Zaman</label>
                    <input type="text" id="reminder-input-time" placeholder="Örn: 5dk, 18:30, her gün" class="console-input">
                    <small>Desteklenenler: 10dk, 2sa, yarin 10:00, her gun 09:00</small>
                </div>
            </div>
            <div class="modal-footer">
                <button id="save-reminder-btn" class="btn-primary">Oluştur</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    const closeModal = () => modal.classList.add('hidden');
    modal.querySelector('.close-modal').addEventListener('click', closeModal);

    // Save logic
    modal.querySelector('#save-reminder-btn').addEventListener('click', async () => {
        const title = document.getElementById('reminder-input-title').value;
        const time = document.getElementById('reminder-input-time').value;

        if (title && time) {
            await createReminder(title, time);
            closeModal();
        }
    });
}
