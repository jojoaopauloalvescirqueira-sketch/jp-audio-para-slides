/* Composição virada_banco_ajuda_v1. O relógio da fala vem do plano compilado. */
window.MotorCenas.registrarKit('pictograma-coreografia', api => {
  const {data, landscape, colors, node, set, text, rectangle, line, circle, smoothstep, mix, colorMix} = api;
  const {cues, corte, comparacao} = data.coreografia;
  const floor = 1250, seat = 979;
  const frame = name => cues[name].frame;
  const ease = (f, start, end) => smoothstep((f - start) / (end - start));
  const interp = (a, b, u) => a.map((x, i) => mix(x, b[i], u));
  const point = (x, y) => [x, y];
  const group = (p, name, attributes = {}) => node('g', {'data-elemento':name, ...attributes}, p);
  const stroke = (g, p, q, color, width, attrs = {}) =>
    set(line(g, ...p, ...q, color, width), attrs);
  const limb = (g, joints, color, width, part) => node('path', {
    d: 'M ' + joints.map(p => p.join(' ')).join(' L '), fill:'none', stroke:color,
    'stroke-width':width, 'stroke-linecap':'round', 'stroke-linejoin':'round', 'data-parte':part
  }, g);

  function title(parent, f) {
    const cue = cues.virada;
    const intro = .30*ease(f,-2,12)+.70*ease(f, cues.conceito.frame - 5, cues.conceito.end);
    const turn = ease(f, cue.start, cue.end);
    const rotate = ease(f, cue.frame - 9, cue.frame + 6);
    const depart = ease(f, corte - 13, corte);
    const field = node('g', {transform:`translate(0 ${-18*depart})`, opacity:1-depart,
      'data-virada':turn > 0 && turn < 1 ? 'sim' : 'nao'}, parent);
    const negative = ease(f, frame('negacao') - 3, frame('negacao') + 1);
    const pulse = Math.sin(Math.PI * ease(f, frame('negacao'), cues.negacao.end)) * .16;
    const release = ease(f, cue.frame + 6, cue.end);
    const block = group(field, 'negacao', {opacity:negative*(1-release), 'data-negacao':'sim'});
    set(block,{transform:`translate(480 662) scale(${1+pulse}) translate(-480 -662)`});
    const not = text(block,'NÃO',480,688,260,98,{fill:colors.osso});
    not.classList.add('picto-display');
    const strike = ease(f,cue.start,cue.frame-10);
    if (strike > 0) stroke(block, [388,657], [388+184*strike,657], colors.acento, 8, {'data-risco':'sim'});
    const word = group(field,'conceito',{opacity:intro});
    const base = text(word,'AM',342,927,290,226,{fill:colors.osso});
    base.classList.add('picto-display');
    const letter = group(field,'letra',{opacity:intro, 'data-letra':rotate>=.5?'A':'O'});
    const face = Math.max(.025,Math.abs(Math.cos(rotate*Math.PI)));
    set(letter,{transform:`translate(548 0) scale(${face} 1)`});
    const glyph = text(letter,rotate>=.5?'A':'O',0,927,168,226,{fill:rotate>=.5?colors.acento:colors.osso});
    glyph.classList.add('picto-display');
    text(word,'R',680,927,160,226,{fill:colors.osso}).classList.add('picto-display');
    const note = group(field,'classe',{opacity:intro*(.78+.22*turn)});
    text(note,rotate>=.5?'verbo':'substantivo',480,1023+13*Math.sin(rotate*Math.PI),500,46,
         {fill:rotate>=.5?colors.acento:colors.suave});
  }

  function feet(f, start, end, from, to) {
    const u = ease(f,start,end);
    const stride = u*2;
    const x = mix(from,to,u);
    const cycle = stride*Math.PI*2;
    const bounce = f>start && f<end ? Math.sin(Math.PI*u)**.4 : 0;
    const lead = 31*Math.sin(cycle)*bounce;
    return [[x-23+lead, floor-20-41*Math.max(0, Math.cos(cycle))*bounce],
            [x+24-lead, floor-20-41*Math.max(0,-Math.cos(cycle))*bounce]];
  }

  function figure(parent, info) {
    const {id, x, y, lean, legs, hand, color, pose, opacity=1, face=1, glow=0, primary=false, support} = info;
    const g = group(parent,id,{'data-persistente':'sim','data-pose':pose,'data-cor':color,
      'data-chao':'chao','data-quadril-raio':26,'data-principal':primary?'sim':'nao',opacity,
      ...(support ? {'data-apoio':support} : {}), transform:`translate(${x} ${y})`});
    const breath=info.breath;
    const hip=[0,0], shoulder=[lean,-190+breath], head=[lean*1.12,-288+breath];
    if(glow>0) set(circle(g,...head,78,'none'),{'data-parte':'brilho',stroke:color,'stroke-width':4,opacity:glow});
    legs.forEach(([footX,footY],index)=>{
      const foot=[footX-x,footY-y];
      const offset=info.bend ? info.bend*(index ? .75 : 1) : 0;
      const knee=[Math.max(foot[0], (foot[0]+offset))+offset*.13, mix(0,foot[1],.50)];
      limb(g,[hip,knee],index?color:colors.suave,53,'coxa');
      limb(g,[knee,foot],color,38,'canela');
      rectangle(g,foot[0]-20,foot[1]-9,52,29,color,13).dataset.parte='pe';
    });
    const torsoBase=[lean*.15,-30];
    const length=Math.hypot(shoulder[0]-torsoBase[0],shoulder[1]-torsoBase[1]);
    const torso=rectangle(g,-57,-57,114,length+114,color,57);
    const angle=90+Math.atan2(shoulder[1]-torsoBase[1],shoulder[0]-torsoBase[0])*180/Math.PI;
    set(torso,{'data-parte':'tronco',transform:`translate(${torsoBase.join(' ')}) rotate(${angle+180})`});
    circle(g,...head,65,color).dataset.parte='cabeca';
    const relaxed=[shoulder[0]-face*29,shoulder[1]+180];
    const spare=info.spare ? [info.spare[0]-x,info.spare[1]-y] : relaxed;
    const lead = hand ? [hand[0]-x,hand[1]-y] : [shoulder[0]+face*44,shoulder[1]+174];
    for(const [i, palm] of [spare,lead].entries()){
      const start=[shoulder[0]+(i?34:-31),shoulder[1]+17];
      const elbow=[mix(start[0],palm[0],.46)-(i?-1:1)*face*30,
        mix(start[1],palm[1],.50)+31];
      limb(g,[start,elbow,palm],color,i?31:29,'braco');
      circle(g,...palm,19,color).dataset.parte=i?'mao':'mao_secundaria';
    }
  }

  function arrow(parent, from, to, u, color) {
    if(u<=.01)return;
    const end=interp(from,to,u);
    const dx=end[0]-from[0],dy=end[1]-from[1],len=Math.hypot(dx,dy);
    if(len<12)return;
    const vx=dx/len,vy=dy/len;
    const base=[end[0]-25*vx,end[1]-25*vy];
    stroke(parent,from,base,color,9);
    node('path',{d:`M ${end.join(' ')} L ${base[0]-13*vy} ${base[1]+13*vx} L ${base[0]+13*vy} ${base[1]-13*vx} Z`,fill:color},parent);
  }

  function action(parent, f) {
    const sit=frame('sentar'), rise=frame('levantar'), help=frame('ajudar');
    const ready=help-4, reach=help+1, contact=help+8, pull=contact+4, lift=pull+3, lifted=help+29;
    const entrance=ease(f,corte,corte+12);
    const stage= node('g',{opacity:entrance},parent);
    const compare=ease(f,comparacao+5,comparacao+40);
    const left=ease(f,frame('fazer'),cues.fazer.end);
    const right=ease(f,frame('receber'),cues.receber.end);
    const tempo=f/30;
    const breath=Math.sin(tempo*5.2)*4;
    const ground=group(stage,'chao');
    stroke(ground,[96,floor],[863,floor],colors.linha,3,{'data-parte':'piso'});
    const bench=group(stage,'banco',{opacity:1-ease(f,ready-12,ready+1)});
    rectangle(bench,133,seat,166,21,colors.suave,9).dataset.parte='assento';
    rectangle(bench,151,seat+20,15,floor-seat-20,colors.linha,6);
    rectangle(bench,267,seat+20,15,floor-seat-20,colors.linha,6);

    const arrive=ease(f,corte+6,sit-12);
    const sitDown=ease(f,sit-7,sit+9);
    const stand=ease(f,rise-2,rise+11);
    const settled=sitDown*(1-stand);
    const step=ease(f,rise+6,ready);
    let x=mix(395,323,arrive)-49*settled+75*step;
    x=mix(x,310,compare);
    const y=mix(941,seat-26,settled)+8*Math.sin(sitDown*Math.PI)-12*Math.sin(stand*Math.PI);
    const turn=ease(f,sit-12,sit-4);
    const lean=32*(turn-settled*.5)*(1-stand)+74*Math.sin(Math.PI*ease(f,rise-13,rise+6))
      +54*ease(f,reach,contact)*(1-ease(f,pull,lifted));
    const standingFeet=feet(f,rise+6,ready,x-75*step,x+75*(1-step));
    const walking=f>rise+6 && f<ready;
    const arriveFeet=feet(f,corte+6,sit-12,395,323);
    const stepped=f<=sit-12 ? arriveFeet : walking ? standingFeet : [[x-22,floor-20],[x+34,floor-20]];
    const legs=stepped.map((foot,i)=>[mix(foot[0],348+i*33,settled),foot[1]]);

    const peerOpacity=ease(f,rise-8,rise+12);
    const up=ease(f,lift,lifted);
    const receiverX=mix(690,659,compare)-43*up*(1-compare);
    const receiverY=mix(floor-28,941,up);
    const grip=[mix(558,526,up),mix(1054,844,up)];
    const mainNeutral=[x+63,y-15], receiverNeutral=[receiverX-60,receiverY-25];
    const delivery=frame('fazer'), exchange=delivery+13, transfer=exchange+4;
    const gift=[485,805+breath];
    const making=ease(f,delivery,exchange), receiving=ease(f,delivery+5,exchange);
    const taken=ease(f,transfer,transfer+14);
    const afterOffer=[x+103,y-135], afterReceive=[receiverX-72,receiverY-132];
    const offer=interp(gift,afterOffer,taken);
    const catchAt=interp([receiverX-76,receiverY-145],interp(gift,afterReceive,taken),receiving);
    const reachOut=ease(f,reach,contact);
    const release=ease(f,lifted,lifted+9);
    const mainHand=interp(interp(mainNeutral,grip,reachOut*(1-release)),offer,making);
    const peerReady=ease(f,contact-5,contact);
    const otherHand=interp(interp(receiverNeutral,grip,peerReady*(1-release)),catchAt,right*release);
    const mainSpare=[x-54-36*left,y-28-96*left];
    const peerSpare=[receiverX+45+55*right*release,receiverY-28-100*right*release];
    const mainColor=colorMix(colors.osso,colors.acento,ease(f,rise-3,rise+11));

    const helping=group(stage,'ajuda',{'data-ajuda-de':'agente','data-ajuda-para':'outro',
      'data-contato-esperado':f>=contact && f<=lifted?'sim':'nao',
      'data-tracao':f>=pull?'sim':'nao','data-pausa':f>=ready && f<reach?'sim':'nao',
      'data-subida':up>0?'sim':'nao'});
    figure(stage,{id:'outro',x:receiverX,y:receiverY,lean:-20*(1-up),breath,
      legs:[[receiverX-72*(1-up)-26*up,floor-20],[receiverX+60*(1-up)+29*up,floor-20]],
      color:colors.osso,hand:otherHand,spare:peerSpare,pose:up===1?'em_pe':up>0?'erguendo':'sentado_no_chao',
      bend:22*(1-up),face:-1,opacity:peerOpacity});
    const sitting=settled>.98;
    figure(stage,{id:'agente',x,y,lean,legs,breath,color:mainColor,hand:mainHand,spare:mainSpare,
      primary:true,pose:sitting?'sentado':'em_pe',support:sitting?'banco':undefined,
      bend:20*settled,glow:.65*Math.sin(Math.PI*ease(f,reach,lifted+9))});
    if(f>=delivery+5){
      const received=f>=transfer;
      const owner=received?otherHand:mainHand;
      const token=group(stage,'oferta',{'data-entrega':'sim','data-dono':received?'outro':'agente',
        opacity:ease(f,delivery+5,delivery+10)});
      set(circle(token,...owner,14,colors.acento),{'stroke-width':4,stroke:colors.fundo});
    }
    if(f>=contact && f<=lifted)
      set(circle(helping,...grip,24,'none'),{stroke:colors.acento,'stroke-width':3,opacity:.68});

    const waitStart=frame('esperar');
    const wait=ease(f,waitStart,waitStart+12)*(1-ease(f,rise-26,rise-12));
    if(wait>0){
      const clock=group(stage,'relogio',{opacity:wait});
      const c=[636,842];
      set(circle(clock,...c,57,'none'),{stroke:colors.suave,'stroke-width':5});
      const a=(f-waitStart)*.10;
      stroke(clock,c,[c[0]+36*Math.sin(a),c[1]-36*Math.cos(a)],colors.osso,6);
      const dots=group(stage,'espera',{opacity:wait});
      for(let i=0;i<3;i++)set(circle(dots,605+i*31,945,7,colors.osso),{opacity:.55+.44*Math.sin(f*.17-i)});
    }
    if(right>0 || left>0){
      const divider=group(stage,'divisoria',{opacity:compare*.8});
      stroke(divider,[487,594],[487,1181],colors.linha,2,{'stroke-dasharray':'6 10','pathLength':587});
      for(const [name,label,tx,alpha,ink] of [
        ['receber','RECEBE',668,right,colors.osso],['fazer','FAZ',303,left,colors.acento]
      ]){
        if(alpha<=.01)continue;
        const g=group(stage,name,{opacity:alpha});
        const t=text(g,label,tx,545,333,72,{fill:ink});
        t.dataset.titulo='sim'; t.classList.add('picto-display');
      }
      const arrows=group(stage,'setas');
      [987,1046,1110].forEach((y,i)=>{
        const shift=7*Math.sin(f*.14+i);
        const progressRight=ease(f,frame('receber')+6+i*3,frame('receber')+26+i*3);
        const progressLeft=ease(f,frame('fazer')+i*3,frame('fazer')+17+i*3);
        arrow(arrows,[854,y+shift],[peerSpare[0]+22,peerSpare[1]+(i-1)*15],progressRight,colors.osso);
        const start=[mainHand[0]+23,mainHand[1]+(i-1)*13];
        const destination=[otherHand[0]-12,otherHand[1]+(i-1)*71+shift];
        if(destination[0]-start[0]>20)
          arrow(arrows,start,destination,progressLeft,colors.acento);
      });
    }
  }

  return scene => {
    const paint=(world,defs,t)=>{
      const f=t*30;
      const drift=4.6*Math.sin(t*2.05), driftY=4.0*Math.sin(t*2.9);
      const scale=(landscape?.70:1)*(1+.006*Math.sin(t*1.6));
      const center=landscape?960:478, cy=landscape?526:945;
      const shot=node('g',{transform:`translate(${center+drift} ${cy+driftY}) scale(${scale}) translate(-480 -945)`},world);
      if(f<corte) title(shot,f);
      else action(shot,f);
    };
    paint.events=Object.entries(cues).filter(([,cue])=>cue.scene===scene.id).map(([name,cue])=>({
      scene:scene.id,element:name,action:name,group:name,word:cue.word,emphasis:true,
      start:cue.start/30,end:cue.end/30,landing:cue.frame/30,target:cue.frame/30,minimum:cue.minimum
    }));
    return paint;
  };
});
