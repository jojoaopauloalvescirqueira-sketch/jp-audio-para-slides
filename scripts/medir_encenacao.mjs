/* Exporta caixas de objetos e câmera do palco. A pose vem de poses.json. */
import {createRequire} from 'node:module';
import {writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';

const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||'playwright');
const [preview,out]=process.argv.slice(2);
const browser=await chromium.launch({headless:true,
  ...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
try {
  const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(preview).href+'?render=1');
  const report=await page.evaluate(async()=>{
    await document.fonts.ready;
    await window.assetsReady;
    const svg=document.querySelector('#palco');
    const data=JSON.parse(document.querySelector('#dados').textContent);
    const bounds=el=>{const r=el.getBoundingClientRect();return [r.left,r.top,r.right,r.bottom];};
    const title=el=>el.dataset.titulo==='sim';
    const graphics=el=>{
      const boxes=[...el.children].filter(child=>!title(child)).map(bounds);
      if(!boxes.length)return bounds(el);
      return [Math.min(...boxes.map(b=>b[0])),Math.min(...boxes.map(b=>b[1])),
        Math.max(...boxes.map(b=>b[2])),Math.max(...boxes.map(b=>b[3]))];
    };
    function labelOcclusion(){
      const stage=bounds(svg);
      const masses=[...svg.querySelectorAll('[data-massa]')].map(shape=>({
        shape, box:bounds(shape), inverse:shape.getScreenCTM().inverse()}));
      return [...svg.querySelectorAll('[data-rotulo-cena]')].filter(el=>{
        const [l,t,r,b]=bounds(el);
        if(l<stage[0]||t<stage[1]||r>stage[2]||b>stage[3])return true;
        if(r<=l||b<=t)return false;
        for(const {shape,box,inverse} of masses){
          const [x,y,w,z]=box;
          if(Math.min(r,w)-Math.max(l,x)<3||Math.min(b,z)-Math.max(t,y)<3)continue;
          for(const u of [.2,.4,.6,.8]){
            for(const v of [.25,.5,.75]){
              if(shape.isPointInFill(new DOMPoint(l+(r-l)*u,t+(b-t)*v).matrixTransform(inverse)))return true;
            }
          }
        }
        return false;
      }).map(el=>el.textContent);
    }
    const frames=[];
    for(let f=0;f<Math.round(data.duracao*30);f++){
      const scene=window.render(f/30);
      const floor=svg.querySelector('[data-parte=piso]');
      const m=(floor?.parentNode||svg).getScreenCTM();
      const matrix=[m.a,m.d,m.e,m.f];
      const explicit=[...svg.querySelectorAll('[data-objeto-cena]')];
      const legacy=[...svg.querySelectorAll('[data-elemento^=ideia-], [data-elemento=linha-do-tempo]')]
        .flatMap(g=>[...g.children].filter(el=>!title(el)).map((el,i)=>({
          id:g.dataset.elemento+'-'+i, box:bounds(el), actor:null, relation:null})));
      const objects=explicit.length?explicit.map(el=>({
        id:el.dataset.objetoCena, box:graphics(el), actor:el.dataset.ator||null,
        relation:el.dataset.relacao||null, abstract:el.dataset.abstrato==='sim'})):legacy;
      const titles=[...svg.querySelectorAll('[data-elemento=titulo] [data-titulo]')].map(bounds);
      const privateText=[...svg.querySelectorAll('text')].map(el=>el.querySelector('tspan')
        ?[...el.querySelectorAll('tspan:not([visibility=hidden])')].map(span=>span.textContent).join('')
        :el.textContent);
      frames.push({f,scene,matrix,objects,titles,privateText,labelOcclusion:labelOcclusion()});
    }
    return {frames,active:Math.round((data.repouso??data.duracao)*30),scenes:data.cenas};
  });
  if(errors.length)throw Error(errors.join('\n'));
  await writeFile(out,JSON.stringify(report)+'\n');
} finally {await browser.close();}
