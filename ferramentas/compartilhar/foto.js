const { chromium } = require('playwright');
(async () => {
  const [html, out, w, h] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  await p.goto('file://' + require('path').resolve(html)); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(400);
  await p.locator('#c').screenshot({ path: out, type: 'jpeg', quality: 88 }); await b.close();
})();
