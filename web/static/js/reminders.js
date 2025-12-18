/**
 * AtomAgent - Reminders Module
 * Manages reminders and scheduled tasks UI
 */

import { state } from './state.js';

// State for reminders
state.reminders = [];
let countdownIntervals = {};

/**
 * Load reminders from API
 */
export async function loadReminders() {
    try {
        const response = await fetch('/api/reminders');
        if (response.ok) {
            state.reminders = await response.json();
            renderRemindersPanel();
        }
    } catch (error) {
        console.error('Failed to load reminders:', error);
    }
}

/**
 * Create a new reminder
 */
export async function createReminder(title, timeOrCron, message = '', action = 'notify') {
    try {
        const response = await fetch('/api/reminders', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title,
                time_or_cron: timeOrCron,
                message,
                action
            })
        });

        if (response.ok) {
            const data = await response.json();
            await loadReminders();
            return data;
        }
    } catch (error) {
        console.error('Failed to create reminder:', error);
    }
    return null;
}

/**
 * Delete a reminder
 */
export async function deleteReminder(reminderId) {
    try {
        const response = await fetch(`/api/reminders/${reminderId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await loadReminders();
            return true;
        }
    } catch (error) {
        console.error('Failed to delete reminder:', error);
    }
    return false;
}

/**
 * Dismiss a triggered reminder
 */
export async function dismissReminder(reminderId) {
    try {
        const response = await fetch(`/api/reminders/${reminderId}/dismiss`, {
            method: 'PUT'
        });

        if (response.ok) {
            await loadReminders();
            return true;
        }
    } catch (error) {
        console.error('Failed to dismiss reminder:', error);
    }
    return false;
}

/**
 * Format time remaining
 */
function formatTimeRemaining(seconds) {
    if (seconds === null || seconds === undefined) return '';

    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
        return `${hours}sa ${mins}dk ${secs}sn`;
    } else if (mins > 0) {
        return `${mins}dk ${secs}sn`;
    } else {
        return `${secs}sn`;
    }
}

/**
 * Start countdown for a reminder
 */
function startCountdown(reminderId, initialSeconds) {
    // Clear existing interval if any
    if (countdownIntervals[reminderId]) {
        clearInterval(countdownIntervals[reminderId]);
    }

    let remaining = initialSeconds;

    const interval = setInterval(() => {
        remaining--;

        const el = document.querySelector(`[data-reminder-id="${reminderId}"] .countdown`);
        if (el) {
            if (remaining <= 0) {
                el.textContent = 'Şimdi!';
                el.classList.add('triggered');
                clearInterval(interval);
            } else {
                el.textContent = formatTimeRemaining(remaining);
            }
        } else {
            clearInterval(interval);
        }
    }, 1000);

    countdownIntervals[reminderId] = interval;
}

/**
 * Render reminders panel
 */
export function renderRemindersPanel() {
    const container = document.getElementById('reminders-panel');
    if (!container) return;

    // Clear old intervals
    Object.values(countdownIntervals).forEach(clearInterval);
    countdownIntervals = {};

    const pending = state.reminders.filter(r => r.status === 'pending');
    const triggered = state.reminders.filter(r => r.status === 'triggered');

    let html = `
        <div class="reminders-header">
            <div class="reminders-title">
                <span class="reminders-icon">🔔</span>
                <span>Hatırlatıcılar</span>
                <span class="reminders-count">${pending.length}</span>
            </div>
        </div>
    `;

    // Triggered reminders (priority)
    if (triggered.length > 0) {
        html += '<div class="reminders-section triggered">';
        for (const r of triggered) {
            html += `
                <div class="reminder-item triggered" data-reminder-id="${r.id}">
                    <div class="reminder-info">
                        <span class="reminder-icon">🔔</span>
                        <span class="reminder-title">${escapeHtml(r.title)}</span>
                    </div>
                    <div class="reminder-actions">
                        <button class="reminder-dismiss-btn" onclick="window.AtomAgent.dismissReminder('${r.id}')">
                            Kapat
                        </button>
                    </div>
                </div>
            `;
        }
        html += '</div>';
    }

    // Pending reminders
    if (pending.length > 0) {
        html += '<div class="reminders-list">';
        for (const r of pending) {
            const isRecurring = r.is_recurring;
            let timeDisplay = '';

            if (isRecurring) {
                timeDisplay = `🔄 ${r.cron_expression || 'Tekrarlayan'}`;
            } else {
                // One-time reminder: Show Date/Time + Countdown
                let dateStr = '';
                if (r.trigger_time) {
                    const date = new Date(r.trigger_time);
                    dateStr = date.toLocaleString('tr-TR', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                }
                timeDisplay = `<span class="reminder-datetime">${dateStr}</span> <span class="countdown">(${formatTimeRemaining(r.time_remaining)})</span>`;
            }

            html += `
                <div class="reminder-item ${isRecurring ? 'recurring' : 'one-time'}" data-reminder-id="${r.id}">
                    <div class="reminder-info">
                        <span class="reminder-icon">${isRecurring ? '🔄' : '⏱️'}</span>
                        <div class="reminder-content">
                            <span class="reminder-title">${escapeHtml(r.title)}</span>
                            <span class="reminder-time">${timeDisplay}</span>
                        </div>
                    </div>
                    <button class="reminder-delete-btn" onclick="window.AtomAgent.deleteReminder('${r.id}')" title="Sil">
                        ✕
                    </button>
                </div>
            `;

            // Start countdown for one-time reminders
            if (!isRecurring && r.time_remaining > 0) {
                setTimeout(() => startCountdown(r.id, r.time_remaining), 100);
            }
        }
        html += '</div>';
    } else if (triggered.length === 0) {
        html += `
            <div class="reminders-empty">
                <div class="reminders-empty-icon">⏰</div>
                <p>Aktif hatırlatıcı yok</p>
                <p class="reminders-hint">Agent'a "10 dk sonra hatırlat" diyebilirsin</p>
            </div>
        `;
    }

    container.innerHTML = html;
}

/**
 * Handle reminder triggered event from WebSocket
 */
export function handleReminderTriggered(reminder) {
    // Reload reminders
    loadReminders();

    // Show notification
    showReminderNotification(reminder);
}

/**
 * Show reminder notification
 */
function showReminderNotification(reminder) {
    console.log('[Reminders] Notification triggered:', reminder);

    // Remove existing notification for this reminder if exists (to update message)
    const existing = document.querySelector(`.reminder-notification[data-id="${reminder.id}"]`);
    if (existing) {
        existing.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'reminder-notification';
    notification.setAttribute('data-id', reminder.id); // Track ID
    notification.innerHTML = `
        <div class="reminder-notification-content">
            <span class="reminder-notification-icon">🔔</span>
            <div class="reminder-notification-text">
                <strong class="notification-title">${escapeHtml(reminder.title)}</strong>
                <p class="notification-message">${escapeHtml(reminder.message)}</p>
            </div>
            <button class="reminder-notification-close" onclick="this.parentElement.parentElement.remove()">✕</button>
        </div>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 10 seconds (if not "Processing")
    if (!reminder.message.includes('İşleniyor')) {
        setTimeout(() => {
            if (notification.parentNode) notification.remove();
        }, 10000);
    } else {
        // If processing, remove faster or let next update replace it
        // Or keep it until result comes
    }

    // Play sound (only if not processing, or different sound?)
    try {
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.play().catch(e => console.log('Audio play failed:', e));
    } catch (e) { }
}

/**
 * Escape HTML for safe rendering
 */
function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    loadReminders();

    // Refresh every 30 seconds to sync with server
    setInterval(loadReminders, 30000);
});

// Expose to global
if (typeof window !== 'undefined') {
    window.AtomAgent = window.AtomAgent || {};
    window.AtomAgent.deleteReminder = deleteReminder;
    window.AtomAgent.dismissReminder = dismissReminder;
    window.AtomAgent.createReminder = createReminder;
}
