/**
 * AtomAgent - Console Tab (Split View: Thoughts & Terminal)
 */

export function initConsole() {
    setupConsoleListeners();
    setupResizer();
}

function getElements() {
    return {
        thoughtsOutput: document.getElementById('agent-thoughts'),
        terminalOutput: document.getElementById('terminal-output'),
        terminalInput: document.getElementById('terminal-input'), // ID remains same
        terminalClear: document.getElementById('terminal-clear'),
        resizer: document.getElementById('console-resizer'),
        topPane: document.querySelector('.console-pane.top'),
        bottomPane: document.querySelector('.console-pane.bottom')
    };
}

function setupConsoleListeners() {
    const els = getElements();

    // Terminal Input
    els.terminalInput?.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const cmd = els.terminalInput.value.trim();
            if (cmd) {
                sendCommand(cmd);
                els.terminalInput.value = '';
            }
        }
    });

    // Clear Button
    els.terminalClear?.addEventListener('click', () => {
        if (els.terminalOutput) els.terminalOutput.innerHTML = '';
        if (els.thoughtsOutput) els.thoughtsOutput.innerHTML = '';
        // Add default system lines
        appendLog('agent', 'System log cleared.', 'system');
        appendLog('terminal', 'Terminal cleared.', 'system');
    });

    // Filter Buttons logic
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const group = e.target.parentElement; // .filter-group
            const pane = group.closest('.console-pane'); // .console-pane (top or bottom)
            const output = pane.querySelector('.console-output');
            const filterType = e.target.dataset.filter;

            // Toggle active class
            group.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            // Filter Logic
            const lines = output.querySelectorAll('.console-line');
            lines.forEach(line => {
                if (filterType === 'all') {
                    line.classList.remove('hidden');
                } else {
                    if (line.classList.contains(filterType)) {
                        line.classList.remove('hidden');
                    } else {
                        line.classList.add('hidden');
                    }
                }
            });
        });
    });
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
        // Min height 50px
        const newHeight = Math.max(50, startHeight + diff);
        // Max height constraint (relative to container)
        els.topPane.style.height = `${newHeight}px`;
        els.topPane.style.flex = 'none'; // Disable flex grow/shrink to respect height
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

// === API ===

export function appendLog(target, message, type = 'info') {
    const els = getElements();
    const container = target === 'agent' ? els.thoughtsOutput : els.terminalOutput;

    if (!container) return;

    const div = document.createElement('div');
    div.className = `console-line ${type}`;

    // Timestamp for terminal
    if (target === 'terminal') {
        const time = new Date().toLocaleTimeString('tr-TR', { hour12: false });
        div.innerHTML = `<span style="opacity:0.5">[${time}]</span> ${escapeHtml(message)}`;
    } else {
        div.textContent = message; // Agent thoughts might be raw text
    }

    // v2.2 - Add source type class for filtering
    // type argument is now used as the specific tag (e.g. 'docker', 'terminal', 'agent', 'tool')
    // We append it to classList
    div.classList.add(type);

    // Auto-scroll only if near bottom
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    container.appendChild(div);
    if (isNearBottom) {
        container.scrollTop = container.scrollHeight;
    }
}

function sendCommand(cmd) {
    appendLog('terminal', `$ ${cmd}`, 'system');

    // Send to backend via global AtomAgent.socket or similar
    // Assuming 'sandbox_command' or similar type exists
    // For now we reuse the tool execution format or a dedicated channel
    // TODO: Connect to websocket
    console.log("Sending command:", cmd);

    if (window.AtomAgent && window.AtomAgent.ws) {
        window.AtomAgent.send({
            type: "docker_command", // Reusing existing message type if valid
            command: cmd
        });
    }
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
