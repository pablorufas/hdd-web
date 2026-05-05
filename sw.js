// HdD — Service Worker
// Estrategia: cache-first para assets, network-first para artículos

const CACHE_NAME = 'hdd-v2';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/noticias.html',
  '/educacion.html',
  '/newsletter.html',
  '/manifiesto.html',
  '/assets/style.css',
  '/assets/script.js',
  '/assets/icons/icon-192.png',
  '/assets/icons/icon-512.png'
];

// Instalar: precachear assets estáticos
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// Activar: limpiar caches antiguas
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Fetch: cache-first para CSS/JS/imágenes, network-first para HTML
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Solo manejar mismo origen
  if (url.origin !== location.origin) return;

  const isAsset = /\.(css|js|png|jpg|jpeg|svg|woff2|ico)$/.test(url.pathname);

  if (isAsset) {
    // Cache-first
    event.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
        return response;
      }))
    );
  } else {
    // Network-first con cache: 'no-cache' para que el CDN de GitHub Pages
    // no sirva versiones antiguas — el navegador siempre pide contenido fresco
    event.respondWith(
      fetch(new Request(request, { cache: 'no-cache' }))
        .then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request).then(cached => cached || caches.match('/index.html')))
    );
  }
});
