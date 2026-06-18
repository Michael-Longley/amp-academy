/* tutor-contrib-pwa service worker */
const CACHE_VERSION = "{{ PWA_CACHE_VERSION }}";
const APP_SHELL_CACHE = "pwa-shell-v" + CACHE_VERSION;
const CONTENT_CACHE  = "pwa-content-v" + CACHE_VERSION;

const APP_SHELL_URLS = [
  "{{ PWA_START_URL }}",
  "/manifest.json",
  "/icons/icon-192.png",
  "/icons/icon-512.png",
  "/offline.html",
];

const APP_SHELL_PATTERNS = [
  /\.js(\?.*)?$/,
  /\.css(\?.*)?$/,
  /\/fonts\//,
];

const CONTENT_CACHE_TTL_MS = 24 * 60 * 60 * 1000;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(APP_SHELL_CACHE)
      .then((cache) => cache.addAll(APP_SHELL_URLS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => k !== APP_SHELL_CACHE && k !== CONTENT_CACHE)
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET" || !request.url.startsWith(self.location.origin)) return;
  const url = new URL(request.url);
  if (
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/oauth2/") ||
    url.pathname.startsWith("/login") ||
    url.pathname.startsWith("/logout")
  ) return;
  if (isAppShell(url.pathname)) {
    event.respondWith(cacheFirst(request, APP_SHELL_CACHE));
    return;
  }
  event.respondWith(networkFirst(request));
});

function isAppShell(pathname) {
  if (APP_SHELL_URLS.includes(pathname)) return true;
  return APP_SHELL_PATTERNS.some((re) => re.test(pathname));
}

async function cacheFirst(request, cacheName) {
  const cached = await caches.match(request, { cacheName });
  return cached || fetch(request);
}

async function networkFirst(request) {
  const cache = await caches.open(CONTENT_CACHE);
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cloned = response.clone();
      const headers = new Headers(cloned.headers);
      headers.set("x-sw-cached-at", Date.now().toString());
      const timestamped = new Response(await cloned.blob(), {
        status: cloned.status, statusText: cloned.statusText, headers,
      });
      cache.put(request, timestamped);
    }
    return response;
  } catch (_networkError) {
    const cached = await cache.match(request);
    if (cached) {
      const cachedAt = parseInt(cached.headers.get("x-sw-cached-at") || "0", 10);
      if (Date.now() - cachedAt < CONTENT_CACHE_TTL_MS) return cached;
    }
    return caches.match("/offline.html");
  }
}

self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; }
  catch (_) { data = { title: "Notification", body: event.data ? event.data.text() : "" }; }
  const { title = "Notification", body = "", url = "/" } = data;
  event.waitUntil(
    self.registration.showNotification(title, {
      body, icon: "/icons/icon-192.png", badge: "/icons/icon-192.png",
      data: { url }, requireInteraction: false,
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clients) => {
      for (const client of clients) {
        if (new URL(client.url).pathname === targetUrl && "focus" in client) return client.focus();
      }
      return self.clients.openWindow(targetUrl);
    })
  );
});
