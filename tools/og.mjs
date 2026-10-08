// 用法(在 Mac): node tools/og.mjs   → 生成 og-en-v2.png / og-zh-v2.png（1200×630）
import puppeteer from 'puppeteer-core'; import path from 'path'; import { fileURLToPath } from 'url';
const dir = path.dirname(fileURLToPath(import.meta.url)), root = path.resolve(dir, '..');
const b = await puppeteer.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true, args: ['--no-sandbox', '--allow-file-access-from-files', '--user-data-dir=/tmp/chrome-prof-og-' + process.pid] });
for (const L of ['en', 'zh']) {
  const p = await b.newPage(); await p.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
  await p.goto(`file://${dir}/og.html?${L}`, { waitUntil: 'networkidle0' }); await new Promise(r => setTimeout(r, 500));
  await p.screenshot({ path: `${root}/og-${L}-v2.png`, type: 'png' }); await p.close();
}
await Promise.race([b.close(), new Promise(r => setTimeout(r, 4000))]); process.exit(0);
