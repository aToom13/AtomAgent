/**
 * AtomAgent Web UI - Main Application Entry Point
 * Modular ES6 Architecture
 * v2.0 - Enhanced with Agent System, Todos, Memory, Metrics
 */

import { state, getElements } from './state.js';
import { connectWebSocket } from './websocket.js';
import { loadSessions, loadSession, deleteSession, newChat, renderSessions, confirmDeleteSession, cancelDeleteSession } from './sessions.js';
import { sendMessage, stopGeneration, autoResizeTextarea, handleInputKeydown } from './chat.js';
import { toggleSidebar, switchTab, setupResizeHandle } from './ui.js';
import { loadSettings, openSettings, closeSettings, switchSettingsTab, switchModelRole, switchFallbackRole, updateModel, addFallback, deleteFallback, loadPrompt, savePrompt } from './settings.js';
import { loadWorkspaceFiles, loadDockerFiles, openFile, openDockerFile, saveFile, setupFileTabs } from './files.js';
import { checkDockerStatus, setupDockerRefresh } from './docker.js';
import { toggleThinking, toggleThinkingPanel } from './thinking.js';
import { renderToolsPanel, clearToolHistory } from './tools.js';
import { renderBrowserPanel, showBrowserEntry, clearBrowserHistory } from './browser.js';
import { renderTasksPanel, clearCompletedTasks, clearAllTasks } from './tasks.js';
import { initAttachments, removeAttachment, clearAttachments } from './attachments.js';

// v2.0 New Modules
import { AGENTS, renderAgentSelector, setActiveAgent, toggleAutoRouting, routeMessage, getActiveAgent, updateAgentUI, toggleAgentDropdown, renderAgentListInSettings } from './agents.js';
import { renderTodosPanel, addTodo, updateTodo, setTodoStatus, cycleTodoStatus, toggleTodoChildren, clearCompletedTodos, clearAllTodos, handleTodoUpdate, deleteTodo } from './todos.js';
import { renderMemoryPanel, addMemory, updateMemory, deleteMemory, filterMemories, toggleMemoryTag, openAddMemoryModal, closeAddMemoryModal, saveNewMemory, handleMemoryUpdate, searchMemories } from './memory.js';
import { initCanvas, loadUrl as loadCanvasUrl, refreshCanvas, retryCanvas, handleServerStart, handleCanvasMessage, terminalExec, clearTerminal } from './canvas.js';

// Initialize application
document.addEventListener('DOMContentLoaded', init);

async function init() {
    setupEventListeners();
    await loadSessions();
    await loadSettings();
    connectWebSocket();
    loadWorkspaceFiles();
    checkDockerStatus();
    setupFileTabs();
    setupDockerRefresh();
    
    // Initialize panels
    renderToolsPanel();
    renderBrowserPanel();
    renderTasksPanel();
    
    // Initialize attachments
    initAttachments();
    
    // v2.0 Initialize new panels
    renderTodosPanel();
    renderMemoryPanel();
    updateAgentUI();
    renderAgentListInSettings();
    
    // Initialize canvas
    initCanvas();
}

function setupEventListeners() {
    const elements = getElements();
    
    // Sidebar toggle
    document.getElementById('toggle-sidebar')?.addEventListener('click', toggleSidebar);
    document.getElementById('expand-sidebar')?.addEventListener('click', toggleSidebar);
    
    // New chat
    document.getElementById('new-chat-btn')?.addEventListener('click', newChat);
    document.getElementById('new-chat-collapsed')?.addEventListener('click', newChat);
    
    // Settings
    document.getElementById('settings-btn')?.addEventListener('click', openSettings);
    document.getElementById('settings-collapsed')?.addEventListener('click', openSettings);
    document.getElementById('close-settings')?.addEventListener('click', closeSettings);
    document.querySelector('.modal-backdrop')?.addEventListener('click', closeSettings);
    
    // Message input
    elements.messageInput?.addEventListener('keydown', handleInputKeydown);
    elements.messageInput?.addEventListener('input', autoResizeTextarea);
    elements.sendBtn?.addEventListener('click', sendMessage);
    elements.stopBtn?.addEventListener('click', stopGeneration);
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Settings tabs
    document.querySelectorAll('.settings-tab').forEach(btn => {
        btn.addEventListener('click', () => switchSettingsTab(btn.dataset.settings));
    });
    
    // Prompt selector
    document.getElementById('prompt-select')?.addEventListener('change', loadPrompt);
    document.getElementById('save-prompt-btn')?.addEventListener('click', savePrompt);
    
    // Save file
    document.getElementById('save-file-btn')?.addEventListener('click', saveFile);
    
    // Model role tabs
    document.querySelectorAll('#model-role-tabs .role-tab').forEach(btn => {
        btn.addEventListener('click', () => switchModelRole(btn.dataset.role));
    });
    
    // Fallback role tabs
    document.querySelectorAll('#fallback-role-tabs .role-tab').forEach(btn => {
        btn.addEventListener('click', () => switchFallbackRole(btn.dataset.role));
    });
    
    // Add fallback button
    document.getElementById('add-fallback-btn')?.addEventListener('click', addFallback);
    
    // Resize handle
    setupResizeHandle();
}

// Export functions to window for inline onclick handlers
window.AtomAgent = {
    // Sessions
    loadSession,
    deleteSession,
    newChat,
    confirmDeleteSession,
    cancelDeleteSession,
    
    // Settings
    updateModel,
    deleteFallback,
    removeCommand: () => {}, // TODO: implement
    
    // Files
    loadWorkspaceFiles,
    loadDockerFiles,
    openFile,
    openDockerFile,
    
    // Thinking
    toggleThinking,
    toggleThinkingPanel,
    
    // Tools
    clearToolHistory,
    
    // Browser
    showBrowserEntry,
    clearBrowserHistory,
    
    // Tasks
    clearCompletedTasks,
    clearAllTasks,
    
    // Attachments
    removeAttachment,
    clearAttachments,
    
    // v2.0 - Agents
    setActiveAgent,
    toggleAutoRouting,
    toggleAgentDropdown,
    
    // v2.0 - Todos
    cycleTodoStatus,
    toggleTodoChildren,
    clearCompletedTodos,
    clearAllTodos,
    
    // v2.0 - Memory
    deleteMemory,
    filterMemories,
    toggleMemoryTag,
    openAddMemoryModal,
    closeAddMemoryModal,
    saveNewMemory,
    
    // Canvas
    loadCanvasUrl,
    refreshCanvas,
    retryCanvas,
    handleServerStart,
    terminalExec,
    clearTerminal
};
