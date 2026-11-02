/* Fixtory Admin — แถบเมนูล่างแบบแอป (ใช้ร่วมกันทุกหน้าหลังร้าน) */
(function () {
  var GAS_URL = 'https://script.google.com/macros/s/AKfycbwfy2uHH4QJOM851_HBz3eoUCbwBvnZo1fGzf8DNChs5hS03Ml-335eATS3XTbifVYo9Q/exec';
  var SHEET_URL = 'https://docs.google.com/spreadsheets/d/16uKGJIaiGbsmQmMO5gJtaC5GXyJ1CNR_v7U55-4geVM/edit';
  var CATALOG_URL = 'https://fixtory-studio.pages.dev/catalog';
  var key = ''; try { key = localStorage.getItem('fxLabelKey') || ''; } catch (e) {}
  var page = (location.pathname.split('/').pop() || 'admin.html').replace(/\.html$/, '');
  var P = {
    home: '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h5v-6h4v6h5V10"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="3.5" cy="6" r="1"/><circle cx="3.5" cy="12" r="1"/><circle cx="3.5" cy="18" r="1"/>',
    chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    more: '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    print: '<path d="M6 9V3h12v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M6 14h12v7H6z"/>',
    users: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    stock: '<path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 12l9 4 9-4M3 17l9 4 9-4"/>',
    coin: '<circle cx="12" cy="12" r="9"/><path d="M15 9.5c-.5-1-1.6-1.5-3-1.5-1.7 0-3 .8-3 2s1.3 1.7 3 2 3 .8 3 2-1.3 2-3 2c-1.4 0-2.5-.5-3-1.5M12 6v2M12 16v2"/>',
    sheet: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M4 9h16M4 15h16M10 3v18"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    cart: '<path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 2-1.5L21 8H6"/><circle cx="10" cy="20.5" r="1"/><circle cx="17" cy="20.5" r="1"/>',
    link: '<path d="M10 14a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1"/><path d="M14 10a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>'
  };
  function ic(k) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + P[k] + '</svg>'; }
  var standaloneNow = false; try { standaloneNow = matchMedia('(display-mode: standalone)').matches || navigator.standalone === true; } catch (e) {}
  var TABS = [['admin', 'home', 'หน้าแรก', 'admin.html'], ['orders', 'list', 'ออเดอร์', 'orders.html'], ['insights', 'chart', 'ยอดขาย', 'insights.html']];
  var MORE = [
    ['เครื่องมือร้าน'],
    ['print', 'พิมพ์ใบปะหน้า', 'labels.html'],
    ['users', 'ตัวแทน', 'agents.html'],
    ['stock', 'สต๊อก & ต้นทุน', 'dashboard.html'],
    ['coin', 'สรุปค่าคอมเซลล์', GAS_URL + '?report=commission&key=' + encodeURIComponent(key), 1],
    ['sheet', 'ชีตออเดอร์', SHEET_URL, 1],
    ['edit', 'แก้ข้อมูลสินค้า', 'https://claude.ai/artifact/464DJRbj5uyXQzqGRXmeTy', 1],
    ['หน้าของลูกค้า'],
    ['grid', 'แคตตาล็อก', 'catalog', 1],
    ['cart', 'หน้าสั่งซื้อ', 'shop-order.html', 1],
    ['link', 'คัดลอกลิงก์แคตตาล็อก', '#copy']
  ];
  var css = document.createElement('style');
  css.textContent =
    '.fxbar{display:none}' +
    '.fxthm{width:38px;height:38px;border-radius:12px;border:1px solid var(--line,#E6DDD3);background:var(--surface,#fff);color:var(--muted,#7A6E66);display:inline-grid;place-items:center;cursor:pointer;padding:0;flex:none;margin-left:auto}' +
    '.fxthm svg{width:18px;height:18px}' +
    '.fxthm.fixed{position:fixed;top:calc(12px + env(safe-area-inset-top));right:12px;z-index:40}' +
    '@media (max-width:900px){' +
    'body{padding-bottom:calc(70px + env(safe-area-inset-bottom))!important}' +
    '.fxbar{display:grid;grid-template-columns:repeat(4,1fr);position:fixed;left:0;right:0;bottom:0;z-index:50;background:var(--surface,#fff);border-top:1px solid var(--line,#E6DDD3);padding:6px 6px calc(6px + env(safe-area-inset-bottom));box-shadow:0 -4px 16px rgba(0,0,0,.06)}' +
    '.fxbar a,.fxbar button{display:flex;flex-direction:column;align-items:center;gap:3px;text-decoration:none;border:0;background:none;font:inherit;font-size:11.5px;font-weight:600;color:var(--muted,#7A6E66);padding:4px 0;cursor:pointer;border-radius:12px}' +
    '.fxbar svg{width:23px;height:23px}' +
    '.fxbar .on{color:var(--accent,#C4704B)}' +
    '.fxbar .on svg{stroke-width:2.4}}' +
    '.fxsheet{position:fixed;inset:0;z-index:60;background:rgba(0,0,0,.4);display:flex;align-items:flex-end;justify-content:center}' +
    '.fxsheet[hidden]{display:none}' +
    '.fxsheet .pn{background:var(--surface,#fff);color:var(--ink,#2C2420);width:100%;max-width:560px;border-radius:20px 20px 0 0;padding:8px 10px calc(14px + env(safe-area-inset-bottom));max-height:85vh;overflow:auto}' +
    '.fxsheet .gr{width:40px;height:4px;border-radius:4px;background:var(--line,#E6DDD3);margin:4px auto 6px}' +
    '.fxsheet h3{font-size:12px;color:var(--faint,#A89D94);font-weight:600;letter-spacing:.04em;margin:12px 12px 4px}' +
    '.fxsheet a{display:flex;align-items:center;gap:12px;padding:11px 12px;border-radius:12px;text-decoration:none;color:inherit;font-size:15px;font-weight:600}' +
    '.fxsheet a:active,.fxsheet a:hover{background:var(--sunk,color-mix(in srgb,var(--ink,#2C2420) 6%,transparent))}' +
    '.fxsheet a i{width:38px;height:38px;border-radius:11px;background:var(--accent-soft,color-mix(in srgb,var(--accent,#C4704B) 18%,transparent));color:var(--accent,#C4704B);display:grid;place-items:center;flex:none}' +
    '.fxsheet a i svg{width:20px;height:20px}' +
    '.fxsheet a span{flex:1}.fxsheet a small{font-size:12px;color:var(--faint,#A89D94);font-weight:400}';
  document.head.appendChild(css);

  var bar = document.createElement('nav');
  bar.className = 'fxbar'; bar.setAttribute('aria-label', 'เมนูหลังร้าน');
  bar.innerHTML = TABS.map(function (t) {
    return '<a href="' + t[3] + '"' + (page === t[0] ? ' class="on" aria-current="page"' : '') + '>' + ic(t[1]) + t[2] + '</a>';
  }).join('') + '<button type="button" id="fxMoreBtn"' + (['labels', 'agents'].indexOf(page) > -1 ? ' class="on"' : '') + '>' + ic('more') + 'เพิ่มเติม</button>';
  document.body.appendChild(bar);

  var sheet = document.createElement('div');
  sheet.className = 'fxsheet'; sheet.hidden = true; sheet.setAttribute('role', 'dialog'); sheet.setAttribute('aria-label', 'เมนูเพิ่มเติม');
  sheet.innerHTML = '<div class="pn"><div class="gr"></div>' + MORE.map(function (m) {
    if (m.length === 1) return '<h3>' + m[0] + '</h3>';
    var inApp = standaloneNow && !/^https?:/.test(m[2]);
    var ext = m[3] && !inApp ? ' target="_blank" rel="noopener"' : '';
    return '<a href="' + m[2] + '"' + ext + (m[2] === '#copy' ? ' id="fxCopy"' : '') + '><i>' + ic(m[0]) + '</i><span>' + m[1] + '</span>' + (m[3] ? '<small>↗</small>' : '') + '</a>';
  }).join('') + '</div>';
  document.body.appendChild(sheet);

  // ---------- ปุ่มสลับโหมดมืด/สว่าง (ใช้ค่าเดียวกับหน้าสั่งซื้อ: localStorage 'fx-theme') ----------
  var R = document.documentElement;
  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M4.6 4.6l1.6 1.6M17.8 17.8l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.6 19.4l1.6-1.6M17.8 6.2l1.6-1.6"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z"/></svg>';
  function themeNow() { return R.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); }
  var tb = document.createElement('button');
  tb.type = 'button'; tb.className = 'fxthm';
  function paintThm() {
    var d = themeNow() === 'dark';
    tb.innerHTML = d ? SUN : MOON; tb.title = d ? 'โหมดสว่าง' : 'โหมดมืด'; tb.setAttribute('aria-label', tb.title);
    var bg = getComputedStyle(document.body).backgroundColor;
    document.querySelectorAll('meta[name="theme-color"]').forEach(function (m) { m.setAttribute('content', bg); });
  }
  tb.onclick = function () {
    var t = themeNow() === 'dark' ? 'light' : 'dark';
    R.setAttribute('data-theme', t); try { localStorage.setItem('fx-theme', t); } catch (e) {}
    paintThm();
  };
  var slot = document.getElementById('reload');
  if (slot && slot.parentNode) slot.parentNode.insertBefore(tb, slot);
  else { var top = document.querySelector('.top'); if (top) top.appendChild(tb); else { tb.classList.add('fixed'); document.body.appendChild(tb); } }
  paintThm();
  try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paintThm); } catch (e) {}
  // ---------- ปุ่มย้อนกลับ (back) แบบแอป ----------
  var standalone = false; try { standalone = matchMedia('(display-mode: standalone)').matches || navigator.standalone === true; } catch (e) {}
  var isHome = page === 'admin' || page === '';
  function openSheet() { sheet.hidden = false; history.pushState({ fxSheet: 1 }, ''); }
  function closeSheet(viaBack) { if (sheet.hidden) return; sheet.hidden = true; if (!viaBack && history.state && history.state.fxSheet) history.back(); }
  document.getElementById('fxMoreBtn').onclick = openSheet;
  sheet.addEventListener('click', function (e) { if (e.target === sheet) closeSheet(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeSheet(); });
  // สลับหน้าจากแถบล่าง/เมนู: จากหน้าย่อยให้แทนที่หน้าเดิม เพื่อให้ back กลับหน้าแรกเสมอ
  function go(e) {
    var a = e.currentTarget, h = a.getAttribute('href');
    if (!h || a.target === '_blank' || h.charAt(0) === '#') return;
    e.preventDefault();
    var adminPage = /^(admin|orders|insights|labels|agents)\.html/.test(h);
    if (isHome || h === 'admin.html' || !adminPage) { location.href = h; } else { location.replace(h); }
  }
  bar.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', go); });
  sheet.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', go); });
  // เปิดหน้าย่อยตรง ๆ (ไม่มีหน้าแรกอยู่ข้างหลัง) → ใส่หน้าแรกไว้ใต้ เพื่อให้ back กลับหน้าแรก
  var first = false; try { first = !sessionStorage.getItem('fxNavStarted'); sessionStorage.setItem('fxNavStarted', '1'); } catch (e) {}
  if (standalone && !isHome && (first || history.length <= 1)) {
    var here = location.href;
    history.replaceState({ fxHome: 1 }, '', 'admin.html');
    history.pushState(null, '', here);
  }
  // หน้าแรก: กด back ครั้งแรกขึ้นเตือน ครั้งที่สองภายใน 2 วินาทีจึงออกจากแอป
  var toast = null, guardTimer = null;
  function showToast(t) {
    if (!toast) { toast = document.createElement('div'); toast.style.cssText = 'position:fixed;left:50%;bottom:calc(84px + env(safe-area-inset-bottom));transform:translateX(-50%);background:var(--ink,#2C2420);color:var(--bg,#fff);padding:10px 16px;border-radius:99px;font-size:14px;z-index:70;box-shadow:0 4px 16px rgba(0,0,0,.2);white-space:nowrap'; document.body.appendChild(toast); }
    toast.textContent = t; toast.hidden = false;
  }
  if (standalone && isHome && !(history.state && history.state.fxGuard)) history.pushState({ fxGuard: 1 }, '');
  window.addEventListener('popstate', function (e) {
    if (!sheet.hidden) { closeSheet(true); return; }
    if (e.state && e.state.fxHome && !isHome) { location.replace('admin.html'); return; }
    if (standalone && isHome && !(e.state && e.state.fxGuard)) {
      showToast('กดย้อนกลับอีกครั้งเพื่อออกจากแอป');
      clearTimeout(guardTimer);
      guardTimer = setTimeout(function () { if (toast) toast.hidden = true; history.pushState({ fxGuard: 1 }, ''); }, 2000);
    }
  });
  var cp = document.getElementById('fxCopy');
  cp.onclick = function (e) {
    e.preventDefault();
    var s = cp.querySelector('span');
    (navigator.clipboard ? navigator.clipboard.writeText(CATALOG_URL) : Promise.reject()).then(function () { s.textContent = 'คัดลอกแล้ว ✓'; }, function () { s.textContent = CATALOG_URL; });
    setTimeout(function () { s.textContent = 'คัดลอกลิงก์แคตตาล็อก'; }, 2500);
  };
})();
