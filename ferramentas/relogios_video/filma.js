// filma a página (window.seek(t)) em cenas: um arquivo .mp4 por cena, depois junta sem recodificar
const { chromium } = require('playwright');
const { spawn, execFileSync } = require('child_process');
const fs = require('fs'), path = require('path');
(async () => {
  const [arq, saida, durStr, ...cortes] = process.argv.slice(2);
  const FPS = 30, DUR = +durStr, C = [0, ...cortes.map(Number), DUR];
  const b = await chromium.launch();
  const pg = await b.newPage({ viewport: { width: 720, height: 1280 }, deviceScaleFactor: 1 });
  await pg.goto('file://' + path.resolve(arq));
  await pg.evaluate(() => window.pronto); await pg.waitForTimeout(700);
  const lista = [];
  for (let s = 0; s < C.length - 1; s++) {
    const tmp = `cena${s + 1}.tmp.mp4`, fim = `cena${s + 1}.mp4`;
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '20', '-preset', 'medium', '-pix_fmt', 'yuv420p', '-r', String(FPS), tmp]);
    let err = ''; ff.stderr.on('data', d => err += d);
    const f0 = Math.round(C[s] * FPS), f1 = Math.round(C[s + 1] * FPS);
    for (let f = f0; f < f1; f++) {
      await pg.evaluate(x => window.seek(x), f / FPS);
      const buf = await pg.screenshot({ type: 'jpeg', quality: 92, clip: { x: 0, y: 0, width: 720, height: 1280 } });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    const code = await new Promise(r => ff.on('close', r));
    if (code !== 0) { console.log('ffmpeg falhou na cena', s + 1, err); process.exit(1); }
    fs.renameSync(tmp, fim); lista.push(fim);
    console.log('cena', s + 1, f1 - f0, 'quadros');
  }
  await b.close();
  fs.writeFileSync('lista.txt', lista.map(f => `file '${f}'`).join('\n') + '\n');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', 'lista.txt', '-c', 'copy', 'mudo.tmp.mp4']);
  fs.renameSync('mudo.tmp.mp4', saida);
  console.log('ok', saida);
})();
