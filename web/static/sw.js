/**
 * Service Worker - AtomAgent PWA
 * Offline support and caching
 */

const CACHE_NAME = 'atomagent-v1';
const STATIC_CACHE = 'atomagent-static-v1';

// Static assets to cache
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/css/variables.css',
    '/static/css/sidebar.css',
    '/static/css/chat.css',
    '/static/css/panels.css',
    '/static/css/buttons.css',
    '/static/css/modal.css',
    '/static/css/mobile.css',
    '/static/css/responsive.css',
    '/static/js/app.js',
    '/static/js/websocket.js',
    '/static/js/chat.js',
    '/static/js/sessions.js',
    '/static/js/mobile.js',
    '/static/js/state.js',
    '/static/js/ui.js',
    '/static/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => self.skipWaiting())
            .catch((err) => {
                console.error('[SW] Cache failed:', err);
            })
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => name !== CACHE_NAME && name !== STATIC_CACHE)
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip WebSocket and API requests
    if (url.pathname.startsWith('/ws/') || 
        url.pathname.startsWith('/api/') ||
        request.method !== 'GET') {
        return;
    }
    
    // Cache-first for static assets
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request)
                .then((cached) => {
                    if (cached) {
                        return cached;
                    }
                    return fetch(request)
                        .then((response) => {
                            if (response.ok) {
                                const clone = response.clone();
                                caches.open(STATIC_CACHE)
                                    .then((cache) => cache.put(request, clone));
                            }
                            return response;
                        });
                })
        );
        return;
    }
    
    // Network-first for HTML
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    const clone = response.clone();
                    caches.open(CACHE_NAME)
                        .then((cache) => cache.put(request, clone));
                    return response;
                })
                .catch(() => {
                    return caches.match(request)
                        .then((cached) => cached || caches.match('/'));
                })
        );
        return;
    }
});

// Background sync for offline messages
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-messages') {
        console.log('[SW] Syncing offline messages...');
        // Implement offline message sync if needed
    }
});

// Push notifications
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const data = event.data.json();
    
    event.waitUntil(
        self.registration.showNotification(data.title || 'AtomAgent', {
            body: data.body || 'Yeni bildirim',
            icon: '/static/icons/icon-192.png',
            badge: '/static/icons/icon-72.png',
            tag: data.tag || 'atomagent-notification',
            data: data.url || '/'
        })
    );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Focus existing window if open
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Open new window
                if (clients.openWindow) {
                    return clients.openWindow(event.notification.data || '/');
                }
            })
    );
});

console.log('[SW] Service worker loaded');
