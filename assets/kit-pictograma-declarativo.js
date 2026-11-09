/* Padrões reutilizáveis de composição no palco Pictograma. */
window.MotorCenas.registrarKit('pictograma-declarativo', api=>{
  const {data,width,height,colors,node,text,line,circle,rectangle,smoothstep,colorMix,cameraLayer}=api;
  const rig=window.PictogramaRig,b=data.rig_anatomico,bible=data.bible;
  const {environment,bench}=window.PictogramaPalco;
  const typography=window.PictogramaVirada(api);
  const visualMotion=window.PictogramaVisuais?.(api);
  const scenery=window.PictogramaCenarios?.(api);
  const painter=window.PictogramaEfeitos(api,{destaques:[]},bible);
  const floor=height*.65, scale=height*.060, yaw=82;
  const fx=data.composicao_declarativa;
  const intentional=fx.gestual==='expressivo_intencional';
  const acting=window.PictogramaAcoes;
  const blocking={centro:[.46,.62],esquerda:[.31,.59],direita:[.68,.49],dupla:[.36,.54],percurso:[.25,.46]};
  const layouts={
    pergunta:{actor:.68,visual:.28}, enumeracao:{actor:.73,visual:.28},
    objecao:{actor:.32,visual:.62}, citacao:{actor:.70,visual:.28},
    conclusao:{actor:.68,visual:.31}, conceito:{actor:.70,visual:.28},
    transformacao:{actor:.69,visual:.27}, comparacao:{actor:.68,visual:.28},
    virada:{actor:.70,visual:.30}, numero_data:{actor:.73,visual:.27},
    causa_efeito:{actor:.68,visual:.31}
  };
  function drawBook(group,x,y,unit,open,turn){
    const g=node('g',{'data-livro-material':'sim',transform:`translate(${x} ${y}) scale(${unit})`},group);
    const w=.38+.43*open;
    const cover=colorMix(colors.fundo,colors.acento,.65);
    const paper=colors.osso, shade=colorMix(colors.fundo,colors.osso,.84);
    const edge=(side,rise=0)=>`M 0 -.11 Q ${side*w*.55} ${-.68+rise} ${side*w} ${-.57+rise}
      L ${side*w*1.03} .16 Q ${side*w*.54} .13 0 .38 Z`;
    node('path',{fill:cover,d:`M 0 -.18 Q ${-w*.5} -.70 ${-w*1.05} -.61 L ${-w*1.13} .21
      Q ${-w*.5} .20 0 .47 Q ${w*.50} .20 ${w*1.13} .21 L ${w*1.05} -.61 Q ${w*.5} -.70 0 -.18 Z`},g);
    node('path',{fill:shade,d:edge(-1,.055)},g);
    node('path',{fill:shade,d:edge(1,.055)},g);
    node('path',{fill:paper,d:edge(-1)},g);
    node('path',{fill:shade,d:edge(1)},g);
    const ink=colorMix(colors.fundo,colors.osso,.58);
    for(const sign of [-1,1])for(const n of [0,1,2,3]){
      const row=-.40+n*.112;
      node('path',{d:`M ${sign*w*.22} ${row+.13} Q ${sign*w*.56} ${row-.035} ${sign*w*(n===3?.65:.83)} ${row-.035}`,
        fill:'none',stroke:ink,'stroke-width':.014,'stroke-linecap':'round'},g);
    }
    line(g,0,-.09,0,.395,cover,.026);
    if(turn>0&&turn<1){
      const a=Math.PI*turn, leaf=w*.98*Math.cos(a), bow=.43*Math.sin(a);
      node('path',{'data-pagina-em-virada':'sim',fill:paper,stroke:shade,'stroke-width':.014,
        d:`M 0 -.11 Q ${leaf*.55} ${-.68-bow} ${leaf} ${-.56-bow} L ${leaf*1.04} ${.15-bow}
          Q ${leaf*.55} ${.13-bow} 0 .38 Z`},g);
    }
  }
  function bookGeometry(open,turn,facing){
    const lateral=[.94,0,.342];
    const front=[-.342*facing,0,.94*facing];
    const up=[front[0]*.72,-.694,front[2]*.72];
    const normal=[-front[0]*.694,-.72,-front[2]*.694];
    const origin=[0,-3.49-.49*open,facing*(.74+.22*open)];
    const width=.47+.30*open;
    const at=(u,v,r=0)=>origin.map((value,i)=>value+u*lateral[i]+v*up[i]+r*normal[i]);
    const phase=Math.PI*turn;
    const grips=[at(-width*.83,-.42,.025),at(width*.83*Math.cos(phase),-.42,
      width*.83*Math.sin(phase)*.78+.025)];
    // The turning hand returns to its original cover as the leaf settles.
    if(turn>.84){
      const settle=smoothstep((turn-.84)/.16);
      grips[1]=grips[1].map((v,i)=>v+(at(width*.83,-.42,.025)[i]-v)*settle);
    }
    const angle=yaw*Math.PI/180;
    const camera=normal[0]*Math.sin(angle)-normal[2]*Math.cos(angle);
    const reader=-normal[2]*facing-normal[1]*.60;
    return {at,grips,width,camera,reader,turn};
  }
  function paintHeldBook(group,geometry,project){
    const {at,width:w,camera,reader,turn}=geometry;
    const vec=(u,v,depth)=>project(at(u,v,depth)).join(' ');
    const leaf=(edge,fold=0)=>`M ${vec(0,-.44,0)} Q ${vec(edge*.56,-.47,fold*.48)} ${vec(edge,-.41,fold)}
      L ${vec(edge,.48,fold)} Q ${vec(edge*.45,.52,fold*.48)} ${vec(0,.45,0)} Z`;
    const body=node('g',{'data-livro-orientado':'sim','data-normal-leitor':reader,
      'data-normal-camera':camera},group);
    const cover=colorMix(colors.fundo,colors.acento,.63);
    const leather=colorMix(colors.fundo,colors.acento,.51);
    for(const side of [-1,1]){
      const lip=w*1.07*side;
      node('path',{d:leaf(lip,-.065),fill:cover,stroke:leather,'stroke-width':2.1},body);
      node('path',{d:leaf(w*side,.025),
        fill:camera>0?(side===1?colorMix(colors.fundo,colors.osso,.87):colors.osso):leather,
        stroke:colorMix(colors.fundo,colors.osso,.74),'stroke-width':2.3},body);
      if(camera>0){
        for(const v of [-.19,.01,.20,.36]){
          node('path',{d:`M ${vec(w*.20*side,v,.038)} Q ${vec(w*.49*side,v-.015,.047)}
            ${vec(w*.79*side,v+.015,.038)}`,fill:'none',stroke:colorMix(colors.fundo,colors.osso,.60),
            'stroke-width':1.25,'stroke-linecap':'round'},body);
        }
      }
    }
    const [a,b]=[project(at(0,-.44)),project(at(0,.45))];
    line(body,a[0],a[1],b[0],b[1],cover,3);
    if(turn>0&&turn<1){
      const angle=turn*Math.PI, edge=w*Math.cos(angle), fold=w*Math.sin(angle)*.78;
      node('path',{'data-pagina-em-virada':'sim',d:leaf(edge,fold),fill:colors.osso,
        stroke:colorMix(colors.fundo,colors.osso,.78),'stroke-width':1.5},body);
    }
  }
  function mark(group,kind,x,y,r,t){
    const fill=colors.osso,accent=colors.acento, soft=colors.suave;
    const stroke=(a,b,c,d,w=5)=>line(group,a,b,c,d,accent,w);
    const p=(d,paint=accent)=>node('path',{d,fill:paint},group);
    if(kind==='livro'){
      drawBook(group,x,y,r,1,0);
    } else if(kind==='relogio'){
      node('circle',{cx:x,cy:y,r,fill:'none',stroke:accent,'stroke-width':5},group);
      const a=t*.6;
      stroke(x,y,x+Math.sin(a)*r*.72,y-Math.cos(a)*r*.72);
      stroke(x,y,x-r*.38,y-r*.23);
    } else if(kind==='linha'||kind==='seta'){
      stroke(x-r,y,x+r,y);
      p(`M ${x+r} ${y} l ${-r*.38} ${-r*.26} v ${r*.52} Z`);
      if(kind==='linha')for(const u of [-.7,-.16,.56])circle(group,x+r*u,y,7,fill);
    } else if(kind==='casa'){
      p(`M ${x-r} ${y-r*.15} L ${x} ${y-r*.94} ${x+r} ${y-r*.15} L ${x+r*.77} ${y-r*.15} V ${y+r*.67}
       H ${x-r*.77} V ${y-r*.15} Z`,fill);
    } else if(kind==='coracao'){
      p(`M ${x} ${y+r*.8} C ${x-r*1.6} ${y-r*.3} ${x-r} ${y-r*1.15} ${x} ${y-r*.42}
       C ${x+r} ${y-r*1.15} ${x+r*1.6} ${y-r*.3} ${x} ${y+r*.8} Z`);
    } else if(kind==='mao'){
      p(`M ${x-r} ${y+r*.40} L ${x-r*.41} ${y-r*.03} Q ${x} ${y-r*.47} ${x+r*.63} ${y-r*.52}
       Q ${x+r*.91} ${y-r*.43} ${x+r*.66} ${y-r*.21} L ${x+r*.06} ${y+r*.23}
       Q ${x+r*.48} ${y+r*.32} ${x+r*.83} ${y+r*.01} Q ${x+r} ${y+r*.24} ${x+r*.73} ${y+r*.46}
       Q ${x+r*.13} ${y+r} ${x-r*.28} ${y+r*.64} Z`);
    } else if(kind==='pausa'){
      for(const u of [-.55,0,.55])circle(group,x+r*u,y,Math.max(4,r*.15),fill);
    } else if(kind==='data'){
      rectangle(group,x-r,y-r*.7,2*r,1.5*r,fill,9);
      line(group,x-r*.71,y-r*.29,x+r*.71,y-r*.29,colors.fundo,4);
      circle(group,x,y+r*.22,r*.14,colors.fundo);
    } else if(kind==='pergunta'||kind==='moeda'){
      if(kind==='moeda')node('circle',{cx:x,cy:y,r,fill:'none',stroke:accent,'stroke-width':4},group);
      text(group,kind==='pergunta'?'?':'$',x,y+r*.53,2*r,1.65*r,{fill:accent});
    } else circle(group,x,y,r,soft);
  }
  function label(parent,value,x,y,max,size,ink){
    const el=text(parent,value,x,y,max,size,{fill:ink});
    el.classList.add('picto-display');
    el.dataset.titulo='sim';
    return el;
  }
  return (scene,previous)=>{
    const layout=layouts[scene.padrao], action=scene.movimento;
    const authored=blocking[scene.layout];
    const alternate=action?.variacao==='B';
    const [actorX,propX]=authored??[.68,layout.visual>.47?.31:layout.visual];
    const x=width*actorX,visual=width*propX;
    const paired=action?.alvo==='outro'&&action?.figura!=='animal';
    const pairGap=intentional&&['entregar','receber'].includes(action?.tipo)?.20:.27;
    const nextX=paired?(intentional?x+(actorX<.5?1:-1)*width*pairGap:
      scene.layout==='dupla'?width*.64:x+(actorX<.5?1:-1)*width*.27):x;
    const outward=paired?Math.sign(nextX-x):(propX>actorX?1:-1);
    const facing=scene.layout?outward:1;
    const titleY=height*.245;
    const transfer=intentional&&paired&&['entregar','receber'].includes(action?.tipo);
    const continuing=transfer&&action.tipo==='receber'&&action.relacao==='segurado';
    const transferFrame=continuing?previous.movimento.pouso:action?.pouso;
    const mood=scene.atmosfera;
    const sharing=mood?.tipo==='partilha'?(continuing||scene.manter_posse?previous?.paint?.partilha:
      transfer&&action.objeto==='coracao'?{
        quadro:transferFrame,from:action.tipo==='entregar'?0:1,to:action.tipo==='entregar'?1:0
      }:null):null;
    const sharedOrigin=intentional&&action?.tipo==='ajudar_a_levantar';
    const actorOrigin=i=>i?(sharedOrigin?x:authored?nextX:x-width*.29):x;
    const chair=(frame,up,dir=facing)=>acting.move(b,rig.chair(b,frame,up,{bracosContinuos:true}),0,dir);
    const continuesBook=intentional&&action?.tipo==='olhar_para'&&action.objeto==='livro'&&
      previous?.movimento?.tipo==='ler'&&previous.movimento.objeto==='livro'&&previous.layout===scene.layout;
    const readsBook=intentional&&action?.tipo==='ler'&&action.objeto==='livro';
    const bookMotion=f=>{
      const open=continuesBook?1:smoothstep((f-action.inicio)/Math.max(1,action.pouso+4-action.inicio));
      const end=Math.round(scene.fim*30)-1;
      const turn=continuesBook?0:smoothstep((f-action.pouso-9)/Math.min(21,Math.max(1,end-action.pouso-9)));
      return {open,turn,shift:.69+.23*open, lift:3.48+.48*open};
    };
    const bookPose=(f,base)=>{
      const {open,turn}=bookMotion(f);
      const model=bookGeometry(open,turn,facing);
      const length=b.ossos.mao, direction=[0,-.95,.312*facing];
      const hands=model.grips.map(grip=>grip.map((value,i)=>value-length*direction[i]));
      return rig.pose(b,{...base.control,hands,mode:'leitura',headPitch:continuesBook?8:12+9*open,
        handDirections:[direction,direction],armPoles:[[-.38,.74,-.30*facing],[.38,.74,-.30*facing]]});
    };
    const stays=scene.manter_elenco?previous.paint.state(Math.round(scene.inicio*30)-1):null;
    const intentionalPose=f=>{
      const seat=scene.assento===true;
      const kind=action?.tipo;
      const time=action?Math.max(0,Math.min(1,(f-action.inicio)/Math.max(1,action.fim-1-action.inicio))):0;
      const inWindow=action&&f>=action.inicio&&f<action.fim;
      const base=seat?chair(30,false):rig.neutral(b,facing);
      const second=rig.neutral(b,-facing);
      const active=base;
      if(stays){
        const nod=smoothstep((f-action.pouso+5)/9)*(1-smoothstep((f-action.pouso-7)/12));
        const weight=(f-Math.round(scene.inicio*30))/20;
        return stays.map(({actor},i)=>acting.settleAfterHelp(b,actor,weight,(i?6:-5)*nod));
      }
      if(readsBook||continuesBook)return [bookPose(f,base)];
      if(action?.oracao)return [acting.prayer(b,base,action,f,facing)];
      if(kind==='sentar')return [chair(30*time,false)];
      if(kind==='levantar'){
        const rising=chair(30*time,true);
        const step=action.passo_final;
        return [step&&f>=step.inicio?acting.stepFrom(b,rising,(f-step.inicio)/(step.fim-step.inicio)):rising];
      }
      if(kind==='sentar_juntos'){
        const elder=chair(26,false,-facing);
        return [chair(30*time,false),rig.pose(b,{...elder.control,spine:[19,9,5]})];
      }
      if(kind==='acompanhar_espera')
        return [acting.posture(b,active,'olhar_para',.26),chair(30,false,-facing)];
      if(kind==='ajudar_a_levantar')return acting.help(b,time*(b.ajuda.fim+8),{contatoDesenhado:true,bracosContinuos:true});
      if(kind==='tentar_levantar')return inWindow?
        acting.resolve(b,{...action,direcao:facing},f,chair(30,false)):[chair(30,false)];
      if(['andar_ate','aproximar','afastar'].includes(kind)){
        const dir=kind==='afastar'?-facing:facing;
        return [acting.move(b,rig.walk(b,time*b.marcha.quadros_por_passo),0,dir)];
      }
      if(transfer){
        const d=f-transferFrame, giver=kind==='entregar'||continuing?0:1;
        const actors=[active,second];
        const contact=smoothstep((d+12)/8)*(1-smoothstep((d-4)/12));
        const height=-3.65;
        const mid=(x+nextX)/2;
        for(const [i,pose] of actors.entries()){
          const dir=i?-facing:facing;
          const local=(mid-actorOrigin(i))/scale/Math.sin(yaw*Math.PI/180);
          const ready=smoothstep((d+12)/8);
          const holder=i===giver?1-smoothstep((d-4)/12):ready;
          const held=local*.54;
          const reach=held+(local-held)*contact;
          const weight=Math.max(holder,contact);
          actors[i]=weight>0?acting.holdHands(b,pose,'D',[.03,height,reach],dir,weight):pose;
        }
        const care=action.cuidado;
        if(care&&f>=care.inicio&&f<=care.fim)
          actors[1]=acting.care(b,actors[1],(f-care.inicio)/(care.fim-care.inicio));
        return actors;
      }
      if(action?.acentos){
        const accent=action.acentos.find(row=>f>=row.inicio&&f<row.fim);
        let speaker=accent?acting.expressive(b,active,{...action,...accent,tipo:'conversar',
          perfil_conversa:accent.tipo},f,facing):active;
        const last=action.acentos.at(-1);
        const delay=f-last.pouso;
        const nod=smoothstep((delay-5)/6)*(1-smoothstep((delay-11)/7));
        const gravity=action.acentos.find(row=>row.tipo==='recolher');
        if(gravity){
          const tension=smoothstep((f-gravity.inicio)/(gravity.pouso-gravity.inicio||1));
          const answer=smoothstep((f-gravity.inicio-3)/(gravity.pouso-gravity.inicio||1));
          speaker=rig.pose(b,{...speaker.control,headPitch:(speaker.control.headPitch??0)+20*tension,
            spine:speaker.control.spine.map((v,i)=>v+[5,6,2][i]*tension)});
          return [speaker,rig.pose(b,{...second.control,headPitch:28*answer,
            spine:second.control.spine.map((v,i)=>v+[3,5,2][i]*answer)})];
        }
        return [speaker,rig.pose(b,{...second.control,headPitch:8*nod})];
      }
      let performance=action;
      if(kind==='apontar'){
        const targetX=paired?nextX:visual;
        const targetY=paired?floor-scale*4.1:height*.48;
        const target=[0,(targetY-floor)/scale,(targetX-x)/scale/Math.sin(yaw*Math.PI/180)];
        performance={...action,alvoManual:target};
      }
      const result=inWindow?acting.expressive(b,active,performance,f,facing):active;
      if(!paired)return [result];
      const listener=acting.posture(b,second,'olhar_para',inWindow?.22:0);
      return [result,listener];
    };
    const pose=(f)=>{
      if(intentional)return intentionalPose(f);
      let active;
      const seated=scene.manter_sentado?window.PictogramaAcoes.chair(b,30,false):null;
      const standingAtSeat=fx.assento?window.PictogramaAcoes.chair(b,0,false):null;
      const base=seated??standingAtSeat??rig.neutral(b,facing);
      const targeted=paired;
      const contactDistance=action?.tipo==='entregar'?Math.abs(f-action.pouso):Infinity;
      const amplitude=smoothstep((contactDistance-4)/7);
      if(action?.tipo==='sentar_juntos'&&action.figura==='idoso'&&action.variacao==='A'){
        const elder=window.PictogramaAcoes.posture(b,rig.neutral(b,-facing),'curvar',.49);
        return [window.PictogramaAcoes.posture(b,base,'olhar_para',.48),elder];
      }
      if(action?.tipo==='sentar_juntos'){
        const tempo=30*smoothstep((f-action.inicio)/Math.max(1,action.pouso-action.inicio));
        const elder=window.PictogramaAcoes.chair(b,26,false);
        const curved=action.figura==='idoso'?rig.pose(b,{...elder.control,spine:[19,9,5]}):elder;
        return [window.PictogramaAcoes.chair(b,tempo,false),curved];
      }
      if(action&&f<action.fim){
        active=window.PictogramaAcoes.resolve(b,{...action,corpo:!!authored,amplitude_corpo:amplitude,
          passos:action.tipo==='andar_ate'&&scene.layout==='percurso'?2:1,
          direcao:authored?facing:targeted?-1:1},f,base);
      }else if(action?.tipo==='sentar'||seated){
        active=[window.PictogramaAcoes.chair(b,30,false)];
      }else{
        const ctrl=base.control;
        const breath=(fx.sensivel?.35:.65)*Math.sin(f*.16);
        active=[rig.pose(b,{...ctrl,spine:[ctrl.spine[0]+breath,ctrl.spine[1],ctrl.spine[2]]})];
      }
      if(targeted&&active.length===1){
        if(authored&&action.tipo==='conversar'){
          const secondStart=Math.min(action.fim-5,action.pouso+8);
          const secondary=rig.neutral(b,-facing);
          if(f<secondStart){
            const listening=.26*Math.sin(Math.PI*smoothstep((f-action.inicio)/Math.max(1,secondStart-action.inicio)));
            active[0]=window.PictogramaAcoes.resolve(b,{...action,fim:secondStart,corpo:true,direcao:facing},f,base)[0];
            active.push(window.PictogramaAcoes.posture(b,secondary,'olhar_para',listening));
          }
          else {
            const listening=.26*Math.sin(Math.PI*smoothstep((f-secondStart)/Math.max(1,action.fim-secondStart)));
            active[0]=window.PictogramaAcoes.posture(b,base,'olhar_para',listening);
            active.push(...window.PictogramaAcoes.resolve(b,{tipo:'conversar',corpo:true,
              direcao:-facing,inicio:secondStart,fim:action.fim},f,secondary));
          }
        }else if(action.tipo==='entregar')active.push(...window.PictogramaAcoes.resolve(b,
          {...action,tipo:'receber',direcao:authored?-facing:1},f));
        else active.push(rig.neutral(b,authored?-facing:1));
      }
      if(action?.figura==='crianca'&&active.length===2)
        active[1]=window.PictogramaAcoes.posture(b,active[1],'curvar',.42);
      if(authored&&paired&&action.tipo==='entregar'&&active.length===2){
        const gripDistance=Math.abs(f-action.pouso);
        const gripWeight=gripDistance<=4?1:.28*(1-smoothstep((gripDistance-4)/5));
        if(gripWeight>0){
          const localGrip=(nextX-x)/scale/2/Math.sin(yaw*Math.PI/180);
          active[0]=window.PictogramaAcoes.holdHands(b,active[0],'D',[.05,-3.95,localGrip],facing,gripWeight);
          active[1]=window.PictogramaAcoes.holdHands(b,active[1],'D',[.05,-3.95,-localGrip],-facing,gripWeight);
        }
      }
      return active;
    };
    const cast=[{id:'principal',scale}];
    if(paired)cast.push({id:action?.figura??'interlocutor',scale:action?.figura==='crianca'?scale*.64:scale});
    const inherited=scene.manter_posse?previous?.paint?.posse:null;
    const state=f=>pose(f).map((actor,i)=>({
      ...(!inherited||i!==inherited.owner?{}:{
        priorHolder:previous.paint.state(Math.round(scene.inicio*30)-1)[i]?.actor
      }),
      actor,x:stays?.[i].x??actorOrigin(i),id:stays?.[i].id??cast[i]?.id??'interlocutor',unit:stays?.[i].unit??cast[i]?.scale??scale
    })).map(({priorHolder,...entry})=>priorHolder?{...entry,actor:priorHolder}:entry);
    const benchInfo=()=>{
      const standingElder=action?.tipo==='sentar_juntos'&&action.figura==='idoso'&&action.variacao==='A';
      if(standingElder || !((intentional?scene.assento:scene.manter_sentado)||
          ['sentar','levantar','sentar_juntos','acompanhar_espera','tentar_levantar'].includes(action?.tipo)))return null;
      const double=action?.tipo==='sentar_juntos';
      const waiting=action?.tipo==='acompanhar_espera';
      const left=double?Math.min(x,nextX)-scale*1.02:(waiting?nextX:x)-scale*1.26;
      return {x:left,comprimento:double?Math.abs(nextX-x)+scale*2.29:scale*1.22,
        pernas:double?[.02,.96]:[.12,.35]};
    };
    const transitionAt=f=>{
      const frames=scene.entrada_continua?.quadros;
      if(!frames||!previous?.paint?.state)return null;
      const start=Math.round(scene.inicio*30)-(scene.entrada_continua.preparo_anterior??0);
      if(f<start||f-start>=frames)return null;
      const oldFrame=start-1;
      return {t:(f-start+1)/frames,oldFrame,old:previous.paint.state(oldFrame)};
    };
    const motion=(raw,transition)=>{
      if(!transition||continuing||stays)return raw;
      const t=transition.t;
      return raw.map(actor=>{
        const before=transition.old.find(item=>item.id===actor.id);
        if(!before)return {...actor,alpha:smoothstep((t-.43)/.57),reveal:true};
        if(t>=1)return actor;
        const from=acting.move(b,before.actor,(before.x-actor.x)/actor.unit/Math.sin(yaw*Math.PI/180));
        const blend=acting.bridge(b,from,actor.actor,t,'Continuação',{preserveHands:true});
        return {...actor,actor:blend};
      });
    };
    const drawBench=(stage,defs,spec,alpha=1)=>{
      if(!spec || alpha<=0)return;
      const layer=node('g',{'data-apoio-persistente':'banco',opacity:alpha},stage);
      const seat=bench(layer,defs,bible,{...spec,floor,height:scale*6,colors});
      seat.base.setAttribute('transform',`translate(0 ${floor-1.48*scale-seat.top})`);
    };
    const drawActor=(stage,defs,entry,i,ink,frame)=>{
      const {actor,x:origin,unit,id,alpha=1,yaw:angle=yaw,reveal=false}=entry;
      const layer=node('g',{'data-elemento':'figura-'+i,'data-identidade':id,opacity:alpha},stage);
      if(reveal&&alpha>0&&alpha<1){
        // A borda do cenário descobre o elenco novo enquanto o pé fica plantado.
        const direction=Math.sign(origin-x)||1;
        const edge=origin+direction*unit*(2.55-5.10*alpha);
        const key='revelar-'+i;
        const gradient=node('linearGradient',{id:key+'-luz',gradientUnits:'userSpaceOnUse',
          x1:edge-direction*unit*.55,x2:edge+direction*unit*.55,y1:0,y2:0},defs);
        node('stop',{offset:0,'stop-color':'#000'},gradient);
        node('stop',{offset:1,'stop-color':'#fff'},gradient);
        const mask=node('mask',{id:key,maskUnits:'userSpaceOnUse',x:0,y:0,width,height},defs);
        rectangle(mask,0,0,width,height,'url(#'+key+'-luz)');
        layer.setAttribute('mask','url(#'+key+')');
      }
      const shape=rig.draw(layer,actor,b,{yaw:angle,color:ink,exporting:true,
        transform:`translate(${origin} ${floor}) scale(${unit})`});
      painter.shapeLayer(defs,shape,frame,i===0);
    };
    const paint=(stage,defs,t,_primary,next,{propsOnly=false,omitObject=null}={})=>{
      const f=propsOnly?Math.round(scene.fim*30)-1:Math.round(t*30);
      const elapsed=Math.max(0,f/30-scene.inicio);
      let screen=stage;
      const tempo=fx.sensivel?.68:1;
      const phase=t*tempo;
      stage=cameraLayer(stage,{x:.50+.010*Math.sin(phase*2.2),y:.50+.006*Math.sin(phase*3.1),
        zoom:(intentional?.97:alternate?.94:1)+.012*Math.sin(phase*1.4)});
      const physical=stage;
      const preparing=!propsOnly&&next?.entrada_continua?.preparo_anterior&&next.paint.continuaEm(f);
      const transition=propsOnly?null:transitionAt(f);
      const drawing=preparing||motion(state(f),transition);
      const present=action?.presenca&&f>action.inicio&&f<action.fim-1;
      const handEntry=present?smoothstep((f-action.inicio)/Math.max(1,action.pouso-action.inicio)):0;
      const handLeave=present?smoothstep((f-action.presenca.sustenta_ate)/(action.fim-1-action.presenca.sustenta_ate)):0;
      const handLight=handEntry*(1-handLeave);
      const wristX=x+facing*scale*(1.91+.32*(1-handEntry)+.22*handLeave);
      const wristY=floor-scale*(6.20+1.32*(1-handEntry)+.58*handLeave);
      const actors=drawing.map(entry=>entry.actor);
      const xAt=i=>drawing[i].x;
      const progress=action?smoothstep((f-action.inicio)/Math.max(1,action.fim-action.inicio)):0;
      const projected=(i,joint)=>{
        const [px,py]=rig.project(actors[i].joints[joint],drawing[i].yaw??yaw);
        const unit=drawing[i].unit;
        return [xAt(i)+px*unit,floor+py*unit];
      };
      if(!propsOnly){
        const blend=transition?smoothstep(transition.t):1;
        const focus=transition?transition.old[0].x+(x-transition.old[0].x)*blend:x;
        environment(stage,defs,bible,colors,{width,height,floor,focus,head:scale});
        const oldScenery=previous?.cenario_ilustrado;
        const newScenery=scene.cenario_ilustrado;
        const changesScenery=transition&&oldScenery?.tipo!==newScenery?.tipo;
        if(changesScenery&&oldScenery)
          scenery(node('g',{opacity:1-blend},stage),defs,oldScenery,transition.oldFrame,transition.old[0].x);
        if(newScenery)
          scenery(node('g',{opacity:changesScenery?blend:1},stage),defs,newScenery,f,x,stage);
        painter.illuminate(stage,defs,f,[focus,floor-scale*3.9]);
        const oldMood=previous?.atmosfera;
        const sameMood=mood&&oldMood?.tipo===mood.tipo;
        const currentStrength=mood?(sameMood?1:smoothstep((f-mood.pouso+1)/(mood.tipo==='partilha'?10:17))):0;
        const exitWithReceiver=oldMood?.tipo==='partilha'&&action?.tipo==='olhar_para'&&!paired;
        const oldStrength=transition&&!sameMood&&oldMood?
          1-smoothstep(transition.t/(exitWithReceiver?.52:1)):0;
        const chest=(cast,i)=>{
          const body=cast[i];
          const [u,v]=rig.project(body.actor.joints.toracica,body.yaw??yaw);
          return [body.x+u*body.unit,floor+v*body.unit];
        };
        const moodSpec=(cast,gift,scene,tag)=>{
          const [u,v]=chest(cast,0);
          const usable=gift&&cast.length>Math.max(gift.from,gift.to);
          return {tag,x:u,y:v,floor,head:scale,
            windowSide:scene.cenario_ilustrado?.tipo==='janela'?cast[0].x>width*.49:null,
            gift:usable?{from:chest(cast,gift.from),to:chest(cast,gift.to),
              progress:smoothstep((f-gift.quadro+1)/10)}:null};
        };
        if(oldStrength>0)
          scenery.atmosfera(stage,defs,oldMood,f,oldStrength,
            moodSpec(transition.old,previous.paint.partilha,previous,scene.id+'-anterior'));
        if(currentStrength>0)
          scenery.atmosfera(stage,defs,mood,f,currentStrength,moodSpec(drawing,sharing,scene,scene.id+'-atual'));
        if(present){
          const beam=node('g',{'data-holofote-presenca':'sim',opacity:handLight},stage);
          const warm=colorMix(colors.osso,colors.acento,.22);
          const glow=node('radialGradient',{id:'presenca-holofote',cx:.53,cy:.54,r:.53},defs);
          for(const [offset,level] of [[0,.30],[.57,.15],[1,0]])
            node('stop',{offset,'stop-color':warm,'stop-opacity':level},glow);
          const fall=node('linearGradient',{id:'presenca-feixe',x1:0,y1:0,x2:.18,y2:1},defs);
          for(const [offset,level] of [[0,0],[.26,.13],[.72,.09],[1,0]])
            node('stop',{offset,'stop-color':warm,'stop-opacity':level},fall);
          const softness=node('filter',{id:'presenca-suave',x:'-15%',width:'130%',y:'-12%',height:'124%'},defs);
          node('feGaussianBlur',{stdDeviation:18},softness);
          const source=wristX+facing*scale*.98, center=(x+wristX)/2;
          node('path',{d:`M ${source-scale*.18} ${height*.155} H ${source+scale*.18}
            L ${center+scale*2.55} ${floor-4} Q ${center} ${floor+scale*.16} ${center-scale*2.05} ${floor-4} Z`,
            fill:'url(#presenca-feixe)',filter:'url(#presenca-suave)'},beam);
          node('ellipse',{cx:(x+wristX*2)/3,cy:(wristY+floor)/2-scale*1.45,rx:scale*2.8,ry:scale*3.16,
            fill:'url(#presenca-holofote)'},beam);
          node('ellipse',{cx:center,cy:floor-2,rx:scale*2.45,ry:scale*.34,
            fill:'url(#presenca-holofote)'},beam);
        }
        for(const [i,entry] of drawing.entries()){
          const {actor,unit,alpha=1,yaw:angle=yaw}=entry;
          const shadow=node('g',{opacity:alpha},stage);
          for(const side of ['E','D']){
            const support=actor.contacts.find(c=>c.id==='pe'+side);
            const foot=support?.real??actor.joints['planta'+side];
            const [local]=rig.project(foot,angle);
            painter.contact(shadow,defs,i+'-'+side,xAt(i)+unit*local,floor+6,unit,
              Math.min(1,Math.max(0,-foot[1]*3)));
          }
        }
        const ground=line(stage,width*.09,floor,width*.81,floor,colors.linha,2);
        ground.dataset.parte='piso';
        ground.dataset.elemento='piso';
        const newBench=benchInfo();
        const oldBench=transition?previous.paint.benchInfo():null;
        const sameBench=oldBench&&newBench&&oldBench.x===newBench.x&&oldBench.comprimento===newBench.comprimento;
        if(transition&&!sameBench)drawBench(stage,defs,oldBench,1-blend);
        drawBench(stage,defs,newBench,transition&&!sameBench?blend:1);
        const actorColor=action?.tipo==='virar'?
          colorMix(colors.osso,colors.acento,smoothstep((f-action.pouso+4)/8)):colors.acento;
        const gray=(mood?.tipo==='chuva'?currentStrength:0)+(oldMood?.tipo==='chuva'?oldStrength:0);
        const warm=mood&&['aura','claridade','partilha'].includes(mood.tipo)?currentStrength:0;
        const paintMood=color=>colorMix(colorMix(color,'#abb7ba',gray*.74),'#ead59b',warm*.12);
        const inks=[paintMood(actorColor),paintMood(colors.osso)];
        if(transition){
          for(const old of transition.old.filter(item=>!drawing.some(current=>current.id===item.id))){
            const alpha=1-smoothstep(transition.t/.52);
            if(alpha>0)drawActor(stage,defs,{...old,alpha,reveal:true},'saida-'+old.id,colors.osso,f);
          }
        }
        drawing.forEach((entry,i)=>drawActor(stage,defs,entry,i,inks[i],f));
        window.pictogramaQuadro={frame:f,actors,yaw,scale,floor,inks,origins:actors.map((_,i)=>xAt(i)),
          projections:drawing.map(({unit,yaw:angle=yaw,id})=>({unit,angle,id})),
          gesto:intentional?action?.gesto:null,transfer,transferFrame,partilha:sharing,transicao:preparing?0:(transition?.t??null)};
        if(transition && !continuing){
          const oldAlpha=1-smoothstep(transition.t/(previous.paint.posse?.kind==='coracao'?.52:.42));
          if(oldAlpha>0){
            const oldProps=node('g',{opacity:oldAlpha,'data-transicao':'aderecos'},screen);
            previous.paint(oldProps,defs,t,false,scene,{propsOnly:true,omitObject:continuesBook?'livro':inherited?.kind});
          }
          const alpha=smoothstep((transition.t-.36)/.64);
          stage=node('g',{opacity:alpha},stage);
          screen=node('g',{opacity:alpha},screen);
        }
      }
      if(inherited&&inherited.kind!==omitObject&&actors[inherited.owner]){
        const {owner,kind}=inherited;
        const [hx,hy]=projected(owner,'maoD');
        const held=node('g',{'data-objeto-cena':kind+'-0','data-ator':owner,'data-relacao':'segurado'},physical);
        mark(held,kind,hx,hy-scale*.46,scale*.55,t);
      }
      if((readsBook||continuesBook)&&omitObject!=='livro'){
        const {open,turn}=bookMotion(f);
        const model=bookGeometry(open,turn,facing);
        const palms=['E','D'].map(side=>projected(0,'mao'+side));
        const bookPoint=point=>{
          const [u,v]=rig.project(point,drawing[0].yaw??yaw);
          return [xAt(0)+u*scale,floor+v*scale];
        };
        const ideals=model.grips.map(bookPoint);
        const delta=palms[0].map((value,i)=>
          ((value-ideals[0][i])+(palms[1][i]-ideals[1][i]))/2);
        const project=point=>bookPoint(point).map((value,i)=>value+delta[i]);
        const layer=node('g',{'data-objeto-cena':'livro-0','data-ator':0,'data-relacao':'segurado',
          'data-livro-na-mao':'sim','data-virada':turn},continuesBook?physical:stage);
        paintHeldBook(layer,model,project);
        for(const [i,[hx,hy]] of palms.entries()){
          const [gx,gy]=project(model.grips[i]);
          node('circle',{'data-apoio-livro':i?'D':'E',cx:gx,cy:gy,r:1,fill:'none'},layer);
          node('ellipse',{'data-palma-livro':i?'D':'E',cx:hx,cy:hy,rx:scale*.063,ry:scale*.044,
            fill:colors.acento},layer);
        }
      }
      if(present){
        const hand=node('g',{'data-figura':'mao-aberta','data-mao-presente':'sim',opacity:handLight,transform:
          `translate(${wristX} ${wristY}) rotate(${36*facing}) scale(${scale*.73})`},physical);
        const fade=node('linearGradient',{id:'mao-presente-luz',gradientUnits:'userSpaceOnUse',
          x1:0,y1:-2.7,x2:0,y2:-.36},defs);
        node('stop',{offset:0,'stop-color':colors.osso,'stop-opacity':0},fade);
        node('stop',{offset:1,'stop-color':colors.osso},fade);
        node('path',{'data-contorno-presenca':'sim',fill:'url(#mao-presente-luz)',d:
          'M -.42 -2.7 C -.37 -1.9 -.30 -1.32 -.33 -.68 C -.34 -.41 -.49 -.31 -.59 -.08 L -.77 .32 Q -.82 .43 -.74 .47 Q -.65 .51 -.58 .41 L -.42 .24 Q -.34 .17 -.31 .25 L -.33 1.02 Q -.34 1.17 -.23 1.19 Q -.13 1.20 -.12 1.06 L -.08 .63 L -.06 1.25 Q -.05 1.40 .05 1.40 Q .16 1.40 .17 1.25 L .20 .63 L .23 1.13 Q .24 1.27 .34 1.25 Q .43 1.23 .42 1.10 L .40 .57 L .46 .87 Q .50 1.00 .58 .96 Q .66 .92 .63 .78 L .54 .34 Q .51 .12 .43 -.15 Q .36 -.39 .33 -.73 C .29 -1.34 .38 -2.00 .42 -2.7 Z'},hand);
        node('path',{fill:colorMix(colors.fundo,colors.osso,.84),d:
          'M -.35 .14 Q -.25 -.19 -.02 -.07 Q .12 .01 .19 .20 Q .04 .08 -.10 .18 Q -.25 .31 -.35 .14 Z'},hand);
      }else if(action?.tipo==='mao_presente'&&!action.presenca){
        const entry=smoothstep((f-action.inicio)/Math.max(1,action.pouso-action.inicio));
        const hand=node('g',{'data-figura':'mao-aberta',transform:
          `translate(${visual+width*.025} ${height*(.045+.230*entry)}) scale(${scale*.87})`},stage);
        node('path',{fill:colors.osso,d:'M -.24 -1.14 L .22 -1.14 L .27 -.60 L .53 -.22 Q .65 .02 .50 .08 Q .37 .13 .27 -.02 L .17 -.14 L .15 .61 Q .12 .83 -.04 .78 L -.10 .25 L -.14 .73 Q -.25 .90 -.35 .75 L -.36 .22 L -.43 .65 Q -.57 .76 -.63 .57 L -.57 .09 L -.66 .37 Q -.80 .47 -.83 .29 L -.72 -.16 Q -.61 -.51 -.34 -.63 Z'},hand);
      }
      if(action?.figura==='idoso'){
        const [hx,hy]=projected(1,'maoD');
        node('path',{fill:'none',stroke:colors.osso,'stroke-width':scale*.062,
          d:`M ${hx+scale*.28} ${hy} q ${-scale*.20} ${-scale*.12} ${-scale*.32} ${scale*.08} L ${hx} ${floor}`},stage);
      }
      if(action?.figura==='animal'){
        const animal=node('g',{'data-figura':'animal',transform:`translate(${visual} ${floor}) scale(${scale})`},stage);
        node('path',{fill:colors.osso,d:'M -.65 -.33 Q -.35 -.68 .17 -.53 L .41 -.78 L .66 -.74 L .77 -.56 L .51 -.44 L .42 0 H .32 L .29 -.31 H -.24 L -.36 0 H -.48 L -.45 -.32 L -.68 -.23 L -.79 -.37 Z'},animal);
      }
      if(scene.grafico){
        visualMotion(screen,scene.grafico,f);
      }else if(authored&&scene.padrao==='comparacao'&&scene.rotulos.length===2){
        const y=height*.418;
        const sway=(progress-.5)*scale*.12;
        label(screen,scene.rotulos[0],width*.215,y+sway,width*.26,height*.042,colors.osso);
        label(screen,scene.rotulos[1],width*.705,y-sway,width*.26,height*.042,colors.acento);
      }else if(scene.titulo){
        const heading=node('g',{'data-elemento':'titulo'},screen);
        const isDate=scene.padrao==='numero_data';
        const growth=isDate&&authored?1+.13*Math.sin(Math.PI*smoothstep((f-(action?.pouso??f))/13)):1;
        label(heading,scene.titulo,width*(authored?Math.min(.69,propX):.44),titleY,width*.72,height*.036*growth,colors.osso);
      }
      if(authored&&action){
        if(scene.virada){
          typography(screen,f,{words:scene.virada,corte:Math.round(scene.fim*30),floor,
            cues:{conceito:{frame:action.inicio},virada:{frame:action.pouso}},
            marks:{centro_tipo:width*.45,linha_conceito:height*.268,
              largura_palavra:width*.35,tamanho_palavra:height*.057}});
        }
        const relation=action.relacao??({ler:'segurado',receber:'segurado',entregar:'entregue',
          carregar:'carregado',romper:'segurado',apontar:'olhado',esperar:'olhado',
          olhar_para:'olhado',andar_ate:'apoiado'}[action.tipo]??'olhado');
        const props=[action.objeto,action.acessorio].filter(kind=>
          kind&&kind!==omitObject&&!(kind==='livro'&&(readsBook||continuesBook))&&!(scene.grafico?.tipo==='relogio'&&kind==='relogio'));
        const owner=transfer?(action.tipo==='entregar'||continuing?Number(f>=transferFrame):Number(f<transferFrame)):
          action.tipo==='entregar'&&actors.length>1&&f>=action.pouso?1:0;
        const grip=actors[owner].contacts.find(c=>c.tipo==='par');
        const contact=grip&&rig.project(grip.real,yaw);
        const hand=contact?[xAt(owner)+contact[0]*scale,floor+contact[1]*scale]:projected(owner,'maoD');
        const head=projected(0,'cabeca');
        const positions=props.map((kind,i)=>{
          const physical=['segurado','entregue','carregado'].includes(relation);
          let point=physical?[hand[0],hand[1]-scale*(transfer?.46:action.tipo==='entregar'?.68:.42)]:[visual,height*.48];
          if(kind==='livro'&&action.tipo==='ler'){
            const otherHand=projected(owner,'maoE');
            point=[(hand[0]+otherHand[0])/2,(hand[1]+otherHand[1])/2-scale*.34];
          }
          if(kind==='data')point=[width*.70,height*.38];
          if(action.tipo==='romper'){
            const sign=i?1:-1;
            const separate=f>=action.pouso?smoothstep((f-action.pouso)/12):0;
            const palm=projected(owner,i?'maoD':'maoE');
            point=[Math.min(width*.77,Math.max(width*.16,x+sign*scale*(1.68+separate*.35))),
              palm[1]+scale*.35+sign*separate*scale*.16];
          }
          if(kind==='linha'&&action.tipo!=='romper')point=[width*.48,floor-scale*.19];
          if(kind==='relogio')point=[head[0]+outward*scale*1.70,head[1]+scale*.24];
          return point;
        });
        if(action.tipo==='romper'&&positions.length===2){
          const [a,z]=positions, y=(a[1]+z[1])/2;
          const mid=(a[0]+z[0])/2;
          if(f<action.pouso)line(stage,a[0],a[1],z[0],z[1],colors.osso,6);
          else {
            line(stage,a[0],a[1],mid-scale*.24,y+scale*.12,colors.osso,6);
            line(stage,mid+scale*.24,y-scale*.16,z[0],z[1],colors.osso,6);
          }
        }
        props.forEach((kind,i)=>{
          const [u,v]=positions[i];
          const size=scale*(transfer&&kind==='coracao'?.55:.77);
          const layer=node('g',{'data-objeto-cena':kind+'-'+i,'data-ator':owner,'data-relacao':relation},stage);
          if(kind==='linha'&&action.tipo==='romper'){
            node('path',{d:`M ${u-size} ${v+size*.52} L ${u-size*.56} ${v-size*.52} H ${u+size*.56} L ${u+size} ${v+size*.52} Z`,fill:colors.osso},layer);
          }else if(kind==='linha'){
            line(layer,width*.14,v,width*.77,v,colors.acento,6);
            for(let j=0;j<4;j++){
              const at=width*(.18+j*.18);
              line(layer,at,v,at,v-scale*.41,colors.osso,4);
            }
            layer.dataset.abstrato='sim';
          }else{
            mark(layer,kind,u,v,size,t);
          }
          if(!scene.grafico&&scene.rotulos[i]&&(kind!=='data'||f>=action.pouso)){
            const labelSize=kind==='data'?.022+.021*smoothstep((f-action.pouso)/14):.021;
            const caption=label(layer,scene.rotulos[i],u,Math.min(height*.60,v+size+height*.033),
              width*.27,height*labelSize,i?colors.osso:colors.acento);
            caption.dataset.rotuloCena='sim';
          }
        });
        return;
      }
      if(['comparacao','objecao'].includes(scene.padrao)){
        const mid=(x+visual)/2;
        line(stage,mid,height*.28,mid,height*.56,colors.linha,2)
          .setAttribute('stroke-dasharray','6 10');
      }
      const glyphSwap=scene.padrao==='transformacao'&&scene.rotulos.length===2&&
        scene.rotulos.every(label=>Array.from(label).length===1);
      if(glyphSwap){
        const flip=smoothstep(elapsed/.62);
        const y=height*.42,scaleX=Math.max(.03,Math.abs(Math.cos(Math.PI*flip)));
        const turn=node('g',{'data-elemento':'letra-em-virada',
          transform:`translate(${visual} ${y}) scale(${scaleX} 1)`},stage);
        label(turn,scene.rotulos[flip>=.5?1:0],0,0,width*.28,height*.14,
          flip>=.5?colors.acento:colors.osso);
      }
      const timeline=scene.padrao==='numero_data'||scene.simbolos[0]==='linha'&&
        ['enumeracao','objecao'].includes(scene.padrao);
      if(timeline){
        const axis=node('g',{'data-elemento':'linha-do-tempo'},stage);
        const base=height*.47,left=width*.10,right=width*.45;
        const grow=smoothstep(elapsed/.55);
        line(axis,left,base,left+(right-left)*grow,base,colors.acento,7);
        const fractions=[.08,.37,.66,.95];
        fractions.forEach((fraction,i)=>{
          if(grow<fraction)return;
          const markX=left+(right-left)*fraction;
          const size=11+1.2*Math.sin(t*3+i);
          line(axis,markX,base-size*2,markX,base+size*2,colors.osso,4);
          circle(axis,markX,base,size,colors.acento);
        });
        if(scene.padrao==='numero_data')mark(axis,'data',right,base-height*.066,height*.027,t);
      }
      const count=glyphSwap||timeline?0:Math.max(scene.rotulos.length,scene.simbolos.length);
      const radius=height*(scene.padrao==='numero_data'?.030:.023);
      for(let i=0;i<count;i++){
        const y=height*(count===1?.412:.346+i*.107);
        const sway=(fx.sensivel?4:8)*Math.sin(t*4+i);
        const opacity=smoothstep((elapsed-i*.15)/.29);
        const staged=actors.length>1&&scene.simbolos.every(kind=>kind==='circulo');
        if(staged&&!scene.rotulos[i])continue;
        const layer=node('g',{opacity,'data-elemento':'ideia-'+i},stage);
        if(scene.simbolos[i]&&!staged)mark(layer,scene.simbolos[i],visual,y+sway,radius,t);
        if(scene.rotulos[i])label(layer,scene.rotulos[i],visual,y+radius+height*.026,width*.31,
          height*(scene.padrao==='numero_data'?.037:.022),i===0?colors.acento:colors.osso);
      }
    };
    paint.events=action?[{scene:scene.id,element:action.ator,action:action.tipo,group:action.tipo,
      word:action.palavra,emphasis:true,start:action.inicio/30,end:action.fim/30,
      landing:action.pouso/30,target:action.pouso/30,minimum:8}]:[];
    if(scene.grafico){
      const g=scene.grafico;
      paint.events.push({scene:scene.id,element:'grafico',action:g.tipo,group:'grafico',
        word:g.palavra,emphasis:true,start:g.inicio/30,end:g.fim/30,
        landing:g.pouso/30,target:g.pouso/30,minimum:8});
    }
    if(Number.isInteger(action?.segunda_palavra)){
      paint.events.push({scene:scene.id,element:action.ator,action:'recusar',
        group:action.tipo,word:action.segunda_palavra,emphasis:true,
        start:action.segundo_pouso/30,end:action.fim/30,
        landing:action.segundo_pouso/30,target:action.segundo_pouso/30,minimum:8});
    }
    paint.state=state;
    paint.partilha=sharing;
    paint.posse=inherited??(transfer?{kind:action.objeto,owner:action.tipo==='entregar'||continuing?1:0}:null);
    paint.continuaEm=f=>{
      const prep=transitionAt(f);
      return prep&&motion(state(f),prep);
    };
    paint.benchInfo=benchInfo;
    return paint;
  };
});
