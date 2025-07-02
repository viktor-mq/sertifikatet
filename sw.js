/**
 * Sertifikatet Service Worker
 * Phase 10: Offline Support and PWA
 */

const CACHE_NAME = 'sertifikatet-v1.0.0';
const OFFLINE_PAGE = '/offline';

// Files to cache for offline functionality
const STATIC_CACHE_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/js/quiz.js',
    '/static/manifest.json',
    '/static/images/profiles/selskapslogo.png',
    '/offline',
    
    // Core pages
    '/quiz/categories',
    '/video',
    '/game',
    '/learning',
    
    // External dependencies
    'https://cdn.tailwindcss.com',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
    /\/api\/quiz\/.*/,
    /\/api\/progress\/.*/,
    /\/api\/leaderboard\/.*/
];

// Background sync tags
const SYNC_TAGS = {
    QUIZ_SUBMISSION: 'quiz-submission',
    PROGRESS_UPDATE: 'progress-update',
    FEEDBACK_SUBMISSION: 'feedback-submission'
};

// Install event - cache static resources
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching static files');
                return cache.addAll(STATIC_CACHE_FILES);
            })
            .then(() => {
                console.log('Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('Service Worker: Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle network requests
self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);
    
    // Skip non-HTTP requests
    if (!request.url.startsWith('http')) {
        return;
    }
    
    // Handle different types of requests
    if (request.method === 'GET') {
        event.respondWith(handleGetRequest(request));
    } else if (request.method === 'POST') {
        event.respondWith(handlePostRequest(request));
    }
});

// Handle GET requests with cache strategies
async function handleGetRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Strategy 1: Cache First for static assets
        if (isStaticAsset(url)) {
            return await cacheFirst(request);
        }
        
        // Strategy 2: Network First for API calls
        if (isApiCall(url)) {
            return await networkFirst(request);
        }
        
        // Strategy 3: Stale While Revalidate for pages
        if (isPageRequest(url)) {
            return await staleWhileRevalidate(request);
        }
        
        // Default: Network First
        return await networkFirst(request);
        
    } catch (error) {
        console.error('Service Worker: Fetch failed', error);
        return await handleOfflineFallback(request);
    }
}

// Handle POST requests for offline queue
async function handlePostRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first
        const response = await fetch(request);
        
        if (response.ok) {
            return response;
        } else {
            throw new Error('Network request failed');
        }
        
    } catch (error) {
        console.log('Service Worker: POST request failed, queuing for background sync');
        
        // Store request for background sync
        await queueRequest(request);
        
        // Return offline response
        return new Response(
            JSON.stringify({
                success: false,
                message: 'Request queued for when connection is restored',
                offline: true
            }),
            {
                status: 202,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Cache strategies
async function cacheFirst(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
}

async function networkFirst(request) {
    const cache = await caches.open(CACHE_NAME);
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
        
    } catch (error) {
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        throw error;
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    // Return cached response immediately if available
    const responsePromise = cachedResponse || fetch(request);
    
    // Update cache in background
    fetch(request)
        .then(response => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
        })
        .catch(error => {
            console.log('Service Worker: Background update failed', error);
        });
    
    return responsePromise;
}

// Offline fallbacks
async function handleOfflineFallback(request) {
    const url = new URL(request.url);
    
    // Return cached version if available
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
        return cache.match(OFFLINE_PAGE);
    }
    
    // Return offline JSON for API requests
    if (isApiCall(url)) {
        return new Response(
            JSON.stringify({
                success: false,
                message: 'You are currently offline. Please check your connection.',
                offline: true
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
    
    // Return empty response for other requests
    return new Response('Offline', { status: 503 });
}

// Request classification helpers
function isStaticAsset(url) {
    return url.pathname.match(/\.(css|js|png|jpg|jpeg|gif|svg|ico|woff2?|ttf)$/i) ||
           url.hostname !== self.location.hostname;
}

function isApiCall(url) {
    return url.pathname.startsWith('/api/') ||
           API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isPageRequest(url) {
    return url.hostname === self.location.hostname &&
           !url.pathname.startsWith('/api/') &&
           !isStaticAsset(url);
}

// Background sync for offline requests
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    switch (event.tag) {
        case SYNC_TAGS.QUIZ_SUBMISSION:
            event.waitUntil(syncQuizSubmissions());
            break;
        case SYNC_TAGS.PROGRESS_UPDATE:
            event.waitUntil(syncProgressUpdates());
            break;
        case SYNC_TAGS.FEEDBACK_SUBMISSION:
            event.waitUntil(syncFeedbackSubmissions());
            break;
        default:
            event.waitUntil(syncAllPendingRequests());
    }
});

// Queue requests for background sync
async function queueRequest(request) {
    const requestData = {
        url: request.url,
        method: request.method,
        headers: Object.fromEntries(request.headers.entries()),
        body: await request.text(),
        timestamp: Date.now()
    };
    
    // Store in IndexedDB
    await storeInIndexedDB('pending-requests', requestData);
    
    // Register background sync
    const tag = determineRequestTag(request.url);
    await self.registration.sync.register(tag);
}

// Sync functions
async function syncQuizSubmissions() {
    const requests = await getFromIndexedDB('pending-requests', (req) => 
        req.url.includes('/quiz/') && req.method === 'POST'
    );
    
    for (const request of requests) {
        await retryRequest(request);
    }
}

async function syncProgressUpdates() {
    const requests = await getFromIndexedDB('pending-requests', (req) => 
        req.url.includes('/api/progress') && req.method === 'POST'
    );
    
    for (const request of requests) {
        await retryRequest(request);
    }
}

async function syncFeedbackSubmissions() {
    const requests = await getFromIndexedDB('pending-requests', (req) => 
        req.url.includes('/feedback') && req.method === 'POST'
    );
    
    for (const request of requests) {
        await retryRequest(request);
    }
}

async function syncAllPendingRequests() {
    const requests = await getFromIndexedDB('pending-requests');
    
    for (const request of requests) {
        await retryRequest(request);
    }
}

async function retryRequest(requestData) {
    try {
        const response = await fetch(requestData.url, {
            method: requestData.method,
            headers: requestData.headers,
            body: requestData.body
        });
        
        if (response.ok) {
            console.log('Service Worker: Request synced successfully', requestData.url);
            await removeFromIndexedDB('pending-requests', requestData.timestamp);
            
            // Notify client about successful sync
            self.clients.matchAll().then(clients => {
                clients.forEach(client => {
                    client.postMessage({
                        type: 'SYNC_SUCCESS',
                        url: requestData.url,
                        timestamp: requestData.timestamp
                    });
                });
            });
        } else {
            throw new Error(`Request failed with status ${response.status}`);
        }
        
    } catch (error) {
        console.error('Service Worker: Request sync failed', error);
        
        // Retry later if request is not too old (24 hours)
        const age = Date.now() - requestData.timestamp;
        if (age > 24 * 60 * 60 * 1000) {
            console.log('Service Worker: Removing old request', requestData.url);
            await removeFromIndexedDB('pending-requests', requestData.timestamp);
        }
    }
}

// Helper functions
function determineRequestTag(url) {
    if (url.includes('/quiz/')) return SYNC_TAGS.QUIZ_SUBMISSION;
    if (url.includes('/api/progress')) return SYNC_TAGS.PROGRESS_UPDATE;
    if (url.includes('/feedback')) return SYNC_TAGS.FEEDBACK_SUBMISSION;
    return 'generic-sync';
}

// IndexedDB helpers
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('SertifikatetDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('pending-requests')) {
                const store = db.createObjectStore('pending-requests', { keyPath: 'timestamp' });
                store.createIndex('url', 'url', { unique: false });
                store.createIndex('method', 'method', { unique: false });
            }
        };
    });
}

