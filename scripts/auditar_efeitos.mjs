import {createRequire} from 'node:module';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';

// Aplica as regras aos dados extraídos do SVG. Os testes injetam os mesmos defeitos.
export function inspecionar(rows){
  const failures=[];
  const first=rows.find(row=>row.strike);
  const prior=new Map();
  const known=new Set();
  for(const row of rows){
    const f=row.f;
    if((first&&f>=first.f+15&&row.negative)||row.premature)
      failures.push({codigo:'EC-073',quadro:f});
    if(row.occlusion||!row.same)
      failures.push({codigo:'EC-076',quadro:f});
    if(row.direction===false)
      failures.push({codigo:'EC-079',quadro:f});
    if(row.missingContact)
      failures.push({codigo:'EC-081',quadro:f});
    const hearts=new Map((row.hearts??[]).filter(obj=>obj.opacity>.15).map(obj=>[obj.id,obj]));
    for(const id of row.expectedHearts??[])known.add(id);
    for(const id of hearts.keys())known.add(id);
    for(const id of known){
      const before=prior.get(id), after=hearts.get(id);
      if(!after || (before&&Math.hypot(after.x-before.x,after.y-before.y)>85))
        failures.push({codigo:'EC-084',quadro:f,objeto:id});
      if(after)prior.set(id,after);
    }
  }
  return failures;
}

