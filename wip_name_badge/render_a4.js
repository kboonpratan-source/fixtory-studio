// A4 สำหรับปริ้นต์บูท: node wip_name_badge/render_a4.js → wip_name_badge/poster_a4_src.png (สูง 3508 px = A4 @300dpi)
// แล้วรัน: python3 wip_name_badge/make_a4.py → name_pop_poster_a4.pdf (ที่ root ของ branch)
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1024, height: 1536 }, deviceScaleFactor: 3508 / 1536 });
  await p.goto('file://' + path.join(__dirname, 'name_badge_poster_th.html'));
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(300);
  await p.screenshot({ path: path.join(__dirname, 'poster_a4_src.png'), type: 'png' });
  await b.close();
})();
