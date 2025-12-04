/**
 * AtomAgent - Docker Functions
 */

import { escapeHtml } from './utils.js';

let currentDockerCommand = null;

export async function checkDockerStatus() {
    const indicator = document.getElementById('docker-indicator');
    const statusText = document.getElementById('docker-status-text');
    
    if (!indicator || !statusText) return;
    
    indicator.className = 'docker-indicator loading';
    statusText.textContent = 'Bağlantı kontrol ediliyor...';
    
    try {
        const response = await fetch('/api/docker/status');
        const data = await response.json();
        
        if (data.running) {
            indicator.className = 'docker-indicator online';
            statusText.textContent = `Container çalışıyor: ${data.container_id || 'sandbox'}`;
        } else {
            indicator.className = 'docker-indicator offline';
            statusText.textContent = 'Container çalışmıyor';
        }
    } catch (error) {
        indicator.className = 'docker-indicator offline';
        statusText.textContent = 'Docker bağlantısı yok';
    }
}

export function addDockerLog(command, output, isError = false) {
    const dockerOutput = document.getElementById('docker-output');
    if (!dockerOutput) return;
    
    const time = new Date().toLocaleTimeString('tr-TR');
    const line = document.createElement('div');
    line.className = 'docker-line';
    line.innerHTML = `
        <span class="docker-time">[${time}]</span>
        <span class="docker-cmd">$ ${escapeHtml(command)}</span>
        <div class="${isError ? 'docker-error' : 'docker-output-text'}">${escapeHtml(output)}</div>
    `;
    dockerOutput.appendChild(line);
    dockerOutput.scrollTop = dockerOutput.scrollHeight;
}

export function addDockerCommand(command, status) {
    const dockerOutput = document.getElementById('docker-output');
    if (!dockerOutput) return;
    
    const time = new Date().toLocaleTimeString('tr-TR');
    const line = document.createElement('div');
    line.className = 'docker-line running';
    line.id = 'docker-cmd-' + Date.now();
    line.innerHTML = `
        <span class="docker-time">[${time}]</span>
        <span class="docker-cmd">$ ${escapeHtml(command)}</span>
        <div class="docker-status">⏳ Çalışıyor...</div>
    `;
    dockerOutput.appendChild(line);
    dockerOutput.scrollTop = dockerOutput.scrollHeight;
    currentDockerCommand = line;
    
    highlightDockerTab();
}

export function addDockerOutput(output, status) {
    const dockerOutput = document.getElementById('docker-output');
    if (!dockerOutput) return;
    
    if (currentDockerCommand) {
        const statusEl = currentDockerCommand.querySelector('.docker-status');
        if (statusEl) {
            const isError = output.toLowerCase().includes('error') || output.toLowerCase().includes('failed');
            statusEl.className = isError ? 'docker-error' : 'docker-output-text';
            statusEl.innerHTML = escapeHtml(output).replace(/\n/g, '<br>');
        }
        currentDockerCommand.classList.remove('running');
        currentDockerCommand = null;
    } else {
        const time = new Date().toLocaleTimeString('tr-TR');
        const line = document.createElement('div');
        line.className = 'docker-line';
        const isError = output.toLowerCase().includes('error') || output.toLowerCase().includes('failed');
        line.innerHTML = `
            <span class="docker-time">[${time}]</span>
            <div class="${isError ? 'docker-error' : 'docker-output-text'}">${escapeHtml(output).replace(/\n/g, '<br>')}</div>
        `;
        dockerOutput.appendChild(line);
    }
    
    dockerOutput.scrollTop = dockerOutput.scrollHeight;
}

export function highlightDockerTab() {
    const dockerTab = document.querySelector('[data-tab="docker"]');
    if (dockerTab && !dockerTab.classList.contains('active')) {
        dockerTab.classList.add('has-activity');
        setTimeout(() => dockerTab.classList.remove('has-activity'), 3000);
    }
}

export function setupDockerRefresh() {
    const refreshBtn = document.getElementById('docker-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', checkDockerStatus);
    }
}