const called=process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url);
if(called){
  const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||'playwright');
  const [preview,output,widthArg='1080',heightArg='1920']=process.argv.slice(2);
  const [width,height]=[Number(widthArg),Number(heightArg)];
  const browser=await chromium.launch({headless:true,
    ...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
  try{
    await mkdir(output,{recursive:true});
    const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
    const errors=[];
    page.on('pageerror',e=>errors.push(e.message));
    await page.goto(pathToFileURL(path.resolve(preview)).href+'?render=1');
    await page.evaluate(async()=>{await document.fonts.ready;await window.assetsReady;});
    const result=await page.evaluate(()=>{
      const stage=document.querySelector('#palco');
      const button=document.querySelector('#alternar-efeitos');
      const data=JSON.parse(document.querySelector('#dados').textContent);
      const rows=[];
      const rect=node=>{
        const q=node.getBoundingClientRect();
        return [q.x,q.y,q.width,q.height];
      };
      const opacity=node=>{
        let o=1;
        for(let p=node;p&&p!==stage;p=p.parentElement)o*=+(p.getAttribute('opacity')??1);
        return o;
      };
      const shapeSnapshot=()=>JSON.stringify({
        actors:[...stage.querySelectorAll('[data-rig-anatomico] [data-massa]')].map(el=>
          [el.outerHTML,...rect(el)]),
        text:[...stage.querySelectorAll('text')].map(el=>[el.outerHTML,...rect(el)]),
        contacts:window.pictogramaQuadro?.actors.map(actor=>actor.contacts)
      });
      const [width,height]=data.dimensoes;
      const cue=data.coreografia.cues.virada.frame;
      const mask=new OffscreenCanvas(216,384),small=new OffscreenCanvas(108,192);
      const pen=mask.getContext('2d'), thumb=small.getContext('2d',{willReadFrequently:true});
      thumb.imageSmoothingQuality='high';
      function movingSilhouette(groups){
        pen.resetTransform();
        pen.clearRect(0,0,216,384);
        const sx=216/width,sy=384/height;
        for(const group of groups)for(const el of group.querySelectorAll('[data-massa]')){
          const m=el.getScreenCTM();
          pen.setTransform(m.a*sx,m.b*sy,m.c*sx,m.d*sy,m.e*sx,m.f*sy);
          pen.fillStyle=el.getAttribute('fill');
          if(el.tagName==='ellipse'){
            const prop=n=>Number(el.getAttribute(n));
            pen.beginPath();
            pen.ellipse(prop('cx'),prop('cy'),prop('rx'),prop('ry'),0,0,Math.PI*2);
            pen.fill();
          }else pen.fill(new Path2D(el.getAttribute('d')));
        }
        thumb.clearRect(0,0,108,192);
        thumb.drawImage(mask,0,0,108,192);
        const d=thumb.getImageData(0,0,108,192).data;
        let compact='';
        for(let i=0;i<d.length;i+=4){
          const y=Math.round(.2126*d[i]+.7152*d[i+1]+.0722*d[i+2]);
          compact+=String.fromCharCode(y,d[i+3]);
        }
        return btoa(compact);
      }
      for(let f=0;f<Math.round(window.duration*30);f++){
        window.render(f/30);
        const neg=stage.querySelector('[data-negacao]');
        const glyph=stage.querySelector('[data-letra=A]');
        const fx=[...stage.querySelectorAll('[data-fx]')];
        const active=fx.filter(el=>!el.dataset.fx.startsWith('contato:'));
        const groups=[...stage.querySelectorAll('[data-rig-anatomico]')];
        const actors=window.pictogramaQuadro?.actors??[];
        const visibleCaptions=[...stage.querySelectorAll('[data-palavra][visibility=visible]')];
        // Os nós decorativos ficam antes dos atores e das legendas na ordem de pintura.
        const occlusion=active.some(el=>groups.some(actor=>!(el.compareDocumentPosition(actor)&Node.DOCUMENT_POSITION_FOLLOWING)))||
          visibleCaptions.some(text=>fx.some(el=>!(el.compareDocumentPosition(text)&Node.DOCUMENT_POSITION_FOLLOWING)));
        const gradients=[...stage.querySelectorAll('[id^=fx-tonal]')];
        const direction=gradients.every(g=>g.tagName==='radialGradient'&&
          ['cx','cy'].every(k=>g.getAttribute(k)==='1'));
        const hearts=[...stage.querySelectorAll('[data-objeto-id]')].map(el=>{
          const [x,y,w,h]=rect(el);
          return {id:el.dataset.objetoId,opacity:opacity(el),x:x+w/2,y:y+h/2};
        });
        const expectedHearts=[];
        if(f>=data.coreografia.cues.receber.frame)expectedHearts.push('coracao-recebido');
        if(f>=data.coreografia.cues.fazer.frame+6)expectedHearts.push('coracao-oferecido');
        const dim=stage.querySelector('[data-fx=escurecimento]');
        const dimStrength=dim?Number(dim.getAttribute('opacity')):0;
        const dimPeak=dimStrength>.14;
        const onLift=f===data.coreografia.cues.levantar.frame;
        const shades=groups.map(group=>{
          const [x,y,w,h]=rect(group.querySelector('[data-massa=cabeca]'));
          const floor=stage.querySelector('[data-parte=piso]')?.getBoundingClientRect().y??1250;
          return {lit:[x+.29*w,y+.29*h],shade:[x+.73*w,y+.73*h],bg:[x-.07*w,y+h*.48],floor};
        });
        const contacts=fx.filter(el=>el.dataset.fx.startsWith('contato:')).map(el=>{
          const [x,y,w,h]=rect(el);
          return {alvo:el.dataset.fx.slice(8),p:[x+w*.5,y+h*.65],bg:[x+w*.12,y+h*.65],
            caixa:[x,y,w,h]};
        });
        const expected=actors.flatMap((actor,i)=>actor.contacts.filter(c=>/^pe[ED]$/.test(c.id))
          .map(c=>i+'-'+c.id.slice(-1)));
        const bench=stage.querySelector('[data-elemento=banco]');
        if(bench&&opacity(bench)>.45)expected.push('banco','banco-2');
        const supported=contacts.filter(c=>expected.includes(c.alvo));
        const missingContact=expected.some(id=>!supported.some(c=>c.alvo===id));
        const title=[...stage.querySelectorAll('[data-titulo=sim], [data-palavra][visibility=visible]')]
          .filter(el=>opacity(el)>=.94).map(el=>rect(el))
          .filter(([x,y,w,h])=>x>=0&&y>=0&&w>=5&&h>=5&&x+w<width&&y+h<height);
        const motion=movingSilhouette(groups);
        const on=shapeSnapshot();
        button.setAttribute('aria-pressed','false');
        window.render(f/30);
        const same=on===shapeSnapshot()&&!stage.querySelector('[data-fx],[data-fx-sombra]');
        button.setAttribute('aria-pressed','true');
        rows.push({f,negative:!!neg,strike:neg?.dataset.riscoCompleto==='true',
          premature:f>=cue&&f<cue+6&&!neg,legibleA:!!glyph,occlusion,direction,missingContact,same,
          shades,contacts:supported,title,motion,hearts,expectedHearts,dimStrength,dimPeak,onLift});
      }
      return {rows,dimensions:data.dimensoes};
    });
    if(errors.length)throw Error(errors.join('\n'));
    const issues=inspecionar(result.rows);
    const turns=[75,90,240,279,375,390];
    if(width===1080&&height===1920&&result.rows.length===432){
      for(const f of turns){
        await page.evaluate(t=>window.seek(t),f/30);
        for(const [name,state] of [['com','true'],['sem','false']]){
          await page.evaluate(value=>{
            const el=document.getElementById('alternar-efeitos');
            if(el.getAttribute('aria-pressed')!==value)el.click();
          },state);
          const current=await page.evaluate(()=>Number(document.getElementById('tempo').value));
          if(Math.abs(current-f/30)>.011)throw Error('O botão mudou a posição da prévia.');
          await page.locator('#palco').screenshot({path:path.join(output,f+'-'+name+'.png')});
        }
        await page.evaluate(()=>document.querySelector('#alternar-efeitos').click());
      }
    }
    await writeFile(path.join(output,'amostras-efeitos.json'),JSON.stringify({...result,issues})+'\n');
    console.log(JSON.stringify({quadros:result.rows.length,issues}));
  }finally{
    await browser.close();
  }
}
