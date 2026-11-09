import {createRequire} from 'node:module';
import {writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';

const [preview, destination, rawWidth, rawHeight, rawCount] = process.argv.slice(2);
const [width,height,count]=[rawWidth,rawHeight,rawCount].map(Number);
const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH});
try {
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(preview).href+'?render=1');
  await page.evaluate(async()=>{await document.fonts.ready; await window.assetsReady;});
  const data=await page.evaluate(({width,height,count})=>{
    const svg=document.querySelector('#palco');
    const opacity=el=>{
      let value=1;
      for(let item=el;item!==svg;item=item.parentElement) value*=+(item.getAttribute('opacity')??1);
      return value;
    };
    const matrix=el=>{
      const m=el.getCTM();
      return [m.a,m.b,m.c,m.d,m.e,m.f];
    };
    const box=el=>{
      const b=el.getBoundingClientRect();
      return [b.x,b.y,b.width,b.height];
    };
    const frames=[];
    for(let index=0;index<count;index++){
      const scene=window.render(index/30);
      const text=[];
      for(const node of svg.querySelectorAll('text')){
        const spans=[...node.querySelectorAll('tspan')];
        for(const part of spans.length?spans:[node]){
          if(!part.textContent || getComputedStyle(part).visibility!=='visible' || opacity(part)<=.01 ||
              part.getNumberOfChars()===0)continue;
          const pos=part.getStartPositionOfChar(0);
          const style=getComputedStyle(part);
          text.push({value:part.textContent,x:pos.x,y:pos.y,advance:part.getComputedTextLength(),
            display:node.classList.contains('picto-display'),font_size:parseFloat(style.fontSize),
            color:'#'+style.fill.match(/\d+/g).slice(0,3).map(n=>(+n).toString(16).padStart(2,'0')).join(''),opacity:opacity(part),matrix:matrix(part),bbox:box(part)});
        }
      }
      const joints={};
      for(const el of svg.querySelectorAll('[data-figura-rig]')){
        joints[el.dataset.elemento]={};
        for(const joint of el.querySelectorAll('[data-articulacao]')){
          const p=new DOMPoint(+joint.getAttribute('cx'),+joint.getAttribute('cy')).matrixTransform(joint.getCTM());
          joints[el.dataset.elemento][joint.dataset.articulacao]=[p.x,p.y];
        }
      }
      const body=svg.cloneNode(true);
      body.setAttribute('width',width);
      body.setAttribute('height',height);
      body.removeAttribute('id');
      body.querySelectorAll('text,[data-articulacao],[data-eixo]').forEach(node=>node.remove());
      frames.push({index,scene,svg:new XMLSerializer().serializeToString(body),text,joints});
    }
    return {size:[width,height],fps:30,frames,events:window.animationEvents};
  },{width,height,count});
  if(errors.length)throw new Error(errors.join('\n'));
  await writeFile(destination,JSON.stringify(data));
} finally {
  await browser.close();
}
