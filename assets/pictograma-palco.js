/* Luz e profundidade do Pictograma, reutilizadas pela folha de modelo e pela cena. */
window.PictogramaPalco = (() => {
  const {svg,shade}=window.PictogramaFigura;
  function gradient(defs,id,type,props,stops){
    const paint=svg(defs,type,{id,...props});
    for(const [offset,ink,opacity=1] of stops)
      svg(paint,'stop',{offset,'stop-color':ink,'stop-opacity':opacity});
    return `url(#${id})`;
  }
  function environment(layer,defs,bible,colors,{width,height,floor,focus,head}){
    const value=bible.luz.fundo_centro[0];
    const center=shade(colors.fundo,-value);
    const ambient=gradient(defs,'ambiente','radialGradient',{
      gradientUnits:'userSpaceOnUse',cx:focus,cy:floor-head*2.4,r:width*.75},
      [[0,center],[.72,colors.fundo],[1,shade(colors.fundo,value)]]);
    svg(layer,'rect',{x:0,y:0,width,height,fill:ambient,'data-ambiente':center});
    const plane=gradient(defs,'plano-chao','linearGradient',{x1:0,y1:0,x2:0,y2:1},
      [[0,colors.linha,0],[.43,colors.linha,.19],[1,colors.linha,.02]]);
    svg(layer,'path',{d:`M 0 ${floor-head*.10} Q ${width/2} ${floor-head*.62} ${width} ${floor-head*.10}
      L ${width} ${floor+head*.55} Q ${width/2} ${floor+head*.82} 0 ${floor+head*.55} Z`,fill:plane});
    const focusPaint=gradient(defs,'foco-chao','radialGradient',{},
      [[0,colors.acento,.11],[.59,colors.acento,.036],[1,colors.acento,0]]);
    svg(layer,'ellipse',{cx:focus,cy:floor,rx:head*2.45,ry:head*.27,fill:focusPaint});
  }
  function contact(parent,defs,bible,id,x,y,rx,ry,altitude=0){
    if(!defs.querySelector('#sombra-contato')){
      gradient(defs,'sombra-contato','radialGradient',{},[[0,'#000000',1],[.56,'#000000',.67],[1,'#000000',0]]);
    }
    const alpha=bible.luz.sombra_contato[0]*(1-.82*altitude);
    return svg(parent,'ellipse',{cx:x,cy:y,rx:rx*(1-.22*altitude),ry,fill:'url(#sombra-contato)',
      opacity:alpha,'data-sombra-contato':id});
  }
  function bench(parent,defs,bible,{x,floor,height,colors,id='banco',comprimento=null,pernas=[.15,.80]}){
    const unit=height/bible.canon.cabecas;
    const top=floor-bible.objetos.banco.altura_h[0]*height;
    const depth=comprimento??height*bible.objetos.banco.profundidade_min_h*1.22;
    const edge=x+depth;
    const base=svg(parent,'g',{'data-elemento':id,'data-objeto':'banco',
      'data-borda':edge,'data-profundidade':depth,'data-chao-y':floor});
    const paint=gradient(defs,'madeira-banco','linearGradient',{x1:0,y1:0,x2:1,y2:1},
      [[.56,colors.suave],[.58,shade(colors.suave,bible.luz.reducao_luminancia[0])]]);
    contact(base,defs,bible,id,x+depth/2,floor,depth*.53,unit*.10);
    for(const p of pernas.map(pos=>x+depth*pos)){
      svg(base,'rect',{x:p,y:top+unit*.10,width:unit*.19,height:floor-top-unit*.10,rx:unit*.075,
        fill:paint});
    }
    svg(base,'rect',{x,y:top,width:depth,height:unit*.20,rx:unit*.075,fill:paint,'data-parte':'assento'});
    return {base,top,edge,depth};
  }
  return {environment,contact,bench};
})();
