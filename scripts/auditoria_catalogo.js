/* Checagens geométricas do catálogo. Coordenadas são lidas do SVG renderizado. */
(() => {
  const distance = (a,b) => Math.hypot(a.x-b.x,a.y-b.y);
  const inside = (element, point, stage) => !!element && element.isPointInFill(
    new DOMPoint(point.x,point.y).matrixTransform(element.getCTM().inverse().multiply(stage.getCTM())));
  const point = (element, stage, x='cx', y='cy') => {
    if(!element) return null;
    return new DOMPoint(Number(element.getAttribute(x)),Number(element.getAttribute(y)))
      .matrixTransform(stage.getCTM().inverse().multiply(element.getCTM()));
  };
  const joint = (actor,id,stage) => point(actor?.querySelector('[data-articulacao='+id+']'),stage);
  const juncoes = ({pescoço, ombros, perfil}) => pescoço && ombros.every(Boolean) &&
    perfil.every(({largo, cintura, salto}) => largo > cintura && salto <= .23);
  const palmas = ({ligacoes, distancia, cabeca, altura, pouso}) => ligacoes.length === 2 &&
    ligacoes.every(Boolean) && distancia <= cabeca*.9 && altura <= cabeca*.75 && pouso;
  function afirmacoes(claim, fact){
    switch(claim.tipo){
      case 'maos_em_contato': return fact.maos_em_contato;
      case 'pes_no_chao': return fact.pes_no_chao;
      case 'sentado_no_banco': return fact.sentado_no_banco;
      case 'palmas_no_peito': return fact.palmas_no_peito;
      case 'coracao_nas_maos': return fact.coracao_nas_maos;
      case 'agente_a_esquerda': return fact.agente_a_esquerda;
      default: return false;
    }
  }

  const shortEvent = event => !Number.isFinite(event.start) || !Number.isFinite(event.end) ||
    Math.round((event.end-event.start)*30)<event.minimum;
  const changeOpacity = (previous, next) => Math.abs(next-previous)>.35;
  function texto(stage, data, frame, mark) {
    const opacity = el => {
      let value = 1;
      for(let part=el;part&&part!==stage;part=part.parentElement)
        value*=Number(part.getAttribute('opacity')??1);
      return value;
    };
    const texts=[...stage.querySelectorAll('text,foreignObject')]
      .filter(el=>opacity(el)>.035&&getComputedStyle(el).visibility==='visible');
    const box=el=>el.getBoundingClientRect();
    const intersects=(a,b)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>2 &&
      Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>2;
    const falling=stage.querySelector('[data-queda=sim]');
    if(falling&&opacity(falling)>.035){
      const collision=texts.some(el=>!falling.contains(el)&&intersects(box(el),box(falling)));
      mark('EC-025',frame,'NÃO',collision?'Use um corredor de saída livre para a palavra riscada.':null);
    }
    const ids = new Set(data.cenas.map(scene=>scene.id.toUpperCase()));
    const internal=texts.some(el=>(el.textContent.toUpperCase().match(/[A-Z0-9_-]+/g)||[])
      .some(word=>ids.has(word))) ||
      [...stage.querySelectorAll('[data-progresso], [role=progressbar]')].some(el=>opacity(el)>.035);
    mark('EC-028',frame,'palco',internal?'Mantenha IDs e barra de progresso apenas nos controles.':null);
    const dash=texts.some(el=>/^\s*(?:[—–-]\s*){2,}$/.test(el.textContent));
    mark('EC-029',frame,'palco',dash?'Remova a sequência de traços decorativos.':null);
    const titles=texts.filter(el=>el.hasAttribute('data-titulo'));
    const floor=stage.querySelector('[data-parte=piso]');
    if(floor && titles.length){
      const y=box(floor).top;
      const near=titles.some(el=>box(el).top<y+38 && box(el).bottom>y-38);
      mark('EC-027',frame,'rótulo',near?'Separe o rótulo da faixa dos pés e da linha do chão.':null);
    }
    const exiting=[...stage.querySelectorAll('[data-transicao=saida]')].filter(el=>opacity(el)>.10);
    if(exiting.length){
      const outgoing=texts.filter(el=>el.closest('[data-transicao=saida]')&&opacity(el)>.25);
      const incoming=[...stage.querySelectorAll('[data-pose], [data-titulo]')]
        .filter(el=>!el.closest('[data-transicao=saida]')&&opacity(el)>.25);
      const collision=outgoing.some(el=>incoming.some(other=>intersects(box(el),box(other))));
      mark('EC-019',frame,'transição',collision?'Separe a saída da entrada para não sobrepor a leitura.':null);
    }
    const animated=titles.some(el=>el.querySelectorAll('[data-palavra]').length>=4);
    mark('EC-030',frame,'palco',animated?'Reserve a revelação da frase inteira para a legenda.':null);
  }
  const opacityOf = el => {
    let value=1;
    for(let node=el;node;node=node.parentElement)value*=Number(node.getAttribute('opacity')??1);
    return value;
  };
  function comparacao(stage, first, second, frame, mark){
    const line=stage.querySelector('[data-elemento=divisoria] line');
    if(!line||opacityOf(line)<.02||!first||!second)return;
    const x=point(line,stage,'x1','y1').matrixTransform(stage.getScreenCTM()).x;
    const arms='[data-contorno-continuo=braco], [data-parte=mao], [data-parte=mao_secundaria], [data-dobra-palma], [data-palma-pintada]';
    for(const [actor,left] of [[first,true],[second,false]]){
      const crosses=[...actor.querySelectorAll(arms)].some(el=>{
        if(opacityOf(el)<.02)return false;
        const r=el.getBoundingClientRect();
        const stroke=Number(el.getAttribute('stroke-width')||0)*Math.hypot(el.getScreenCTM().a,el.getScreenCTM().b)/2;
        return left?r.right+stroke>x-2:r.left-stroke<x+2;
      });
      mark('EC-042',frame,actor.dataset.elemento,crosses?'Mantenha o braço dentro do próprio lado da divisória.':null);
    }
    const arrows=[...stage.querySelectorAll('[data-elemento=sai] [data-objeto=seta]')]
      .filter(el=>opacityOf(el)>=.02);
    if(arrows.length){
      const crosses=arrows.some(el=>el.getBoundingClientRect().right+
        Number(el.dataset.traco||0)*Math.hypot(el.getScreenCTM().a,el.getScreenCTM().b)/2>x-2);
      mark('EC-042',frame,'seta',crosses?
        'Termine a seta antes da divisória para liberar o trajeto até as palmas.':null);
    }
  }
  function inspect(stage, data, frame, mark){
    const actors=[...stage.querySelectorAll('[data-figura-rig]')]
      .filter(actor=>Number(actor.getAttribute('opacity')??1)>.25);
    const first=actors.find(actor=>actor.dataset.elemento==='agente');
    const second=actors.find(actor=>actor.dataset.elemento==='outro');
    const hand=(actor,side)=>joint(actor,'mao'+side,stage);
    const head=(actor)=>Number(actor?.dataset.canonH)/data.bible.canon.cabecas;
    const claims=(data.afirmacoes_storyboard||[]).filter(row=>row.quadro===frame);
    const cues=data.coreografia.cues;
    if(data.rig_anatomico){
      const benchLayer=stage.querySelector('[data-elemento=banco]');
      if(benchLayer&&Number(benchLayer.getAttribute('opacity'))>.12&&(frame<cues.sentar.frame-12||frame>cues.levantar.frame)){
        const actor=stage.querySelector('[data-elemento=agente] [data-rig-anatomico]');
        const legs=actor?[...actor.querySelectorAll('[data-massa^=perna], [data-massa^=pe]')]
          .filter(el=>el.dataset.massa!=='pescoco'):[];
        const benchParts=[...benchLayer.querySelectorAll('rect')];
        const overlap=benchParts.some(part=>{
          const b=part.getBoundingClientRect();
          return legs.some(leg=>{
            const r=leg.getBoundingClientRect();
            const l=Math.max(b.left,r.left),t=Math.max(b.top,r.top);
            const z=Math.min(b.right,r.right),h=Math.min(b.bottom,r.bottom);
            for(let x=l+2;x<z-1;x+=3)for(let y=t+2;y<h-1;y+=3){
              const pt=new DOMPoint(x,y).matrixTransform(stage.getScreenCTM().inverse());
              if(inside(part,pt,stage)&&inside(leg,pt,stage))return true;
            }
            return false;
          });
        });
        mark('EC-003',frame,'pernas_banco_anatomico',overlap?
          'Separe os contornos das pernas e do banco antes de sentar.':null);
      }
      const planted=frame>=cues.receber.frame&&frame<cues.fazer.frame-8;
      const landed=stage.querySelector('[data-modo-entrega=trajeto][data-dono=outro]');
      if(!claims.length&&!planted&&!landed)return;
      const [a,b]=[...stage.querySelectorAll('[data-rig-anatomico]')].map(el=>el.parentElement);
      const node=(actor,id)=>point(actor?.querySelector('[data-ponto-anatomico='+id+']'),stage);
      const mass=(actor,id)=>actor?.querySelector('[data-massa='+id+']');
      const head=b&&mass(b,'cabeca').getBoundingClientRect().height;
      const hands=b&&['E','D'].map(side=>node(b,'mao'+side));
      const center=hands&&new DOMPoint((hands[0].x+hands[1].x)/2,(hands[0].y+hands[1].y)/2);
      const bench=stage.querySelector('[data-parte=assento]')?.getBoundingClientRect();
      const floor=stage.querySelector('[data-parte=piso]')?.getBoundingClientRect();
      const hip=node(a,'pelve'),screen=hip?.matrixTransform(stage.getScreenCTM());
      const heart=stage.querySelector('[data-chegada=pouso] path,[data-dono=outro] path');
      const heartEnd=heart&&new DOMPoint(0,.88).matrixTransform(stage.getCTM().inverse().multiply(heart.getCTM()));
      const p=node(a,'maoD'), q=node(b,'maoD');
      const grip=p&&q&&distance(p,q)<head*.44&&[.25,.5,.75].some(k=>{
        const m={x:p.x+(q.x-p.x)*k,y:p.y+(q.y-p.y)*k};
        return inside(mass(a,'maoD'),m,stage)&&inside(mass(b,'maoD'),m,stage);
      });
      const fact={
        maos_em_contato:grip,
        palmas_no_peito:!!(center&&distance(...hands)<head*.54&&Math.abs(center.y-node(b,'toracica').y)<head*.72
          && ['E','D'].every(side=>node(b,'cotovelo'+side).y>node(b,'punho'+side).y)),
        coracao_nas_maos:!!(center&&heartEnd&&distance(center,heartEnd)<head*.12),
        sentado_no_banco:!!(bench&&screen&&screen.x>=bench.left&&screen.x<=bench.right
          && Math.abs(screen.y+mass(a,'cabeca').getBoundingClientRect().height*.31-bench.top)<8),
        pes_no_chao:!!(a&&floor&&['E','D'].every(side=>Math.abs(mass(a,'pe'+side).getBoundingClientRect().bottom-floor.top)<3)),
        agente_a_esquerda:!!(hip&&b&&hip.x<node(b,'pelve').x)
      };
      if((planted||landed)&&b){
        const bothPalms=hands.every((tip,i)=>{
          const side='ED'[i], palm=mass(b,'mao'+side), wrist=node(b,'punho'+side);
          const other=mass(b,'mao'+'DE'[i]);
          const torso=mass(b,'tronco');
          const px=(tip.x+wrist.x)/2,py=(tip.y+wrist.y)/2;
          const visible=[-.10,0,.10].flatMap(dx=>[0,.05,.10].map(dy=>({x:px+dx*head,y:py+dy*head})))
            .filter(pt=>inside(palm,pt,stage)&&!inside(other,pt,stage)&&!inside(heart,pt,stage)&&
              (i===1||!inside(torso,pt,stage)));
          return visible.length>=2;
        });
        mark('EC-013',frame,'palmas_anatomicas',bothPalms&&fact.palmas_no_peito&&fact.coracao_nas_maos?
          null:'Deixe duas palmas apoiando o coração visíveis e ligadas aos antebraços.');
        const divider=stage.querySelector('[data-elemento=divisoria] line');
        if(divider){
          const limit=divider.getBoundingClientRect().left;
          const armMax=Math.max(...['bracoE','bracoD','maoE','maoD'].map(key=>mass(a,key).getBoundingClientRect().right));
          const armMin=Math.min(...['bracoE','bracoD','maoE','maoD'].map(key=>mass(b,key).getBoundingClientRect().left));
          const stray=[...stage.querySelectorAll('[data-objeto=seta]')].some(el=>el.getBoundingClientRect().right>limit);
          mark('EC-042',frame,'comparacao_anatomica',armMax<limit&&armMin>limit&&!stray?
            null:'Mantenha braços e setas em seus lados; apenas o objeto atravessa a divisória.');
        }
      }
      for(const row of claims)
        mark('EC-017',frame,row.tipo,afirmacoes(row,fact)?null:'Corrija a nota ou a geometria: a afirmação não aparece no quadro.');
      return;
    }
    comparacao(stage,first,second,frame,mark);
    if(first && second && frame<cues.levantar.frame-27) {
      const a=first.getBoundingClientRect(), b=second.getBoundingClientRect();
      const gap=b.left-a.right;
      mark('EC-021',frame,'outro',gap<head(second)*.13?
        'Afaste a segunda figura durante sua entrada.':null);
    }
    if(first?.dataset.pose==='em_pe' && frame>=data.coreografia.comparacao && frame<cues.fazer.frame-1){
      const hip=joint(first,'quadril',stage);
      const rest=['E','D'].every(side=>Math.abs(hip.x-hand(first,side).x)<head(first)*1.45);
      mark('EC-011',frame,'agente',rest?null:'Mantenha os braços de repouso próximos do tronco.');
    }
    const scene=data.cenas.find(row=>row.inicio<=frame/30 && frame/30<row.fim);
    const active=stage.querySelector('[data-elemento=recepcao], [data-elemento=oferta]');
    if(second && scene && frame>=cues.receber.frame && frame<cues.fazer.frame-8){
      const palmCount=second.querySelectorAll('[data-palma-aberta]').length;
      const competing=stage.querySelector('[data-elemento=chega]');
      mark('EC-022',frame,'recepção',active&&palmCount===2&&!competing?null:
        'Mostre uma só metáfora e um objeto que chega às duas palmas.');
    }

    for(const actor of actors){
      if(!actor.hasAttribute('data-contorno-cinematico')) continue;
      const neck=actor.querySelector('[data-parte=pescoco]');
      const torso=actor.querySelector('[data-parte=tronco]');
      const skull=actor.querySelector('[data-parte=cabeca]');
      if(!neck || !torso || !skull){
        mark('EC-012',frame,actor.dataset.elemento,'Mantenha cabeça, pescoço e tronco preenchidos e ligados.');
        continue;
      }
      const n=joint(actor,'pescoco',stage), t=point(skull,stage);
      const intersects=(a,b,p,q)=>[.15,.30,.45,.60,.75,.90].some(k=>{
        const probe={x:p.x+(q.x-p.x)*k,y:p.y+(q.y-p.y)*k};
        return inside(a,probe,stage)&&inside(b,probe,stage);
      });
      const hip=joint(actor,'quadril',stage), height=head(actor);
      const apparent=torso.getBoundingClientRect();
      const skullBox=skull.getBoundingClientRect();
      mark('EC-008',frame,actor.dataset.elemento,apparent.width<skullBox.width*.74?
        'Use um tronco preenchido proporcional à cabeça.':null);
      const feet=[...actor.querySelectorAll('[data-parte=pe]')];
      const width=feet.map(el=>el.getBBox());
      if(width.length===2)
        mark('EC-009',frame,actor.dataset.elemento,width.some(r=>r.width>height*1.02 || r.height<height*.15)?
          'Encurte o pé e mantenha espessura e ponta arredondada.':null);
      if(actor.dataset.pose==='sentado_no_chao'){
        const feet=['E','D'].map(side=>joint(actor,'pe'+side,stage));
        mark('EC-010',frame,actor.dataset.elemento,distance(...feet)<height*.12?
          'Separe as pernas e os pés na silhueta da pose de chão.':null);
      }
      const shoulderChecks=['E','D'].map((side,i)=>{
        const arm=actor.querySelector('[data-contorno-continuo=braco][data-lado='+side+']');
        const shoulder=joint(actor,'ombro'+side,stage);
        const elbow=joint(actor,'cotovelo'+side,stage);
        const mid=joint(actor,'ombro'+(i?'E':'D'),stage);
        const toward=ratio=>({x:shoulder.x+(mid.x-shoulder.x)*ratio,y:shoulder.y+(mid.y-shoulder.y)*ratio});
        return [0,.10,.20,.30].some(offset=>intersects(torso,arm,toward(offset),elbow));
      });
      const localWidth = y => {
        let width=0;
        for(let x=-height;x<=height;x+=height/80)
          if(torso.isPointInFill(new DOMPoint(x,y)))width+=height/80;
        return width/height;
      };
      const box=torso.getBBox();
      const r=f=>localWidth(box.y+box.height*f);
      const perfil=[{largo:r(.32),cintura:r(.65),salto:Math.abs(r(.29)-r(.35))}];
      const measured={pescoço:intersects(neck,skull,n,t)&&intersects(neck,torso,n,hip),ombros:shoulderChecks,perfil}; const ok=juncoes(measured);
      mark('EC-012',frame,actor.dataset.elemento,ok?null:'Una pescoço e braços ao tronco e arredonde os ombros.', measured);
    }

    const seat=stage.querySelector('[data-parte=assento]');
    if(seat && first && first.dataset.pose==='em_pe' && Number(seat.parentElement.getAttribute('opacity')??1)>.5){
      const area=seat.getBoundingClientRect();
      const hip=joint(first,'quadril',stage);
      mark('EC-003',frame,'agente',hip.x>=area.left && hip.x<=area.right?
        'Mantenha a figura em pé ao lado do banco.':null);
    }
    const grip=stage.querySelector('[data-contato-esperado=sim]');
    if(grip && first){
      const handGlyph=first.querySelector('[data-parte=mao]');
      const limb=first.querySelector('[data-contorno-continuo=braco][data-lado=D]');
      const wrist=hand(first,'D');
      const visibleHand=inside(handGlyph,wrist,stage)&&inside(limb,wrist,stage);
      mark('EC-015',frame,'agente',visibleHand?null:'Desenhe a mão no fim do antebraço durante a pega.');
    }
    const halo=stage.querySelector('[data-parte=brilho], [fill="url(#halo-impulso)"]');
    if(halo && first){
      const haloCenter=point(halo,stage);
      const firstGap=distance(haloCenter,joint(first,'pescoco',stage));
      const wrong=second && firstGap>distance(haloCenter,joint(second,'pescoco',stage));
      mark('EC-020',frame,'brilho',wrong?'Reserve o brilho para a figura que inicia a ação.':null);
      const stops=[...stage.querySelectorAll('#halo-impulso stop')];
      const softened=stops.length>=3 && +stops[0].getAttribute('stop-opacity')>0 &&
        +stops.at(-1).getAttribute('stop-opacity')===0 &&
        !halo.getAttribute('stroke');
      mark('EC-023',frame,'brilho',softened?null:'Use brilho difuso até transparência, sem aro.');
    }
    const palms=second ? [...second.querySelectorAll('[data-palma-aberta]')] : [];
    let palmFacts=false, heartOnHands=false;
    if(palms.length){
      const height=head(second), hands=['E','D'].map(side=>hand(second,side));
      const center=joint(second,'quadril',stage);
      const neck=joint(second,'pescoco',stage);
      const chest={x:(center.x+neck.x)/2,y:(center.y+neck.y)/2};
      const mid={x:(hands[0].x+hands[1].x)/2,y:(hands[0].y+hands[1].y)/2};
      const links=hands.map((p,i)=>{
        const side=['E','D'][i];
        return inside(palms.find(el=>el.dataset.lado===side),p,stage) &&
          !!second.querySelector('[data-dobra-palma='+side+']');
      });
      const heightDelta=Math.abs(mid.y-chest.y);
      const heart=stage.querySelector('[data-chegada=pouso] path, [data-dono=outro] path');
      const heartPoint=heart && new DOMPoint(0,.88)
        .matrixTransform(stage.getCTM().inverse().multiply(heart.getCTM()));
      const comparison=stage.querySelector('[data-elemento=divisoria] line');
      heartOnHands=!!heartPoint&&distance(heartPoint,mid)<=height*(comparison ? .21 : .48);
      const elbows=['E','D'].map(side=>joint(second,'cotovelo'+side,stage));
      const tuck=elbows.every((elbow,i)=>elbow.y-hands[i].y>=height*.16 &&
        Math.abs(elbow.x-hands[i].x)<=height*.64);
      palmFacts=palmas({ligacoes:links,distancia:distance(...hands),cabeca:height,altura:heightDelta,pouso:true}) &&
        (!comparison||(tuck&&distance(...hands)<=height*.49));
    }
    if(second?.hasAttribute('data-contorno-cinematico') && frame>=cues.receber.frame &&
        (frame<cues.fazer.frame-8 || frame>=cues.fazer.frame+30 ||
         !!stage.querySelector('[data-modo-entrega=trajeto][data-dono=outro]')))
      mark('EC-013',frame,'outro',palmFacts&&heartOnHands?null:
        'Mostre palmas unidas aos antebraços, no peito, e pouse o coração nelas.');
    if(claims.length){
      const grip=first&&second&&distance(hand(first,'D'),hand(second,'E'))<=8&&
        inside(first.querySelector('[data-parte=mao]'),hand(first,'D'),stage)&&
        inside(second.querySelector('[data-parte=mao_secundaria]'),hand(second,'E'),stage);
      const floor=stage.querySelector('[data-parte=piso]');
      const ground=floor?.getBoundingClientRect().top;
      const feet=first ? [...first.querySelectorAll('[data-parte=pe]')] : [];
      const seat=stage.querySelector('[data-parte=assento]')?.getBoundingClientRect();
      const hip=first&&joint(first,'quadril',stage).matrixTransform(stage.getScreenCTM());
      const radius=first&&Number(first.dataset.quadrilRaio)*Math.hypot(first.getScreenCTM().a,first.getScreenCTM().b);
      const fact={maos_em_contato:!!grip,palmas_no_peito:palmFacts,coracao_nas_maos:heartOnHands,
        sentado_no_banco:!!(seat&&hip&&first.dataset.pose==='sentado'&&first.dataset.apoio==='banco'&&
          hip.x>=seat.left&&hip.x<=seat.right&&Math.abs(hip.y+radius-seat.top)<=9),
        pes_no_chao:Number.isFinite(ground)&&feet.length===2&&
          feet.every(foot=>Math.abs(ground-foot.getBoundingClientRect().bottom)<=6),
        agente_a_esquerda:!!(first&&second&&joint(first,'quadril',stage).x<joint(second,'quadril',stage).x)};
      for(const row of claims)
        mark('EC-017',frame,row.tipo,afirmacoes(row,fact)?null:'Corrija a nota ou a geometria: a afirmação não aparece no quadro.');
    }
  }
  function enumeracao(scene,visible,frame){
    const config=scene?.revelacao_figuras;
    const ease=value=>{
      const u=Math.min(1,Math.max(0,value));
      return u*u*(3-2*u);
    };
    const expected=config&&frame<config.saida_fim?
      scene.figuras.filter(figure=>frame>=figure.pouso):[];
    return expected.length===visible.length&&expected.every((figure,index)=>{
      const item=visible[index];
      const entry=ease((frame-figure.pouso+1)/config.entrada_quadros);
      const exit=1-ease((frame-config.saida_inicio)/(config.saida_fim-config.saida_inicio));
      return item.tipo===figure.tipo&&Math.abs(item.opacity-entry*exit)<.001;
    });
  }
  function presenca(action,frame,{quantidade,opacidade,folga,cotovelo}){
    if(!action?.presenca||frame<=action.inicio||frame>=action.fim-1)return quantidade===0;
    if(quantidade!==1||opacidade<=0||!Number.isFinite(folga)||folga<15)return false;
    if(frame>=action.pouso&&frame<=action.presenca.sustenta_ate&&opacidade<.99)return false;
    if(frame>=action.presenca.alcance&&frame<=action.presenca.sustenta_ate)
      return folga<=83&&cotovelo>=0;
    return true;
  }
  function folgaContornos(first,second){
    if(!first||!second)return null;
    const outline=path=>{
      const matrix=path.getScreenCTM();
      const length=path.getTotalLength();
      const samples=Math.max(1,Math.ceil(length*Math.hypot(matrix.a,matrix.b)/2));
      return Array.from({length:samples+1},(_,i)=>path.getPointAtLength(length*i/samples).matrixTransform(matrix));
    };
    const a=outline(first), b=outline(second);
    const firstInverse=first.getScreenCTM().inverse(), secondInverse=second.getScreenCTM().inverse();
    if(a.some(p=>second.isPointInFill(p.matrixTransform(secondInverse)))||
       b.some(p=>first.isPointInFill(p.matrixTransform(firstInverse))))return 0;
    let gap=Infinity;
    for(const x of a)for(const y of b)gap=Math.min(gap,distance(x,y));
    return gap;
  }
  const livroApoiado=({distancias,virada,pagina})=>distancias.length===2&&
    distancias.every(d=>Number.isFinite(d)&&d<=18)&&pagina===(virada>0&&virada<1);
  const luzDaPresenca=({maos,feixes,opacidadeMao,opacidadeFeixe,limite})=>
    maos===feixes&&(!maos||(maos===1&&limite<=1335&&Math.abs(opacidadeMao-opacidadeFeixe)<.001));
  const livroOrientado=({leitor,camera,orientados})=>orientados===1&&leitor>.7&&Math.abs(camera)<.55;
  const oracaoVisivel=({palmas,distancia,dedos})=>palmas===2&&distancia<18&&dedos.every(y=>y<-22);
  const sombraVisivel=({falante,ouvinte,gestoOuvinte})=>
    falante>=16&&ouvinte>=20&&!gestoOuvinte;
  const atmosferaVisivel=({tipo,opacidade,limite,detalhes})=>
    ['sombra','aura','chuva','claridade','partilha'].includes(tipo)&&
    opacidade>0&&opacidade<=1&&limite<=1338&&detalhes;
  const partilhaVisivel=({progress,stage,owner,donor,receiver,expected})=>
    Number.isFinite(progress)&&Math.abs(progress-expected)<.001&&
    stage===(progress>=.5?'recebe':'doa')&&owner===(expected>0?receiver:donor);
  const elencoEstavel=({atores,banco,desvio,emPe})=>atores===2&&!banco&&desvio<=3&&emPe;
  const passoPlantado=({apoio,fracao,avanco,balanco})=>apoio<=3&&
    (fracao<1||avanco>=55)&&(fracao<.27||fracao>.73||balanco>=6);
  const cuidadoAposEntrega=({dono,segura,gesto,fracao})=>dono===1&&segura<=3&&
    (fracao<.40||fracao>.62||gesto>=18);
  const objetoComDono=(items,kind,owner)=>items.length===1&&items[0].kind===kind&&
    items[0].owner===owner&&items[0].opacity>=.99;
  const rotuloVisivel=(box,occluders)=>{
    const [x,y,w,h]=box;
    return w>0&&h>0&&x>=0&&y>=360&&x+w<=904&&y+h<=1338&&
      !occluders.some(([a,b,c,d])=>x<a+c&&a<x+w&&y<b+d&&b<y+h);
  };
  const api={juncoes,palmas,afirmacoes,inspect,texto,shortEvent,changeOpacity,enumeracao,presenca,folgaContornos,
    livroApoiado,luzDaPresenca,livroOrientado,oracaoVisivel,sombraVisivel,atmosferaVisivel,partilhaVisivel,
    elencoEstavel,passoPlantado,cuidadoAposEntrega,objetoComDono,rotuloVisivel};
  if(typeof module==='object') module.exports=api;
  else window.AuditoriaCatalogo=api;
})();
