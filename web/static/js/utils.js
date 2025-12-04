/**
 * AtomAgent - Utility Functions
 */

export function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

export function formatDate(isoString) {
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Az önce';
    if (diff < 3600000) return Math.floor(diff / 60000) + ' dk önce';
    if (diff < 86400000) return Math.floor(diff / 3600000) + ' saat önce';
    if (diff < 604800000) return Math.floor(diff / 86400000) + ' gün önce';
    
    return date.toLocaleDateString('tr-TR');
}

export function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
        marked.setOptions({
            highlight: function(code, lang) {
                if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return code;
            },
            breaks: true
        });
        return marked.parse(text);
    }
    return escapeHtml(text).replace(/\n/g, '<br>');
}

export function highlightCode() {
    if (typeof hljs !== 'undefined') {
        document.querySelectorAll('pre code').forEach(block => {
            hljs.highlightElement(block);
        });
    }
}

export function showNotification(message, type = 'success') {
    // TODO: Implement toast notification
    console.log(`[${type}] ${message}`);
}

export function scrollToBottom(element) {
    if (element) {
        element.scrollTop = element.scrollHeight;
    }
}
