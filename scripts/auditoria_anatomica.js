/* Verifica as poses do solver e os contornos efetivamente desenhados na folha. */
window.AuditoriaAnatomica=(()=>{
  const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
  const supports=p=>p.contacts.filter(c=>c.tipo==='chao'||c.tipo==='assento');
  const zBounds=rows=>[Math.min(...rows.map(c=>c.real[2])),Math.max(...rows.map(c=>c.real[2]))];
  const sid=name=>name.replace(/[ED]$/,'');
  const sides=['E','D'];
  const has=(actor,part)=>actor.querySelector('[data-massa="'+part+'"]');

  function contorno(actor,pose,yaw,mark){
    const p=window.PictogramaRig.viewJoints(pose,yaw);
    const torso=has(actor,'tronco');
    const width=(shape,y,x)=>{
      if(!shape)return 0;
      let count=0;
      for(let u=-.85;u<=.85;u+=.015)
        if(shape.isPointInFill(new DOMPoint(x+u,y)))count++;
      return count*.015;
    };
    if(pose.mode==='repouso'&&yaw===0){
      const chest=width(torso,p.toracica[1]+.14,p.toracica[0]);
      const waist=width(torso,p.lombar[1],p.lombar[0]);
      const pelvis=width(torso,p.pelve[1]-.08,p.pelve[0]);
      mark('EC-052',chest>waist+.08&&pelvis>waist+.015,{chest,waist,pelvis});
      const continuous=sides.every(side=>{
        const leg=has(actor,'perna'+side), hip=new DOMPoint(...p['quadril'+side]);
        return !!leg&&leg.getAttribute('fill')===torso?.getAttribute('fill')&&
          torso.isPointInFill(hip)&&leg.isPointInFill(hip);
      });
      mark('EC-063',continuous);
      mark('EC-064',waist/chest>=.72&&waist/chest<=.76,{ratio:waist/chest});
      const widths=sides.map(side=>has(actor,'pe'+side)?.getBBox().width??0);
      mark('EC-065',widths.every(w=>w>=.32),{widths});
      mark('EC-053',sides.every(s=>p['ombro'+s][1]<p.lombar[1]-.40&&
        has(actor,'braco'+s)?.isPointInFill(new DOMPoint(...p['ombro'+s]))));
      const neck=has(actor,'pescoco'),head=has(actor,'cabeca');
      const gap=(torso&&head)?torso.getBBox().y-(head.getBBox().y+head.getBBox().height):0;
      mark('EC-054',neck&&gap>=.06&&gap<=.42,{gap});
      mark('EC-056',sides.every(s=>has(actor,'polegar'+s)?.getBBox().height>.08&&
        distance(p['punho'+s],p['mao'+s])>.25));
      mark('EC-057',sides.every(s=>has(actor,'pe'+s)?.getBBox().height>.15));
    }
    if(pose.mode==='repouso'&&yaw===45){
      const lengths=['ombro','quadril'].map(part=>{
        const left=pose.joints[part+'E'],right=pose.joints[part+'D'];
        return Math.abs(p[part+'E'][0]-p[part+'D'][0])/Math.abs(left[0]-right[0]);
      });
      const far=Math.abs(p.ombroE[0]-p.toracica[0]),near=Math.abs(p.ombroD[0]-p.toracica[0]);
      const line=Math.abs(p.ombroE[1]-p.ombroD[1]);
      mark('EC-066',lengths.every(k=>k>.60&&k<.80)&&far<near*.94&&line<1e-6,{lengths,far,near,line});
    }
    if(pose.mode==='repouso'&&yaw===90){
      mark('EC-055',sides.every(s=>{
        const leg=has(actor,'perna'+s);
        const sample=(a,z,k)=>a.map((v,i)=>v+(z[i]-v)*k);
        const thigh=sample(p['quadril'+s],p['joelho'+s],.31);
        const calf=sample(p['joelho'+s],p['tornozelo'+s],.38);
        const knee=p['joelho'+s];
        return width(leg,...[thigh[1],thigh[0]])>width(leg,knee[1],knee[0])+.08 &&
          width(leg,calf[1],calf[0])>width(leg,p['tornozelo'+s][1]-.04,p['tornozelo'+s][0])+.08;
      }));
    }
  }

  // Use the production SVG paths as alpha masks, independent of joint-to-joint distance.
  function gripPixels(actors, b, doc){
    const yaw=82, scale=64, width=384,height=405;
    const svg=doc.createElementNS('http://www.w3.org/2000/svg','svg');
    const canvas=new OffscreenCanvas(width,height);
    const context=canvas.getContext('2d',{willReadFrequently:true});
    const parts=[];
    for(const actor of actors){
      const shape=window.PictogramaRig.draw(svg,actor,b,{yaw});
      parts.push([...shape.querySelectorAll('[data-massa]')]);
    }
    const paint=(nodes)=>{
      context.resetTransform();
      context.clearRect(0,0,width,height);
      context.setTransform(scale,0,0,scale,width/2,height-12);
      for(const node of nodes){
        if(node.tagName==='ellipse'){
          const n=k=>+node.getAttribute(k);
          context.beginPath();
          context.ellipse(n('cx'),n('cy'),n('rx'),n('ry'),0,0,2*Math.PI);
          context.fill();
        }else{
          context.fill(new Path2D(node.getAttribute('d')));
        }
      }
      return context.getImageData(0,0,width,height).data;
    };
    const contact=actors[0].contacts.find(c=>c.tipo==='par');
    if(!contact)return null;
    const [x,y]=window.PictogramaRig.project(contact.real,yaw);
    const cx=Math.round(width/2+scale*x),cy=Math.round(height-12+scale*y);
    const isHand=n=>/^(mao|polegar)[ED]$/.test(n.dataset.massa);
    const hands=parts.map(nodes=>paint(nodes.filter(isHand)));
    const bodies=parts.map(nodes=>paint(nodes.filter(n=>!isHand(n))));
    let crossing=0, meet=0;
    const r=b.ossos.mao*.8*scale;
    for(let i=0;i<width*height;i++){
      const a=i*4+3;
      const h0=hands[0][a]>=160,h1=hands[1][a]>=160;
      const b0=bodies[0][a]>=160,b1=bodies[1][a]>=160;
      if(!(b0||h0)||!(b1||h1))continue;
      const near=(i%width-cx)**2+(Math.floor(i/width)-cy)**2<=r*r;
      if(h0&&h1&&!b0&&!b1&&near)meet++;
      else crossing++;
    }
    const i=(cy*width+cx)*4+3;
    return {overlapOutsideHandPx:crossing,sharedHandPx:meet,occludedByBody:bodies.some(m=>m[i]>128),
      contactBetween:actors[0].joints.toracica[2]+.35<contact.real[2]&&
        contact.real[2]<actors[1].joints.toracica[2]-.35,maskPxPerHead:scale};
  }

  function avaliar(data,doc,{pixels=true}={}){

    const {sequences,bible:b}=data, issues=[], checks={}, samples={};
    const px=b.apoio.pix_por_cabeca;
    let section='folha anatômica', frame=0;
    const proportions=[];
    function mark(code,ok,info={}){
      const check=checks[code]??={n:0,falhas:0};
      check.n++;
      if(ok)return;
      check.falhas++;
      issues.push({codigo:code,nivel:'bloqueante',ensaio:section,quadro:frame,detalhe:info});
    }
    if(doc){
      for(const svg of doc.querySelectorAll('svg[data-ensaio=anatomia]')){
        const yaw=+svg.dataset.yaw;
        const i=+svg.dataset.personagem;
        contorno(svg.querySelector('[data-rig-anatomico]'),data.neutral[i],yaw,mark);
      }
    }
    for(const p of data.neutral){
      for(const side of sides){
        const thigh=distance(p.joints['quadril'+side],p.joints['joelho'+side]);
        const shin=distance(p.joints['joelho'+side],p.joints['tornozelo'+side]);
        const ratio=thigh/shin, knee=-p.joints['joelho'+side][1]/b.altura;
        mark('EC-062',ratio>=1.13&&ratio<=1.17&&knee>=.25&&knee<=.28,{ratio,knee});
        const flex=p.angles['joelho'+side];
        mark('EC-072',flex>=0&&flex<=5,{side,flex});
        proportions.push({ratio,knee,flex});
      }
    }
    samples.proporcoes=proportions;
    for(const [name,frames] of Object.entries(sequences)){
      section=name;
      const last=new Map();
      let maxDrift=0, maxFloor=0, minimumMargin=Infinity;
      const final=frames.at(-1)[0], first=frames[0][0];
      if(name==='marcha'){
        const advance=Math.abs(final.joints.pelve[2]-first.joints.pelve[2]);
        mark('EC-047',advance>=final.expected*b.apoio.avanço_minimo,{advance,planned:final.expected});
        const heights=frames.map(([p])=>p.center[1]);
        const amplitude=Math.max(...heights)-Math.min(...heights);
        mark('EC-047',amplitude/b.altura>=.02&&amplitude/b.altura<=.03,{amplitude});
        const loading=frames.filter((_,i)=>i%b.marcha.quadros_por_passo===4)
          .map(([p])=>p.angles[p.feet[0].mode==='calcanhar'?'joelhoE':'joelhoD']);
        const swing=frames.flatMap(([p])=>sides.flatMap((side,i)=>p.feet[i].mode==='livre'?[p.angles['joelho'+side]]:[]));
        const angle=(a,z)=>Math.atan2(z[2]-a[2],a[1]-z[1])*180/Math.PI;
        const trunk=frames.map(([p])=>angle(p.joints.pelve,p.joints.toracica));
        const head=frames.map(([p])=>angle(p.joints.cervical,p.joints.cabeca));
        const trunkMax=Math.max(...trunk.map(Math.abs));
        const headRange=Math.max(...head)-Math.min(...head);
        mark('EC-067',trunkMax<=5,{trunkMax});
        mark('EC-068',headRange<=3&&Math.max(...head.map(Math.abs))<=3,{headRange});
        const arm=sides.map(side=>frames.map(([p])=>p.joints['punho'+side][2]-p.joints.pelve[2]));
        const opposite=[0,b.marcha.quadros_por_passo].every((i,j)=>
          arm[j][i]<-.23&&arm[1-j][i]>.23);
        mark('EC-069',opposite&&arm.every(w=>Math.min(...w)<-.23&&Math.max(...w)>.23),{opposite});
        samples.marcha={advance,planned:final.expected,amplitude,loadingKneeDeg:loading,
          swingKneePeakDeg:Math.max(...swing),trunkMax,headRange};

      }
      let pullVelocities=[];
      const gripMasks=[];
      if(name==='ajuda'){
        const {tracao:begin,pouso:end}=b.ajuda;
        const held=frames.slice(0,begin).map(actors=>actors.every(p=>p.contacts.some(c=>c.tipo==='par')));
        const holdCount=held.length-1-held.lastIndexOf(false);
        const total=(frames.length-1)/30;
        mark('EC-071',total>=1.5&&total<=2.5&&holdCount>=8,{holdCount,total});
        samples.ajuda={holdCount,total};
        const phase=frames.slice(begin,end+1).map(pair=>pair[1].joints.pelve[1]);
        pullVelocities=phase.slice(1).map((y,i)=>(phase[i]-y)*30);
        const peak=Math.max(...pullVelocities), when=pullVelocities.indexOf(peak);
        mark('EC-048',end-begin>=18&&end-begin<=30&&when>=3&&when<pullVelocities.length-3&&
          pullVelocities[0]<peak*.35&&pullVelocities.at(-1)<peak*.35&&pullVelocities.every(v=>v>0),
          {peak,when});
      }
      for(const [i,actors] of frames.entries()){
        frame=i;
        for(const [actor,p] of actors.entries()){
          for(const bone of p.bones){
            const measured=distance(p.joints[bone.inicio],p.joints[bone.fim]);
            mark('EC-060',bone.nominal>0&&Math.abs(measured/bone.nominal-1)<=.01,{bone:bone.fim,measured,nominal:bone.nominal});
          }
          for(const [joint,angle] of Object.entries(p.angles)){
            const [lo,hi]=b.limites[sid(joint)];
            mark('EC-059',Number.isFinite(angle)&&angle>=lo-1e-6&&angle<=hi+1e-6,{joint,angle,lo,hi});
          }
          const bend=['lombar','toracica','cervical'].map(key=>Math.abs(p.angles[key]));
          const total=bend.reduce((a,z)=>a+z,0);
          if(total>=12)mark('EC-050',Math.max(...bend)/total<=.72&&bend.filter(x=>x>=2).length>=2,{bend});
          const currentKeys=new Set();
          for(const c of p.contacts){
            const key=actor+':'+c.id+':'+c.fase;
            currentKeys.add(key);
            const error=distance(c.real,c.alvo)*px;
            if(c.tipo==='chao'&&/^(pe|sola|ponta)/.test(c.id)){
              const floor=Math.abs(c.real[1])*px;
              mark('EC-046',floor<=2,{id:c.id,pix:floor});
              maxFloor=Math.max(maxFloor,floor);
            }
            const previous=last.get(key);
            const drift=previous?distance(c.real,previous)*px:0;
            if(!previous)last.set(key,c.real);
            if(c.tipo==='chao'&&/^(pe|sola|ponta)/.test(c.id)){
              maxDrift=Math.max(maxDrift,drift);
              const code=name==='sentar'?'EC-045':'EC-044';
              mark(code,Math.max(drift,error)<=2,{id:c.id,drift,error});
              if(name==='marcha'){
                const progress=i? p.joints.pelve[2]-frames[i-1][actor].joints.pelve[2]:0;
                const delta=previous?c.real[2]-previous[2]:0;
                mark('EC-043',!(Math.abs(delta)*px>2&&delta*progress<0),{delta,progress});
              }
            }else{
              mark(c.tipo==='par'?'EC-048':'EC-061',error<=2&&
                (c.tipo==='par'||drift<=2),{id:c.id,drift,error});
            }
          }
          for(const key of last.keys())
            if(key.startsWith(actor+':')&&!currentKeys.has(key))last.delete(key);
          if(p.mode==='marcha'||p.mode==='repouso'){
            const tight=sides.every(s=>Math.abs(p.joints['punho'+s][0]-p.joints.pelve[0])<=.95);
            mark('EC-058',tight);
          }
          const paired=actors.length===2&&actors.every(person=>person.contacts.some(c=>c.tipo==='par'));
          if(paired&&actor!==0)continue;
          const people=paired?actors:[p];
          const support=people.flatMap(supports);
          const center=people.reduce((acc,v)=>acc+v.center[2],0)/people.length;
          const old=frames[Math.max(0,i-1)];
          const prior=paired?old.reduce((acc,v)=>acc+v.center[2],0)/old.length:old[actor].center[2];
          const dynamic=name==='marcha'||(name==='ajuda'&&i<b.ajuda.pouso+4);
          const velocity=i?(center-prior)*30:0;
          const forecast=dynamic?Math.sign(velocity)*Math.min(Math.abs(velocity)*.13,.30):0;
          const n=b.marcha.quadros_por_passo;
          const landing=(Math.floor(i/n)+1)*n;
          const next=name==='marcha'?[
            ...window.PictogramaRig.walk(b,landing).contacts.filter(c=>c.fase==='calcanhar'),
            ...window.PictogramaRig.walk(b,landing+Math.ceil(n*.28)).contacts.filter(c=>c.fase==='dedos')
          ]:[];
          const [lo,hi]=zBounds([...support,...next]);
          // Expand only by the physical contact patch of the foot, hand or seat.
          const edge=support.some(c=>c.tipo==='assento')?.38:.18;
          const margin=Math.min(center+forecast-lo+edge,hi+edge-center-forecast);
          minimumMargin=Math.min(minimumMargin,margin);
          mark('EC-061',support.length>0&&margin>=0,{center,forecast,margin});
        }
        if(name==='ajuda'){
          const [h,g]=actors;
          const separation=Math.abs(h.joints.toracica[2]-g.joints.toracica[2]);
          mark('EC-051',separation>=.80,{separation});
          const a=h.contacts.find(c=>c.tipo==='par'),z=g.contacts.find(c=>c.tipo==='par');
          if(a||z)mark('EC-048',a&&z&&distance(a.real,z.real)*px<=2);
          if(a&&z&&doc&&pixels){
            const result=gripPixels(actors,b,doc);
            gripMasks.push({frame:i,...result});
            mark('EC-070',result.overlapOutsideHandPx<=3,result);
            mark('EC-071',result.sharedHandPx>=10&&!result.occludedByBody&&result.contactBetween,result);
          }
          if(i>=b.ajuda.tracao+13&&i<=b.ajuda.pouso-2){
            const base=Math.abs(h.feet[0].anchor[2]-h.feet[1].anchor[2]);
            const lean=h.angles.lombar+h.angles.toracica;
            mark('EC-049',base>=.70&&lean<-2&&sides.every(s=>h.angles['joelho'+s]>=15),{base,lean});
          }
        }
      }
      samples[name]={...samples[name],maxDrift,maxFloor,minimumMargin,...(pullVelocities.length?{pullVelocities,gripMasks}:{})};
    }
    return {issues,checks,samples};
  }

  return {avaliar,contorno,gripPixels};
})();
