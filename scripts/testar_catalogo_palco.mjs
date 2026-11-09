/* Reintroduz defeitos em um quadro real sem editar o HTML nem o PNG de produção. */
import {createRequire} from 'node:module';
import {mkdir} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||'playwright');
const browser=await chromium.launch({headless:true,
  ...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
try{
  const page=await browser.newPage({viewport:{width:1080,height:1920}});
  await page.goto(pathToFileURL(process.argv[2]).href+'?render=1');
  await page.evaluate(async()=>{await document.fonts.ready;await window.assetsReady;});
  for(const file of ['auditoria_catalogo.js','auditoria_coreografia.js','auditoria_proporcoes.js'])
    await page.addScriptTag({path:fileURLToPath(new URL(file,import.meta.url))});
  const output=process.argv[3];
  const result=await page.evaluate(async(capture)=>{
    const data=JSON.parse(document.querySelector('#dados').textContent);
    const stage=document.querySelector('#palco');
    const s=selector=>stage.querySelector(selector);
    const hero=()=>s('[data-elemento=agente]');
    const peer=()=>s('[data-elemento=outro]');
    const move=(el,x,y)=>el.setAttribute('transform',(el.getAttribute('transform')||'')+` translate(${x} ${y})`);
    const pos=(el,field,delta)=>el.setAttribute(field,+el.getAttribute(field)+delta);
    const textAt=(value,x,y)=>{
      const el=document.createElementNS('http://www.w3.org/2000/svg','text');
      el.setAttribute('x',x); el.setAttribute('y',y); el.setAttribute('fill','#ECE6D8'); el.style.fontSize='50px'; el.textContent=value;
      stage.append(el); return el;
    };
    const cases={
      'EC-001':['P','contorno_atravessa_chao',190,()=>move(hero().querySelector('[data-parte=pe]'),0,24)],
      'EC-002':['C','segmento_atravessa',165,()=>{
        const axis=hero().querySelector('[data-eixo=canela]');
        const seat=s('[data-parte=assento]'), r=seat.getBBox();
        const map=axis.getScreenCTM().inverse().multiply(seat.getScreenCTM());
        const xy=(x,y)=>{const p=new DOMPoint(x,y).matrixTransform(map);return p.x+' '+p.y;};
        axis.setAttribute('d',`M ${xy(r.x+15,r.y+r.height/2)} L ${xy(r.x+r.width-15,r.y+r.height/2)}`);
      }],
      'EC-003':['N','EC-003',112,()=>{
        const seat=s('[data-parte=assento]').getBoundingClientRect();
        const m=hero().getScreenCTM();
        move(hero(),((seat.left+seat.right)/2-m.e)/m.a,0);
      }],
      'EC-004':['C','quadril_sem_apoio',165,()=>move(hero(),0,-18)],
      'EC-005':['P','pose_fora_da_altura',165,()=>pos(hero().querySelector('[data-parte=cabeca]'),'cy',-180)],
      'EC-006':['P','altura_em_cabecas',302,()=>pos(hero().querySelector('[data-parte=cabeca]'),'ry',76)],
      'EC-007':['P','escala_sem_camera',300,()=>hero().setAttribute('transform',hero().getAttribute('transform')+' scale(.90)')],
      'EC-008':['N','EC-008',302,()=>hero().querySelector('[data-parte=tronco]').setAttribute('transform','scale(.18 1)')],
      'EC-009':['N','EC-009',165,()=>{
        const foot=hero().querySelector('[data-parte=pe]');
        const x=foot.getBBox().x, y=foot.getBBox().y;
        foot.setAttribute('d',`M${x} ${y}h220v14h-220Z`);
      }],
      'EC-010':['N','EC-010',227,()=>{
        const left=peer().querySelector('[data-articulacao=peE]');
        const right=peer().querySelector('[data-articulacao=peD]');
        for(const key of ['cx','cy'])right.setAttribute(key,left.getAttribute(key));
      }],
      'EC-011':['N','EC-011',336,()=>pos(hero().querySelector('[data-articulacao=maoD]'),'cx',180)],
      'EC-012':['N','EC-012',165,()=>move(hero().querySelector('[data-parte=pescoco]'),0,-110)],
      'EC-013':['N','EC-013',336,()=>move(peer().querySelector('[data-palma-aberta]'),0,-120)],
      'EC-014':['C','subida_precoce',272,()=>s('[data-ajuda-de]').dataset.subida='sim'],
      'EC-015':['N','EC-015',276,()=>hero().querySelector('[data-parte=mao]').remove()],
      'EC-016':['C','maos_sem_contato',276,()=>{
        const arm=hero().querySelector('[data-articulacao=maoD]');
        pos(arm,'cx',85); pos(arm,'cy',-75);
      }],
      'EC-017':['N','EC-017',276,()=>{
        const arm=hero().querySelector('[data-articulacao=maoD]');
        const shoulder=peer().querySelector('[data-articulacao=ombroE]');
        const p=new DOMPoint(+shoulder.getAttribute('cx'),+shoulder.getAttribute('cy'))
          .matrixTransform(arm.getScreenCTM().inverse().multiply(shoulder.getScreenCTM()));
        arm.setAttribute('cx',p.x); arm.setAttribute('cy',p.y);
      }],
      'EC-017-mao-desenhada':['N','EC-017',276,()=>{
        const visibleHand=hero().querySelector('[data-parte=mao]');
        const shoulder=peer().querySelector('[data-articulacao=ombroE]');
        const p=new DOMPoint(+shoulder.getAttribute('cx'),+shoulder.getAttribute('cy'))
          .matrixTransform(visibleHand.getScreenCTM().inverse().multiply(shoulder.getScreenCTM()));
        visibleHand.setAttribute('cx',p.x); visibleHand.setAttribute('cy',p.y);
      }],
      'EC-018':['C','salto_entre_quadros',299,()=>move(hero(),105,0)],
      'EC-018-cor':['C','cor_abrupta',299,()=>hero().querySelector('[data-parte=tronco]').setAttribute('fill','#ffffff')],
      'EC-019':['T','EC-019',165,()=>{
        const a=hero().getBoundingClientRect();
        const exit=document.createElementNS('http://www.w3.org/2000/svg','g');
        exit.dataset.transicao='saida'; stage.append(exit);
        exit.append(textAt('Título da cena anterior',a.x+24,a.y+110));
      }],
      'EC-020':['N','EC-020',253,()=>{
        const halo=s('[fill="url(#halo-impulso)"]');
        const r=peer().getBoundingClientRect(), h=halo.getBoundingClientRect();
        move(halo,(r.left+r.right-h.left-h.right)/2,0);
      }],
      'EC-021':['N','EC-021',215,()=>move(peer(),-315,0)],
      'EC-022':['N','EC-022',336,()=>s('[data-elemento=recepcao]').remove()],
      'EC-023':['N','EC-023',253,()=>{
        const halo=s('[fill="url(#halo-impulso)"]');
        halo.setAttribute('stroke','#84BD9B');halo.setAttribute('stroke-width',2);
      }],
      'EC-024':['C','negacao_perdida',55,()=>s('[data-negacao]').remove()],
      'EC-025':['T','EC-025',93,()=>{
        const falling=s('[data-queda=sim]');
        const r=falling.getBoundingClientRect(), t=s('[data-elemento=deus]').getBoundingClientRect();
        move(falling,t.x-r.x,t.y-r.y);
      }],
      'EC-026':['C','texto_duplicado',175,()=>{
        textAt('eu sento e',180,530);
      }],
      'EC-027':['T','EC-027',336,()=>{
        const line=s('[data-parte=piso]').getBoundingClientRect();
        textAt('RECEBE',650,line.y+22).dataset.titulo='sim';
      }],
      'EC-028':['T','EC-028',175,()=>{
        textAt('CENA '+data.cenas[0].id,110,430);
      }],
      'EC-028-barra':['T','EC-028',175,()=>{
        const bar=document.createElementNS('http://www.w3.org/2000/svg','rect');
        for(const [key,value] of Object.entries({x:70,y:370,width:780,height:5,fill:'#9CC6A6'}))
          bar.setAttribute(key,value);
        bar.dataset.progresso='sim'; stage.append(bar);
      }],
      'EC-029':['T','EC-029',175,()=>{
        textAt('— — —',160,650);
      }],
      'EC-030':['T','EC-030',175,()=>{
        const text=textAt('',130,590);
        text.dataset.titulo='sim';
        for(const [i,word] of 'eu sento e espero'.split(' ').entries()){
          const span=document.createElementNS('http://www.w3.org/2000/svg','tspan');
          span.dataset.palavra=i; span.textContent=word+' '; text.append(span);
        }
      }],
      'EC-034':['P','membro_muda_comprimento',300,()=>pos(hero().querySelector('[data-articulacao=maoD]'),'cx',90)],
      'EC-042':['N','EC-042',408,()=>move(peer().querySelector('[data-palma-aberta][data-lado=E]'),-185,0)],
      'EC-042-seta':['N','EC-042',394,()=>{
        const arrow=s('[data-elemento=sai] [data-objeto=seta]');
        const r=peer().querySelector('[data-palma-aberta][data-lado=E]').getBoundingClientRect();
        const a=arrow.getBoundingClientRect();
        move(arrow,r.x+r.width/2-a.x-a.width/2,r.y+r.height/2-a.y-a.height/2);
      }],
    };
    const opacity=el=>{
      let a=1;
      for(let node=el;node&&node!==stage;node=node.parentElement)a*=Number(node.getAttribute('opacity')??1);
      return a;
    };
    const region=el=>{const b=el.getBoundingClientRect();return[b.x,b.y,b.width,b.height];};
    const visible=el=>el.querySelector('tspan')?
      [...el.querySelectorAll('tspan[visibility=visible]')].map(n=>n.textContent).join('').toUpperCase():
      el.textContent.toUpperCase();
    const logs=[];
    for(const [id,[engine,code,frame,mutate]] of Object.entries(cases)){
      let example;
      const run=async apply=>{
        const issues=[];
        const flag=(name,f)=>{if(f===frame)issues.push(name);};
        const normal=(name,f,id,fix)=>{if(fix)flag(name,f);};
        const audit=window.auditoriaCoreografia(data,flag,opacity,visible,region);
        const props=window.auditarProporcoes(data.bible,flag);
        const start=engine==='C'&&frame>210 ? frame-12 : Math.max(0,frame-1);
        for(let f=start;f<=frame;f++){
          const scene=window.render(f/30);
          if(apply&&f===frame){mutate(); if(capture)example=stage.innerHTML;}
          if(engine==='C')audit(f,scene,false);
          else if(engine==='P')await props.inspect(stage,f,scene);
          else if(engine==='N')window.AuditoriaCatalogo.inspect(stage,data,f,normal);
          else window.AuditoriaCatalogo.texto(stage,data,f,normal);
        }
        return issues;
      };
      const base=await run(false);
      const broken=await run(true);
      logs.push({id,frame,code,base,broken,ok:!base.includes(code)&&broken.includes(code),example});
    }
    return logs;
  },Boolean(output));
  if(output){
    await mkdir(output,{recursive:true});
    for(const row of result){
      if(!row.ok || !row.example)continue;
      await page.evaluate(html=>{document.querySelector('#palco').innerHTML=html;},row.example);
      await page.locator('#palco').screenshot({path:path.join(output,row.id+'.png')});
    }
  }
  console.log(JSON.stringify(result.map(({example,...row})=>row),null,2));
  if(result.some(row=>!row.ok))process.exitCode=1;
}finally{await browser.close();}
