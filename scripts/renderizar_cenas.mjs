import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const [html, destination, rawWidth, rawHeight, mode, argument, rawPages='4', assetsHash=''] = process.argv.slice(2);
const width=Number(rawWidth), height=Number(rawHeight), pages=Number(rawPages);
if (!Number.isInteger(pages) || pages < 1 || pages > 12) throw Error('Use entre 1 e 12 páginas.');
const require = createRequire(import.meta.url);
let playwright;
try { playwright = require('playwright'); }
catch {
  try { playwright = createRequire(path.join(path.dirname(html), '..', 'package.json'))('playwright'); }
  catch {
    if (!process.env.PLAYWRIGHT_MODULE) throw Error('Instale playwright ou indique PLAYWRIGHT_MODULE.');
    playwright = require(process.env.PLAYWRIGHT_MODULE);
  }
}
const options = {headless:true};
if (process.env.CHROME_PATH) options.executablePath=process.env.CHROME_PATH;
await fs.mkdir(destination,{recursive:true});
const manifest = path.join(destination,'render_manifest.json');
const video=mode==='video';
const withoutShadows=process.env.JP_RENDER_SEM_SOMBRAS==='1';
const withoutEffects=process.env.JP_RENDER_SEM_EFEITOS==='1';
const renderQuery=withoutShadows?'?render=1&sombras=desligadas':
  withoutEffects?'?render=1&efeitos=desligados':'?render=1';
const requests=video ? null : JSON.parse(await fs.readFile(argument,'utf8'));
const count=video ? Number(argument) : requests.length;
if (!Number.isInteger(count) || count < 1) throw Error('Número de quadros inválido.');
const hash=createHash('sha256').update(await fs.readFile(html)).update(assetsHash)
  .update(JSON.stringify({width,height,count,requests,fps:30,...(withoutShadows?{withoutShadows}: {}),...(withoutEffects?{withoutEffects}: {})})).digest('hex');
const existing=await fs.readFile(manifest,'utf8').then(JSON.parse).catch(()=>null);
const resume=video && existing?.sha256===hash;
if (video && !resume) {
  const files=await fs.readdir(destination);
  await Promise.all(files.filter(name=>/^\d{6}\.png$/.test(name)).map(name=>fs.unlink(path.join(destination,name))));
  await fs.writeFile(manifest,JSON.stringify({sha256:hash,count,width,height,fps:30}));
}
const browser=await playwright.chromium.launch(options);
let index=0, written=0;
try {
  async function renderPage() {
    const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
    const errors=[];
    page.on('pageerror',error=>errors.push(error.message));
    await page.goto(pathToFileURL(html).href+renderQuery);
    await page.evaluate(async()=>{ await document.fonts.ready; await window.assetsReady; });
    while (index<count) {
      const i=index++;
      const [name,t]=video ? [String(i).padStart(6,'0'),i/30] : requests[i];
      if (!/^[\w-]+$/.test(name)) throw Error('Nome de quadro inválido.');
      const file=path.join(destination,name+'.png');
      if (resume && await fs.stat(file).then(info=>info.size>32).catch(()=>false)) continue;
      const errorsGeometry=await page.evaluate(time=>{
        window.seek(time);
        const stage=document.getElementById('palco').getBoundingClientRect();
        return [...document.querySelectorAll('[data-seguro]')].filter(node=>{
          const b=node.getBoundingClientRect();
          const vertical=stage.height>stage.width;
          const limit=node.getAttribute('data-seguro')==='texto' && vertical;
          const eps=1;
          return b.left<stage.left-eps || b.right>stage.right+eps ||
            b.top<stage.top+(limit?370:0)-eps || b.bottom>stage.bottom-(limit?490:0)+eps ||
            (limit && b.bottom>stage.top+700 && b.right>stage.left+900+eps);
        }).map(node=>node.getAttribute('data-seguro'));
      },t);
      if (errors.length || errorsGeometry.length) throw Error([...errors,...errorsGeometry.map(v=>'Fora da área segura: '+v)].join('\n'));
      const png=await page.locator('#palco').screenshot({timeout:15000});
      const temporary=file+'.tmp';
      await fs.writeFile(temporary,png);
      await fs.rename(temporary,file);
      written++;
    }
    await page.close();
  }
  await Promise.all(Array.from({length:Math.min(count,pages)},()=>renderPage()));
  console.log(`${count} quadros · ${written} novos · ${count-written} retomados`);
} finally {
  await browser.close();
}
