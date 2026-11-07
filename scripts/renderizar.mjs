import {createRequire} from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import {pathToFileURL} from 'node:url';

const out=path.resolve(process.argv[2]);
const require=createRequire(import.meta.url);
let chromium;
try { ({chromium}=require('playwright')); }
catch {
  try { ({chromium}=createRequire(path.join(out,'..','package.json'))('playwright')); }
  catch {
    if (!process.env.PLAYWRIGHT_MODULE) throw new Error('Instale playwright no projeto ou defina PLAYWRIGHT_MODULE.');
    ({chromium}=require(process.env.PLAYWRIGHT_MODULE));
  }
}
const only=new Set((process.argv[3]||'').split(',').filter(Boolean));
const options={headless:true};
if(process.env.CHROME_PATH) options.executablePath=process.env.CHROME_PATH;
const browser=await chromium.launch(options);
const checks=[];
try {
  const page=await browser.newPage();
  await page.goto(pathToFileURL(path.join(out,'apresentacao.html')).href+'?render=');
  await page.evaluate(()=>document.fonts.ready);
  const {size,scenes}=await page.evaluate(()=>({size:window.sceneSize,scenes:window.sceneData}));
  await page.setViewportSize({width:size[0],height:size[1]});
  for(const scene of scenes) {
    if(only.size&&!only.has(scene.id)) continue;
    await page.evaluate(id=>window.show(id),scene.id);
    await page.evaluate(async()=>Promise.all([...document.images].filter(i=>i.closest('.active')).map(i=>i.decode())));
    const issues=await page.evaluate(()=>{
      const slide=document.querySelector('.slide.active');
      const box=slide.getBoundingClientRect();
      const vertical=box.width===1080&&box.height===1920;
      const ymin=box.top+(vertical?370:.079*box.height);
      const ymax=box.top+(vertical?1430:.921*box.height);
      const arr=[],texts=[];
      for(const e of slide.querySelectorAll('h1,h2,p,.caption,.note,.source')) {
        if(!e.textContent.trim()) continue;
        const r=e.getBoundingClientRect();
        if(!r.width||!r.height) continue;
        const item={tag:e.className||e.tagName,text:e.textContent};
        if(e.scrollWidth>e.clientWidth+2) arr.push({...item,erro:'overflow'});
        if(r.left<box.left+.079*box.width||r.right>box.right-.079*box.width||r.top<ymin||r.bottom>ymax)
          arr.push({...item,erro:'margem',rect:{x:r.x,y:r.y,w:r.width,h:r.height}});
        texts.push({r,item});
      }
      for(let i=0;i<texts.length;i++) for(let j=i+1;j<texts.length;j++) {
        const a=texts[i].r,b=texts[j].r;
        if(Math.min(a.right,b.right)-Math.max(a.left,b.left)>2&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2)
          arr.push({erro:'sobreposicao',textos:[texts[i].item.text,texts[j].item.text]});
      }
      return arr;
    });
    checks.push({slide:scene.id,issues});
    if(issues.length) console.log(scene.id,JSON.stringify(issues));
    await page.screenshot({path:path.join(out,'png',scene.id+'.png')});
  }
  fs.writeFileSync(path.join(out,only.size?'validacao_layout-amostra.json':'validacao_layout.json'),JSON.stringify(checks,null,2));
} finally { await browser.close(); }
if(checks.some(c=>c.issues.length)) throw new Error('Layout com problemas; veja validacao_layout.json.');