async function storeInIndexedDB(storeName, data) {
    const db = await openIndexedDB();
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    return store.add(data);
}

async function getFromIndexedDB(storeName, filter) {
    const db = await openIndexedDB();
    const transaction = db.transaction([storeName], 'readonly');
    const store = transaction.objectStore(storeName);
    
    return new Promise((resolve, reject) => {
        const results = [];
        const cursor = store.openCursor();
        
        cursor.onsuccess = (event) => {
            const cursor = event.target.result;
            if (cursor) {
                const value = cursor.value;
                if (!filter || filter(value)) {
                    results.push(value);
                }
                cursor.continue();
            } else {
                resolve(results);
            }
        };
        
        cursor.onerror = () => reject(cursor.error);
    });
}

async function removeFromIndexedDB(storeName, key) {
    const db = await openIndexedDB();
    const transaction = db.transaction([storeName], 'readwrite');
    const store = transaction.objectStore(storeName);
    return store.delete(key);
}

// Message handling for client communication
self.addEventListener('message', (event) => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
        case 'CACHE_QUIZ_DATA':
            cacheQuizData(data);
            break;
        case 'GET_CACHE_STATUS':
            getCacheStatus().then(status => {
                event.ports[0].postMessage(status);
            });
            break;
        case 'CLEAR_CACHE':
            clearCache().then(() => {
                event.ports[0].postMessage({ success: true });
            });
            break;
    }
});

// Cache quiz data for offline use
async function cacheQuizData(quizData) {
    const cache = await caches.open(CACHE_NAME);
    
    const response = new Response(JSON.stringify(quizData), {
        headers: { 'Content-Type': 'application/json' }
    });
    
    await cache.put('/api/quiz/offline-data', response);
    console.log('Service Worker: Quiz data cached for offline use');
}

// Get cache status
async function getCacheStatus() {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    
    return {
        cacheSize: keys.length,
        lastUpdated: Date.now(),
        version: CACHE_NAME
    };
}

// Clear cache
async function clearCache() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('Service Worker: All caches cleared');
}

// Periodic cache cleanup
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'cache-cleanup') {
        event.waitUntil(cleanupOldCache());
    }
});

async function cleanupOldCache() {
    const cache = await caches.open(CACHE_NAME);
    const keys = await cache.keys();
    
    // Remove old entries (older than 7 days)
    const maxAge = 7 * 24 * 60 * 60 * 1000; // 7 days
    const now = Date.now();
    
    for (const request of keys) {
        const response = await cache.match(request);
        const dateHeader = response.headers.get('date');
        
        if (dateHeader) {
            const responseDate = new Date(dateHeader).getTime();
            if (now - responseDate > maxAge) {
                await cache.delete(request);
                console.log('Service Worker: Removed old cache entry', request.url);
            }
        }
    }
}

console.log('Service Worker: Script loaded successfully');
