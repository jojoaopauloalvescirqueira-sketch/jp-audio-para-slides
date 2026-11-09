/* Cada entrada reproduz um defeito na medição ou na forma que o auditor consome. */
window.testarMutacoesAnatomicas=()=>{
  const {avaliar}=window.AuditoriaAnatomica;
  const base=window.ensaioRig;
  const frame=(d,phase,i,actor=0)=>d.sequences[phase][i][actor];
  const foot=(d,phase,i)=>frame(d,phase,i).contacts.find(c=>/^pe/.test(c.id));
  const cases=[
    ['EC-043',d=>foot(d,'marcha',6).real[2]-=.15],
    ['EC-044',d=>foot(d,'marcha',5).real[2]+=.15],
    ['EC-045',d=>foot(d,'sentar',8).real[2]+=.10],
    ['EC-046',d=>foot(d,'marcha',5).real[1]+=.10],
    ['EC-047',d=>frame(d,'marcha',31).joints.pelve[2]=frame(d,'marcha',0).joints.pelve[2]],
    ['EC-048',d=>{for(let i=25;i<49;i++)frame(d,'ajuda',i,1).joints.pelve[1]=frame(d,'ajuda',24,1).joints.pelve[1];}],
    ['EC-049',d=>Object.assign(frame(d,'ajuda',41).angles,{lombar:10,toracica:8})],
    ['EC-050',d=>Object.assign(frame(d,'sentar',14).angles,{lombar:25,toracica:0,cervical:0})],
    ['EC-051',d=>frame(d,'ajuda',19,1).joints.toracica=frame(d,'ajuda',19).joints.toracica.slice()],
    ['EC-052',null,'tronco','M-.62 -4.9 H.62 V-2.7 H-.62Z',0],
    ['EC-053',null,'bracoE','M -1 -2 H -.6 V -1 H -1 Z',0],
    ['EC-054',null,'pescoco',null,0],
    ['EC-055',null,'pernaE','M-.26 -3.1 H.26 V-.2 H-.26Z',90],
    ['EC-056',null,'polegarE',null,0],
    ['EC-057',null,'peE','M-.65 -.05 H0 V0 H-.65Z',0],
    ['EC-058',d=>frame(d,'marcha',7).joints.punhoE[0]-=.90],
    ['EC-059',d=>frame(d,'marcha',7).angles.joelhoE=-5],
    ['EC-060',d=>frame(d,'marcha',7).joints.joelhoE[1]+=.17],
    ['EC-061',d=>frame(d,'sentar',15).center[2]+=1.4],
    ['EC-062',d=>d.neutral[0].joints.joelhoE[1]-=.27],
    ['EC-063',null,'pernaE','#665142',0,'fill'],
    ['EC-064',null,'tronco','M-.65 -4.72 H.65 V-3.9 H.33 V-3.1 H.50 V-2.5 H-.50 V-3.1 H-.33 V-3.9 H-.65 Z',0],
    ['EC-065',null,'peE','M-.38 -.22 H-.24 V0 H-.38 Z',0],
    ['EC-066',d=>d.neutral[0].joints.ombroD[2]+=.58],
    ['EC-067',d=>frame(d,'marcha',7).joints.toracica[2]+=.25],
    ['EC-068',d=>frame(d,'marcha',7).joints.cabeca[2]+=.12],
    ['EC-069',d=>d.sequences.marcha.forEach(([p])=>{p.joints.punhoD[2]=p.joints.pelve[2]-.45;})],
    ['EC-070',d=>Object.values(frame(d,'ajuda',19,1).joints).forEach(point=>{point[2]-=1.65;})],
    ['EC-071',d=>{
      // Same mathematical contact, displaced into a body and hidden in the rendered view.
      for(const actor of d.sequences.ajuda[19]){
        const c=actor.contacts.find(c=>c.tipo==='par');
        c.real=d.sequences.ajuda[19][1].joints.toracica.slice();
        c.alvo=c.real.slice();
      }
    },null,null,null,null,d=>{
      for(let i=0;i<21;i++)for(const p of d.sequences.ajuda[i])p.contacts=p.contacts.filter(c=>c.tipo!=='par');
    }],
    ['EC-072',d=>{d.neutral[0].angles.joelhoD=13;}],
  ];
  const initial=avaliar(base,document);
  return cases.map(([id,mutate,part,shape,yaw,attribute='d',secondMutation])=>{
    const data=structuredClone(base);
    let saved;
    let el;
    let parent;
    let next;
    if(mutate)mutate(data);
    else {
      el=document.querySelector(`[data-ensaio=anatomia][data-yaw="${yaw}"][data-personagem="0"] [data-massa="${part}"]`);
      saved=el.getAttribute(attribute);
      parent=el.parentElement;
      next=el.nextSibling;
      if(shape===null)el.remove();
      else el.setAttribute(attribute,shape);
    }
    const errors=avaliar(data,document,{pixels:id==='EC-070'||id==='EC-071'}).issues;
    if(el){
      if(shape===null)parent.insertBefore(el,next);
      else el.setAttribute(attribute,saved);
    }
    const detected=list=>list.some(r=>r.codigo===id&&r.nivel==='bloqueante');
    let second=true;
    if(secondMutation){
      const short=structuredClone(base);
      secondMutation(short);
      second=detected(avaliar(short,document,{pixels:false}).issues);
    }
    return {id,ok:!initial.issues.some(r=>r.codigo===id)&&detected(errors)&&second};
  });
};
