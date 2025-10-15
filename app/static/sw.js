const CACHE_NAME = 'republica-manager-v1';
const urlsToCache = [
    '/',
    '/escala',
    // Adicione aqui outras URLs importantes que você quer que funcionem offline
];

// Instala o Service Worker e adiciona os arquivos ao cache
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
        .then(cache => {
            console.log('Cache aberto');
            return cache.addAll(urlsToCache);
        })
    );
});

// Intercepta as requisições e serve do cache se disponível
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
        .then(response => {
            // Se encontrar no cache, retorna o cache. Senão, faz a requisição normal.
            return response || fetch(event.request);
        })
    );
});
