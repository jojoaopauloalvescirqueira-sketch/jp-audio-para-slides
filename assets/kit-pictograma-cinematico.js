/* Ensaio de cena para o plano virada_banco_ajuda_v2. */
window.MotorCenas.registrarKit('pictograma-cinematico', api => {
  const {data,landscape,colors,node,set,text,rectangle,line,circle,smoothstep,mix,colorMix}=api;
  const {bible,coreografia}=data;
  const {cues,corte,comparacao,encenacao}=coreografia;
  const {texto:words,marcas:marks}=encenacao;
  const effects=data.efeitos_pictograma&&window.PictogramaEfeitos(api,data.efeitos_pictograma,bible);
  const refined=!data.piloto_godot;
  const pilot=refined||Boolean(data.piloto_godot);
  const {anatomy,pose,draw,blend,relaxed,gap}=PictogramaFigura;
  const {environment,bench,contact}=PictogramaPalco;
  const {altura:h,chao:floor}=coreografia.enquadramento;
  const a=anatomy(bible,h);
  const ease=(f,s,e)=>smoothstep((f-s)/(e-s));
  const wave=(f,s,e)=>Math.sin(Math.PI*ease(f,s,e));
  const group=(p,id,attrs={})=>node('g',{'data-elemento':id,...attrs},p);
  const frame=name=>cues[name].frame;
  const seatY=floor-bible.objetos.banco.altura_h[0]*h;
  const makePose=(name,x,facing=1,phase)=>pose(bible,a,name,x,floor,{seat:seatY,phase,facing});
  const transferFrame=frame('fazer')+17;
  const releaseFrame=frame('fazer')+13, landingFrame=frame('fazer')+24;
  const dividerX=data.rig_anatomico?marks.divisoria:marks.divisoria_legado;

  function combine(p,q,u,name){
    const pHands=relaxed(bible,a,p), qHands=relaxed(bible,a,q);
    return {...p,name,x:mix(p.x,q.x,u),y:mix(p.y,q.y,u),angle:mix(p.angle,q.angle,u),
      feet:p.feet.map((point,i)=>blend(point,q.feet[i],u)),
      arms:pHands.map((point,i)=>blend(p.arms[i]||point,q.arms[i]||qHands[i],u))};
  }
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

  function typography(stage,f){
    const turn=cues.virada;
    const face=ease(f,turn.frame-7,turn.frame+6);
    const show=ease(f,0,9);
    const reveal=.56+.44*ease(f,frame('conceito')-2,frame('conceito')+10);
    const exit=ease(f,corte-11,corte);
    const newLetter=face>=.5;
    const scaleX=Math.max(.028,Math.abs(Math.cos(face*Math.PI)));
    const settle=1+.052*wave(f,turn.frame+4,turn.frame+13);
    const y=pilot?marks.linha_conceito-36*ease(f,corte-5,corte):marks.linha_conceito-76*exit;
    const token=node('g',{opacity:show*reveal*(1-exit),'data-virada':'sim'},stage);
    const dropStart=turn.frame+6, dropEnd=turn.frame+17;
    const drop=effects?ease(f,dropStart,dropEnd):0;
    const negationExit=effects?drop:ease(f,turn.frame+6,turn.frame+(pilot?35:13));
    const leadSize=75;
    const subject=label(token,'deus',words.sujeito,0,marks.linha_superior,265,leadSize,colors.osso);
    const copula=label(token,'verbo-titulo',words.copula,0,marks.linha_superior,125,leadSize,colors.osso);
    const prefix=label(token,'prefixo',words.prefixo,0,y,440,205,colors.osso);
    const suffix=label(token,'sufixo',words.sufixo,0,y,440,205,colors.osso);
    const glyph=group(token,'letra',{'data-letra':newLetter?words.depois:words.antes});
    const letter=text(glyph,words.antes,0,0,440,205,{fill:newLetter?colors.acento:colors.osso});
    letter.classList.add('picto-display');
    const oldWidth=letter.getComputedTextLength();
    letter.textContent=words.depois;
    const slot=Math.max(oldWidth,letter.getComputedTextLength());
    if(!newLetter)letter.textContent=words.antes;
    const start=marks.centro_tipo-(prefix.getComputedTextLength()+slot+suffix.getComputedTextLength())/2;
    const advance=start+prefix.getComputedTextLength();
    set(prefix,{x:start,'text-anchor':'start'});
    set(suffix,{x:advance+slot,'text-anchor':'start'});
    set(glyph,{transform:`translate(${advance+slot/2} ${y}) scale(${scaleX*settle} ${settle})`});
    const release=effects?0:negationExit;
    const pulse=1+.14*wave(f,frame('negacao')-2,frame('negacao')+12);
    const negAlpha=show*(1-negationExit)*(1-exit);
    const neg=group(stage,'negacao',{'data-negacao':'sim',opacity:negAlpha});
    const negative=text(neg,words.negacao,0,0,190,leadSize,{fill:colors.osso});
    negative.classList.add('picto-display');
    negative.dataset.titulo='sim';
    const subjectWidth=subject.getComputedTextLength(), copulaWidth=copula.getComputedTextLength();
    const negativeWidth=negative.getComputedTextLength(), space=24;
    const full=subjectWidth+negativeWidth+copulaWidth+space*2;
    const compact=subjectWidth+space+copulaWidth;
    const firstX=marks.centro_tipo-full/2, compactX=marks.centro_tipo-compact/2;
    set(subject,{x:mix(firstX,compactX,release)+subjectWidth/2});
    set(copula,{x:mix(firstX+full,compactX+compact,release)-copulaWidth/2});
    if(effects){
      set(neg,{transform:`translate(${firstX+subjectWidth+space+negativeWidth/2} ${marks.linha_superior+25*drop}) scale(${pulse})`,
        'data-queda':f>dropStart&&f<dropEnd?'sim':'nao'});
    }else if(pilot){
      const shrink=ease(f,turn.frame+6,turn.frame+10);
      const drift=ease(f,turn.frame+10,turn.frame+30);
      const fall=ease(f,turn.frame+30,turn.frame+35);
      const xpos=mix(firstX+subjectWidth+space+negativeWidth/2,96,drift);
      set(neg,{transform:`translate(${xpos} ${marks.linha_superior+35*shrink+92*fall})
        scale(${pulse*(1-.76*shrink)})`,'data-queda':shrink>0?'sim':'nao'});
    }else{
    set(neg,{transform:`translate(${firstX+subjectWidth+space+negativeWidth/2} ${marks.linha_superior+release*70}) scale(${pulse})`});
    }
    const strike=ease(f,turn.start,effects?turn.frame+5:turn.frame-10);
    if(strike>0){
      neg.dataset.riscoCompleto=String(strike===1);
      const point=[-76+152*strike,-28-7*strike];
      shape(neg,[-76,-28],point,colors.acento,8,{'data-risco':'sim'});
      const flash=wave(f,turn.start,turn.frame-9);
      if(flash>0&&!effects)node('circle',{cx:point[0],cy:point[1],r:10+8*flash,fill:colors.acento,opacity:flash*.33},neg);
    }
    if(effects&&f>=dropEnd)neg.remove();
    label(token,'classe',newLetter?words.classe_depois:words.classe_antes,marks.centro_tipo,marks.linha_classe+12*Math.sin(face*Math.PI),385,50,
      newLetter?colors.acento:colors.osso);
    if(f>=corte-16){
      const u=ease(f,corte-16,corte);
      const sweep=group(stage,'linha-de-palco',{opacity:u*.69});
      const xx=90+(1-u)*220, yy=mix(1014,floor,u);
      shape(sweep,[xx,yy],[960-xx,yy],colors.acento,3);
    }
  }

  function sceneState(f){
    const sit=frame('sentar'),up=frame('levantar'),help=frame('ajudar');
    const stop=help-4, reach=help+1, touch=help+8, pull=touch+4, lift=pull+3, finish=help+29;
    const arrive=ease(f,corte+5,sit-10);
    const down=ease(f,sit-5,sit+12);
    const rising=ease(f,up-4,up+8);
    const walking=ease(f,up+5,stop);
    const compare=ease(f,comparacao+3,comparacao+34);
    const startX=466, edgeX=377, sitX=242, frontX=371, finalX=275;
    let agent=makePose('em_pe',mix(startX,edgeX,arrive));
    if(f>corte+5&&f<sit-10){
      const stride=makePose('andando',agent.x,1,arrive*.74);
      agent=combine(agent,stride,Math.sin(arrive*Math.PI),'andando');
    }
    if(f>=sit-10&&f<=up+8){
      const held=makePose('sentado',sitX);
      held.arms=[[sitX+142,held.y+4],[sitX+187,held.y+20]];
      const start=makePose('em_pe',edgeX);
      const lean=makePose('inclinado',mix(edgeX,sitX,.47));
      agent= f<sit-5?combine(start,lean,ease(f,sit-10,sit-5),'inclinado'):
        combine(lean,held,down,down>=.99?'sentado':'baixando');
      if(f>=up-14){
        const tip=makePose('inclinado',sitX+67);
        if(f<up-4)agent=combine(held,tip,ease(f,up-14,up-4),'inclinado');
        else agent=combine(tip,makePose('em_pe',edgeX),rising,'erguendo');
      }
    }
    if(f>up+8){
      const start=makePose('em_pe',mix(edgeX,frontX,walking));
      const stride=makePose('andando',start.x,1,walking*.8);
      agent=combine(start,stride,Math.sin(walking*Math.PI),'andando');
      if(f>=stop){
        const targetX=mix(frontX,finalX,compare);
        const base=makePose('em_pe',targetX);
        const ready=makePose('inclinado',targetX-9);
        ready.y=base.y+9;
        ready.feet=base.feet;
        ready.angle=34;
        const brace=ease(f,reach,touch)*(1-ease(f,lift,finish));
        agent=combine(base,ready,brace,brace>.03?'apoiado':'em_pe');
      }
    }
    const receiverOpacity=ease(f,up-46,up-27);
    const rx=mix(635,650,compare);
    const spread=pilot?129*(1-ease(f,up-25,up+10)):0;
    const base=makePose('sentado_no_chao',587+spread);
    base.angle=29;
    base.feet=[[870,floor-a.ankle-49],[843,floor-a.ankle]];
    base.arms=[[551+spread,floor-h*.10],[712+spread,floor-h*.171]];
    const helped=ease(f,lift,finish);
    const other=combine(base,makePose('em_pe',rx-5*(1-compare),1),helped,
      helped===0?'sentado_no_chao':helped===1?'em_pe':'erguendo');
    const hold=ease(f,reach,touch)*(1-ease(f,finish,finish+9));
    const waitHand=ease(f,touch-5,touch)*(1-ease(f,finish,finish+9));
    const grip=[mix(534,501,helped),mix(989,822,helped)-22*wave(f,pull,finish)];
    const rest=state=>{
      const hands=relaxed(bible,a,state);
      if(!pilot)return hands;
      return hands.map((p,i)=>[mix(p[0],state.x+(i?1:-1)*h*.115,.84),p[1]+h*.028]);
    };
    const [agentRest,agentNear]=rest(agent);
    const [peerRest,peerNear]=rest(other);
    const receive=pilot?ease(f,frame('receber')-13,frame('receber')):ease(f,frame('receber')-2,frame('receber')+11);
    const give=ease(f,frame('fazer'),frame('fazer')+13);
    const accept=ease(f,frame('fazer')+5,frame('fazer')+13);
    const moveObject=ease(f,transferFrame,transferFrame+13);
    const present=[agent.x+99,agent.y-105];
    const shared=[493,agent.y-137];
    const leftPalm=[other.x-(refined?22:74),other.y-135], rightPalm=[other.x+(refined?22:58),other.y-135];
    const offer=refined?[agent.x+116,agent.y-112]:blend(shared,present,moveObject);
    const take=blend(shared,leftPalm,moveObject);
    const agentNeutral=pilot&&agent.name==='em_pe';
    const peerNeutral=pilot&&other.name==='em_pe';
    agent.arms=[(!agentNeutral&&agent.arms[0])||agentRest,
      blend(blend((!agentNeutral&&agent.arms[1])||agentNear,grip,hold),offer,
        refined?give*(1-ease(f,landingFrame+3,landingFrame+16)):give)];
    const restingFirst=blend((!peerNeutral&&other.arms[0])||peerRest,grip,waitHand);
    const restingSecond=(!peerNeutral&&other.arms[1])||peerNear;
    other.arms=refined?[blend(restingFirst,leftPalm,receive),blend(restingSecond,rightPalm,receive)]:[blend(restingFirst,rightPalm,receive),
      blend(blend(restingSecond,leftPalm,receive),take,accept)];
    return {agent,other,grip,receiverOpacity,compare,give,receive,touch,pull,lift,finish,stop,reach};
  }

  // Keep the rig's joint axes for measurement and paint one outline over each pair of bones.
  function continuousLimbs(actor,info){
    const point=id=>{
      const el=actor.g.querySelector('[data-articulacao='+id+']');
      return [+el.getAttribute('cx'),+el.getAttribute('cy')];
    };
    const normal=(a,b)=>{
      const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy);
      return [-dy/len,dx/len];
    };
    const at=(point,n,r)=>[point[0]+n[0]*r,point[1]+n[1]*r].join(' ');
    const measure=bible.forma;
    if(refined) set(actor.g,{'data-contorno-cinematico':'sim'});
    const legWidth=info.pose.name==='sentado_no_chao'||info.pose.name==='erguendo'?
      Math.min(measure.coxa_diametros_h[0],measure.apoio_chao_h*1.85):measure.coxa_diametros_h[0];
    for(const [i,side] of ['E','D'].entries()){
      const layer=i?actor.g:actor.g.firstElementChild;
      const direct=part=>layer.querySelector(':scope > [data-parte='+part+']');
      for(const [from,mid,to,first,second,widths] of [
        ['quadril','joelho','tornozelo','coxa','canela',
          [legWidth,measure.canela_diametros_h[0],measure.canela_diametros_h[1]]],
        ['ombro','cotovelo','mao','braco','antebraco',
          [measure.braco_diametros_h[0],measure.antebraco_diametros_h[0],measure.antebraco_diametros_h[1]]]
      ]){
        const shoulder=point(from+side),joint=point(mid+side),end=point(to+side);
        const start=refined&&first==='braco'?blend(blend(shoulder,blend(point('ombroE'),point('ombroD'),.5),.25),joint,.17):
          pilot&&first==='braco'?blend(shoulder,joint,.14):shoulder;
        const n=normal(start,joint), m=normal(joint,end);
        const [a,b,c]=widths.map((w,index)=>w*h/2*
          (refined&&first==='braco'&&index===0?.58:pilot&&first==='braco'&&index===0?.88:1));
        const t=(p,q,k,r)=>at(blend(p,q,k),r,b);
        const elbow=(sign)=>{
          const control=[joint[0]+(n[0]+m[0])*b*sign*.59,joint[1]+(n[1]+m[1])*b*sign*.59];
          return control.join(' ');
        };
        const minus=v=>v.map(x=>-x);
        const firstPart=direct(first), secondPart=direct(second);
        const open=refined&&first==='braco'&&info.openPalm>.05;
        const aPalm=anatomy(bible,info.height).palm;
        const sideSign=i?-1:1;
        const p=(x,y)=>`${end[0]+x*aPalm*sideSign} ${end[1]+y*aPalm}`;
        const top=at(blend(end,joint,.20),m,(i?-1:1)*c);
        const bottom=at(blend(end,joint,.20),m,(i?1:-1)*c);
        const cup=`Q${p(-.34,-.28)} ${p(-.16,-.16)} Q${p(.14,-.08)} ${p(.61,-.30)}`;
        const returnCup=`Q${p(.77,-.28)} ${p(.68,-.03)} Q${p(.36,.39)} ${p(-.12,.35)}`;
        const terminal=open?(i?
          `L${top} ${cup} ${returnCup} L${bottom}`:
          `L${bottom} L${p(-.12,.35)} Q${p(.36,.39)} ${p(.68,-.03)}
          Q${p(.77,-.28)} ${p(.61,-.30)} Q${p(.14,-.08)} ${p(-.16,-.16)} Q${p(-.34,-.28)} ${top}`):
          `L${at(end,m,-c)} A${c} ${c} 0 0 1 ${at(end,m,c)}`;
        const d=`M${at(start,n,-a)} L${t(joint,start,.12,minus(n))}
          Q${elbow(-1)} ${t(joint,end,.12,minus(m))}
          ${terminal}
          L${t(joint,end,.12,m)} Q${elbow(1)} ${t(joint,start,.12,n)}
          L${at(start,n,a)} A${a} ${a} 0 0 1 ${at(start,n,-a)}Z`;
        set(firstPart,{d,'data-parte':first==='coxa'?'perna':second,'data-contorno-continuo':first,'data-lado':side,
          ...(open?{'data-palma-aberta':'sim'}:{})});
        if(open){
          actor.g.querySelector('[data-parte='+(i?'mao':'mao_secundaria')+']').remove();
          actor.g.append(firstPart);
          const insideEdge=i?-1:1;
          const startCrease=at(blend(joint,end,.04),m,insideEdge*b*.36);
          const midCrease=at(blend(joint,end,.47),m,insideEdge*c*.58);
          node('path',{d:`M${p(-.44,-.12)} Q${p(-.47,-.42)} ${p(-.24,-.30)}
            Q${p(.08,-.08)} ${p(.45,-.23)} Q${p(.69,-.30)} ${p(.62,-.08)}
            Q${p(.38,.26)} ${p(-.10,.22)} Q${p(-.32,.15)} ${p(-.44,-.12)}Z`,
            fill:colorMix(info.color,colors.fundo,.17),stroke:colorMix(info.color,colors.fundo,.42),
            'stroke-width':3.6,'stroke-linejoin':'round','data-palma-pintada':side},actor.g);
          node('path',{d:`M${startCrease} Q${midCrease} ${p(-.30,.12)}`,
            fill:'none',stroke:colorMix(info.color,colors.fundo,.48),'stroke-width':4.2,
            'stroke-linecap':'round','stroke-linejoin':'round',opacity:.82,'data-dobra-palma':side},actor.g);
        }
        if(first==='coxa')
          set(layer.querySelector(':scope > [data-eixo=canela]'),{'data-raio-inicial':b,'data-raio-final':c});
        secondPart.remove();
      }
      const foot=direct('pe');
      const cx=+foot.getAttribute('cx'), cy=+foot.getAttribute('cy');
      const r=+foot.getAttribute('rx')*.91, ry=+foot.getAttribute('ry')*.91;
      const direction=info.pose.facing;
      const p=(x,y)=>`${cx+x*r*direction} ${cy+Number(foot.getAttribute('ry'))+(y-1)*ry}`;
      const sole=node('path',{fill:foot.getAttribute('fill'),'data-parte':'pe',
        d:`M${p(-1,.30)} Q${p(-1,-.73)} ${p(-.54,-.92)}
          C${p(.07,-1.03)} ${p(.23,-.69)} ${p(.69,-.49)}
          Q${p(1,-.34)} ${p(1,.33)} Q${p(.95,1)} ${p(.59,1)}
          H${cx-r*.66*direction} Q${p(-.98,1)} ${p(-1,.30)}Z`});
      foot.replaceWith(sole);
    }
    if(!refined&&info.openPalm>.05){
      for(const [name,sign] of [['mao_secundaria',-1],['mao',1]]){
        const hand=actor.g.querySelector('[data-parte='+name+']');
        const x=+hand.getAttribute('cx'),y=+hand.getAttribute('cy');
        const p=(u,v)=>`${x+u*a.palm*sign} ${y+v*a.palm}`;
        const palm=node('path',{fill:hand.getAttribute('fill'),'data-parte':name,
          'data-palma-aberta':'sim',d:`M${p(-.55,-.13)} Q${p(-.39,-.39)} ${p(-.09,-.29)}
          Q${p(.24,-.13)} ${p(.73,-.24)} Q${p(.86,-.23)} ${p(.77,-.02)}
          Q${p(.45,.34)} ${p(-.12,.35)} Q${p(-.49,.36)} ${p(-.55,-.13)}Z`});
        hand.remove();
        actor.g.append(palm);
      }
    }
  }

  // A single light field across the neck, shoulders and arms keeps the joins invisible.
  function upperBodyLight(actor,defs,info){
    const existing=defs.querySelector('#luz-'+info.id);
    const shadow=existing.dataset.sombra;
    const pieces=actor.g.querySelectorAll('[data-parte=tronco],[data-parte=cabeca],[data-parte=antebraco],'+
      '[data-parte=mao],[data-parte=mao_secundaria],[data-parte=pescoco],:scope > ellipse:not([data-parte])');
    for(const [index,piece] of [...pieces].entries()){
      const matrix=actor.g.getCTM().inverse().multiply(piece.getCTM()).inverse();
      const id=info.id+'-luz-superior-'+index;
      const gradient=node('linearGradient',{id,gradientUnits:'userSpaceOnUse',
        gradientTransform:`matrix(${[matrix.a,matrix.b,matrix.c,matrix.d,matrix.e,matrix.f].join(' ')})`,
        x1:-a.shoulders*.62,y1:-h*.56,x2:a.shoulders*.72,y2:0},defs);
      node('stop',{offset:.17,'stop-color':info.color},gradient);
      node('stop',{offset:.89,'stop-color':shadow},gradient);
      set(piece,{fill:`url(#${id})`});
      if(!refined&&piece.dataset.palmaAberta==='sim')
        set(piece,{stroke:colorMix(info.color,colors.fundo,.54),'stroke-width':4,'stroke-linejoin':'round'});
    }
  }

  function actorLayer(stage,defs,info,f){
    const actor=draw(stage,defs,bible,{...info,contour:refined});
    continuousLimbs(actor,info);
    upperBodyLight(actor,defs,info);
    const rank=a.head;
    for(const [x,y] of actor.soles){
      const drift=Math.max(0,Math.min(1,(floor-y)/rank));
      const resting=info.pose.name==='sentado_no_chao';
      const shadow=contact(stage,defs,bible,info.id,x,resting?y:floor,a.foot*.69,rank*.11,resting?0:drift);
      set(shadow,{opacity:Number(shadow.getAttribute('opacity'))*(info.opacity??1)});
      stage.insertBefore(shadow,actor.g);
    }
    if(info.pose.name==='sentado_no_chao'){
      const shadow=contact(stage,defs,bible,info.id,info.pose.x,floor,a.hips*.67,rank*.13);
      stage.insertBefore(shadow,actor.g);
    }
    const bloom=wave(f,frame('levantar')-1,frame('levantar')+bible.luz.halo.quadros);
    if(info.primary&&bloom>.01){
      const g=node('g',{opacity:bloom*bible.luz.halo.opacidade},stage);
      const cy=info.pose.y-a.torso*.78;
      const glow=node('radialGradient',{id:'halo-impulso'},defs);
      for(const [offset,opacity] of [[0,.84],[.48,.37],[1,0]])
        node('stop',{offset,'stop-color':colors.acento,'stop-opacity':opacity},glow);
      node('ellipse',{cx:info.pose.x+24,cy,rx:a.head*(1.36+.43*bloom),ry:a.head*1.71,
        fill:'url(#halo-impulso)'},g);
      stage.insertBefore(g,actor.g);
    }
    return actor;
  }

  function heartTrajectory(f,giver,palms){
    const travel=ease(f,releaseFrame,landingFrame);
    const target=effects?[palms[0]-a.head*.26,palms[1]-a.head*.49]:palms;
    const position=blend(giver,target,travel);
    position[1]-=111*Math.sin(Math.PI*travel);
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
        circle(dots,640+57*i,924-7*p,11+6*p,colors.osso);
      }
    }
    const cue=frame('receber'), outgoing=frame('fazer');
    const opacity=ease(f,cue-2,cue+9);
    if(opacity<=0 && (!pilot||f<cue-13))return;
    const divider=group(stage,'divisoria',{opacity:.64*states.compare*opacity});
    shape(divider,[dividerX,527],[dividerX,1181],colors.linha,2,{'stroke-dasharray':'6 10','pathLength':654});
    label(stage,'receber',words.direita,675,447,295,62,colors.osso,opacity);
    label(stage,'fazer',words.esquerda,286,447,275,62,colors.acento,opacity);
    if(pilot && f>=cue-13 && (effects||f<outgoing+3)){
      const u=ease(f,cue-13,cue);
      const palms=blend(second.hands[1],second.hands[0],.5);
      const owner=blend([palms[0]+128,palms[1]-141],palms,u);
      const side=a.head*(refined?.88:.94);
      const heart=group(stage,'recepcao',{'data-objeto':'simbolo','data-chegada':f>=cue?'pouso':'trajeto',
        opacity:ease(f,cue-13,cue-7)*(effects?1:1-ease(f,outgoing-8,outgoing+3)),
        ...(effects?{'data-objeto-id':'coracao-recebido'}:{})});
      drawHeart(heart,owner,owner[1]-side*.88,side,effects?colors.osso:colors.acento);
    }
    if(f<outgoing+(effects?-1:4))return;
    if(refined){
      const launch=first.hands[1];
      const palms=blend(second.hands[0],second.hands[1],.5);
      const landed=f>=landingFrame;
      const flying=f>=releaseFrame&&!landed;
      const owner=heartTrajectory(f,launch,palms);
      const side=a.head*(effects?.73:.88);
      const top=owner[1]-side*.88;
      const stream=group(stage,'sai',{opacity:(1-ease(f,releaseFrame+2,landingFrame+5))});
      const from=[launch[0]+10,launch[1]-49], to=[dividerX-22,launch[1]-100];
      if(from[0]<to[0]-5)arrow(stream,from,to,ease(f,outgoing+4,releaseFrame),colors.acento);
      const object=group(stage,'oferta',{'data-entrega':'sim','data-modo-entrega':'trajeto',
        'data-dono':landed?'outro':flying?'trajeto':'agente',
        'data-objeto':'simbolo',opacity:effects?ease(f,outgoing-1,outgoing+6):ease(f,outgoing+4,outgoing+10),
        ...(effects?{'data-objeto-id':'coracao-oferecido'}:{})});
      drawHeart(object,owner,top,side);
      return;
    }
    const recipient=f>=transferFrame;
    const travel=ease(f,transferFrame,transferFrame+14);
    const cream=refined?blend(second.hands[0],second.hands[1],travel*.5):blend(second.hands[1],second.hands[0],travel*.5);
    const owner=recipient?cream:first.hands[1];
    const side=a.head*.94;
    const top=owner[1]-side*.91-(recipient?22*Math.sin(Math.PI*travel):0)+(refined&&recipient?8:0);
    const launch=[states.agent.x+108,states.agent.y-123];
    const from=[launch[0]+a.palm*.37,launch[1]+15];
    const to=[owner[0]-side*.44,top+side*.48];
    const stream=group(stage,'sai',{opacity:1-.56*ease(f,transferFrame+11,transferFrame+26)});
    const u=ease(f,outgoing+4,outgoing+17);
    if(to[0]>from[0]){
      for(const [i,part] of [.40,1].entries())
        arrow(stream,blend(from,to,i*.49),blend(from,to,part),u,colors.acento);
    }
    const object=group(stage,'oferta',{'data-entrega':'sim','data-dono':recipient?'outro':'agente',
      'data-objeto':'simbolo','data-mao-receptora':refined?'E':'D',opacity:ease(f,outgoing+4,outgoing+10)});
    drawHeart(object,owner,top,side);
  }

  function drawHeart(object,owner,top,side,ink=colors.acento){
    node('path',{transform:`translate(${owner[0]} ${top}) scale(${side})`,
      d:'M 0 .88 C -.12 .78 -.5 .55 -.5 .28 C -.5 -.02 -.15 -.08 0 .14 C .15 -.08 .5 -.02 .5 .28 C .5 .55 .12 .78 0 .88 Z',
      fill:ink,stroke:colors.fundo,'stroke-width':.033},object);
  }

  const anatomical=data.rig_anatomico&&window.PictogramaAtuacao(data.rig_anatomico,cues,corte,marks);
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
    environment(shot,defs,bible,colors,{width:1080,height:1920,floor,focus:marks.foco,head:a.head});
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
      effects.contact(shot,defs,'banco',83,floor+6,scale,0,opacity);
      effects.contact(shot,defs,'banco-2',141,floor+6,scale,0,opacity);
    }
    const floorLayer=group(shot,'chao');
    const {a:zoom,e:shift}=shot.getScreenCTM();
    const floorLeft=Math.max(45,(14-shift)/zoom), floorRight=Math.min(875,(885-shift)/zoom);
    shape(floorLayer,[floorLeft,floor],[floorRight,floor],colors.linha,2,{'data-parte':'piso'});
    const seat=bench(shot,defs,bible,{x:marks.banco_x,floor,height:h,colors,comprimento:marks.banco_comprimento,pernas:[.15,.49]});
    // Align the painted seat to the approved pelvis support geometry.
    set(seat.base,{opacity:ease(f,corte+16,corte+24)*(1-ease(f,frame('levantar')-12,frame('levantar')))});
    const seats=seat.base.querySelector('[data-parte=assento]');
    if(seats)set(seat.base,{transform:`translate(0 ${floor-1.48*scale-seatY})`});
    effects?.dim(shot,f);
    const inks=[colorMix(colors.osso,colors.acento,ease(f,frame('levantar')-12,frame('levantar'))),colors.osso];
    const painted=actors.map((actor,index)=>{
      const id=index?'outro':'agente';
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
    label(shot,'esperar',words.espera,685,516,350,63,colors.osso,wordIn);
    label(shot,'agir',words.acao,748,506,320,67,colors.acento,wordOut);
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
    const shift=2.4*Math.sin(f*.084)-(anatomical?42:70)*room, dy=4*Math.sin(f*.058);
    const x=landscape?960:480,y=landscape?540:960;
    const shot=node('g',{transform:`translate(${x+shift} ${y+dy}) scale(${zoom}) translate(-480 -960)`,
      'data-zoom':zoom/zoomBase},stage);
    if(f<corte){
      if(anatomical)window.pictogramaQuadro={frame:Math.round(f),actors:[]};
      environment(shot,defs,bible,colors,{width:1080,height:1920,floor:1060,focus:478,head:a.head});
      typography(shot,f);
      return;
    }
    if(anatomical){anatomicalScene(shot,defs,f);return;}
    const states=sceneState(f);
    environment(shot,defs,bible,colors,{width:1080,height:1920,floor,
      focus:mix(states.agent.x+72,485,states.compare),head:a.head});
    const floorLayer=group(shot,'chao');
    shape(floorLayer,[91,floor],[873,floor],colors.linha,2,{'data-parte':'piso'});
    const seat=bench(shot,defs,bible,{x:94,floor,height:h,colors});
    set(seat.base,{opacity:1-ease(f,frame('ajudar')-17,frame('ajudar')-2)});
    const {agent,other,touch,pull,lift:liftFrame,finish,reach,stop}=states;
    const color=colorMix(colors.osso,colors.acento,ease(f,frame('levantar')-3,frame('levantar')+12));
    const entrance=ease(f,corte-4,corte+8);
    const breath=Math.sin(f*.17)*2.2;
    const receiver=actorLayer(shot,defs,{id:'outro',height:h,pose:other,color:colors.osso,receivingRig:refined&&f>=frame('receber')-18,
      opacity:states.receiverOpacity,openPalm:states.receive,
      forearmProjection:refined?1-.52*states.receive:1,breath:-breath*.8,headLag:2*wave(f,liftFrame,finish)-3*wave(f,touch-7,liftFrame+2),expression:'neutro'},f);
    const helper=actorLayer(shot,defs,{id:'agente',height:h,pose:agent,color,primary:true,opacity:entrance,
      support:agent.name==='sentado'?'banco':undefined,breath,
      headLag:-3*wave(f,frame('sentar')-4,frame('sentar')+12),
      expression:f>=frame('levantar')?'disposto':agent.name==='sentado'?'cansado':'neutro'},f);
    const grip=group(shot,'ajuda',{'data-ajuda-de':'agente','data-ajuda-para':'outro',
      'data-contato-esperado':f>=touch&&f<=finish?'sim':'nao','data-tracao':f>=pull?'sim':'nao',
      'data-pausa':f>=stop&&f<reach?'sim':'nao','data-subida':f>liftFrame?'sim':'nao','data-mao-outro':'E'});
    if(f>=touch&&f<=finish&&gap(helper.hands[1],receiver.hands[0])<5){
      const [x,y]=helper.hands[1], r=a.palm*.5;
      const p=(u,v)=>`${x+u*r} ${y+v*r}`;
      node('path',{d:`M${p(.85,-.35)} Q${p(.47,-.89)} ${p(.02,-.63)}
        Q${p(-.35,-.37)} ${p(-.40,.03)}`,fill:'none',stroke:colors.osso,
        'stroke-width':r*.34,'stroke-linecap':'round'},grip);
    }
    const wordIn=ease(f,corte+29,corte+42)*(1-ease(f,frame('levantar')-46,frame('levantar')-33));
    const wordOut=ease(f,frame('levantar')-11,frame('levantar')+2)*(1-ease(f,comparacao-11,comparacao-1));
    label(shot,'esperar',words.espera,685,516,350,63,colors.osso,wordIn);
    label(shot,'agir',words.acao,748,506,320,67,colors.acento,wordOut);
    symbols(shot,f,states,helper,receiver);
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
});
