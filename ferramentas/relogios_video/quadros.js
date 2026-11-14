// tira alguns quadros para conferir antes de filmar
const { chromium } = require('playwright');
(async () => {
  const [arq, ...ts] = process.argv.slice(2);
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 720, height: 1280 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + require('path').resolve(arq));
  await pg.evaluate(() => window.pronto); await pg.waitForTimeout(600);
  for (const t of ts) { await pg.evaluate(x => window.seek(x), +t); await pg.screenshot({ path: 'q-' + t + '.jpg', type: 'jpeg', quality: 90, clip: { x: 0, y: 0, width: 720, height: 1280 } }); }
  console.log('fontes:', await pg.evaluate(() => [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight + ' ' + f.style).join(' | ')));
  await b.close();
})();
