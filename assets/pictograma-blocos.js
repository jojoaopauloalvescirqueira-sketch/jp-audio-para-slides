/* Blocos anatômicos, gráficos e de câmera do Pictograma. */
window.PictogramaBlocos=api=>{
  const {data,landscape,colors,node,set,text,rectangle,line,circle,smoothstep,mix,colorMix}=api;
  const {bible,coreografia}=data;
  const {cues,corte,comparacao,encenacao}=coreografia;
  const {texto:words,marcas:marks}=encenacao;
  const {virada,atuacao}=coreografia.parametros;
  const typography=window.PictogramaVirada(api);
  const effects=data.efeitos_pictograma&&window.PictogramaEfeitos(api,data.efeitos_pictograma,bible);
  const {anatomy,blend}=PictogramaFigura;
  const {environment,bench}=PictogramaPalco;
  const {altura:h,chao:floor}=coreografia.enquadramento;
  const a=anatomy(bible,h);
  const ease=(f,s,e)=>smoothstep((f-s)/(e-s));
  const wave=(f,s,e)=>Math.sin(Math.PI*ease(f,s,e));
  const group=(p,id,attrs={})=>node('g',{'data-elemento':id,...attrs},p);
  const frame=name=>cues[name].frame;
  const seatY=floor-bible.objetos.banco.altura_h[0]*h;
  const releaseFrame=frame('fazer')+13, landingFrame=frame('fazer')+24;
  const dividerX=marks.divisoria;

  function label(p,id,value,x,y,available,size,fill,opacity=1){
    if(opacity<=0)return;
    const g=group(p,id,{opacity});
    const el=text(g,value,x,y,available,size,{fill});
    el.classList.add('picto-display');
    el.dataset.titulo='sim';
    return el;
  }
  function shape(parent,p,q,color,width,attrs={}){
    return set(line(parent,...p,...q,color,width),attrs);
  }
  function arrow(g,from,to,progress,ink){
    if(progress<=.02)return;
    const end=blend(from,to,progress);
    const d=[end[0]-from[0],end[1]-from[1]], len=Math.hypot(...d);
    const width=Math.max(9,a.head*bible.objetos.seta_traco_min_cabeca);
    const tip=a.head*bible.objetos.seta_ponta_min_cabeca;
    if(len<tip+4)return;
    const [dx,dy]=d.map(x=>x/len);
    const base=[end[0]-tip*dx,end[1]-tip*dy];
    const half=width*1.38;
    const arrow=group(g,g.dataset.elemento+'-'+g.childNodes.length,{'data-objeto':'seta','data-traco':width,'data-ponta':tip});
    shape(arrow,from,base,ink,width);
    node('path',{d:`M${end.join(' ')} L${base[0]-dy*half} ${base[1]+dx*half}
      L${base[0]+dy*half} ${base[1]-dx*half} Z`,fill:ink},arrow);
  }

  function heartTrajectory(f,giver,palms){
    const travel=ease(f,releaseFrame,landingFrame);
    const target=effects?[palms[0]-a.head*.26,palms[1]-a.head*.49]:palms;
    const position=blend(giver,target,travel);
    position[1]-=atuacao.arco*Math.sin(Math.PI*travel);
    return position;
  }
  function symbols(stage,f,states,first,second){
    const wait=ease(f,frame('esperar')-2,frame('esperar')+12)*(1-ease(f,frame('levantar')-44,frame('levantar')-31));
    if(wait>.02){
      const c=[marks.relogio_x,marks.relogio_y], r=a.head*.52;
      const clock=group(stage,'relogio',{opacity:wait,'data-objeto':'simbolo'});
      node('circle',{cx:c[0],cy:c[1],r,fill:colors.fundo,stroke:colors.osso,'stroke-width':8},clock);
      const angle=(f-frame('esperar'))*.12;
      shape(clock,c,[c[0]+Math.cos(angle)*r*.73,c[1]+Math.sin(angle)*r*.73],colors.acento,8);
      shape(clock,c,[c[0]-r*.28,c[1]-r*.20],colors.osso,7);
      const dots=group(stage,'espera',{opacity:wait,'data-objeto':'simbolo'});
      for(let i=0;i<3;i++){
        const p=.7+.3*Math.sin(f*.22-i*.78);
        circle(dots,atuacao.pontos.x+atuacao.pontos.passo*i,atuacao.pontos.y-7*p,11+6*p,colors.osso);
      }
    }
    const cue=frame('receber'), outgoing=frame('fazer');
    const opacity=ease(f,cue-2,cue+9);
    if(opacity<=0 && f<cue-13)return;
    const divider=group(stage,'divisoria',{opacity:.64*states.compare*opacity});
    shape(divider,[dividerX,atuacao.divisoria[0]],[dividerX,atuacao.divisoria[1]],colors.linha,2,{'stroke-dasharray':'6 10','pathLength':atuacao.divisoria[1]-atuacao.divisoria[0]});
    label(stage,'receber',words.direita,...atuacao.receber,colors.osso,opacity);
    label(stage,'fazer',words.esquerda,...atuacao.oferecer,colors.acento,opacity);
    if(f>=cue-13 && (effects||f<outgoing+3)){
      const u=ease(f,cue-13,cue);
      const palms=blend(second.hands[1],second.hands[0],.5);
      const owner=blend([palms[0]+atuacao.chegada[0],palms[1]+atuacao.chegada[1]],palms,u);
      const side=a.head*.88;
      const heart=group(stage,'recepcao',{'data-objeto':'simbolo','data-chegada':f>=cue?'pouso':'trajeto',
        opacity:ease(f,cue-13,cue-7)*(effects?1:1-ease(f,outgoing-8,outgoing+3)),
        ...(effects?{'data-objeto-id':'coracao-recebido'}:{})});
      drawHeart(heart,owner,owner[1]-side*.88,side,effects?colors.osso:colors.acento);
    }
    if(f<outgoing+(effects?-1:4))return;
      const launch=first.hands[1];
      const palms=blend(second.hands[0],second.hands[1],.5);
      const landed=f>=landingFrame;
      const flying=f>=releaseFrame&&!landed;
      const owner=heartTrajectory(f,launch,palms);
      const side=a.head*(effects?.73:.88);
      const top=owner[1]-side*.88;
      const stream=group(stage,'sai',{opacity:(1-ease(f,releaseFrame+2,landingFrame+5))});
      const from=[launch[0]+atuacao.seta[0],launch[1]+atuacao.seta[1]], to=[dividerX+atuacao.seta[2],launch[1]+atuacao.seta[3]];
      if(from[0]<to[0]-5)arrow(stream,from,to,ease(f,outgoing+4,releaseFrame),colors.acento);
      const object=group(stage,'oferta',{'data-entrega':'sim','data-modo-entrega':'trajeto',
        'data-dono':landed?'outro':flying?'trajeto':'agente',
        'data-objeto':'simbolo',opacity:effects?ease(f,outgoing-1,outgoing+6):ease(f,outgoing+4,outgoing+10),
        ...(effects?{'data-objeto-id':'coracao-oferecido'}:{})});
      drawHeart(object,owner,top,side);
  }

  function drawHeart(object,owner,top,side,ink=colors.acento){
    node('path',{transform:`translate(${owner[0]} ${top}) scale(${side})`,
      d:'M 0 .88 C -.12 .78 -.5 .55 -.5 .28 C -.5 -.02 -.15 -.08 0 .14 C .15 -.08 .5 -.02 .5 .28 C .5 .55 .12 .78 0 .88 Z',
      fill:ink,stroke:colors.fundo,'stroke-width':.033},object);
  }

  const anatomical=window.PictogramaAcoes.sequencia(data.rig_anatomico,coreografia.sequencia);
  const exporting=new URLSearchParams(location.search).has('render');
  let showBones=false;
  if(anatomical&&!exporting){
    const button=document.querySelector('#ver-diagnostico');
    if(button)button.onclick=()=>{
      showBones=!showBones;
      button.setAttribute('aria-pressed',String(showBones));
      button.textContent=showBones?'Ocultar diagnóstico':'Mostrar diagnóstico';
      document.querySelectorAll('#palco [data-diagnostico]').forEach(el=>
        el.setAttribute('visibility',showBones?'visible':'hidden'));
    };
  }

  function anatomicalScene(shot,defs,f){
    const actors=anatomical.at(f);
    const scale=h/6, x0=marks.origem_ator, yaw=marks.angulo;
    const projected=v=>{
      const [x,y]=window.PictogramaRig.project(v,yaw);
      return [x0+x*scale,floor+y*scale];
    };
    environment(shot,defs,bible,colors,{width:atuacao.palco[0],height:atuacao.palco[1],floor,focus:marks.foco,head:a.head});
    if(effects?.enabled()){
      const main=actors[0];
      const center=projected(main.joints.toracica);
      let hand,trail;
      if(actors.length===2){
        const giver=projected(main.joints.maoD);
        const receiver=blend(projected(actors[1].joints.maoE),projected(actors[1].joints.maoD),.5);
        hand=heartTrajectory(f,giver,receiver);
        hand[1]-=a.head*.30;
        if(f>releaseFrame && f<=landingFrame+2){
          trail=heartTrajectory(f-4,giver,receiver);
          trail[1]-=a.head*.30;
        }
      }
      effects.illuminate(shot,defs,f,center,hand,trail);
      for(const [index,actor] of actors.entries()){
        for(const side of ['E','D']){
          const planted=actor.contacts.find(c=>c.id==='pe'+side);
          const foot=planted?.real??actor.joints['planta'+side];
          const [x]=projected(foot);
          effects.contact(shot,defs,index+'-'+side,x,floor+6,scale,
            Math.min(1,Math.max(0,-foot[1]*3)));
        }
      }
      const opacity=ease(f,corte+16,corte+24)*(1-ease(f,frame('levantar')-12,frame('levantar')));
      effects.contact(shot,defs, 'banco',atuacao.sombras_banco[0],floor+6,scale,0,opacity);
      effects.contact(shot,defs, 'banco-2',atuacao.sombras_banco[1],floor+6,scale,0,opacity);
    }
    const floorLayer=group(shot,'chao');
    const {a:zoom,e:shift}=shot.getScreenCTM();
    const floorLeft=Math.max(atuacao.chao[0],(atuacao.chao[1]-shift)/zoom), floorRight=Math.min(atuacao.chao[2],(atuacao.chao[3]-shift)/zoom);
    shape(floorLayer,[floorLeft,floor],[floorRight,floor],colors.linha,2,{'data-parte':'piso'});
    const seat=bench(shot,defs,bible,{x:marks.banco_x,floor,height:h,colors,comprimento:marks.banco_comprimento,pernas:atuacao.pernas_banco});
    // Align the painted seat to the approved pelvis support geometry.
    set(seat.base,{opacity:ease(f,corte+16,corte+24)*(1-ease(f,frame('levantar')-12,frame('levantar')))});
    const seats=seat.base.querySelector('[data-parte=assento]');
    if(seats)set(seat.base,{transform:`translate(0 ${floor-1.48*scale-seatY})`});
    effects?.dim(shot,f);
    const inks=[colorMix(colors.osso,colors.acento,ease(f,frame('levantar')-12,frame('levantar'))),colors.osso];
    const painted=actors.map((actor,index)=>{
      const id=atuacao.papeis[index];
      const layer=group(shot,id,{transform:`translate(${x0} ${floor}) scale(${scale})`});
      const actorSvg=window.PictogramaRig.draw(layer,actor,data.rig_anatomico,{
        yaw,color:inks[index],diagnostic:showBones,exporting
      });
      effects?.shapeLayer(defs,actorSvg,f,index===0);
      const j=actor.joints;
      const hands=['E','D'].map(side=>projected(j['mao'+side]));
      const probe=(name,p)=>node('circle',{cx:p[0],cy:p[1],r:0,'data-ponto-anatomico':name},layer);
      for(const name of ['pelve','toracica','cabeca','maoE','maoD','cotoveloE','cotoveloD','punhoE','punhoD'])
        probe(name,projected(j[name]).map((v,i)=>(v-[x0,floor][i])/scale));
      return {hands,actorSvg};
    });
    const wordIn=ease(f,corte+29,corte+42)*(1-ease(f,frame('levantar')-44,frame('levantar')-33));
    const wordOut=ease(f,frame('levantar')-11,frame('levantar')+2)*(1-ease(f,comparacao-11,comparacao-1));
    label(shot,'esperar',words.espera,...atuacao.espera,colors.osso,wordIn);
    label(shot,'agir',words.acao,...atuacao.acao,colors.acento,wordOut);
    if(painted.length===2)symbols(shot,f,{compare:1},painted[0],painted[1]);
    else if(wordIn>.02)symbols(shot,f,{compare:0},painted[0],null);
    window.pictogramaQuadro={frame:Math.round(f),actors,yaw,scale,x0,floor,inks};
  }

  function paint(stage,defs,f){
    const camera=coreografia.camera;
    const zoomBase=landscape?camera.base_horizontal:1;
    const breathing=camera.respiracao.zoom*Math.sin(f*camera.respiracao.velocidade);
    const impulses=camera.impulsos.reduce((sum,{inicio,fim,delta})=>sum+delta*wave(f,inicio,fim),0);
    const {inicio,fim,delta}=camera.abertura;
    const zoom=zoomBase*(1+breathing+impulses+delta*ease(f,inicio,fim));
    const up=frame('levantar'), help=frame('ajudar');
    const room=ease(f,up-56,up-39)*(1-ease(f,help+20,help+37));
    const shift=2.4*Math.sin(f*.084)-42*room, dy=4*Math.sin(f*.058);
    const [x,y]=landscape?atuacao.centro_horizontal:atuacao.centro;
    const shot=node('g',{transform:`translate(${x+shift} ${y+dy}) scale(${zoom}) translate(${-atuacao.centro[0]} ${-atuacao.centro[1]})`,
      'data-zoom':zoom/zoomBase},stage);
    const block=coreografia.blocos.find(({de,ate})=>de<=f&&(ate===null||f<ate));
    const blocks={
      virada_tipografica(){
        window.pictogramaQuadro={frame:Math.round(f),actors:[]};
        environment(shot,defs,bible,colors,{width:atuacao.palco[0],height:atuacao.palco[1],floor:virada.chao,focus:virada.foco,head:a.head});
        typography(shot,f,{cues,corte,words,marks:{...marks,...virada},effects,floor});
      },
      atuacao_anatomica(){anatomicalScene(shot,defs,f);},
    };
    if(!block||!blocks[block.tipo])throw Error('Bloco de palco ausente ou inválido.');
    blocks[block.tipo]();

  }

  return scene=>{
    const render=(stage,defs,t)=>paint(stage,defs,t*30);
    render.events=Object.entries(cues).filter(([,cue])=>cue.scene===scene.id).map(([name,cue])=>({
      scene:scene.id,element:name,action:name,group:name,word:cue.word,emphasis:true,
      start:cue.start/30,end:cue.end/30,landing:cue.frame/30,target:cue.frame/30,minimum:cue.minimum
    }));
    const wait=cues.esperar;
    if(wait.scene===scene.id){
      for(const [element,action] of [['relogio','girar'],['espera','pulsar']]){
        render.events.push({scene:scene.id,element,action,group:'espera',word:wait.word,emphasis:false,
          start:(wait.frame-2)/30,end:(frame('levantar')-31)/30,landing:wait.frame/30,
          target:wait.frame/30,minimum:6});
      }
    }
    return render;
  };
};
