/* Captura referências do palco e máscaras independentes para encontrar oclusão. */
import {createRequire} from 'node:module';
import {writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';

const {chromium}=createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE||'playwright');
const [preview,output]=process.argv.slice(2);
const browser=await chromium.launch({headless:true,
  ...(process.env.CHROME_PATH?{executablePath:process.env.CHROME_PATH}:{})});
try{
  const page=await browser.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.goto(pathToFileURL(preview).href+'?render=1');
  const report=await page.evaluate(async()=>{
    await document.fonts.ready;
    await window.assetsReady;
    const data=JSON.parse(document.querySelector('#dados').textContent);
    if(!data.rig_anatomico)throw Error('A prévia não usa o rig anatômico.');
    const r=window.PictogramaRig, all=[];
    const rect=el=>{const q=el.getBoundingClientRect();return [q.left,q.top,q.right,q.bottom];};
    const local=(x,y,el)=>new DOMPoint(x,y).matrixTransform(el.getScreenCTM());
    const isHand=n=>/^(mao|polegar)[ED]$/.test(n.dataset.massa);
    function collision(groups,grip){
      if(groups.length<2)return null;
      const [a,z]=groups.map(rect);
      const x=Math.floor(Math.max(a[0],z[0])),y=Math.floor(Math.max(a[1],z[1]));
      const w=Math.ceil(Math.min(a[2],z[2]))-x,h=Math.ceil(Math.min(a[3],z[3]))-y;
      if(w<1||h<1)return {fora:0,maos:0};
      const canvas=new OffscreenCanvas(w,h),ctx=canvas.getContext('2d',{willReadFrequently:true});
      function mask(group,hand){
        ctx.resetTransform();ctx.clearRect(0,0,w,h);
        for(const el of group.querySelectorAll('[data-massa]')){
          if(isHand(el)!==hand)continue;
          const m=el.getScreenCTM();
          ctx.setTransform(m.a,m.b,m.c,m.d,m.e-x,m.f-y);
          if(el.tagName==='ellipse'){
            const n=k=>+el.getAttribute(k);
            ctx.beginPath();ctx.ellipse(n('cx'),n('cy'),n('rx'),n('ry'),0,0,Math.PI*2);ctx.fill();
          }else ctx.fill(new Path2D(el.getAttribute('d')));
        }
        return ctx.getImageData(0,0,w,h).data;
      }
      const [ha,hz]=groups.map(g=>mask(g,true));
      const [ba,bz]=groups.map(g=>mask(g,false));
      let fora=0,maos=0;
      for(let p=0;p<w*h;p++){
        const i=4*p+3;
        const h0=ha[i]>=160,h1=hz[i]>=160,b0=ba[i]>=160,b1=bz[i]>=160;
        if(!(h0||b0)||!(h1||b1))continue;
        const inside=grip&&Math.hypot(x+p%w-grip[0],y+Math.floor(p/w)-grip[1])<=45;
        if(inside&&h0&&h1&&!b0&&!b1)maos++;
        else fora++;
      }
      return {fora,maos};
    }
    function benchCrossing(groups){
      const visible=el=>{
        for(let e=el;e&&e.id!=='palco';e=e.parentElement){
          const style=getComputedStyle(e);
          if(Number(style.opacity)<=.01||style.display==='none'||style.visibility==='hidden')return false;
        }
        return true;
      };
      const legs=[...document.querySelectorAll('#palco [data-objeto=banco] rect:not([data-parte=assento])')].filter(visible);
      if(!legs.length)return [];
      return groups.flatMap((actor,i)=>[...actor.querySelectorAll('[data-massa=peE], [data-massa=peD]')].flatMap(foot=>{
        const [x,y,r,b]=rect(foot);
        const fm=foot.getScreenCTM().inverse();
        return legs.map(leg=>{
          const [u,v,w,z]=rect(leg), lm=leg.getScreenCTM().inverse();
          let pixels=0;
          for(let yy=Math.ceil(Math.max(y,v));yy<Math.min(b,z);yy++){
            for(let xx=Math.ceil(Math.max(x,u));xx<Math.min(r,w);xx++){
              const p=new DOMPoint(xx+.5,yy+.5);
              if(foot.isPointInFill(p.matrixTransform(fm))&&leg.isPointInFill(p.matrixTransform(lm)))pixels++;
            }
          }
          return {ator:i,pe:foot.dataset.massa,pixels};
        }).filter(pair=>pair.pixels>0);
      }));
    }
    function shoeTemplate(el,foot,bounds){
      const [x,y,r,b]=bounds;
      const l=Math.floor(x)-3,t=Math.floor(b)-26,w=Math.ceil(r)-l+3,h=30;
      const canvas=new OffscreenCanvas(w,h),ctx=canvas.getContext('2d',{willReadFrequently:true});
      for(const item of el.querySelectorAll('[data-massa]')){
        const rect=item.getBoundingClientRect();
        if(rect.right<l||rect.left>l+w||rect.bottom<t||rect.top>t+h)continue;
        const m=item.getScreenCTM();
        ctx.setTransform(m.a,m.b,m.c,m.d,m.e-l,m.f-t);
        ctx.fillStyle=item===foot?'#ffffff':'#000000';
        if(item.tagName==='ellipse'){
          const a=k=>+item.getAttribute(k);
          ctx.beginPath();ctx.ellipse(a('cx'),a('cy'),a('rx'),a('ry'),0,0,Math.PI*2);ctx.fill();
        }else ctx.fill(new Path2D(item.getAttribute('d')));
      }
      const d=ctx.getImageData(0,0,w,h).data, positive=[];
      for(let j=0;j<h;j++)for(let i=0;i<w;i++){
        const k=4*(j*w+i);
        if(d[k]>115&&d[k+3]>115)positive.push([l+i,t+j]);
      }
      return positive;
    }
    function headSamples(group){
      const head=group.querySelector('[data-massa=cabeca]');
      const [x,y,right,bottom]=rect(head);
      const w=right-x,h=bottom-y;
      const parts=[...group.querySelectorAll('[data-massa]')];
      const after=parts.slice(parts.indexOf(head)+1);
      const inside=(element,pt)=>element.isPointInFill(
        new DOMPoint(...pt).matrixTransform(element.getScreenCTM().inverse()));
      const visible=ratios=>ratios.map(([u,v])=>[x+u*w,y+v*h]).find(pt=>
        inside(head,pt)&&after.every(part=>!inside(part,pt)));
      const lit=visible([[.29,.29],[.33,.26],[.26,.33]]);
      const shade=visible([[.73,.73],[.76,.73],[.71,.79],[.81,.70],[.67,.82]]);
      return lit&&shade?{lit,shade,bg:[x-.07*w,y+h*.48]}:null;
    }
    let priorScene=null;
    for(let f=0;f<Math.round(data.duracao*30);f++){
      const scene=window.render(f/30);
      const frame=window.pictogramaQuadro;
      if(document.querySelector('#palco [data-diagnostico]'))throw Error('Diagnóstico presente no render.');
      if(!frame?.actors.length){all.push({f,scene,actors:[]});continue;}
      const groups=[...document.querySelectorAll('#palco [data-rig-anatomico]')];
      const floor=document.querySelector('#palco [data-parte=piso]');
      const stroke=floor.getAttribute('stroke');
      const fp=local(+floor.getAttribute('x1'),+floor.getAttribute('y1'),floor);
      const fq=local(+floor.getAttribute('x2'),+floor.getAttribute('y2'),floor);
      const contact=frame.actors[0].contacts.find(c=>c.tipo==='par');
      const grip=contact&&(()=>{const v=local(...r.project(contact.real,frame.yaw),groups[0]);return [v.x,v.y];})();
      const masks=collision(groups,grip);
      const actors=frame.actors.map((actor,i)=>{
        const el=groups[i], m=el.getScreenCTM();
        return {id:i,mode:actor.mode,phase:actor.phase,box:rect(el),ink:frame.inks[i],
          head:rect(el.querySelector('[data-massa=cabeca]')),sombra_cabeca:headSamples(el),
          center:actor.center,angles:actor.angles,bones:actor.bones,joints:actor.joints,contacts:actor.contacts,
          feet:['E','D'].map(side=>{
            const foot=el.querySelector('[data-massa=pe'+side+']');
            const c=actor.contacts.find(a=>a.id==='pe'+side);
            const box=rect(foot), v=c && local(...r.project(c.real,frame.yaw),el);
            return {side,box,anchor:v?[v.x,v.y]:null,template:c?shoeTemplate(el,foot,box):[],ink:foot.getAttribute('fill'),phase:c?.fase??'livre',
              transform:[m.a,m.d,m.e,m.f],facing:actor.facing};
          })};
      });
      const activeScene=data.cenas.find(c=>c.id===scene);
      const action=activeScene?.movimento;
      const seat=svgSeat(action,f);
      function svgSeat(action,frameIndex){
        if(action?.tipo!=='sentar_juntos'||action.variacao==='A'&&action.figura==='idoso'||frameIndex<action.pouso)return null;
        const surface=document.querySelector('#palco [data-parte=assento]');
        if(!surface)return {apoios:[],falha:true};
        const [left,top,right]=rect(surface);
        const apoios=frame.actors.map((actor,i)=>{
          const contact=actor.contacts.find(point=>point.id==='pelve'&&point.tipo==='assento');
          if(!contact)return {ator:i,travado:false};
          const group=groups[i];
          const point=local(...r.project(contact.real,frame.yaw),group);
          const scale=group.getScreenCTM().d;
          const erro=Math.abs(top-point.y-.31*scale);
          return {ator:i,travado:r.distance(contact.real,contact.alvo)<.001,
            dentro:left<=point.x&&point.x<=right,erro_px:erro,x:point.x,assento:[left,top,right]};
        });
        return {apoios,falha:apoios.length!==2||apoios.some(a=>!a.travado||!a.dentro||a.erro_px>2)};
      }
      const shot=data.composicao_declarativa&&activeScene?.layout;
      const cut=Boolean(shot&&priorScene!==null&&scene!==priorScene);
      priorScene=scene;
      all.push({f,scene,actors,grip,masks,cut,assento_duplo:seat,banco:benchCrossing(groups),floor:[fp.x,fq.x,fp.y,stroke]});
    }
    return {frames:all,rig:data.rig_anatomico,source:'Geometria e máscaras isoladas do SVG de exportação'};
  });
  if(errors.length)throw Error(errors.join('\n'));
  await writeFile(output,JSON.stringify(report)+'\n');
}finally{await browser.close();}
