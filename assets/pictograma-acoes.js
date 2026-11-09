/* Mecânica de ações no espaço do rig. A locação e os participantes vêm do plano. */
window.PictogramaAcoes = (() => {
  const rig=()=>window.PictogramaRig;
  const clamp=v=>Math.max(0,Math.min(1,v));
  const ease=v=>{const u=clamp(v);return u*u*(3-2*u);};
  const pulse=u=>Math.sin(Math.PI*clamp(u))**2;
  const move=(b,p,d,facing=p.facing)=>{
    const c=p.control;
    const sign=facing===p.facing?1:-1;
    const tr=v=>v&&[v[0],v[1],v[2]*sign+d];
    return rig().pose(b,{...c,facing,pelvis:tr(c.pelvis),seat:tr(c.seat),
      hands:c.hands?.map(tr),feet:c.feet.map(foot=>Object.fromEntries(Object.entries(foot)
        .map(([key,value])=>[key,Array.isArray(value)?tr(value):value])))});
  };
  function walk(b,f,d=0){return move(b,rig().walk(b,f),d);}
  function chair(b,f,up,d=0){return move(b,rig().chair(b,f,up),d);}
  function bridge(b,start,end,t,phase,{preserveHands=false}={}){
    const p=start.control,q=end.control;
    const blend=(x,y,u)=>x.map((v,i)=>v+(y[i]-v)*u);
    const u=ease(t),facing=p.facing??1;
    const direction=preserveHands?facing+(end.facing-facing)*u:facing;
    const feet=p.feet.map((foot,i)=>{
      const next=q.feet[i], part=clamp(t*2-i);
      if(part===0)return foot;
      if(part===1||rig().distance(foot.heel,next.heel)<.003&&foot.mode===next.mode)return next;
      const heel=blend(foot.heel,next.heel,ease(part));
      const side=preserveHands&&part>=.5?end.facing:facing;
      return rig().foot(b,heel[0],heel[2]+side*b.ossos.calcanhar_planta,side,'livre',
        0,.115*Math.sin(Math.PI*part)+Math.max(0,-heel[1]));
    });
    const hands=preserveHands?['E','D'].map(side=>
      blend(start.joints['punho'+side],end.joints['punho'+side],u)):null;
    const handDirections=preserveHands?['E','D'].map(side=>{
      const direction=pose=>pose.joints['mao'+side].map((n,i)=>n-pose.joints['punho'+side][i]);
      return blend(direction(start),direction(end),u);
    }):q.handDirections;
    const head=c=>c.headPitch??c.spine.reduce((a,v)=>a+v,0);
    const pelvis=blend(p.pelvis,q.pelvis,u);
    if(preserveHands){
      const length=b.ossos.coxa+b.ossos.canela-.002;
      for(const [i,foot] of feet.entries()){
        if(foot.mode==='livre')continue;
        const [x,y,z]=foot.ankle;
        const hipX=pelvis[0]+(i?.35:-.35);
        const vertical=Math.sqrt(Math.max(0,length**2-(hipX-x)**2-(pelvis[2]-z)**2));
        const tilt=q.pelvisTilt??0;
        pelvis[1]=Math.max(pelvis[1],y-vertical-(i?tilt:-tilt));
      }
    }
    const seat=preserveHands&&p.seat&&q.seat&&rig().distance(p.seat,q.seat)<.003?p.seat:null;
    return rig().pose(b,{...q,facing,turn:direction,pelvis,feet,spine:blend(p.spine,q.spine,u),
      headPitch:head(p)+(head(q)-head(p))*u,phase,mode:'transicao',seat,groundSeat:false,
      hands,handDirections,handContacts:null});
  }
  function help(b,f,options){return rig().help(b,f,options);}
  function settleAfterHelp(b,base,t,nod){
    const u=ease(t),c=base.control;
    if(u===0&&!nod)return base;
    const pelvis=[...c.pelvis];
    const reach=b.ossos.coxa+b.ossos.canela-.004;
    let y=pelvis[1]-.24*u;
    for(const [i,shoe] of c.feet.entries()){
      if(shoe.mode==='livre')continue;
      const [fx,fy,fz]=shoe.ankle;
      const horizontal=(fx-pelvis[0]-(i?.35:-.35))**2+(fz-pelvis[2])**2;
      y=Math.max(y,fy-Math.sqrt(Math.max(0,reach**2-horizontal)));
    }
    pelvis[1]=y;
    const spine=c.spine.map((angle,i)=>angle+([3,-2,2][i]-angle)*u);
    const input={...c,pelvis,spine,headPitch:(c.headPitch??0)*(1-u)+nod,
      mode:'repouso',phase:'Estabilizar após soltar',handContacts:null};
    const relaxed=rig().pose(b,{...input,hands:null});
    const hands=['E','D'].map(side=>base.joints['punho'+side].map(
      (v,i)=>v+(relaxed.joints['punho'+side][i]-v)*u));
    return rig().pose(b,{...input,hands});
  }
  function stepFrom(b,base,t){
    const u=clamp(t), facing=base.facing;
    if(u===0)return base;
    const stride=.84, advance=ease(u);
    const foot=base.control.feet[1];
    const lift=.20*Math.sin(Math.PI*u)**2;
    const feet=[base.control.feet[0],rig().foot(b,foot.heel[0],
      foot.heel[2]+facing*(b.ossos.calcanhar_planta+stride*advance),facing,u<1?'livre':'planta',0,lift)];
    const pelvis=[...base.control.pelvis];
    pelvis[2]+=facing*stride*.67*advance;
    pelvis[1]+=.035*Math.sin(Math.PI*u)**2;
    const reach=b.ossos.coxa+b.ossos.canela-.002;
    for(const [i,shoe] of feet.entries()){
      if(shoe.mode==='livre')continue;
      const [x,y,z]=shoe.ankle;
      const horizontal=(x-pelvis[0]-(i?.35:-.35))**2+(z-pelvis[2])**2;
      pelvis[1]=Math.max(pelvis[1],y-Math.sqrt(Math.max(0,reach**2-horizontal)));
    }
    return rig().pose(b,{...base.control,pelvis,feet,hands:null,
      armSwing:.24*Math.sin(Math.PI*u)**2,mode:'marcha',phase:u===1?'Pouso':'Passo de decisão'});
  }
  function care(b,base,t){
    const u=clamp(t),weight=ease(u/.40)*(1-ease((u-.62)/.38));
    if(weight<=0)return base;
    const input=base.control;
    const [x,y,z]=input.pelvis, side=base.facing;
    const wrist=base.joints.punhoE;
    const toward=[x-.44,y-1.27,z+.83*side];
    const hands=[...input.hands];
    hands[0]=wrist.map((v,i)=>v+(toward[i]-v)*weight);
    const handDirections=[...input.handDirections];
    handDirections[0]=[0,.94-.97*weight,side*(.33+.63*weight)];
    return rig().pose(b,{...input,hands,handDirections,headPitch:-8*weight,mode:'acolhimento'});
  }
  function gesture(b,base,{arms=[],tilt=0,pitch=0,lower=0,directions},u,orientacao){
    const p=base.control, weight=pulse(u);
    const [x,y,z]=p.pelvis,f=orientacao??p.facing??1;
    const points=[-1,1].map((side,i)=>{
      const target=arms[i];
      if(!target)return null;
      const shoulder=base.joints['ombro'+(i?'D':'E')];
      const relaxed=[shoulder[0]+side*.035,shoulder[1]+1.75,shoulder[2]];
      const end=[x+target[0],y+target[1],z+target[2]*f];
      return relaxed.map((v,k)=>v+(end[k]-v)*weight);
    });
    return rig().pose(b,{...p,pelvis:[x,y+lower*weight,z],hands:points,
      spine:p.spine.map((n,i)=>n+tilt*weight*[.52,.32,.16][i]),
      headPitch:pitch*weight,handDirections:directions??p.handDirections,seat:null,mode:'gesto'});
  }
  const hand=(x,y,z)=>[x,y,z];
  const verbs={
    entregar:{arms:[null,hand(.45,-1.23,1.02)],tilt:8},
    receber:{arms:[hand(-.31,-1.24,.58),hand(.31,-1.23,.70)]},
    apontar:{arms:[null,hand(.57,-1.66,1.16)]},
    abracar:{arms:[hand(-.50,-1.38,.83),hand(.50,-1.38,.83)],tilt:12},
    ajoelhar:{lower:.60,tilt:13},
    cair:{lower:1.20,tilt:31,pitch:14},
    amparar:{arms:[hand(-.56,-1.34,.79),hand(.39,-1.11,.62)],tilt:6},
    carregar:{arms:[hand(-.52,-.88,.59),hand(.52,-.88,.59)],tilt:8},
    olhar_para:{pitch:14,tilt:6},
    esperar:{tilt:3,pitch:-4},
    pensar:{arms:[null,hand(.28,-2.50,.58)],pitch:14},
    ler:{arms:[hand(-.43,-1.49,.69),hand(.42,-1.47,.69)],pitch:16},
    recolher:{arms:[hand(-.23,-1.44,.43),hand(.23,-1.44,.43)],pitch:15,tilt:7},
    recusar:{arms:[null,hand(.52,-1.90,.96)],tilt:-7},
    mao_presente:{arms:[null,hand(.38,-2.02,1.21)],tilt:5,pitch:-22,directions:[null,[0,-.86,.51]]},
    conversar:{arms:[hand(-.23,-1.34,.52),hand(.44,-1.45,1.03)],tilt:9,pitch:-4},
    mao_no_peito:{arms:[null,hand(-.12,-1.78,.27)],tilt:7,pitch:10},
    orar:{arms:[hand(-.04,-1.28,.54),hand(.04,-1.28,.54)],lower:.58,tilt:19,pitch:20},
    virar:{arms:[hand(-.57,-1.26,.58),hand(.58,-1.19,.53)],tilt:-13,pitch:8},
    romper:{arms:[hand(-.75,-1.46,.63),hand(.75,-1.46,.78)],tilt:9,pitch:13}
  };
  const postures={
    curvar:{drop:.25,travel:.38,lean:37,head:16},
    agachar:{drop:1.10,travel:-.32,lean:30,head:14},
    sentar_no_chao:{drop:2.26,travel:-.65,lean:17,head:11},
    ajoelhar:{drop:1.67,travel:.10,lean:17,head:25},
    orar:{drop:1.67,travel:.10,lean:17,head:26},
    virar:{drop:.18,travel:.35,lean:17,head:9},
    conversar:{drop:.20,travel:.30,lean:18,head:9},
    ler:{drop:.22,travel:.26,lean:22,head:17},
    olhar_para:{drop:.12,travel:.27,lean:15,head:14},
    entregar:{drop:.26,travel:.42,lean:22,head:9},
    receber:{drop:.26,travel:.39,lean:20,head:10},
    abracar:{drop:.25,travel:.38,lean:26,head:10},
    amparar:{drop:.70,travel:.34,lean:27,head:15},
    carregar:{drop:.23,travel:-.27,lean:17,head:7},
    romper:{drop:.34,travel:-.39,lean:-15,head:10},
  };
  function posture(b,base,kind,weight){
    const spec=postures[kind];
    if(!spec)return base;
    const c=base.control, dir=c.facing??1, [x,y,z]=c.pelvis;
    const t=clamp(weight);
    const low=kind==='ajoelhar'||kind==='orar';
    const feet=low?c.feet.map((foot,i)=>i===0?
      rig().foot(b,foot.anchor[0],foot.anchor[2]-1.90*t*dir,dir,
        t>0&&t<.9999?'livre':'planta',0,.11*Math.sin(Math.PI*t)):foot):c.feet;
    return rig().pose(b,{...c,feet,pelvis:[x,y+spec.drop*t,z+spec.travel*t*dir],
      spine:c.spine.map((angle,i)=>angle+spec.lean*t*[.50,.33,.17][i]),
      headPitch:spec.head*t,mode:kind,phase:'Atuação'});
  }
  function resolve(b,action,frame,base=null){
    const {tipo,distancia=0,direcao=1}=action;
    const u=clamp((frame-action.inicio)/(action.fim-action.inicio));
    const neutral=base??rig().neutral(b,direcao);
    if(['andar_ate','aproximar','afastar'].includes(tipo)){
      const stride=u*(action.passos??1)*b.marcha.quadros_por_passo;
      return [move(b,rig().walk(b,stride),distancia,tipo==='afastar'?-direcao:direcao)];
    }
    if(tipo==='tentar_levantar'){
      const landing=action.pouso??Math.round((action.inicio+action.fim)/2);
      const before=frame<=landing;
      const progress=before?clamp((frame-action.inicio)/Math.max(1,landing-action.inicio)):
        clamp((frame-landing)/Math.max(1,action.fim-1-landing));
      const rise=before?ease(progress):1-progress**2.35;
      const amplitude=action.variacao==='B'?.78:1;
      const base=chair(b,14*rise*amplitude,true,distancia);
      const tremor=Math.max(0,1-Math.abs(frame-landing)/4)*Math.sin((frame-landing)*2.1);
      const hands=['E','D'].map(side=>{
        const [x,y,z]=base.joints['joelho'+side];
        return [x,y-.27,z+.02];
      });
      return [rig().pose(b,{...base.control,hands,handDirections:[[0,.99,0],[0,.99,0]],
        spine:base.control.spine.map((angle,index)=>angle+34*rise*[.54,.32,.14][index]+tremor*(index===0?2.1:.55))})];
    }
    if(tipo==='oferecer_e_recusar'){
      const shift=action.segundo_pouso??Math.round((action.inicio+action.fim)/2);
      const facing=action.direcao??1;
      if(frame<shift){
        const peak=action.pouso??Math.round((action.inicio+shift)/2);
        const out=frame<=peak?.5*clamp((frame-action.inicio)/Math.max(1,peak-action.inicio)):
          .5+.5*clamp((frame-peak)/Math.max(1,shift-peak));
        return [gesture(b,neutral,{arms:[null,hand(.36,-1.44,1.08)],tilt:12,pitch:3,
          directions:[null,[0,-.10,facing]]},out,facing)];
      }
      const elapsed=frame-shift;
      const width=action.variacao==='B'?6:10;
      if(elapsed<width){
        const progress=.5*clamp((elapsed+1)/4);
        return [gesture(b,neutral,verbs.mao_no_peito,progress,facing)];
      }
      const withdrawal=elapsed-width;
      const turn=ease(clamp(withdrawal/7));
      const chest=verbs.mao_no_peito.arms[1];
      const away=hand(.56,-1.87,.91);
      const target=chest.map((value,index)=>value+(away[index]-value)*turn);
      return [gesture(b,neutral,{arms:[null,target],tilt:7-18*turn,pitch:10-14*turn,
        directions:[null,[0,-.6*turn,facing*.8]]},.5+.5*clamp((withdrawal-7)/9),facing)];
    }
    if(tipo==='acompanhar_espera'){
      const companion=posture(b,neutral,'olhar_para',.55*pulse(u));
      return [companion,chair(b,26,false)];
    }
    if(tipo==='passo_mao_no_peito'){
      const landing=action.pouso??Math.round((action.inicio+action.fim)/2);
      const step=b.marcha.quadros_por_passo;
      const walkFrame=step*clamp((frame-action.inicio)/Math.max(1,landing-action.inicio));
      const advanced=move(b,rig().walk(b,walkFrame),distancia,direcao);
      return [gesture(b,advanced,verbs.mao_no_peito,.5*clamp(u*2),direcao)];
    }
    if(tipo==='sentar'||tipo==='levantar')return [chair(b,u*(tipo==='sentar'?26:30),tipo==='levantar',distancia)];
    if(tipo==='ajudar_a_levantar')return help(b,u*b.ajuda.fim,{contatoDesenhado:true});
    if(tipo==='sentar_juntos')return [chair(b,u*26,false),chair(b,26,false)];
    if(!verbs[tipo]&&!postures[tipo])throw Error('Ação fora da biblioteca.');
    const landing=action.pouso;
    const progress=landing===undefined?u:frame<landing?
      .5*clamp((frame-action.inicio)/Math.max(1,landing-action.inicio)):
      .5+.5*clamp((frame-landing)/Math.max(1,action.fim-landing));
    const postureKind=tipo==='agachar'&&action.figura==='crianca'?'ajoelhar':tipo;
    const grounded=action.corpo?posture(b,neutral,postureKind,pulse(progress)*(action.amplitude_corpo??1)*(action.variacao==='B'?.72:1)):neutral;
    const hands=verbs[tipo];
    const shaped=hands?gesture(b,grounded,action.corpo?{...hands,lower:0}:hands,progress,direcao):grounded;
    return [move(b,shaped,distancia)];
  }
  function expressive(b,base,action,frame,facing){
    const {tipo,inicio,fim,pouso,gesto}=action;
    const peak=Math.min(fim-4,Math.max(inicio+8,pouso));
    const rising=frame<=peak;
    const toward=ease((frame-inicio)/Math.max(1,peak-inicio));
    const away=ease((fim-1-frame)/Math.max(1,fim-1-peak));
    const phase=rising?toward:action.sustentar?1:away;
    if(gesto.mao==='nenhuma'){
      const kind=tipo==='agachar'&&action.figura==='crianca'?'ajoelhar':tipo;
      const weight=['agachar','ajoelhar','sentar_no_chao','curvar'].includes(kind)?phase:.32*phase;
      return posture(b,base,kind,weight);
    }
    const chestPose=hand(.28,-1.35,.56);
    let spec=verbs[tipo], weight=phase;
    const presence=action.presenca;
    if(presence){
      weight=ease((frame-pouso)/(presence.alcance-pouso))*
        ease((fim-1-frame)/(fim-1-presence.sustenta_ate));
      spec={arms:[null,hand(.54,-1.76,1.12)],directions:[null,[0,-.74,.67*facing]]};
    }
    if(tipo==='mao_no_peito')spec={arms:[null,chestPose],pitch:3,
      directions:[null,[0,-.82,-.42*facing]]};
    if(tipo==='oferecer_e_recusar'){
      const a=ease((frame-inicio)/Math.max(1,pouso-inicio))*(1-ease((frame-pouso)/10));
      const delta=frame-action.segundo_pouso;
      const chest=ease((delta+12)/12)*(1-ease((delta-4)/10));
      const refusal=ease((delta-4)/9)*(1-ease((delta-13)/11));
      weight=Math.min(1,a+.82*(chest+refusal));
      const sum=a+chest+refusal||1;
      const open=hand(.36,-1.44,1.08);
      const closed=chestPose;
      const reject=hand(.53,-1.63,.84);
      const target=open.map((v,i)=>(v*a+closed[i]*chest+reject[i]*refusal)/sum);
      spec={arms:[null,target],pitch:1,directions:[null,[
        0,(-.10*a-.82*chest-.58*refusal)/sum,(a-.42*chest+.80*refusal)*facing/sum]]};
    }
    if(tipo==='conversar'){
      const profiles={
        abrir:{target:hand(.42,-1.25,.82),pitch:-6,direction:[0,-.46,facing*.87]},
        precisar:{target:hand(.38,-1.56,.51),pitch:5,direction:[0,-.61,facing*.48]},
        ponderar:{target:hand(.49,-1.04,.67),pitch:2,direction:[0,.22,facing*.84]},
        recolher:{target:hand(.36,-.76,.47),pitch:10,direction:[0,.37,facing*.49]}
      };
      const shape=profiles[action.perfil_conversa]??
        {target:hand(.38,-1.18,.75),pitch:-3,direction:[0,-.26,facing*.88]};
      spec={arms:[null,shape.target],pitch:shape.pitch,directions:[null,shape.direction]};
    }
    if(tipo==='recusar')spec={arms:[null,hand(.46,-1.40,.76)],pitch:-2,
      directions:[null,[0,-.70,facing*.45]]};
    if(tipo==='ler')spec={...spec,directions:[[0,-.38,facing*.76],[0,-.38,facing*.76]]};
    const gaze=presence?-22*ease((frame-inicio)/Math.max(1,presence.olhar-inicio))*
      ease((fim-1-frame)/(fim-1-presence.sustenta_ate)):0;
    if(!spec || weight<=0&&!gaze)return base;
    if(weight<=0)return rig().pose(b,{...base.control,headPitch:gaze});
    const control=base.control;
    const [x,y,z]=control.pelvis;
    const hands=[...(control.hands??[null,null])];
    const directions=[...(control.handDirections??[null,null])];
    const activeHands=[];
    const armPoles=presence?[null,null]:control.armPoles;
    const reach=b.ossos.braco+b.ossos.antebraco-.035;
    for(const [i,side] of ['E','D'].entries()){
      if(gesto.mao!==side&&gesto.mao!=='ambas')continue;
      const mirrored=gesto.mao===side?spec.arms?.[1-i]:null;
      const local=spec.arms?.[i]??(mirrored&&[-mirrored[0],mirrored[1],mirrored[2]]);
      if(!local)continue;
      const shoulder=base.joints['ombro'+side], wrist=base.joints['punho'+side];
      const desired=action.alvoManual??[x+local[0],y+local[1],z+local[2]*facing];
      const distance=rig().distance(shoulder,desired);
      const factor=distance>reach?reach/distance:1;
      const limited=desired.map((v,k)=>shoulder[k]+(v-shoulder[k])*factor);
      hands[i]=wrist.map((v,k)=>v+(limited[k]-v)*weight);
      activeHands.push(side);
      if(presence){
        const sideSign=i?1:-1;
        armPoles[i]=[sideSign*(.18+.12*weight),weight,(-1+1.20*weight)*facing];
      }
      const direction=spec.directions?.[i]??(presence&&spec.directions?.[1-i]);
      if(direction){
        const rest=[0,.94,.33*facing];
        directions[i]=rest.map((v,k)=>v+(direction[k]-v)*weight);
      }
    }
    return rig().pose(b,{...control,hands,handDirections:directions,armPoles,activeHands,mode:'gesto',
      headPitch:(control.headPitch??0)+(spec.pitch??0)*weight*.55+gaze});
  }

  function prayer(b,base,action,f,facing){
    const {inicio,fim,oracao}=action;
    const weight=ease((f-inicio)/(oracao.palmas-inicio))*
      ease((fim-1-f)/(fim-1-oracao.recolher));
    if(weight<=0)return base;
    const handDirections=[-1,1].map(side=>{
      const rest=[0,.94,.33*facing];
      const direction=[0,-.99,.135*facing+side*.04];
      return rest.map((v,i)=>v+(direction[i]-v)*weight);
    });
    const hands=[-1,1].map((side,i)=>{
      const wrist=base.joints['punho'+(i?'D':'E')];
      const together=[side*.043,-4.16,.91*facing+side*.034];
      return wrist.map((value,j)=>value+(together[j]-value)*weight);
    });
    const armPoles=[[-.64,.81,.25*facing],[.64,.81,.25*facing]];
    return rig().pose(b,{...base.control,hands,handDirections,armPoles,
      headPitch:17*weight,prece:weight,mode:'oracao'});
  }
  function holdHands(b,actor,side,target,facing,weight=1){
    const c=actor.control;
    const index=side==='D'?1:0;
    const hands=[...(c.hands??[null,null])];
    const handDirections=[...(c.handDirections??[null,null])];
    const handContacts=[...(c.handContacts??[null,null])];
    const wrist=actor.joints['punho'+side];
    const grip=[target[0],target[1],target[2]-facing*b.ossos.mao*.76];
    hands[index]=weight===1?target:wrist.map((value,i)=>value+(grip[i]-value)*weight);
    handDirections[index]=[0,.04,facing];
    handContacts[index]=weight===1?'par':null;
    return rig().pose(b,{...c,hands,handDirections,handContacts,facing,mode:'contato'});
  }
  function sequencia(b,plan){
    const {intervalos,distancias,gestos}=plan;
    const fimAjuda=gestos.fim_ajuda;
    const finalHelp=help(b,b.ajuda.fim);
    const chairAt=(f,up)=>chair(b,f,up,distancias.assento);
    const walkAt=f=>walk(b,f,distancias.marcha);
    const smooth=ease;
    const vec=(a,z,t)=>a.map((v,i)=>v+(z[i]-v)*t);
    function upright(c){
      const [a,z]=c.feet.map((foot,i)=>[foot.ankle[0]+(i?-.35:.35),foot.ankle[1],foot.ankle[2]]);
      const knee=4*Math.PI/180,{coxa,canela}=b.ossos;
      const span2=coxa**2+canela**2+2*coxa*canela*Math.cos(knee);
      const mid=vec(a,z,.5);
      mid[1]-=Math.sqrt(span2-rig().distance(a,z)**2/4);
      return mid;
    }
    function comparison(f,index){
      const actor=finalHelp[index],c=actor.control;
      const reach=smooth((f-(gestos.receber-13))/13);
      const offer=smooth((f-gestos.oferecer)/12)*(1-smooth((f-gestos.oferecer-26)/13));
      const rest=smooth((f-fimAjuda)/14);
      const pelvis=vec(c.pelvis,upright(c),rest);
      const [x,y,z]=pelvis;
      const calm=(index?.018:.025)*Math.sin(f*.17+index);
      const near=[-.32,y-1.25,z-.43],far=[.31,y-1.17,z-.18];
      const hands=index?[vec([-.64,y+.20,z],near,reach),vec([.64,y+.20,z],far,reach)]:
        [null,vec([.68,y+.22,z],[.38,y-1.02,z+.82],offer)];
      return rig().pose(b,{...c,pelvis,hands,handContacts:null,groundSeat:false,
        handDirections:index?[[0,-.03,-1],[0,-.03,-1]]:[[0,1,0],[0,-.15,1]],
        spine:[c.spine[0]*(1-rest)+calm,c.spine[1]*(1-rest),c.spine[2]*(1-rest)],headPitch:0,phase:'Comparação',mode:'comparacao'});
    }
    const actions={
      marcha:(t)=>[walkAt(t)],
      transicao_assento:(t,span)=>[bridge(b,walkAt(16),chairAt(0,false),t/span,'Plantar para sentar')],
      sentar:(t)=>[chairAt(Math.min(30,t),false)],
      levantar:(t)=>[chairAt(t,true)],
      aproximar:(t,span,f)=>{
        const actors=help(b,Math.max(0,f-gestos.inicio_ajuda));
        return [bridge(b,chairAt(30,true),actors[0],clamp(t/span),'Dar um passo para ajudar'),actors[1]];
      },
      ajudar:(t,span,f)=>help(b,f-gestos.inicio_ajuda,{contatoDesenhado:true}),
      comparar:(t,span,f)=>[comparison(f,0),comparison(f,1)],
    };
    return {at(frame){
      const f=Math.round(frame);
      const row=intervalos.find(({de,ate})=>de<=f&&(ate===null||f<ate));
      if(!row)return [];
      const {tipo,de,ate}=row;
      return actions[tipo](f-de,ate-de,f);
    }};
  }
  return {resolve,expressive,prayer,settleAfterHelp,stepFrom,care,walk,chair,help,bridge,move,holdHands,sequencia,posture};
})();
