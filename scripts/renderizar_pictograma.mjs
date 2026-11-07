import {createRequire} from 'node:module';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const [html, destination, width, height, mode, argument] = process.argv.slice(2);
const require = createRequire(import.meta.url);
let playwright;
try {
  playwright = require('playwright');
} catch {
  try {
    playwright = createRequire(path.join(path.dirname(html), '..', 'package.json'))('playwright');
  } catch {
    if (!process.env.PLAYWRIGHT_MODULE) throw new Error('Instale playwright ou indique PLAYWRIGHT_MODULE.');
    playwright = require(process.env.PLAYWRIGHT_MODULE);
  }
}
const options = {headless: true};
if (process.env.CHROME_PATH) options.executablePath = process.env.CHROME_PATH;
const browser = await playwright.chromium.launch(options);
try {
  const page = await browser.newPage({viewport: {width: Number(width), height: Number(height)}, deviceScaleFactor: 1});
  const errors = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto(pathToFileURL(html).href + '?render=1');
  await page.evaluate(() => document.fonts.ready.then(() => true));
  await fs.mkdir(destination, {recursive: true});
  const stage = page.locator('#palco');
  const requests = mode === 'video' ? null : JSON.parse(await fs.readFile(argument, 'utf8'));
  const count = mode === 'video' ? Number(argument) : requests.length;
  for (let i = 0; i < count; i++) {
    const [name, t] = mode === 'video' ? [String(i).padStart(8, '0'), i / 30] : requests[i];
    await page.evaluate((time) => window.render(time), t);
    if (errors.length) throw new Error(errors.join('\n'));
    await stage.screenshot({path: path.join(destination, name + '.png'), timeout: 15000});
  }
  console.log(`${count} quadros Pictograma`);
} finally {
  await browser.close();
}
