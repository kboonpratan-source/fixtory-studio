// Fixtory Admin — service worker: รับแจ้งเตือนออเดอร์ใหม่ / สลิปโอน
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (err) { d = { title: 'Fixtory', body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'Fixtory Admin', {
    body: d.body || '',
    icon: '/icons/icon-dark-192.png',
    badge: '/icons/icon-mono-512.png',
    tag: d.tag || undefined,
    renotify: !!d.tag,
    data: { url: d.url || '/admin.html' }
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL(e.notification.data && e.notification.data.url || '/admin.html', self.location.origin).href;
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
    for (const c of list) { if ('focus' in c) { c.navigate(url).catch(() => {}); return c.focus(); } }
    return self.clients.openWindow(url);
  }));
});
