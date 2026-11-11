// Service Worker for THE New ASMA PWA
const CACHE_NAME = 'asma-pwa-v42';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  '/manifest.json',
  '/assets/band_logo.png'
];

self.addEventListener('install', (e) => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) return caches.delete(k);
        })
      )
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = e.request.url;

  // CRITICAL: NEVER intercept /api/ endpoints or PDF download streams.
  // Intercepting attachments in ServiceWorker causes Chromium to fail downloads with about:blank!
  if (url.includes('/api/')) {
    return;
  }

  // Network-First for static assets (fallback to cache on network error or 5xx during cloud restart)
  e.respondWith(
    fetch(e.request)
      .then((response) => {
        if (response && response.status === 200 && e.request.method === 'GET') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
          return response;
        }
        if (response && response.status >= 500) {
          return caches.match(e.request, { ignoreSearch: true }).then((cached) => cached || response);
        }
        return response;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true }))
  );
});
