// 用法(在 Mac): node snap.mjs <outdir> <name>=<url>[@WxH[:full]] ...   例: node snap.mjs shots home=http://localhost:8082/@1440x900:full
import puppeteer from 'puppeteer-core';
import fs from 'fs';
const [out, ...items] = process.argv.slice(2); fs.mkdirSync(out, { recursive: true });
const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-sandbox', '--user-data-dir=/tmp/chrome-prof-snap-' + process.pid, '--autoplay-policy=no-user-gesture-required'] });
for (const it of items) {
  const [name, rest] = [it.slice(0, it.indexOf('=')), it.slice(it.indexOf('=') + 1)];
  const [url, vp = '1440x900'] = rest.split('@'); const full = vp.endsWith(':full'); const [w, h] = vp.replace(':full', '').split('x').map(Number);
  const p = await b.newPage(); await p.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
  p.on('pageerror', e => console.log(name, 'PAGEERROR', e.message)); p.on('console', m => { if (m.type() === 'error') console.log(name, 'CONSOLE', m.text()); }); p.on('requestfailed', r => console.log(name, 'REQFAIL', r.url().slice(0, 100)));
  await p.goto(url, { waitUntil: 'networkidle2', timeout: 60000 }); await p.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { scrollTo(0, y); await new Promise(r => setTimeout(r, 80)); } scrollTo(0, 0); }); await new Promise(r => setTimeout(r, 900));
  await p.screenshot({ path: `${out}/${name}.jpg`, type: 'jpeg', quality: 80, fullPage: full }); await p.close();
}
await Promise.race([b.close(), new Promise(r => setTimeout(r, 4000))]); process.exit(0);
