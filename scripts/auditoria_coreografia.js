/* Verificações específicas da composição coreografada. Coordenadas em pixels do palco. */
window.auditoriaCoreografia = (data, flag, opacity, visibleText, region, mark = () => {}) => {
  const {cues} = data.coreografia;
  const threshold = data.dimensoes[1] * .30;
  const previous = new Map();
  let held = 0, stopped = 0, started = false, rise = false, owner, deliveryHold = 0;
  const close = (a,b) => a && b && Math.hypot(a[0]-b[0],a[1]-b[1]) <= 5;
  const words = s => s.toUpperCase().match(/[\p{L}\p{N}]+/gu) || [];
  const stage = () => document.getElementById('palco');
  const colorDistance = (a,b) => Math.max(...[1,3,5].map(i=>Math.abs(parseInt(a.slice(i,i+2),16)-parseInt(b.slice(i,i+2),16))));
  const center = el => {
    if (!el) return null;
    const [x,y,w,h] = region(el);
    return [x+w/2,y+h/2];
  };
  const palm = (id,side='D') => {
    const actor=stage().querySelector('[data-elemento="'+id+'"]');
    const point=actor?.querySelector('[data-articulacao=mao'+side+']');
    if(!point)return center(actor?.querySelector('[data-parte=mao]'));
    const p=new DOMPoint(+point.getAttribute('cx'),+point.getAttribute('cy')).matrixTransform(point.getScreenCTM());
    return [p.x,p.y];
  };
  const emit = (code,f,id,text) => flag(code,f,id,text);
  return (f, id, last) => {
    const stageEl = stage();
    const neg = stageEl.querySelector('[data-negacao]');
    const a = [...stageEl.querySelectorAll('[data-letra]')].find(el=>el.dataset.letra===(data.coreografia.encenacao?.texto.depois??'A'));
    if(f>=cues.negacao.frame+2 && f<cues.virada.frame+6) {
      mark('EC-024',f,id);
      if(!neg || opacity(neg)<.65 || visibleText(neg)!==(data.coreografia.encenacao?.texto.negacao??'NÃO').toUpperCase())
        emit('negacao_perdida',f,id,'Preserve o NÃO até o A verde estar legível.');
      if(f>=cues.virada.frame-10 && !neg?.querySelector('[data-risco]'))
        emit('negacao_sem_risco',f,id,'Risque o NÃO antes de retirá-lo.');
    }
    if(f===cues.virada.frame+6 && (!a || region(a)[2]<45 || a.querySelector('text')?.getAttribute('fill')!==data.paleta.acento))
      emit('letra_sem_leitura',f,id,'Conclua a virada com o A verde em tamanho de leitura.');
    const titles = [...stageEl.querySelectorAll('text:not([data-legenda])')]
      .filter(el=>opacity(el)>.35).flatMap(el=>words(visibleText(el)));
    const captions = [...stageEl.querySelectorAll('[data-legenda]')].flatMap(el=>words(visibleText(el)));
    if(titles.length>=3 && captions.length>=3)mark('EC-026',f,id);
    for(let i=0;i+2<titles.length;i++)
      if(captions.some((_,j)=>titles.slice(i,i+3).every((w,k)=>w===captions[j+k])))
        emit('texto_duplicado',f,id,'Retire sequências de três palavras repetidas na legenda.');
    const actors=[...stageEl.querySelectorAll('[data-persistente]')];
    const seat=stageEl.querySelector('[data-parte=assento]');
    const floor=stageEl.querySelector('[data-parte=piso]');
    const crosses=(path,target,margin)=>{
      if(!target || opacity(target)<.5)return false;
      const [x,y,w,h]=region(target);
      const length=path.getTotalLength(), matrix=path.getScreenCTM();
      const targetMatrix=target.getScreenCTM().inverse();
      const origin=path.getPointAtLength(0), end=path.getPointAtLength(length);
      const normal=length?[-(end.y-origin.y)/length,(end.x-origin.x)/length]:[0,0];
      const startRadius=+path.dataset.raioInicial||0, endRadius=+path.dataset.raioFinal||0;
      for(let l=4;l<length;l+=5){
        if(startRadius&&target===seat){
          const center=path.getPointAtLength(l);
          const r=startRadius+(endRadius-startRadius)*l/length;
          if([-1,1].some(side=>target.isPointInFill(new DOMPoint(center.x+side*r*normal[0],
            center.y+side*r*normal[1]).matrixTransform(matrix).matrixTransform(targetMatrix))))return true;
        }
        const p=path.getPointAtLength(l).matrixTransform(matrix);
        if(p.x<=x+margin || p.x>=x+w-margin || p.y<=y+margin || p.y>=y+h-margin)
          continue;
        const offsets=[[margin,0],[-margin,0],[0,margin],[0,-margin]];
        if(offsets.every(([dx,dy])=>target.isPointInFill(new DOMPoint(p.x+dx,p.y+dy).matrixTransform(targetMatrix))))
          return true;
      }
      return false;
    };
    for (const el of actors) {
      if(opacity(el)<.40) continue;
      const name=el.dataset.elemento;
      const hip=new DOMPoint(0,0).matrixTransform(el.getScreenCTM());
      const before=previous.get(name);
      const painted=el.querySelector('[data-parte=tronco]')?.getAttribute('fill');
      const ink=painted?.startsWith('#')?painted:el.dataset.cor;
      if(before)mark('EC-018',f,name);
      if(before && Math.hypot(hip.x-before.x,hip.y-before.y)>40)
        emit('salto_entre_quadros',f,name,'Distribua a trajetória, inclusive entre cenas.');
      if(before && colorDistance(ink,before.ink)>32)
        emit('cor_abrupta',f,name,'Mantenha a cor do personagem ou faça uma transição gradual.');
      previous.set(name,{x:hip.x,y:hip.y,ink});
      const radius=Number(el.dataset.quadrilRaio)*Math.abs(el.getScreenCTM().d);
      if(el.dataset.pose==='sentado' || el.dataset.pose==='sentado_no_chao'){
        mark('EC-004',f,name);
        const support=el.dataset.pose==='sentado'?seat:floor;
        const [sx,sy,sw]=support?region(support):[0,-1000,0];
        if(!support || opacity(support)<.5 || hip.x<sx || hip.x>sx+sw || Math.abs(sy-hip.y-radius)>9)
          emit('quadril_sem_apoio',f,name,'Apoie o quadril no chão ou no assento durante a pose.');
      }
      const peer=actors.find(other=>other!==el && opacity(other)>.65);
      const torso=peer?.querySelector('[data-parte=tronco]');
      for(const path of el.querySelectorAll(el.dataset.figuraRig==='sim'?
          'path[data-eixo=braco],path[data-eixo=antebraco],path[data-eixo=canela]':
          'path[data-parte=braco],path[data-parte=canela]')){
        if(seat && opacity(seat)>=.5)mark('EC-002',f,name);
        const supportCrossing=crosses(path,seat,3);
        const actorCrossing=crosses(path,torso,19);
        if(supportCrossing || actorCrossing){
          const part=path.dataset.eixo||path.dataset.parte;
          emit('segmento_atravessa',f,name,`${part}: evite cruzar ${supportCrossing?'o assento':'o tronco da outra figura'}.`);
        }
      }
      if(el.dataset.principal==='sim' && region(el)[3]<threshold)
        emit('figura_pequena',f,name,'Enquadre a figura em pelo menos 30% da altura.');
    }
    const help=stageEl.querySelector('[data-ajuda-de]');
    if(help) {
      const left=stageEl.querySelector('[data-elemento="agente"] [data-parte="cabeca"]');
      const right=stageEl.querySelector('[data-elemento="outro"] [data-parte="cabeca"]');
      if(left && right && opacity(right)>.5 && center(left)[0]>=center(right)[0])
        emit('lado_da_ajuda',f,id,'Mantenha o ajudante à esquerda e o receptor à direita.');
      const contact=close(palm('agente'),palm('outro',help.dataset.maoOutro??'D'));
      if(help.dataset.pausa==='sim') stopped++;
      if(help.dataset.contatoEsperado==='sim')mark('EC-016',f,id);
      if(help.dataset.contatoEsperado==='sim' && !contact)
        emit('maos_sem_contato',f,id,'Junte as duas mãos durante o apoio.');
      if(help.dataset.tracao==='sim' && !started){
        started=true;
        if(held<4 || stopped<4 || stopped>6)
          emit('ritmo_contato',f,id,'Pare por 4–6 quadros e sustente quatro quadros de contato antes de puxar.');
      }
      if(!started) held=contact?held+1:0;
      if(help.dataset.subida==='sim' && !rise){
        rise=true;
        mark('EC-014',f,id);
        if(!started || held<4 || !contact)
          emit('subida_precoce',f,id,'Faça a tração após contato sustentado e só então eleve o receptor.');
      }
    }
    const token=stageEl.querySelector('[data-entrega]');
    if(token){
      const next=token.dataset.dono;
      const hands=close(palm('agente'),palm('outro',token.dataset.maoReceptora??'D'));
      if(token.dataset.modoEntrega==='trajeto'){
        if((!owner&&next!=='agente') ||
          (owner&&next!==owner && !((owner==='agente'&&next==='trajeto')||(owner==='trajeto'&&next==='outro'))))
          emit('entrega_antes_do_contato',f,id,'Mostre o coração saindo do ajudante, em trânsito e depois pousando nas palmas.');
      }else if(owner && next!==owner && (deliveryHold<4 || !hands))
        emit('entrega_antes_do_contato',f,id,'Transfira somente após quatro quadros de mãos em contato.');
      deliveryHold=hands?deliveryHold+1:0;
      owner=next;
    }
    if(last && ((!data.rig_anatomico&&(!started || !rise)) || owner!=='outro'))
      emit('gesto_incompleto',f,id,'Mostre contato, tração e subida dentro do trecho.');
  };
};
