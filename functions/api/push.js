// Fixtory Admin — ส่ง Web Push ไปยังแอปที่เปิดการแจ้งเตือนไว้ (Cloudflare Pages Function: POST /api/push)
// Apps Script เป็นผู้เรียก ส่งรายการเครื่องที่สมัครไว้ + ข้อความ + กุญแจ VAPID มาในคำขอ (ไม่มีความลับเก็บในไฟล์นี้)
// คำขอต้องมี X-Fx-Secret ที่ SHA-256 ตรงกับค่าด้านล่าง
const SECRET_SHA256 = '83c1bd36333cd90fbd3916fe279e3e9b004eab38c6b25109dc9199ff34570e46';

const te = new TextEncoder();
const b64u = {
  enc(buf) { let s = ''; new Uint8Array(buf).forEach(b => s += String.fromCharCode(b)); return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''); },
  dec(str) { str = str.replace(/-/g, '+').replace(/_/g, '/'); while (str.length % 4) str += '='; const b = atob(str); const u = new Uint8Array(b.length); for (let i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
};
const cat = (...a) => { const n = a.reduce((x, y) => x + y.length, 0), o = new Uint8Array(n); let i = 0; a.forEach(x => { o.set(x, i); i += x.length; }); return o; };
async function hmac(key, data) { const k = await crypto.subtle.importKey('raw', key, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']); return new Uint8Array(await crypto.subtle.sign('HMAC', k, data)); }
async function hkdf(salt, ikm, info, len) { const prk = await hmac(salt, ikm); return (await hmac(prk, cat(info, new Uint8Array([1])))).slice(0, len); }

// RFC 8291 (aes128gcm)
async function encrypt(sub, payload) {
  const uaPub = b64u.dec(sub.keys.p256dh), auth = b64u.dec(sub.keys.auth);
  const as = await crypto.subtle.generateKey({ name: 'ECDH', namedCurve: 'P-256' }, true, ['deriveBits']);
  const asPub = new Uint8Array(await crypto.subtle.exportKey('raw', as.publicKey));
  const uaKey = await crypto.subtle.importKey('raw', uaPub, { name: 'ECDH', namedCurve: 'P-256' }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: 'ECDH', public: uaKey }, as.privateKey, 256));
  const ikm = await hkdf(auth, shared, cat(te.encode('WebPush: info\0'), uaPub, asPub), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, te.encode('Content-Encoding: aes128gcm\0'), 16);
  const nonce = await hkdf(salt, ikm, te.encode('Content-Encoding: nonce\0'), 12);
  const key = await crypto.subtle.importKey('raw', cek, 'AES-GCM', false, ['encrypt']);
  const ct = new Uint8Array(await crypto.subtle.encrypt({ name: 'AES-GCM', iv: nonce }, key, cat(te.encode(payload), new Uint8Array([2]))));
  const rs = new Uint8Array([0, 0, 16, 0]);
  return cat(salt, rs, new Uint8Array([asPub.length]), asPub, ct);
}

async function vapidAuth(endpoint, vapid) {
  const aud = new URL(endpoint).origin;
  const head = b64u.enc(te.encode(JSON.stringify({ typ: 'JWT', alg: 'ES256' })));
  const body = b64u.enc(te.encode(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + 12 * 3600, sub: vapid.subject })));
  const key = await crypto.subtle.importKey('jwk', vapid.privateJwk, { name: 'ECDSA', namedCurve: 'P-256' }, false, ['sign']);
  const sig = await crypto.subtle.sign({ name: 'ECDSA', hash: 'SHA-256' }, key, te.encode(head + '.' + body));
  return 'vapid t=' + head + '.' + body + '.' + b64u.enc(sig) + ', k=' + vapid.publicKey;
}

export async function sendOne(sub, payload, vapid) {
  const bodyBytes = await encrypt(sub, payload);
  const r = await fetch(sub.endpoint, {
    method: 'POST',
    headers: { 'Content-Encoding': 'aes128gcm', 'Content-Type': 'application/octet-stream', TTL: '86400', Urgency: 'high', Authorization: await vapidAuth(sub.endpoint, vapid) },
    body: bodyBytes
  });
  return r.status;
}

export async function onRequestPost({ request }) {
  const secret = request.headers.get('X-Fx-Secret') || '';
  const h = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', te.encode(secret)))).map(b => b.toString(16).padStart(2, '0')).join('');
  if (h !== SECRET_SHA256) return new Response(JSON.stringify({ ok: false, error: 'forbidden' }), { status: 403 });
  let d; try { d = await request.json(); } catch (e) { return new Response('{"ok":false}', { status: 400 }); }
  const payload = JSON.stringify(d.payload || {});
  const results = await Promise.all((d.subs || []).map(async s => {
    try { return { endpoint: s.endpoint, status: await sendOne(s, payload, d.vapid) }; }
    catch (e) { return { endpoint: s.endpoint, status: 0, error: String(e) }; }
  }));
  return new Response(JSON.stringify({ ok: true, results }), { headers: { 'Content-Type': 'application/json' } });
}

export async function onRequestGet() {
  return new Response('Fixtory push relay is running', { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
}
