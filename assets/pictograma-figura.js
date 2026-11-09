/* Rig vetorial em unidades da altura em pé. A bíblia fornece as proporções. */
window.PictogramaFigura = (() => {
  const NS='http://www.w3.org/2000/svg';
  const clamp=(u,lo=0,hi=1)=>Math.min(hi,Math.max(lo,u));
  const mix=(a,b,u)=>a+(b-a)*u;
  const blend=(a,b,u)=>[mix(a[0],b[0],u),mix(a[1],b[1],u)];
  const length=([x,y])=>Math.hypot(x,y);
  const gap=(a,b)=>length([b[0]-a[0],b[1]-a[1]]);
  const vector=(p,q)=>[q[0]-p[0],q[1]-p[1]];
  const translate=(a,b)=>[a[0]+b[0],a[1]+b[1]];
  const scale=(p,k)=>p.map(v=>v*k);
  const rad=a=>a*Math.PI/180;
  const rotate=([x,y],a)=>[x*Math.cos(a)-y*Math.sin(a),x*Math.sin(a)+y*Math.cos(a)];
  const svg=(parent,tag,attrs={})=>{
    const el=document.createElementNS(NS,tag);
    for (const [key,value] of Object.entries(attrs)) el.setAttribute(key,value);
    parent.append(el);
    return el;
  };

  function joint(start,target,upper,lower,bend){
    const delta=vector(start,target);
    const unit=scale(delta,1/(length(delta)||1));
    const d=clamp(length(delta),Math.abs(upper-lower)+.001,upper+lower-.001);
    const along=(d*d+upper*upper-lower*lower)/(2*d);
    const away=Math.sqrt(Math.max(0,upper*upper-along*along))*bend;
    return [translate(start,translate(scale(unit,along),[-unit[1]*away,unit[0]*away])),
            translate(start,scale(unit,d))];
  }

  const linear=value=>value<=.04045?value/12.92:((value+.055)/1.055)**2.4;
  const rgb=hex=>hex.slice(1).match(/../g).map(value=>parseInt(value,16)/255);
  const luminosity=hex=>rgb(hex).map(linear).reduce((sum,value,i)=>sum+value*[.2126,.7152,.0722][i],0);
  const luminanceRatio=(a,b)=>(Math.max(luminosity(a),luminosity(b))+.05)/(Math.min(luminosity(a),luminosity(b))+.05);
  function shade(hex,reduction){
    return '#'+rgb(hex).map(value=>{
      const v=linear(value)*(1-reduction);
      const channel=v<=.0031308?12.92*v:1.055*v**(1/2.4)-.055;
      return Math.round(channel*255).toString(16).padStart(2,'0');
    }).join('');
  }
  function ink(defs,id,color,bible){
    const darker=shade(color,bible.luz.reducao_luminancia[0]);
    const theta=rad(bible.luz.direcao_graus);
    const x=Math.cos(theta)/2,y=Math.sin(theta)/2;
    const gradient=svg(defs,'linearGradient',{id,x1:.5-x,y1:.5-y,x2:.5+x,y2:.5+y,
      'data-luz':'sim','data-base':color,'data-sombra':darker});
    for(const [offset,fill] of [[.52,color],[.65,darker]])
      svg(gradient,'stop',{offset,'stop-color':fill});
    return {fill:`url(#${id})`, dark:darker};
  }
  function tapered(parent,a,b,diameters,fill,part){
    const d=vector(a,b), len=length(d);
    const [r,s]=diameters.map(value=>value/2);
    const normal=[-d[1]/len,d[0]/len];
    const p=(c,radius)=>translate(c,scale(normal,radius)).join(' ');
    svg(parent,'path',{d:`M ${p(a,-r)} L ${p(b,-s)} A ${s} ${s} 0 0 1 ${p(b,s)}
      L ${p(a,r)} A ${r} ${r} 0 0 1 ${p(a,-r)} Z`,fill,'data-parte':part});
    // The narrow, invisible axis lets the auditor test limb intersections independently of stroke width.
    svg(parent,'path',{d:`M ${a.join(' ')} L ${b.join(' ')}`,fill:'none',stroke:'none',
      'data-eixo':part});
  }

  function anatomy(bible,height,child=false){
    const c=bible.canon;
    const h=child?height*bible.crianca.altura_relativa[0]:height;
    const head=h/(child?bible.crianca.cabecas[0]:c.cabecas);
    const f=bible.forma;
    return {h,head,hip:h*c.quadril_ao_chao,knee:h*c.joelho_ao_chao,ankle:h*f.altura_tornozelo_h,
      shoulders:head*c.ombros,hips:head*c.quadris,arm:head*c.braco,palm:head*c.mao,foot:head*c.pe,
      torso:h*(1-c.quadril_ao_chao)-head*f.torso_inicio_cabeca};
  }

  function pose(bible,a,name,x,floor,parameters={}){
    const {h,hip,ankle,foot}=a;
    const f=bible.forma, p=bible.poses;
    const ankleY=floor-ankle;
    const facing=parameters.facing??1;
    const xy=(u,v=ankleY)=>[x+u*h*facing,v];
    let y=floor-hip, angle=0, feet=[xy(-.101),xy(.064)], arms=[null,null], kneeOverride;
    switch(name){
    case 'sentado':
      y=(parameters.seat??floor-bible.objetos.banco.altura_h[0]*h)-f.encaixe_quadril_h*h;
      angle=p.sentado.inclinacao;
      feet=[xy(.29),xy(.33)];
      arms=[xy(.17,y+hip*.10),xy(.24,y+hip*.10)];
      break;
    case 'sentado_no_chao':
      y=floor-f.apoio_chao_h*h;
      angle=p.sentado_no_chao.inclinacao;
      feet=[xy(.345),xy(.386)];
      arms=[xy(-.14,floor-.05*h),xy(.225,floor-.06*h)];
      break;
    case 'ajoelhado':
      y=floor-f.quadril_ajoelhado_h*h;
      angle=p.ajoelhado.inclinacao;
      const kneeY=floor-f.apoio_joelho_h*h;
      const upper=a.hip-a.knee, lower=a.knee-a.ankle+h*f.folga_joelho_h;
      const kneeX=x-h*f.quadril_hinge_h+facing*Math.sqrt(Math.max(0,upper**2-(kneeY-y)**2));
      const ankleX=kneeX-facing*Math.sqrt(lower**2-(ankleY-kneeY)**2);
      feet=[[ankleX,ankleY],xy(.27)];
      kneeOverride=[kneeX,kneeY];
      arms=[xy(-.04,y+.037*h),xy(.23,y-.024*h)];
      break;
    case 'inclinado':
      y+=.035*h;
      angle=p.inclinado.inclinacao[0];
      feet=[xy(.032),xy(.112)];
      arms=[xy(.11,y+hip*.33),xy(.31,y+hip*.30)];
      break;
    case 'andando': {
      const step=p.andando.passada[0]/2;
      const phase=parameters.phase??.20;
      const swing=Math.sin(phase*Math.PI*2), lift=Math.cos(phase*Math.PI*2);
      feet=[xy(-step*swing,ankleY-h*f.passo_altura_h*Math.max(0,lift)),
            xy(step*swing,ankleY-h*f.passo_altura_h*Math.max(0,-lift))];
      y+=h*(.031-.014*Math.abs(lift));
      angle=7;
      arms=[xy(.22*swing,y+.08*h),xy(-.22*swing,y+.08*h)];
      break;
    }
    }
    return {name,x,y,angle:angle*facing,feet,arms,foot,facing,kneeOverride};
  }

  function relaxed(bible,a,state){
    const {x,y,angle}=state;
    const side=a.shoulders/2-a.h*bible.forma.ombro_insercao_h;
    return [-1,1].map((direction,i)=>translate([x,y],translate(rotate([direction*side,-a.torso],rad(angle)),
      [(i?.22:-.30)*a.arm,(i?.96:.91)*a.arm])));
  }

  function draw(parent,defs,bible,info){
    const a=anatomy(bible,info.height,info.child);
    const {h,head}=a, f=bible.forma;
    const {name,x,y,angle,feet,arms,facing,kneeOverride}=info.pose;
    const g=svg(parent,'g',{'data-elemento':info.id,'data-persistente':'sim','data-pose':name,
      'data-canon-h':h,'data-pintura':info.paintId??info.id,'data-orientacao':facing<0?'esquerda':'direita','data-crianca':info.child?'sim':'nao','data-figura-rig':'sim','data-cor':info.color,opacity:info.opacity??1,
      'data-chao':info.floorId??'chao','data-principal':info.primary?'sim':'nao',
      'data-quadril-raio':h*(name==='sentado_no_chao'?f.apoio_chao_h:f.encaixe_quadril_h),transform:`translate(${x} ${y})`,
      ...(info.support?{'data-apoio':info.support}:{})});
    if(info.forearmProjection && info.forearmProjection!==1)
      g.dataset.projecaoAntebraco=info.forearmProjection;
    const material=ink(defs,'luz-'+(info.paintId??info.id),info.color,bible);
    const tor=rad(angle), lean=rad(angle+(info.headLag??0));
    const expression=bible.expressao[info.expression??'neutro'];
    const breath=info.breath??0;
    const hip=[0,0], spine=rotate([0,-a.torso+breath],tor);
    const skull=rotate([0,-(h-a.hip-head/2)+breath],lean);
    const headAngle=angle+(info.headLag??0)+expression.cabeca_graus*facing;
    const neck=blend(skull,spine,.70);
    const shoulders=[-1,1].map(i=>translate(spine,rotate([i*(a.shoulders/2-h*f.ombro_insercao_h),0],
      tor+rad(expression.ombros_graus))));
    const contrapposto=name==='em_pe'?rad(bible.poses.em_pe.inclinacao_quadril[0]*facing):0;
    const hips=[-1,1].map(i=>rotate([i*h*f.quadril_hinge_h,0],contrapposto));
    const upper=a.hip-a.knee, lower=a.knee-a.ankle+h*f.folga_joelho_h;
    const knees=[], ankles=[], soles=[], elbows=[], hands=[];
    function leg(i, layer){
      const goal=vector([x,y],feet[i]);
      const side=name==='em_pe'&&i===0 ? 1 : -1;
      const [knee,ankle]=i===0&&kneeOverride?[vector([x,y],kneeOverride),goal]:
        joint(hips[i],goal,upper,lower,side*facing);
      knees[i]=knee; ankles[i]=ankle;
      const ink=i?material.fill:material.dark;
      const peH=f.pe_espessura_h*h;
      const center=[ankle[0]+a.foot*.20*facing,ankle[1]+a.ankle-peH/2];
      soles[i]=[center[0],center[1]+peH/2];
      const thigh=scale(f.coxa_diametros_h,h);
      if(name==='sentado_no_chao'||name==='erguendo')
        thigh[0]=Math.min(thigh[0],f.apoio_chao_h*h*1.85);
      tapered(layer,hips[i],knee,thigh,ink,'coxa');
      tapered(layer,knee,ankle,scale(f.canela_diametros_h,h),ink,'canela');
      svg(layer,'ellipse',{cx:center[0],cy:center[1],rx:a.foot/2,ry:peH/2,
        fill:ink,'data-parte':'pe'});
    }
    function arm(i, layer){
      const shoulder=shoulders[i];
      const target=arms[i]?vector([x,y],arms[i]):translate(shoulder,[(i?.22:-.30)*a.arm,(i?.96:.91)*a.arm]);
      const part=f.braco_fracao_superior, ink=i?material.fill:material.dark;
      const [elbow,hand]=joint(shoulder,target,a.arm*part,a.arm*(1-part)*(info.forearmProjection??1),(i?1:-1)*(info.receivingRig?-1:1));
      elbows[i]=elbow; hands[i]=hand;
      tapered(layer,shoulder,elbow,scale(f.braco_diametros_h,h),ink,'braco');
      tapered(layer,elbow,hand,scale(f.antebraco_diametros_h,h),ink,'antebraco');
      svg(layer,'circle',{cx:hand[0],cy:hand[1],r:a.palm/2,fill:ink,
        'data-parte':i===1?'mao':'mao_secundaria'});
    }
    const far=svg(g,'g');
    leg(0,far); arm(0,far);
    leg(1,g);
    const torso=svg(g,'g',{transform:`rotate(${angle})`});
    const o=a.shoulders/2, q=a.hips/2, w=q*f.cintura_sobre_quadris, top=-a.torso+breath;
    const shoulder = info.contour ?
      `M 0 ${top-h*.066} C ${o*.34} ${top-h*.066} ${o*.78} ${top-h*.038} ${o*.91} ${top+h*.032}
      C ${o*.99} ${top+h*.088} ${w*.99} ${top*.43} ${w} ${top*.28}
      Q ${q*1.04} ${top*.11} ${q*.91} ${h*f.encaixe_quadril_h*.15}
      Q 0 ${h*f.encaixe_quadril_h*1.82} ${-q*.91} ${h*f.encaixe_quadril_h*.15}
      Q ${-q*1.04} ${top*.11} ${-w} ${top*.28}
      C ${-w*.99} ${top*.43} ${-o*.99} ${top+h*.088} ${-o*.91} ${top+h*.032}
      C ${-o*.78} ${top-h*.038} ${-o*.34} ${top-h*.066} 0 ${top-h*.066} Z` :
      `M 0 ${top-h*.034} C ${o*.65} ${top-h*.034} ${o} ${top-h*.025} ${o} ${top+h*.023}
      C ${o*.93} ${top+h*.093} ${w} ${top*.43} ${w} ${top*.28}
      Q ${q*1.04} ${top*.11} ${q*.91} ${h*f.encaixe_quadril_h*.15}
      Q 0 ${h*f.encaixe_quadril_h*1.82} ${-q*.91} ${h*f.encaixe_quadril_h*.15}
      Q ${-q*1.04} ${top*.11} ${-w} ${top*.28}
      C ${-w} ${top*.43} ${-o*.93} ${top+h*.093} ${-o} ${top+h*.023}
      C ${-o} ${top-h*.025} ${-o*.65} ${top-h*.034} 0 ${top-h*.034} Z`;
    svg(torso,'path',{d:shoulder,fill:material.fill,'data-parte':'tronco'});
    svg(g,'ellipse',{cx:neck[0],cy:neck[1],rx:h*f.pescoco_diametro_h/2,ry:h*f.pescoco_altura_h/2+(info.contour?h*.022:0),
      fill:material.fill,...(info.contour?{'data-parte':'pescoco'}:{}),transform:`rotate(${angle} ${neck.join(' ')})`});
    const face=svg(g,'ellipse',{cx:skull[0],cy:skull[1],rx:head*f.oval_cabeca/2,ry:head/2,
      fill:material.fill,transform:`rotate(${headAngle} ${skull.join(' ')})`,'data-parte':'cabeca'});
    arm(1,g);
    const point=(id,coordinates)=>svg(g,'circle',{cx:coordinates[0],cy:coordinates[1],r:0,
      'data-articulacao':id});
    for(const [key,value] of Object.entries({topo:[skull[0],skull[1]-head/2],pescoco:neck,
      quadril:hip,ombroE:shoulders[0],ombroD:shoulders[1],cotoveloE:elbows[0],cotoveloD:elbows[1],
      maoE:hands[0],maoD:hands[1],quadrilE:hips[0],quadrilD:hips[1],joelhoE:knees[0],
      joelhoD:knees[1],tornozeloE:ankles[0],tornozeloD:ankles[1],peE:soles[0],peD:soles[1]}))point(key,value);
    return {g,face,hands:hands.map(p=>translate([x,y],p)),soles:soles.map(p=>translate([x,y],p))};
  }
  async function contour(group, resolution=4){
    const frame=group.getBBox();
    const box=[frame.x-2,frame.y-2,Math.ceil(frame.width+4),Math.ceil(frame.height+4)];
    const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
    svg.setAttribute('viewBox',box.join(' '));
    svg.setAttribute('width',Math.ceil(box[2]*resolution));
    svg.setAttribute('height',Math.ceil(box[3]*resolution));
    const shape=group.cloneNode(true);
    shape.removeAttribute('transform');
    shape.removeAttribute('opacity');
    shape.querySelectorAll('[data-articulacao],[data-eixo]').forEach(el=>el.remove());
    shape.querySelectorAll('[fill]').forEach(el=>el.setAttribute('fill','#FFFFFF'));
    svg.append(shape);
    const src=URL.createObjectURL(new Blob([new XMLSerializer().serializeToString(svg)],{type:'image/svg+xml'}));
    try{
      const img=new Image();
      img.src=src;
      await img.decode();
      const canvas=document.createElement('canvas');
      canvas.width=img.width;canvas.height=img.height;
      const ctx=canvas.getContext('2d',{willReadFrequently:true});
      ctx.drawImage(img,0,0);
      const rgba=ctx.getImageData(0,0,canvas.width,canvas.height).data;
      let top=canvas.height,bottom=-1;
      for(let i=3;i<rgba.length;i+=4)if(rgba[i]>160){
        const row=Math.floor(i/4/canvas.width);
        top=Math.min(top,row);
        bottom=Math.max(bottom,row);
      }
      if(bottom<0) throw new Error('Contorno do personagem sem pixels visíveis.');
      return {top:box[1]+top/resolution,bottom:box[1]+(bottom+1)/resolution,height:(bottom-top+1)/resolution};
    }finally{URL.revokeObjectURL(src);}
  }
  return {anatomy,pose,draw,svg,shade,luminosity,luminanceRatio,blend,gap,contour,relaxed};
})();
