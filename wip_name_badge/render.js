// เรนเดอร์โปสเตอร์: node wip_name_badge/render.js → wip_name_badge/name_badge_poster_th.jpg (1024×1536)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1024, height: 1536 }, deviceScaleFactor: 1 });
  await p.goto('file://' + path.join(__dirname, 'name_badge_poster_th.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  // ตรวจล้นขอบ
  const over = await p.evaluate(() => [...document.querySelectorAll('body *')].filter(e => {
    const r = e.getBoundingClientRect(); return r.right > 1024 || r.bottom > 1536 || r.left < 0 || r.top < 0;
  }).map(e => e.className || e.tagName));
  console.log('overflow:', JSON.stringify(over));
  console.log('fonts:', await p.evaluate(() => [...document.fonts].filter(f => f.status === 'loaded').length));
  await p.screenshot({ path: path.join(__dirname, 'name_badge_poster_th.jpg'), type: 'jpeg', quality: 92 });
  await b.close();
})();
