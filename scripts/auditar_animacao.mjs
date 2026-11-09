import {createRequire} from 'node:module';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {mkdir, writeFile} from 'node:fs/promises';
import path from 'node:path';

const require = createRequire(import.meta.url);
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [preview, output, widthArg, heightArg, mode='amostrada'] = process.argv.slice(2);
const width = Number(widthArg), height = Number(heightArg);
await mkdir(output,{recursive:true});
const browser = await chromium.launch({headless:true,
  ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
try {
  const page = await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto(pathToFileURL(preview).href+'?render=1');
  await page.evaluate(async()=>{await document.fonts.ready;await window.assetsReady;});
  const {coreografia,bible}=await page.evaluate(()=>{
    const data=JSON.parse(document.getElementById('dados').textContent);
    return {coreografia:!!data.coreografia,bible:!!data.bible};
  });
  if (coreografia)
    await page.addScriptTag({path:fileURLToPath(new URL('./auditoria_coreografia.js',import.meta.url))});
  if (bible)
    await page.addScriptTag({path:fileURLToPath(new URL('./auditoria_proporcoes.js',import.meta.url))});
  await page.addScriptTag({path:fileURLToPath(new URL('./auditoria_catalogo.js',import.meta.url))});
  const report=await page.evaluate(async(integral)=>{
    const data=JSON.parse(document.getElementById('dados').textContent);
    const fps=30, active=Math.ceil((data.repouso ?? data.duracao)*fps-1e-8);
    const count=Math.round(data.duracao*fps);
    const events=window.animationEvents;
    const points=new Set([0]);
    for (const item of events) for (const t of [item.start,item.end,item.landing,item.target]) {
      const f=Math.round(t*fps);
      for (let d=-2;d<=2;d++) points.add(f+d);
    }
    const issues=[], failures=[], unique=new Set(), metrics={}, perSecond={};
    const gestual=data.composicao_declarativa?.gestual==='expressivo_intencional';
    const geometria=[];
    const gestures=[], presencas=[], livros=[], luzes=[], atmosferas=[], oracoes=[], continuidades=[];
    let priorPose=null, heldPose=null, startStep=null, startCare=null;
    const distance=(a,b)=>Math.hypot(...a.map((value,i)=>value-b[i]));
    const sampleGesture=(scene,f)=>{
      const q=window.pictogramaQuadro;
      const action=scene.movimento;
      const inside=action && f>=action.inicio && f<action.fim;
      const transfer=Boolean(q.transfer);
      const point=(actor,v)=>{
        const {angle=q.yaw,unit=q.scale}=q.projections?.[actor]??{};
        const [x,y]=window.PictogramaRig.project(v,angle);
        return [q.origins[actor]+x*unit,q.floor+y*unit];
      };
      const actors=q.actors.map((actor,index)=>Object.fromEntries(['E','D'].map((side,i)=>{
        const id='mao'+side;
        const support=actor.contacts.find(row=>row.id===id);
        const residual=actor.residuals.find(row=>row.id===id);
        const declared=q.gesto?.mao;
        const gesture=actor.mode==='gesto'&&Boolean(actor.control.activeHands?.includes(side)??actor.control.hands?.[i]);
        const permitted=inside&&(index===0||transfer)&&(declared===side||declared==='ambas'||transfer);
        return [side,{posicao:point(index,actor.joints['punho'+side]),
          excesso:gesture&&residual?residual.distancia*q.scale:0,
          contato:support&&support.tipo==='par'?distance(point(index,support.real),point(index,support.alvo)):null,
          ativa:gesture,autorizada:Boolean(permitted)}];
      })));
      const contacts=q.actors.map(actor=>actor.contacts.find(c=>c.tipo==='par'));
      const meet=contacts.length===2&&contacts.every(Boolean)?distance(point(0,contacts[0].real),point(1,contacts[1].real)):null;
      const expected=transfer&&Math.abs(f-q.transferFrame)<=4 ||
        action?.tipo==='ajudar_a_levantar'&&['Firmar a pega','Transferir peso','Subir com tração','Estabilizar de mãos dadas'].includes(q.actors[0].phase);
      const continuous=q.transicao!=null;
      const feet=continuous||scene.entrada_continua?q.actors.map((actor,index)=>Object.fromEntries(
        actor.contacts.filter(contact=>contact.tipo==='chao'&&contact.id.startsWith('pe')).map(contact=>
          [contact.id,{posicao:point(index,contact.real),alvo:point(index,contact.alvo),fase:contact.fase}]))):null;
      return {f,scene:scene.id,actors,action:Boolean(action),encontro:meet,contato_esperado:expected,
        ...(q.projections?{ids:q.projections.map(actor=>actor.id)}:{}),
        ...(feet?{pes:feet,transicao:continuous}:{})};
    };
    const flag=(code, frame, element, fix, severity='bloqueante')=>{
      const key=code+'|'+element;
      if (data.bible) failures.push({codigo:code,quadro:frame,elemento:element});
      if (!unique.has(key)) issues.push({codigo:code,quadro:frame,elemento:element,correcao:fix,nivel:severity});
      unique.add(key);
    };
    const effectiveOpacity=(el)=>{
      let alpha=1;
      for (let e=el;e && e.id!=='palco';e=e.parentElement) alpha*=Number(e.getAttribute('opacity') ?? 1);
      return alpha;
    };
    const region=(el)=>{
      const r=el.getBoundingClientRect();
      return [r.x,r.y,r.width,r.height];
    };
    const inter=(a,b)=>Math.min(a[0]+a[2],b[0]+b[2])-Math.max(a[0],b[0])>5 &&
      Math.min(a[1]+a[3],b[1]+b[3])-Math.max(a[1],b[1])>5;
    const sceneIds=new Set(data.cenas.map(scene=>scene.id.toUpperCase()));
    const visibleText=(text)=>{
      const walker=document.createTreeWalker(text,NodeFilter.SHOW_TEXT);
      let result='';
      for(let node=walker.nextNode();node;node=walker.nextNode()){
        const parent=node.parentElement;
        const style=getComputedStyle(parent);
        if(style.visibility==='visible' && effectiveOpacity(parent)>.01 &&
           !parent.closest('[display=none]')) result+=node.textContent;
      }
      return result.toUpperCase().trim();
    };
    const catalogChecks=new Map();
    const mark=(code,frame,id,fix)=>{
      const status=catalogChecks.get(code)||{quadros:0,falhas:0};
      status.quadros++; status.falhas+=Number(Boolean(fix)); catalogChecks.set(code,status);
      if(fix) flag(code,frame,id,fix);
    };
    const choreography=data.coreografia && window.auditoriaCoreografia(data,flag,effectiveOpacity,visibleText,region,mark);
    const proportions=data.bible && window.auditarProporcoes(data.bible,flag,{mark});
    const stage=document.getElementById('palco');
    const lexical=value=>(value.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().match(/[\p{L}\p{N}]+/gu)||[]).join(' ');
    const names=(data.pessoas_privadas||[]).map(name=>' '+lexical(name)+' ');
    let prior=new Map(), lastScene;
    let sampled=0;
    for(let f=0;f<count;f++){
      const t=f/fps, id=window.render(t);
      const scene=data.cenas.find(row=>row.id===id);
      if(choreography) choreography(f,id,f===count-1);
      if (data.auditoria_sincronia && data.legenda) {
        const group=data.legendas.findLast(row=>row.inicio<=f);
        const expected=group && f>= (data.legenda_a_partir ?? 0) && f<group.fim ?
          group.linhas.flat().filter(i=>data.palavras[i].quadro<=f) : [];
        const visible=[...document.querySelectorAll('#palco [data-palavra][visibility=visible]')]
          .map(el=>Number(el.dataset.palavra));
        const visibleSpans=[...stage.querySelectorAll('[data-palavra][visibility=visible]')];
        const shownCorrectly=visibleSpans.every(el=>{
          const word=data.palavras[Number(el.dataset.palavra)];
          return word && el.textContent.trim()===(word.exibicao??word.texto);
        });
        if (!shownCorrectly || expected.length!==visible.length || expected.some((i,j)=>i!==visible[j]))
          flag('sincronia_legenda',f,id,'Alinhe a exibição da legenda ao quadro de cada palavra.');
        const activeFrame=Math.max(...expected.map(i=>data.palavras[i].quadro));
        const highlights=[...document.querySelectorAll('#palco [data-palavra][visibility=visible]')]
          .filter(el=>el.getAttribute('fill')===data.paleta.acento).map(el=>Number(el.dataset.palavra));
        const accents=expected.filter(i=>data.palavras[i].quadro===activeFrame);
        if (accents.length!==highlights.length || accents.some((i,j)=>i!==highlights[j]))
          flag('destaque_legenda',f,id,'Destaque a palavra no quadro alinhado.');
      }
      if(names.length){
        const leak=[...stage.querySelectorAll('text,foreignObject')].filter(el=>effectiveOpacity(el)>0)
          .some(el=>names.some(name=>(' '+lexical(visibleText(el))+' ').includes(name)));
        mark('EC-092',f,id,leak?'Retire o nome privado do texto em tela.':null);
      }
      const check=integral || f%3===0 || points.has(f);
      if (check) {
        if(gestual) gestures.push(sampleGesture(scene,f));
        if(scene.manter_posse){
          const objects=[...stage.querySelectorAll('[data-objeto-cena][data-relacao="segurado"]')];
          if(objects.length!==1||effectiveOpacity(objects[0])<.99)
            flag('posse_interrompida',f,id,'Mantenha visível, na mão de quem recebeu, o mesmo objeto da transferência.');
        }
        const scenery=stage.querySelector('[data-cenario-ilustrado]');
        if(scenery){
          const [x,y,w,h]=region(scenery.querySelector('[data-cenario-area]'));
          const portrait=data.dimensoes[0]<data.dimensoes[1];
          const right=portrait?902:data.dimensoes[0];
          const top=portrait?367:0;
          const bottom=portrait?1335:data.dimensoes[1];
          if(x<0 || y<top || x+w>right || y+h>bottom)
            flag('cenario_area_segura',f,id,'Reposicione o cenário acima da legenda e dentro das margens.');
          if(scenery.querySelectorAll('[data-plano]').length!==3)
            flag('cenario_camadas',f,id,'Mantenha as três camadas da ilustração.');
        }
        const atmosphere=scene.atmosfera;
        const currentMood=stage.querySelector(`[data-id-atmosfera="${id}-atual"]`);
        const qFrame=window.pictogramaQuadro;
        const rules=window.AuditoriaCatalogo;
        if(atmosphere&&f>=atmosphere.pouso){
          const kind=atmosphere.tipo;
          const count=kind==='chuva'?currentMood?.querySelectorAll('[data-gota]').length:
            kind==='aura'?currentMood?.querySelectorAll('[data-aura]').length:currentMood?.children.length;
          // A aura pode ultrapassar o chão no SVG, mas seu recorte visível deve parar antes da legenda.
          const bottom=currentMood?.querySelector('[data-area-atmosfera]')?.getBoundingClientRect().bottom??Infinity;
          const facts={tipo:currentMood?.dataset.atmosfera,opacidade:currentMood?effectiveOpacity(currentMood):0,
            limite:bottom,detalhes:count>0};
          atmosferas.push({quadro:f,...facts});
          const code={sombra:'EC-108',aura:'EC-109',chuva:'EC-110',claridade:'EC-111',partilha:'EC-112'}[kind];
          mark(code,f,id,rules.atmosferaVisivel(facts)?null:
            'Confira a atmosfera no ponto da fala e preserve a faixa da legenda.');
          if(kind==='sombra'){
            const [speaker,listener]=qFrame.actors;
            const evidence={falante:speaker.control.headPitch??0,ouvinte:listener?.control.headPitch??0,
              gestoOuvinte:!!listener?.control.activeHands?.length};
            mark('EC-108',f,id,rules.sombraVisivel(evidence)?null:
              'Encene a reação dos dois personagens com a postura e o olhar.');
          }
          if(kind==='partilha'){
            const light=currentMood?.querySelector('[data-luz-partilha]');
            const heart=[...stage.querySelectorAll('[data-objeto-cena="coracao-0"]')]
              .find(el=>!el.closest('[data-transicao]'));
            const spec=qFrame.partilha;
            const u=Math.max(0,Math.min(1,(f-spec?.quadro+1)/10));
            const expected=u*u*(3-2*u);
            const evidence={progress:Number(light?.dataset.progressoLuz),stage:light?.dataset.luzPartilha,
              owner:Number(heart?.dataset.ator),donor:spec?.from,receiver:spec?.to,expected};
            mark('EC-112',f,id,rules.partilhaVisivel(evidence)?null:
              'Transfira a luz somente no quadro em que o outro recebe o coração.');
          }
        }
        if(gestual&&qFrame){
          const rig=window.PictogramaRig;
          const point=(actor,index,name)=>{
            const {angle=qFrame.yaw,unit=qFrame.scale}=qFrame.projections?.[index]??{};
            const [x,y]=rig.project(actor.joints[name],angle);
            return [qFrame.origins[index]+x*unit,qFrame.floor+y*unit];
          };
          const state=qFrame.actors.map((actor,index)=>Object.fromEntries(
            ['pelve','plantaE','pontaD','maoE','maoD'].map(name=>[name,point(actor,index,name)])));
          if(scene.manter_elenco){
            if(lastScene!==id||!heldPose)heldPose=priorPose;
            const facts={atores:state.length,banco:!!stage.querySelector('[data-apoio-persistente="banco"]'),
              desvio:heldPose?.length===state.length?Math.max(...state.flatMap((actor,i)=>
                ['pelve','plantaE','pontaD'].map(name=>name==='pelve'?
                  Math.abs(actor[name][0]-heldPose[i][name][0]):distance(actor[name],heldPose[i][name])))):Infinity,
              emPe:qFrame.actors.every(actor=>actor.joints.pelve[1]<-2.4)};
            continuidades.push({codigo:'EC-113',quadro:f,...facts});
            mark('EC-113',f,id,rules.elencoEstavel(facts)?null:
              'Mantenha as duas figuras de pé e no enquadramento em que concluíram a ajuda.');
          }
          const step=scene.movimento?.passo_final;
          if(step&&f>=step.inicio){
            if(f===step.inicio||!startStep)startStep=state[0];
            const facts={apoio:distance(startStep.plantaE,state[0].plantaE),
              fracao:Math.min(1,(f-step.inicio)/(step.fim-step.inicio)),
              avanco:Math.abs(state[0].pontaD[0]-startStep.pontaD[0]),
              balanco:startStep.pontaD[1]-state[0].pontaD[1]};
            continuidades.push({codigo:'EC-114',quadro:f,...facts});
            mark('EC-114',f,id,rules.passoPlantado(facts)?null:
              'Plante o apoio, levante o pé de balanço e conclua o avanço.');
          }
          const care=scene.movimento?.cuidado;
          if(care&&f>=care.inicio&&f<=care.fim){
            if(f===care.inicio||!startCare)startCare=state[1];
            const heart=[...stage.querySelectorAll('[data-objeto-cena="coracao-0"]')]
              .find(el=>!el.closest('[data-transicao]'));
            const facts={dono:Number(heart?.dataset.ator),segura:distance(startCare.maoD,state[1].maoD),
              gesto:distance(startCare.maoE,state[1].maoE),fracao:(f-care.inicio)/(care.fim-care.inicio)};
            continuidades.push({codigo:'EC-115',quadro:f,...facts});
            mark('EC-115',f,id,rules.cuidadoAposEntrega(facts)?null:
              'Conserve o coração na mão que recebeu e encene a resposta com a outra mão.');
          }
          priorPose=state;
        }
        const prayer=scene.movimento?.oracao;
        if(prayer&&f>=prayer.palmas&&f<=prayer.recolher){
          const actor=qFrame.actors[0];
          const p=actor.joints;
          const facts={palmas:stage.querySelectorAll('[data-palma-oracao][data-massa]').length,
            distancia:window.PictogramaRig.distance(p.maoE,p.maoD)*qFrame.scale,
            dedos:['E','D'].map(side=>(p['mao'+side][1]-p['punho'+side][1])*qFrame.scale)};
          oracoes.push({quadro:f,...facts});
          mark('EC-107',f,id,rules.oracaoVisivel(facts)?null:
            'Junte as duas palmas no peito com os dedos voltados para cima.');
        }
        const offered=[...stage.querySelectorAll('[data-mao-presente]')];
        const beams=[...stage.querySelectorAll('[data-holofote-presenca]')];
        if(offered.length||beams.length||scene.movimento?.presenca){
          const light={maos:offered.length,feixes:beams.length,
            opacidadeMao:offered[0]?effectiveOpacity(offered[0]):0,
            opacidadeFeixe:beams[0]?effectiveOpacity(beams[0]):0,
            limite:beams[0]?.getBoundingClientRect().bottom??0};
          luzes.push({quadro:f,...light});
          mark('EC-104',f,id,window.AuditoriaCatalogo.luzDaPresenca(light)?null:
            'Faça o feixe acompanhar a mão e mantenha a legenda livre.');
        }
        const book=[...stage.querySelectorAll('[data-livro-na-mao]')].find(el=>
          !el.closest('[data-transicao]')&&effectiveOpacity(el)>.72);
        if(book){
          const distancias=['E','D'].map(side=>{
            const grip=book.querySelector(`[data-apoio-livro="${side}"]`);
            const hand=book.querySelector(`[data-palma-livro="${side}"]`);
            if(!grip||!hand)return Infinity;
            const [x,y,w,h]=region(grip), [a,b,c,d]=region(hand);
            return distance([x+w/2,y+h/2],[a+c/2,b+d/2]);
          });
          const facts={distancias,virada:Number(book.dataset.virada),
            pagina:!!book.querySelector('[data-pagina-em-virada]')};
          const aligned=book.querySelector('[data-livro-orientado]');
          const orientation={orientados:book.querySelectorAll('[data-livro-orientado]').length,
            leitor:Number(aligned?.dataset.normalLeitor),camera:Number(aligned?.dataset.normalCamera)};
          livros.push({quadro:f,...facts,...orientation});
          mark('EC-106',f,id,rules.livroOrientado(orientation)?null:
            'Projete as páginas voltadas para o leitor e de viés para a câmera.');
          mark('EC-103',f,id,window.AuditoriaCatalogo.livroApoiado(facts)?null:
            'Apoie o livro nas mãos e mantenha a folha ligada à lombada durante a virada.');
        }
        if(offered.length||scene.movimento?.presenca){
          const action=scene.movimento;
          const q=window.pictogramaQuadro;
          const side=action?.gesto?.mao==='E'?'E':'D';
          const actor=stage.querySelector('[data-elemento="figura-0"]');
          const part=actor?.querySelector(`[data-massa="mao${side}"]`);
          const thumb=actor?.querySelector(`[data-massa="polegar${side}"]`);
          const outline=offered[0]?.querySelector('[data-contorno-presenca]');
          const audit=window.AuditoriaCatalogo;
          const gap=outline&&Math.min(...[part,thumb].filter(Boolean).map(path=>audit.folgaContornos(outline,path)));
          const joints=q?.actors[0]?.joints;
          const cotovelo=joints&&(joints['cotovelo'+side][1]-joints['ombro'+side][1])*q.scale;
          const evidence={quantidade:offered.length,opacidade:offered.length?effectiveOpacity(offered[0]):0,
            folga:gap??null,cotovelo:cotovelo??null};
          presencas.push({quadro:f,...evidence});
          mark('EC-101',f,id,audit.presenca(action,f,evidence)?null:
            'Apresente a palma, sustente a distância visível com o cotovelo relaxado e conclua a saída na batida.');
        }
        const figures=[...stage.querySelectorAll('[data-figura-enumerada]')];
        if(figures.length||scene.cenario_ilustrado?.figuras){
          const types=figures.map(el=>({tipo:el.dataset.figuraEnumerada,opacity:effectiveOpacity(el)}));
          const matched=window.AuditoriaCatalogo.enumeracao(scene.cenario_ilustrado,types,f);
          const subjects=[...stage.querySelectorAll('[data-elemento^="figura-"],[data-legenda]')]
            .filter(el=>effectiveOpacity(el)>.02).flatMap(el=>{
              const pieces=[...el.querySelectorAll('[data-massa]')];
              return (pieces.length?pieces:[el]).map(region);
            });
          const frame=data.dimensoes;
          const vertical=frame[0]<frame[1];
          const obstructed=figures.some((el,i)=>{
            const box=region(el), [x,y,w,h]=box;
            return (vertical&&(x<0||x+w>900||y<370||y+h>1335))||
              subjects.some(other=>inter(box,other))||figures.slice(0,i).some(other=>inter(box,region(other)));
          });
          mark('EC-100',f,id,matched&&!obstructed?null:
            'Revele as figuras em ordem, mantenha as anteriores visíveis e reserve espaço livre no palco.');
        }
        const graphic=stage.querySelector('[data-grafico]');
        if(graphic && effectiveOpacity(graphic)>.20){
          const area=region(graphic);
          for(const subject of stage.querySelectorAll('[data-elemento^="figura-"],[data-objeto-cena],[data-legenda]')){
            if(effectiveOpacity(subject)>.50 && inter(area,region(subject)))
              flag('grafico_sobreposto',f,id,'Separe o gráfico do ator, do objeto ou da legenda.');
          }
        }
        if(proportions) await proportions.inspect(stage,f,id);
        if(data.bible && data.coreografia) window.AuditoriaCatalogo.inspect(stage,data,f,mark);
        if(data.salvaguardas_declarativas){
          const frame=window.pictogramaQuadro;
          const rigs=[...stage.querySelectorAll('[data-rig-anatomico]')]
            .filter(el=>effectiveOpacity(el)>.72&&!el.closest('[data-elemento^="figura-saida-"]'));
          const floor=stage.querySelector('[data-parte="piso"]');
          const floorY=floor?region(floor)[1]:null;
          const feet=[];
          for(const group of rigs){
            const owner=group.closest('[data-elemento]');
            const index=Number(owner?.dataset.elemento?.split('-').at(-1));
            for(const side of ['E','D']){
              const foot=group.querySelector(`[data-massa="pe${side}"]`);
              const contact=frame?.actors[index]?.contacts.find(row=>row.id==='pe'+side&&row.tipo==='chao');
              if(foot&&contact&&floorY!==null)
                feet.push({box:region(foot),floor:floorY,ink:foot.getAttribute('fill'),fase:contact.fase});
            }
          }
          const action=scene.movimento||{};
          const bench=stage.querySelector('[data-apoio-persistente="banco"] [data-parte="assento"]');
          const standingElder=action.tipo==='sentar_juntos'&&action.figura==='idoso'&&action.variacao==='A';
          const needBench=!standingElder&&(!!scene.assento||
            ['sentar','levantar','sentar_juntos','acompanhar_espera','tentar_levantar'].includes(action.tipo));
          const settled=!frame?.transicao;
          const seat=bench&&effectiveOpacity(bench)>.55?region(bench):null;
          const supports=needBench&&settled;
          const legs=[...stage.querySelectorAll('[data-apoio-persistente="banco"] rect:not([data-parte="assento"])')]
            .filter(el=>effectiveOpacity(el)>.72);
          const feetNodes=rigs.flatMap(el=>[...el.querySelectorAll('[data-massa="peE"],[data-massa="peD"]')]);
          function overlaps(a,b){
            const ra=region(a), rb=region(b);
            if(!inter(ra,rb))return false;
            const ma=a.getScreenCTM().inverse(), mb=b.getScreenCTM().inverse();
            const left=Math.ceil(Math.max(ra[0],rb[0])),right=Math.min(ra[0]+ra[2],rb[0]+rb[2]);
            const top=Math.ceil(Math.max(ra[1],rb[1])),bottom=Math.min(ra[1]+ra[3],rb[1]+rb[3]);
            for(let y=top;y<bottom;y+=2)for(let x=left;x<right;x+=2){
              const point=new DOMPoint(x+.5,y+.5);
              if(a.isPointInFill(point.matrixTransform(ma))&&b.isPointInFill(point.matrixTransform(mb)))return true;
            }
            return false;
          }
          const crossing=legs.some(leg=>feetNodes.some(foot=>overlaps(leg,foot)));
          geometria.push({quadro:f,feet,seat,supports,crossing});
          if(supports||crossing)
            mark('EC-094',f,id,seat&&!crossing?null:
              'O assento deve estar visível e as pernas do banco separadas dos pés.');
          const text=[...stage.querySelectorAll('[data-titulo],[data-rotulo-cena],[data-grafico] text')]
            .filter(el=>effectiveOpacity(el)>.65);
          const bodies=rigs.flatMap(el=>[...el.querySelectorAll('[data-massa]')]).map(region);
          if(scene.titulo||scene.rotulos?.length||scene.grafico||text.length){
            const missing=scene.titulo&&!scene.virada&&!scene.grafico&&scene.padrao!=='comparacao'&&
              settled&&f>=Math.round(scene.inicio*30)+24&&!text.length;
            const occluded=text.some(el=>!window.AuditoriaCatalogo.rotuloVisivel(region(el),bodies));
            mark('EC-096',f,id,missing||occluded?'Separe o texto dos contornos e da margem segura.':null);
          }
          if(settled&&scene.posse_esperada){
            const expected=scene.posse_esperada;
            const owner=f>=expected.pouso?expected.depois:expected.antes;
            const items=[...stage.querySelectorAll(`[data-objeto-cena="${expected.objeto}-0"]`)]
              .filter(el=>!el.closest('[data-transicao]')).map(el=>({
                kind:el.dataset.objetoCena.split('-')[0],owner:Number(el.dataset.ator),opacity:effectiveOpacity(el)
              }));
            mark('EC-084',f,id,window.AuditoriaCatalogo.objetoComDono(items,expected.objeto,owner)?null:
              'Conserve o objeto visível com o doador até a entrega e com quem recebe após o contato.');
          }
          if(settled&&action.tipo==='ler'&&action.objeto==='livro'&&
             !stage.querySelector('[data-livro-na-mao]')){
            mark('EC-103',f,id,'O livro da leitura está ausente.');
            mark('EC-106',f,id,'O plano do livro está ausente.');
          }
        }
        if(data.rotulo_cena===false) window.AuditoriaCatalogo.texto(stage,data,f,mark);
        sampled++;
        if (data.rotulo_cena===false) {
          for (const label of document.querySelectorAll('#palco text, #palco foreignObject')) {
            const words=visibleText(label).match(/[A-Z0-9_-]+/g) || [];
            if (words.some(word=>sceneIds.has(word)))
              flag('id_interno_no_palco',f,id,'Mantenha os identificadores de cena nos controles da prévia.');
          }
        }
      }
      const nodes=[...document.querySelectorAll('#palco [data-elemento]')].filter(el=>!el.closest('[data-transicao]'));
      const current=new Map();
      const texts=[], shapes=[];
      for(const el of nodes){
        const name=el.dataset.elemento, alpha=effectiveOpacity(el);
        if(alpha<=.012) continue;
        const box=region(el);
        if(choreography && !box[2] && !box[3]) continue;
        const position = new DOMPoint(Number(el.getAttribute('x1')||0),Number(el.getAttribute('y1')||0))
          .matrixTransform(el.getScreenCTM());
        const origin=[position.x,position.y];
        const entry={box,origin,alpha,signature:el.outerHTML};
        current.set(name,entry);
        if (!check) continue;
        const previous=prior.get(name);
        if (lastScene===id && previous) {
          if (Math.hypot(origin[0]-previous.origin[0],origin[1]-previous.origin[1])>40)
            flag('salto',f,name,'Distribua o deslocamento em mais quadros.');
          mark('EC-035',f,name);
          if (window.AuditoriaCatalogo.changeOpacity(previous.alpha,alpha))
            flag('opacidade',f,name,'Alongue a entrada ou a saída.');
        } else if(lastScene===id && !previous && el.hasAttribute('data-persistente') &&
                  window.AuditoriaCatalogo.changeOpacity(0,alpha)) {
          flag('opacidade',f,name,'A figura deve entrar gradualmente entre cortes.');
        }
        if ([...box,...origin].some(n=>!Number.isFinite(n)) || /(?:NaN|Infinity|scale\(-)/.test(el.outerHTML))
          flag('transformacao',f,name,'Corrija a transformação inválida.');
        const wide=data.dimensoes[0]>data.dimensoes[1];
        const [x,y,w,h]=box;
        if (alpha>.5 && (x<-2 || y< -2 || x+w>data.dimensoes[0]+2 || y+h>data.dimensoes[1]+2 ||
            (!wide && (y<367 || y+h>1433 || (x+w>902 && y+h>700 && y<1500)))))
          flag('area_segura',f,name,'Reposicione o elemento na área segura, considerando a câmera.');
        if (el.dataset.juntas==='false') flag('juntas',f,name,'Religue cabeça e membros ao tronco.');
        if (el.dataset.superficie && Math.abs(Number(el.dataset.superficie)-Number(el.dataset.contato))>9)
          flag('contato',f,name,'Alinhe a pose à superfície de apoio declarada.');
        if (el.dataset.apoio) {
          const support=nodes.find(x=>x.dataset.elemento===el.dataset.apoio);
          if (!support || effectiveOpacity(support)<.5 || nodes.indexOf(support)>nodes.indexOf(el))
            flag('apoio',f,name,'Mantenha o apoio visível atrás do elemento.');
        }
        if (alpha>.5 && el.dataset.pose) {
          const parts=part=>[...el.querySelectorAll('[data-parte="'+part+'"]')].map(region);
          const soles=[...parts('pe'),...parts('canela')];
          const bottom=Math.max(...soles.map(foot=>foot[1]+foot[3]));
          const floor=nodes.find(item=>item.dataset.elemento===el.dataset.chao)?.querySelector('[data-parte=piso]');
          if (floor && soles.length) {
            const floorY=region(floor)[1];
            if (bottom>floorY+2) flag('pe_atravessa_piso',f,name,'A sola visível deve terminar na linha do chão.');
            if (el.dataset.pose==='em_pe' && bottom<floorY-3)
              flag('pe_sem_contato',f,name,'Mantenha pelo menos uma sola em contato com o chão.');
          }
          const support=nodes.find(item=>item.dataset.elemento===el.dataset.apoio)?.querySelector('[data-parte=assento]');
          if (support && parts('canela').some(shin=>inter(shin,region(support))))
            flag('canela_sobre_assento',f,name,'Desloque a canela para além da borda visível do assento.');
          const [torso]=parts('tronco'), [head]=parts('cabeca');
          if (!torso || !head || torso[2]<head[2]*.74 || torso[2]<torso[3]*.25)
            flag('corpo_palito',f,name,'Use um tronco preenchido e largo, conforme a referência.');
        }
        if (alpha>.5 && el.dataset.legendaDe) {
          const figure=nodes.find(item=>item.dataset.elemento===el.dataset.legendaDe);
          const feet=figure && [...figure.querySelectorAll('[data-parte=pe],[data-parte=canela]')];
          const title=el.querySelector('[data-titulo]');
          if (title && feet?.length) {
            const bottom=Math.max(...feet.map(foot=>{const [,y,,h]=region(foot);return y+h;}));
            const gap=region(title)[1]-bottom;
            if (gap<(wide?23:38)) flag('rotulo_colado_nos_pes',f,name,'Separe o rótulo da sola por uma margem visual.');
          }
        }
        if (alpha>.5 && el.dataset.ajudaDe) {
          const hasGlow=id=>{
            const halo=nodes.find(item=>item.dataset.elemento===id)?.querySelector('[data-parte=brilho]');
            return halo && effectiveOpacity(halo)>.18;
          };
          if (hasGlow(el.dataset.ajudaPara))
            flag('brilho_no_receptor',f,name,'Reserve o brilho para a figura que inicia a ajuda.');
        }
        if (alpha>.72) {
          if (el.querySelector('[data-titulo]')) texts.push([name,region(el.querySelector('[data-titulo]'))]);
          else if (el.dataset.pose) shapes.push([name,box]);
        }
      }
      if (check) {
        for (let i=0;i<texts.length;i++) for (const [name,box] of [...texts.slice(i+1),...shapes]) {
          if (inter(texts[i][1],box)) flag('sobreposicao',f,texts[i][0]+'/'+name,'Separe o texto das figuras e demais títulos.');
        }
        const highlights=new Set(events.filter(row=>row.scene===id && row.emphasis && t>=row.start && t<row.end)
          .map(row=>row.group));
        if (highlights.size>2) flag('destaques_simultaneos',f,id,'Escalone os movimentos de destaque ou agrupe ações que representam o mesmo gesto.');
      }
      if(f<active) {
      const m=metrics[id]??={total:0,moved:0,static:0,longest:0, ids:new Set()};
      m.total++;
      const changes=[...current].filter(([key,item])=>{
        const a=prior.get(key);
        return !a || item.signature!==a.signature || item.box.some((n,i)=>Math.abs(n-a.box[i])>.015);
      });
      const sec=perSecond[Math.floor(t)]??={movimento:0,quadros:0};
      sec.quadros++;
      if (lastScene===id && changes.length) {
        sec.movimento++;m.moved++;m.static=0;changes.forEach(([name])=>m.ids.add(name));
      } else if(lastScene===id) {
        m.static++;m.longest=Math.max(m.longest,m.static);
      }
      }
      const ending=scene.fim<=(f+1)/fps || f===active-1 || f===count-1;
      if (ending && !choreography) for (const [name,item] of current) {
        if(item.alpha>.04 && item.alpha<.96 && !events.some(e=>e.element===name && e.action==='pulsar'))
          flag('opacidade_residual',f,name,'Finalize a transição antes do fim da cena.','atencao');
      }
      prior=current;lastScene=id;
    }
    const totals=Object.fromEntries(Object.entries(metrics).map(([name,m])=>[name,{
      movimento:m.moved/Math.max(1,m.total-1), pausa_maxima_s:m.longest/fps, elementos:m.ids.size,
      quadros:m.total}]));
    if (!choreography && ['abundante','maxima'].includes(data.densidade)) for(const [name,m] of Object.entries(totals)){
      const action=data.cenas.find(scene=>scene.id===name)?.movimento;
      if(gestual && (!action || action.gesto.mao==='nenhuma')) continue;
      if(m.movimento<.85 || m.pausa_maxima_s>.8 || (!gestual && m.elementos<3))
        flag('densidade',Math.round(data.cenas.find(s=>s.id===name).inicio*fps),name,'Acrescente movimento discreto e distribua a ação na cena.');
    }
    if(data.auditoria_sincronia) for(const e of events) {
      const expected=data.palavras[e.word].quadro;
      if(Math.abs(Math.round(e.landing*fps)-expected)>1)
        flag('pouso_fora_do_quadro',expected,e.element,'Faça a pose ou início do gesto coincidir com a palavra.');
    }
    for(const e of events) {
      const at=Math.round(e.start*fps);
      mark('EC-032',at,e.element);
      if(window.AuditoriaCatalogo.shortEvent(e))
        flag('movimento_curto',at,e.element,'Alongue a entrada ou a troca.');
    }
    return {issues,metrics:totals,perSecond,events,sampled,quadros_totais:count,modo:integral?'integral':'amostrada',estimated:data.estimado,duration:data.duracao,
      versao_catalogo:2, checagens_catalogo:Object.fromEntries(catalogChecks),
      visualChecks:data.auditoria_sincronia || false, ...(geometria.length?{geometria_export:geometria}:{}), ...(presencas.length?{presencas}:{}), ...(livros.length?{livros}:{}), ...(luzes.length?{luzes}:{}), ...(atmosferas.length?{atmosferas}:{}), ...(oracoes.length?{oracoes}:{}), ...(continuidades.length?{continuidades}:{}), ...(gestual?{gestos_amostras:gestures}:{}), criterios_artisticos:!!choreography, quadros_ativos:active,
      ...(proportions?{proporcoes:{medicoes:proportions.table,quadros_reprovados:failures}}:{})};
  },mode==='integral');
  for (const message of errors) report.issues.push({codigo:'erro_js',quadro:0,elemento:'palco',
    correcao:message,nivel:'bloqueante'});
  await page.setViewportSize({width:Math.round(width/3),height:Math.round(height/3)});
  const frames=new Set(report.issues.map(i=>i.quadro));
  for (const e of report.events) for(const d of [-.25,0,.25])
    frames.add(Math.max(0,Math.min(Math.round(report.duration*30)-1,Math.round((e.target+d)*30))));
  report.tiras=[];
  for(const frame of [...frames].sort((a,b)=>a-b)) {
    const name='auditoria-quadros/'+String(frame).padStart(6,'0')+'.png';
    await mkdir(path.join(output,'auditoria-quadros'),{recursive:true});
    await page.evaluate(t=>window.render(t),frame/30);
    await page.locator('#palco').screenshot({path:path.join(output,name)});
    report.tiras.push({quadro:frame,arquivo:name});
  }
  await writeFile(path.join(output,'auditoria-dom.json'),JSON.stringify(report,null,2));
} finally {await browser.close();}
