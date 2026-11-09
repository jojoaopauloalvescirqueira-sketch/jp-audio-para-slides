/* Confere juntas e contornos do kit que usa a bíblia do Pictograma. */
window.auditarProporcoes = (bible, flag, options = {}) => {
  const {canon,poses,luz,objetos,auditoria}=bible;
  const {gap,contour,luminosity,luminanceRatio}=window.PictogramaFigura;
  const previous=new Map(), table=[];
  const rect=el=>el.getBoundingClientRect();
  const point=el=>{
    const p=new DOMPoint(+el.getAttribute('cx'),+el.getAttribute('cy')).matrixTransform(el.getScreenCTM());
    return [p.x,p.y];
  };
  const warn=(code,frame,id,fix)=>flag(code,frame,id,fix);
  const finite=value=>Number.isFinite(value);
  const spans=(positions,projection)=>['E','D'].flatMap(side=>[
    gap(positions['ombro'+side],positions['cotovelo'+side]),
    gap(positions['cotovelo'+side],positions['mao'+side])/projection,
    gap(positions['quadril'+side],positions['joelho'+side]),
    gap(positions['joelho'+side],positions['tornozelo'+side])
  ]);
  async function inspect(root,frame,scene){
    const groups=[...root.querySelectorAll('[data-figura-rig]')].filter(g=>(+g.getAttribute('opacity')||0)>.52);
    const backgrounds=[...root.querySelectorAll('[data-ambiente]')].map(n=>n.dataset.ambiente);
    const floor=root.querySelector('[data-parte=piso]');
    const supportY=floor?rect(floor).top:options.floor;
    for(const g of groups){
      const id=g.dataset.elemento,state=g.dataset.pose,h=+g.dataset.canonH;
      const camera=g.closest('[data-zoom]');
      const zoom=camera?+camera.dataset.zoom:1;
      const matrix=g.getScreenCTM(), shown=Math.hypot(matrix.a,matrix.b), expected=h*shown;
      const positions=Object.fromEntries([...g.querySelectorAll('[data-articulacao]')]
        .map(el=>[el.dataset.articulacao,point(el)]));
      const headEl=g.querySelector('[data-parte=cabeca]');
      const head=2*(+headEl.getAttribute('ry'))*Math.hypot(headEl.getScreenCTM().a,headEl.getScreenCTM().b);
      const targetHeads=g.dataset.crianca==='sim'?bible.crianca.cabecas[0]:canon.cabecas;
      const visible=await contour(g,Math.min(4,320/h));
      const proportion=visible.height/h;
      const legs=(supportY-positions.quadril[1])/expected;
      const torso=gap(positions.quadril,positions.pescoco)/expected;
      const targetTorso=1-canon.quadril_ao_chao-(bible.forma.torso_inicio_cabeca*.70+.15)/targetHeads;
      const projection=Number(g.dataset.projecaoAntebraco??1);
      const limbs=spans(positions,projection).map(value=>value/shown);
      const calibratedScale=expected/zoom;
      options.mark?.('EC-006',frame,id);
      if(![h,head,shown,zoom,proportion,legs,torso,...limbs].every(finite) || head<=0 || expected<=0 ||
          Math.abs(expected/head/targetHeads-1)>auditoria.altura_tolerancia ||
          (state==='em_pe'&&Math.abs(visible.height/h-1)>auditoria.altura_tolerancia))
        warn('altura_em_cabecas',frame,id,'Use o cânone escolhido na cabeça e no contorno em pé.');
      if(Math.abs(torso-targetTorso)>auditoria.razao_tolerancia ||
          (state==='em_pe'&&(Math.abs(legs-canon.quadril_ao_chao)>auditoria.razao_tolerancia ||
            ['E','D'].some(side=>Math.abs((supportY-positions['joelho'+side][1])/expected-canon.joelho_ao_chao)>auditoria.razao_tolerancia))))
        warn('razao_corpo',frame,id,'Corrija a relação entre pernas, tronco e altura.');
      const prior=previous.get(id);
      if(prior)options.mark?.('EC-007',frame,id);
      if(prior&&Math.abs(calibratedScale/prior.scale-1)>auditoria.escala_delta)
        warn('escala_sem_camera',frame,id,'Preserve a escala da figura; registre aproximações na câmera.');
      if(prior && g.dataset.encurtamento!=='sim')options.mark?.('EC-034',frame,id);
      if(!Number.isFinite(projection)||projection<.45||projection>1||
          (prior&&g.dataset.encurtamento!=='sim'&&limbs.some((value,i)=>Math.abs(value/prior.limbs[i]-1)>auditoria.membro_delta)))
        warn('membro_muda_comprimento',frame,id,'Mantenha o comprimento do braço e da perna entre quadros.');
      previous.set(id,{scale:calibratedScale,limbs});
      if(['sentado','sentado_no_chao','ajoelhado'].includes(state)){
        options.mark?.('EC-005',frame,id);
        const [,low,high]=poses[state].altura_relativa;
        if(proportion<low||proportion>high)
          warn('pose_fora_da_altura',frame,id,'Respeite a altura canônica da pose no contorno desenhado.');
      }
      if(state==='sentado'){
        const seat=root.querySelector('[data-parte=assento]'), box=seat&&rect(seat);
        const [hipX,hipY]=positions.quadril, hipRadius=+g.dataset.quadrilRaio*shown;
        const right=(g.dataset.orientacao??'direita')==='direita';
        if(!box || hipX<box.left || hipX>box.right || Math.abs(hipY+hipRadius-box.top)>8 ||
            ['E','D'].some(side=>right?positions['joelho'+side][0]<box.right:positions['joelho'+side][0]>box.left))
          warn('sentar_sem_apoio',frame,id,'Apoie o quadril e deixe os joelhos além da borda do assento.');
      }
      if(state==='sentado_no_chao'||state==='ajoelhado'){
        const hips=positions.quadril[1]+(+g.dataset.quadrilRaio)*shown;
        const kneeBottom=Math.max(positions.joelhoE[1],positions.joelhoD[1])+bible.forma.apoio_joelho_h*expected;
        const contact=state==='sentado_no_chao'?hips:kneeBottom;
        if(Math.abs(contact-supportY)>8)
          warn('pose_sem_contato',frame,id,'Coloque o quadril ou o joelho no plano do chão.');
      }
      const contourBase=new DOMPoint(0,visible.bottom).matrixTransform(matrix).y;
      if(finite(supportY))options.mark?.('EC-001',frame,id);
      if(finite(supportY)&&contourBase>supportY+3)
        warn('contorno_atravessa_chao',frame,id,'Mantenha o contorno desenhado acima do chão.');
      if(finite(supportY)&&Math.abs(contourBase-supportY)<=5 && !root.querySelector('[data-sombra-contato="'+id+'"]'))
        warn('sombra_contato_ausente',frame,id,'Desenhe a sombra suave no ponto de contato.');
      const ink=g.dataset.cor;
      const gradient=root.querySelector('#luz-'+(g.dataset.pintura??id));
      if(gradient){
        const direction=(Math.atan2(+gradient.getAttribute('y2')-(+gradient.getAttribute('y1')),
          +gradient.getAttribute('x2')-(+gradient.getAttribute('x1')))*180/Math.PI+360)%360;
        const shadow=gradient.dataset.sombra;
        const dark=1-luminosity(shadow)/luminosity(ink);
        const [,low,high]=luz.reducao_luminancia;
        if(Math.abs(direction-luz.direcao_graus)>.5||dark<low||dark>high)
          warn('sombra_propria_incoerente',frame,id,'A sombra deve seguir a luz do projeto e a diferença da bíblia.');
        if(backgrounds.some(bg=>luminanceRatio(bg,shadow)<luz.contraste_figura))
          warn('contraste_figura',frame,id,'Eleve o contraste da silhueta com o fundo iluminado.');
      }
      table.push({quadro:frame,cena:scene,id,pose:state,altura_contorno_px:visible.height*shown,
        altura_relativa:proportion,altura_em_cabecas:expected/head,pernas_relativo:legs,tronco_relativo:torso,
        escala:calibratedScale,zoom,pontos:positions});
    }
    const primary=groups.find(g=>g.dataset.principal==='sim')||groups[0];
    if(!primary)return;
    const stageScale=Math.hypot(primary.getScreenCTM().a,primary.getScreenCTM().b);
    const actorHeight=+primary.dataset.canonH*stageScale;
    const head=actorHeight/canon.cabecas;
    for(const object of root.querySelectorAll('[data-objeto]')){
      const name=object.dataset.objeto;
      if(name==='banco'){
        const seat=object.querySelector('[data-parte=assento]');
        const box=rect(seat);
        const [,low,high]=objetos.banco.altura_h;
        const relative=(supportY-box.top)/actorHeight;
        if(relative<low||relative>high||box.width<actorHeight*objetos.banco.profundidade_min_h)
          warn('escala_banco',frame,name,'Use a altura e a profundidade canônicas do assento.');
        if(!object.querySelector('[data-sombra-contato]'))
          warn('sombra_contato_ausente',frame,name,'Desenhe a sombra do banco junto ao piso.');
      }else if(name==='simbolo'){
        const box=rect(object);
        if(Math.max(box.width,box.height)<head*objetos.simbolo_min_cabeca)
          warn('simbolo_pequeno',frame,object.dataset.elemento,'Amplie o símbolo para pelo menos 0,8 cabeça.');
      }else if(name==='seta'){
        if(+object.dataset.traco*stageScale+1e-6<head*objetos.seta_traco_min_cabeca ||
            +object.dataset.ponta*stageScale+1e-6<head*objetos.seta_ponta_min_cabeca)
          warn('escala_seta',frame,'seta','Use traço e ponta no peso da bíblia.');
      }
    }
    for(const title of root.querySelectorAll('[data-titulo], [data-legenda]')){
      if(title.getAttribute('visibility')==='hidden')continue;
      const color=title.getAttribute('fill');
      if(color?.startsWith('#')&&backgrounds.some(bg=>luminanceRatio(bg,color)<luz.contraste_texto))
        warn('contraste_texto',frame,scene,'Use contraste de pelo menos 7:1 no texto legível.');
    }
  }
  return {inspect,table};
};
