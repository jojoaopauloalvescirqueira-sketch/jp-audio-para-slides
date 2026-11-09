/* Coordenadas em cabeças: x lateral, y para baixo, z para a frente do palco. */
window.PictogramaRig = (() => {
  const {svg,shade}=window.PictogramaFigura;
  const add=(a,b)=>a.map((v,i)=>v+b[i]);
  const sub=(a,b)=>a.map((v,i)=>v-b[i]);
  const scale=(v,k)=>v.map(x=>x*k);
  const mag=v=>Math.hypot(...v);
  const dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
  const unit=v=>scale(v,1/(mag(v)||1));
  const mid=(a,b)=>lerp(a,b,.5);
  const clamp=(x,min=0,max=1)=>Math.max(min,Math.min(max,x));
  const lerp=(a,b,t)=>add(a,scale(sub(b,a),t));
  const radians=a=>a*Math.PI/180;
  const degrees=a=>a*180/Math.PI;
  const smooth=t=>{t=clamp(t);return t*t*(3-2*t);};
  const ease=(f,a,b)=>smooth((f-a)/(b-a));
  const distance=(a,b)=>mag(sub(a,b));

  function solve(a,target,upper,lower,bend){
    const delta=sub(target,a);
    const along=mag(delta)>1e-9?unit(delta):[0,1,0];
    const projected=sub(bend,scale(along,dot(bend,along)));
    const perpendicular=unit(mag(projected)>1e-9?projected:
      sub([1,0,0],scale(along,along[0])));
    const minimum=Math.sqrt(upper**2+lower**2+2*upper*lower*Math.cos(radians(150)));
    const d=clamp(mag(delta),minimum,upper+lower);
    const k=(d*d+upper*upper-lower*lower)/(2*d);
    const joint=add(a,add(scale(along,k),scale(perpendicular,Math.sqrt(Math.max(0,upper**2-k*k)))));
    const end=add(a,scale(along,d));
    const flex=degrees(Math.acos(clamp(dot(unit(sub(joint,a)),unit(sub(end,joint))),-1,1)));
    return {joint,end,flex,residual:distance(target,end)};
  }

  function foot(b,x,z,facing=1,mode='planta',angle=0,lift=0){
    const angleRad=radians(angle);
    const rotate=(y,d)=>[0,y*Math.cos(angleRad)+d*Math.sin(angleRad),
      facing*(d*Math.cos(angleRad)-y*Math.sin(angleRad))];
    const origin=[x,-lift,z];
    const anchor=mode==='calcanhar'?0:b.ossos.calcanhar_planta;
    const heel=add(origin,rotate(0,-anchor));
    const ball=add(origin,rotate(0,b.ossos.calcanhar_planta-anchor));
    const tip=add(ball,[0,mode==='livre'?Math.sin(angleRad)*b.ossos.planta_ponta:0,
      facing*b.ossos.planta_ponta*(mode==='livre'?Math.cos(angleRad):1)]);
    const ankle=add(heel,rotate(-.24,.19));
    return {heel,ball,tip,ankle,anchor:origin,mode,angle};
  }

  function pose(b,input){
    const {ossos:L,massas:M}=b;
    const f=input.facing??1;
    const direction=input.turn??f;
    const kneePole=[Math.sqrt(Math.max(0,1-direction**2)),0,direction];
    const joints={pelve:input.pelvis};
    const bones=[];
    const lengths={};
    function bone(name,parent,end,nominal){
      joints[name]=end;
      bones.push({inicio:parent,fim:name,nominal,real:distance(joints[parent],end)});
      lengths[name]=nominal;
    }
    let angle=0, parent='pelve';
    for(const [i,name] of ['lombar','toracica','cervical'].entries()){
      angle+=input.spine[i];
      bone(name,parent,add(joints[parent],[0,-L[name]*Math.cos(radians(angle)),direction*L[name]*Math.sin(radians(angle))]),L[name]);
      parent=name;
    }
    const neckLean=radians(input.headPitch??angle+(input.headLag??0));
    bone('cabeca','cervical',add(joints.cervical,[0,-L.cabeca*Math.cos(neckLean),direction*L.cabeca*Math.sin(neckLean)]),L.cabeca);
    const angles={lombar:input.spine[0],toracica:input.spine[1],cervical:input.spine[2]};
    const contacts=[];
    const masses=[[joints.pelve,M.pelve],[mid(joints.lombar,joints.toracica),M.torax],[joints.cabeca,M.cabeca]];
    const residuals=[];
    for(const [i,side] of ['E','D'].entries()){
      const sign=i?1:-1;
      const legRoot='quadril'+side;
      joints[legRoot]=add(joints.pelve,[sign*.35,input.pelvisTilt?sign*input.pelvisTilt:0,0]);
      let shoe=input.feet[i];
      let leg=solve(joints[legRoot],shoe.ankle,L.coxa,L.canela,kneePole);
      if(shoe.mode==='livre'){
        for(let tries=0;tries<4;tries++){
          const shin=sub(leg.end,leg.joint);
          const flex=degrees(Math.atan2(-f*shin[2],shin[1]))-shoe.angle-b.angulo_neutro_tornozelo;
          if(flex>=b.limites.tornozelo[0]&&flex<=b.limites.tornozelo[1])break;
          const angle=shoe.angle+flex-clamp(flex,b.limites.tornozelo[0]+1,b.limites.tornozelo[1]-1);
          shoe=foot(b,shoe.anchor[0],shoe.anchor[2],f,'livre',angle,-shoe.anchor[1]);
          leg=solve(joints[legRoot],shoe.ankle,L.coxa,L.canela,kneePole);
        }
      }
      bone('joelho'+side,legRoot,leg.joint,L.coxa);
      bone('tornozelo'+side,'joelho'+side,leg.end,L.canela);
      const correction=sub(leg.end,shoe.ankle);
      joints['calcanhar'+side]=add(shoe.heel,correction);
      bone('planta'+side,'calcanhar'+side,add(shoe.ball,correction),L.calcanhar_planta);
      bone('ponta'+side,'planta'+side,add(shoe.tip,correction),L.planta_ponta);
      angles['joelho'+side]=leg.flex;
      const thigh=sub(leg.joint,joints[legRoot]);
      angles['quadril'+side]=degrees(Math.atan2(f*thigh[2],thigh[1]))-(input.pelvisPitch??0);
      const shin=sub(leg.end,leg.joint);
      angles['tornozelo'+side]=degrees(Math.atan2(-f*shin[2],shin[1]))-shoe.angle-b.angulo_neutro_tornozelo;
      if(shoe.mode!=='livre'){
        const plant=shoe.mode==='calcanhar'?joints['calcanhar'+side]:joints['planta'+side];
        contacts.push({id:'pe'+side,tipo:'chao',fase:shoe.mode,real:plant,alvo:shoe.anchor});
        if(shoe.mode==='planta')contacts.push({id:'sola'+side,tipo:'chao',fase:'planta',
          real:joints['calcanhar'+side],alvo:shoe.heel});
        if(shoe.mode==='planta'||shoe.mode==='ponta')contacts.push({
          id:'ponta'+side,tipo:'chao',fase:'dedos',real:joints['ponta'+side],alvo:shoe.tip
        });
      }
      residuals.push({id:'pe'+side,distancia:leg.residual});
      masses.push([mid(joints[legRoot],leg.joint),M.coxa],[mid(leg.joint,leg.end),M.canela],
        [mid(joints['calcanhar'+side],joints['planta'+side]),M.pe]);
      const clav='ombro'+side;
      const lift=sign*(input.shoulderTilt??0);
      bone(clav,'toracica',add(joints.toracica,[sign*Math.sqrt(L.clavicula**2-lift**2),lift,0]),L.clavicula);
      const swing=(input.armSwing??0)*sign;
      const defaultHand=add(joints[clav],[sign*.035,Math.sqrt(1.75**2-swing*swing),swing*f]);
      const holding=input.handContacts?.[i];
      const intended=input.hands?.[i]??defaultHand;
      const target=holding==='par'?add(intended,[0,0,-f*L.mao*.76]):intended;
      const arm=solve(joints[clav],target,L.braco,L.antebraco,input.armPoles?.[i]??[sign*.18,0,-f]);
      bone('cotovelo'+side,clav,arm.joint,L.braco);
      bone('punho'+side,'cotovelo'+side,arm.end,L.antebraco);
      const handDirection=unit(input.handDirections?.[i]??[0,.94,.33*f]);
      bone('mao'+side,'punho'+side,add(arm.end,scale(handDirection,L.mao)),L.mao);
      if(holding==='par')contacts.push({id:'mao'+side,tipo:'par',
        real:lerp(arm.end,joints['mao'+side],.76),alvo:intended});
      if(holding==='chao'){
        const palmOffset=[0,.22,handDirection[2]*L.mao*.64];
        contacts.push({id:'mao'+side,tipo:'chao',real:add(arm.end,palmOffset),alvo:add(target,palmOffset)});
      }
      residuals.push({id:'mao'+side,distancia:arm.residual});
      angles['cotovelo'+side]=arm.flex;
      masses.push([mid(joints[clav],arm.joint),M.braco],[mid(arm.joint,arm.end),M.antebraco],
        [mid(arm.end,joints['mao'+side]),M.mao]);
    }
    if(input.seat)contacts.push({id:'pelve',tipo:'assento',real:joints.pelve,alvo:input.seat});
    if(input.groundSeat)contacts.push({id:'pelve',tipo:'assento',real:joints.pelve,alvo:input.pelvis});
    const total=masses.reduce((sum,part)=>sum+part[1],0);
    const center=scale(masses.reduce((sum,[p,w])=>add(sum,scale(p,w)),[0,0,0]),1/total);
    return {joints,bones,angles,contacts,center,residuals,facing:f,
      mode:input.mode,phase:input.phase,expected:input.expected,feet:input.feet,control:input};
  }

  function walk(b,f){
    const {quadros_por_passo:n,passo:s,oscilacao:v}=b.marcha;
    const k=Math.floor(f/n), u=(f-k*n)/n;
    const active=k%2;
    const feet=[0,1].map(i=>{
      const x=i?.37:-.37;
      if(i===active){
        if(u<.28)return foot(b,x,k*s,1,'calcanhar',-13*(1-ease(u,0,.28)));
        const push=u>=.72;
        return foot(b,x,k*s+b.ossos.calcanhar_planta,1,push?'ponta':'planta',18*ease(u,.72,1));
      }
      if(u<.18)return foot(b,x,(k-1)*s+b.ossos.calcanhar_planta,1,'ponta',18+12*ease(u,0,.18));
      const t=(u-.18)/.82;
      const angle=30-43*smooth(t);
      const pivotStart=(k-1)*s+b.ossos.calcanhar_planta;
      const pivotEnd=(k+1)*s+b.ossos.calcanhar_planta*Math.cos(radians(13));
      const pivot=pivotStart+(pivotEnd-pivotStart)*smooth(t);
      const clearance=Math.max(0,-b.ossos.calcanhar_planta*Math.sin(radians(angle)))+.26*Math.sin(Math.PI*t);
      return foot(b,x,pivot,1,'livre',angle,clearance);
    });
    const phase=u<.12?'Contato':u<.33?'Amortecimento':u<.72?'Passagem':'Impulso';
    const pelvisZ=(-.24+k+u)*s;
    const tilt=.047*Math.sin((k+u)*Math.PI);
    let pelvisY=-2.86-v*Math.sin(Math.PI*u)+.032*Math.cos(Math.PI*u)**6;
    const legLength=b.ossos.coxa+b.ossos.canela-.001;
    for(const [i,shoe] of feet.entries()){
      if(shoe.mode==='livre')continue;
      const reach=Math.hypot(shoe.ankle[2]-pelvisZ,shoe.ankle[0]-(i?.35:-.35));
      const reachY=Math.sqrt(Math.max(0,legLength**2-reach**2));
      pelvisY=Math.max(pelvisY,shoe.ankle[1]-reachY-(i?tilt:-tilt));
    }
    const sway=Math.cos(2*Math.PI*u);
    return pose(b,{pelvis:[0,pelvisY,pelvisZ],
      pelvisTilt:tilt,shoulderTilt:-.035*Math.sin((k+u)*Math.PI),
      spine:[2+.5*sway,1,.4],pelvisPitch:-10,headPitch:.65*Math.sin(2*Math.PI*u),feet,phase,
      mode:'marcha',expected:f/n*s,armSwing:.63*Math.cos((k+u)*Math.PI)});
  }

  function chair(b,frame,rising,{bracosContinuos=false}={}){
    const duration=30;
    const f=clamp(frame,0,duration);
    const travel=v=>rising?1-ease(v,4,28):ease(v,0,26);
    const t=travel(f);
    const delayed=travel(f-3);
    const pre=rising?ease(f,0,4):0;
    const bend=v=>6+17*Math.sin(Math.PI*v)+8*v;
    const settle=!rising&&f>=26?2.1*Math.sin(Math.PI*clamp((f-26)/4)):0;
    const lean=bend(t)+settle;
    const y=-2.93+1.14*t;
    const z=.30-.58*t;
    const shift=rising?-.065*pre:0;
    const feet=[foot(b,-.37,.34+shift),foot(b,.37,.50)];
    if(rising&&f>0&&f<4)feet[0]=foot(b,-.37,.34+shift,1,'livre',0,.08*Math.sin(f*Math.PI/4));
    const handY=y+.22*(delayed-t);
    const handZ=z-.14*(delayed-t);
    const hands=[[-.38,handY+.08,handZ+.79],[.39,handY+.06,handZ+.88]];
    const pelvis=[0,y,z];
    const input={pelvis,spine:[lean*.52,lean*.32,lean*.16],headLag:bend(delayed)-lean,feet,
      hands:t>.20?hands:null,seat:t>=.999?[0,-1.79,-.28]:null,
      mode:rising?'levantar':'sentar',phase:rising?
        (f<5?'Preparar apoio':f<12?'Inclinar':f<25?'Estender':'Estabilizar'):
        (f<6?'Preparar':f<18?'Descer em arco':f<26?'Aproximar do assento':'Assentar')};
    if(bracosContinuos){
      const base=pose(b,{...input,hands:null});
      input.hands=['E','D'].map((side,i)=>lerp(base.joints['punho'+side],hands[i],ease(t,.10,.55)));
    }
    return pose(b,input);
  }

  function help(b,frame,{contatoDesenhado=false,bracosContinuos=false}={}){
    const {pega,tracao,pouso}=b.ajuda;
    const fim=b.ajuda.fim+(bracosContinuos?8:0);
    const f=clamp(frame,0,fim);
    const prepare=ease(f,0,14), pull=ease(f,tracao,pouso), end=ease(f,pouso,fim);
    const brace=ease(f,tracao,tracao+13);
    const meeting=ease(f,pega-(bracosContinuos?14:6),pega)*(1-ease(f,pouso+3,fim-1));
    const holding=f>=pega&&f<=pouso+3;
    const palmsTouch=holding || (contatoDesenhado && (f===pega-1||f===pouso+4));
    const phase=f<pega?'Preparar os apoios':f<tracao?'Firmar a pega':
      f<tracao+10?'Transferir peso':f<pouso?'Subir com tração':holding?'Estabilizar de mãos dadas':'Separar';
    const grip=[.23,-2.45-.77*pull,-.34];
    const reach=(start,dir)=>lerp(start,bracosContinuos&&!palmsTouch?
      add(grip,[0,0,-dir*b.ossos.mao*.76]):grip,palmsTouch?1:meeting);
    const helperFeet=[foot(b,-.37,-2.04),foot(b,.37,-1.08)];
    const helper=pose(b,{pelvis:[0,-2.72+.32*prepare-.23*pull-.20*end,-1.38-.08*pull],
      spine:[5-15*brace,3-8*brace,2-4*brace],pelvisPitch:-11*pull,feet:helperFeet,
      hands:[null,reach([.68,-2.78,-1.16],1)],handContacts:[null,palmsTouch?'par':null],
      handDirections:[null,[0,.04,1]],phase,mode:'ajudante'});
    const peerFeet=[-1,1].map((sign,i)=>{
      const start=i*6;
      const p=ease(f,start,start+6);
      const initial=.04+i*.13;
      if(f<=start)return foot(b,.37*sign,initial+b.ossos.calcanhar_planta,-1,'calcanhar',-18);
      return foot(b,.37*sign,initial+.33*p,-1,p<1?'livre':'planta',0,.13*Math.sin(Math.PI*p));
    });
    const palmGround=[-.57,-.22,.92];
    const groundLean=9*ease(f,0,4)*(1-ease(f,9,14));
    const peer=pose(b,{facing:-1,pelvis:[0,-.76-1.91*pull-.15*end,1.66-.30*pull-.11*end],
      spine:[17-13*pull+groundLean,9-6*pull+groundLean*.55,5-4*pull],headPitch:4+5*pull,pelvisPitch:22-20*pull,feet:peerFeet,
      hands:[f>=4&&f<=10?palmGround:null,reach([.65,-1.16,1.39],-1)],
      handContacts:[f>=4&&f<=10?'chao':null,palmsTouch?'par':null],
      handDirections:[[0,.34,-.94],[0,.04,-1]],groundSeat:f<=tracao,phase,mode:'ajudado'});
    return [helper,peer];
  }

  function project(p,view,origin=[0,0,0]){
    const yaw=radians(view);
    const horizontal=p[0]*Math.cos(yaw)+p[2]*Math.sin(yaw);
    if(view!==45)return [horizontal,p[1]];
    const delta=sub(p,origin);
    const depth=-delta[0]*Math.sin(yaw)+delta[2]*Math.cos(yaw);
    const factor=12/(12+depth);
    const center=origin[0]*Math.cos(yaw)+origin[2]*Math.sin(yaw);
    const projectedY=p[1]*(1+(factor-1)*smooth((p[1]+3.35)/1.1));
    return [center+(horizontal-center)*factor,projectedY];
  }

  function viewJoints(rig,yaw){
    const camera=v=>project(v,yaw,rig.joints.pelve);
    const p=Object.fromEntries(Object.entries(rig.joints).map(([id,v])=>[id,camera(v)]));
    if(yaw===45&&rig.mode==='repouso'){
      const collar=(p.ombroE[1]+p.ombroD[1])/2;
      for(const [side,compression] of [['E',.86],['D',1]]){
        p['ombro'+side][1]=collar;
        const shoulder=p['ombro'+side];
        for(const name of ['cotovelo','punho','mao']){
          const point=p[name+side];
          point[0]=shoulder[0]+(point[0]-shoulder[0])*compression;
          if(side==='E')point[0]=shoulder[0]+(point[0]-shoulder[0])*.48;
        }
      }
      p.ombroE[0]=p.toracica[0]+.83*(p.ombroE[0]-p.toracica[0]);
    }
    return p;
  }

  function draw(parent,rig,b,options={}){
    const yaw=options.yaw??82;
    const color=options.color??'#9cc6a6';
    const dark=shade(color,.22);
    const camera=v=>project(v,yaw,rig.joints.pelve);
    const p=viewJoints(rig,yaw);
    const g=svg(parent,'g',{'data-rig-anatomico':'sim',transform:options.transform??''});
    const polygon=(a,fill,attributes={})=>svg(g,'path',{d:a,fill,...attributes});
    const fmt=a=>a.map(v=>v.toFixed(4)).join(' ');
    function contour(points,radii,fill,part){
      const normals=points.map((p,i)=>{
        const a=points[Math.max(i-1,0)],z=points[Math.min(i+1,points.length-1)];
        const n=Math.hypot(z[0]-a[0],z[1]-a[1])||1;
        return [-(z[1]-a[1])/n,(z[0]-a[0])/n];
      });
      const rim=sign=>points.map((v,i)=>v.map((x,j)=>x+sign*normals[i][j]*radii[i]));
      function bezier(points){
        return points.slice(0,-1).map((p,i)=>{
          const prev=points[i-1]??p, next=points[i+1], following=points[i+2]??next;
          const c1=p.map((v,k)=>v+(next[k]-prev[k])/6);
          const c2=next.map((v,k)=>v-(following[k]-p[k])/6);
          return `C ${fmt(c1)} ${fmt(c2)} ${fmt(next)}`;
        }).join(' ');
      }
      const a=rim(1),z=rim(-1).reverse();
      const cap=(r,q)=>`A ${r} ${r} 0 0 0 ${fmt(q)}`;
      polygon(`M ${fmt(a[0])} ${bezier(a)} ${cap(radii.at(-1),z[0])} ${bezier(z)} ${cap(radii[0],a[0])}Z`,fill,{'data-massa':part});
    }
    const lerp2=(a,b,t)=>[a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t];
    function footShape(s,ink){
      const heel=p['calcanhar'+s], ball=p['planta'+s], tip=p['ponta'+s],ankle=p['tornozelo'+s];
      if(yaw===0){
        const [x,y]=ball;
        polygon(`M ${x-.088} ${y-.245} Q ${x} ${y-.32} ${x+.09} ${y-.23}
          L ${x+.195} ${y-.075} Q ${x+.219} ${y-.015} ${x+.156} ${y}
          H ${x-.16} Q ${x-.205} ${y-.025} ${x-.18} ${y-.068} Z`,ink,{'data-massa':'pe'+s});
        return;
      }
      const dx=tip[0]>=heel[0]?1:-1;
      const loc=(q,x,y)=>fmt([q[0]+dx*x,q[1]+y]);
      const heelDown=rig.contacts.some(c=>c.id==='pe'+s&&c.fase==='calcanhar');
      const heelBack=heelDown?-.092:0, heelFront=heelDown?.135:0;
      polygon(`M ${loc(heel,heelBack,0)} Q ${loc(heel,-.12,-.04)} ${loc(ankle,-.14,-.02)}
        Q ${loc(ankle,0,-.17)} ${loc(ankle,.10,-.06)}
        Q ${loc(ball,-.17,-.10)} ${loc(ball,0,-.13)} Q ${loc(tip,-.04,-.13)} ${loc(tip,.045,-.04)}
        Q ${loc(tip,.07,0)} ${loc(tip,0,0)} L ${loc(ball,0,0)} Q ${loc(ball,-.22,-.04)} ${loc(heel,heelFront,0)} Z`,
        ink,{'data-massa':'pe'+s});
    }
    function limb(s,ink,leg){
      if(leg){
        const a=p['quadril'+s],k=p['joelho'+s],z=p['tornozelo'+s];
        contour([a,lerp2(a,k,.31),k,lerp2(k,z,.38),z],[.24,.28,.147,.19,.092],ink,'perna'+s);
        footShape(s,s==='E'?dark:ink); return;
      }
      const a=p['ombro'+s],e=p['cotovelo'+s],w=p['punho'+s],h=p['mao'+s];
      const insertion=lerp2(lerp2(a,p.toracica,.15),e,.047);
      contour([insertion,lerp2(a,e,.32),e,lerp2(e,w,.44),w],[.145,.17,.114,.135,.077],ink,'braco'+s);
      if(rig.control.prece){
        const vector=h.map((value,i)=>value-w[i]);
        const length=Math.hypot(...vector)||1;
        const normal=[-vector[1]/length,vector[0]/length];
        const point=(x,y)=>fmt(w.map((value,i)=>value+normal[i]*x+vector[i]*y));
        polygon(`M ${point(-.071,0)} Q ${point(-.087,.27)} ${point(-.112,.42)}
          Q ${point(-.127,.53)} ${point(-.090,.61)} L ${point(-.069,.91)}
          Q ${point(-.061,1.14)} ${point(-.015,1.16)} Q ${point(.034,1.16)} ${point(.041,.94)}
          L ${point(.057,.57)} Q ${point(.107,.43)} ${point(.088,.31)} L ${point(.069,0)} Z`,
          ink,{'data-massa':'mao'+s,'data-palma-oracao':s});
        return;
      }
      contour([w,h],[.077,.094],ink,'mao'+s);
      const wrist=lerp2(w,h,.10),thumb=lerp2(w,h,.56);
      contour([wrist,[thumb[0]+(s==='E'?-.094:.094),thumb[1]-.11]],[.075,.047],ink,'polegar'+s);
    }
    limb('E',dark,false);
    const projection=Math.abs(Math.cos(radians(yaw)));
    const torsoWidths=[.40+.105*projection,.34+.13*projection,.44+.19*projection,.42+.16*projection,.15];
    // Torso and thighs share one paint layer at the hip. The far leg shade starts below the hip.
    contour([p.pelve,p.lombar,lerp2(p.lombar,p.toracica,.68),p.toracica,lerp2(p.toracica,p.cervical,.56)],torsoWidths,color,'tronco');
    limb('E',color,true);limb('D',color,true);
    contour([lerp2(p.toracica,p.cervical,.49),lerp2(p.cervical,p.cabeca,.45)],[.14,.138],color,'pescoco');
    svg(g,'ellipse',{cx:p.cabeca[0],cy:p.cabeca[1],rx:.39,ry:.50,fill:color,'data-massa':'cabeca'});
    limb('D',color,false);
    if(options.exporting)return g;
    const diagnostic=svg(g,'g',{'data-diagnostico':'sim',visibility:options.diagnostic?'visible':'hidden'});
    for(const bone of rig.bones){
      const a=p[bone.inicio],z=p[bone.fim];
      svg(diagnostic,'line',{x1:a[0],y1:a[1],x2:z[0],y2:z[1],stroke:'#f3b95b','stroke-width':.032});
    }
    for(const pt of Object.values(p))svg(diagnostic,'circle',{cx:pt[0],cy:pt[1],r:.033,fill:'#ffe0a0'});
    const c=camera(rig.center);
    svg(diagnostic,'line',{x1:c[0],y1:c[1],x2:c[0],y2:0,stroke:'#55dce6','stroke-width':.026,'stroke-dasharray':'.09 .07'});
    svg(diagnostic,'circle',{cx:c[0],cy:c[1],r:.081,fill:'#55dce6','data-centro':'sim'});
    const support=rig.contacts.filter(t=>t.tipo==='chao'||t.tipo==='assento').map(t=>camera(t.real));
    if(support.length)svg(diagnostic,'line',{x1:Math.min(...support.map(v=>v[0]))-.10,y1:.09,
      x2:Math.max(...support.map(v=>v[0]))+.10,y2:.09,stroke:'#b6ea88','stroke-width':.052,'data-base':'sim'});
    for(const contact of rig.contacts){
      const q=camera(contact.real);
      svg(diagnostic,'rect',{x:q[0]-.058,y:q[1]-.058,width:.116,height:.116,rx:.017,
        fill:'#d7f89a','data-trava':contact.id});
    }
    return g;
  }

  function neutral(b,facing=1){
    const {coxa,canela}=b.ossos;
    const flex=radians(3);
    const span=Math.sqrt(coxa**2+canela**2+2*coxa*canela*Math.cos(flex));
    const z=.14;
    const pelvis=[-.05,-.24-Math.sqrt(span**2-.11**2),z];
    return pose(b,{facing,pelvis,spine:[3,-2,2],
      feet:[foot(b,-.40,z+(.46-.11)*facing,facing),foot(b,.30,z+(.46+.11)*facing,facing)],
      phase:'Repouso',mode:'repouso'});
  }
  return {pose,draw,solve,foot,walk,chair,help,neutral,project,viewJoints,distance};
})();
