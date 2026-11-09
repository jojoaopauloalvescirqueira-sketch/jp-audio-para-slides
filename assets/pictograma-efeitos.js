/* Camada de pintura. O rig e a linha do tempo continuam como fontes da geometria. */
window.PictogramaEfeitos = (api, plan, bible) => {
  const {node, colors, smoothstep}=api;
  const settings=bible.efeitos;
  const linear=c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4;
  const srgb=c=>c<=.0031308?c*12.92:1.055*c**(1/2.4)-.055;
  const shade=color=>'#'+color.slice(1).match(/../g).map(part=>
    Math.round(srgb(linear(parseInt(part,16)/255)*(1-settings.sombra_relativa))*255)
      .toString(16).padStart(2,'0')).join('');
  const indexes=new WeakMap();
  const next=defs=>{
    const index=(indexes.get(defs)??0)+1;
    indexes.set(defs,index);
    return index;
  };
  const defsByRoot=new WeakMap();
  const enabled=()=>new URLSearchParams(location.search).get('efeitos')!=='desligados' &&
    document.querySelector('#alternar-efeitos')?.getAttribute('aria-pressed')!=='false';
  function radial(layer,defs,{x,y,rx,ry,ink,alpha,label}){
    const id='fx-radial-'+next(defs);
    const g=node('radialGradient',{id},defs);
    for(const [offset,opacity] of [[0,alpha],[.55,alpha*.40],[1,0]])
      node('stop',{offset,'stop-color':ink,'stop-opacity':opacity},g);
    return node('ellipse',{cx:x,cy:y,rx,ry,fill:'url(#'+id+')','data-fx':label},layer);
  }
  function envelope(type,f){
    const e=plan.destaques.find(row=>row.tipo===type&&row.inicio<f&&f<row.fim);
    if(!e)return null;
    const u=f<=e.pouso?(f-e.inicio)/(e.pouso-e.inicio):(e.fim-f)/(e.fim-e.pouso);
    return {ink:colors[e.parametros.cor],alpha:e.parametros.intensidade*smoothstep(u),u:smoothstep(u),dim:e.parametros.escurecimento??0};
  }
  function illuminate(layer,defs,f,location,hand,tail){
    if(!enabled())return;
    radial(layer,defs,{x:location[0],y:location[1],rx:305,ry:465,
      ink:colors.acento,alpha:.055,label:'foco_permanente'});
    const highlight=envelope('foco_difuso',f);
    if(highlight)radial(layer,defs,{x:location[0],y:location[1],rx:214,ry:312,
      ...highlight,alpha:highlight.alpha*.62,label:'transformacao'});
    const delivery=envelope('foco_entrega',f);
    if(delivery&&hand){
      radial(layer,defs,{x:hand[0],y:hand[1],rx:125,ry:90,...delivery,label:'entrega'});
      if(tail){
        const glow=delivery.alpha*1.8;
        node('path',{d:`M ${tail[0]} ${tail[1]} Q ${(tail[0]+hand[0])/2} ${Math.min(tail[1],hand[1])-14} ${hand[0]} ${hand[1]}`,
          fill:'none',stroke:delivery.ink,opacity:glow,'stroke-width':9,'stroke-linecap':'round',
          'data-fx':'trajeto_entrega'},layer);
      }
    }
  }
  function dim(layer,f){
    const e=plan.destaques.find(row=>row.tipo==='foco_difuso'&&row.inicio<f&&f<row.fim);
    if(!enabled()||!e?.parametros.escurecimento)return;
    const ramp=Math.min(6,(e.fim-e.inicio)/2);
    const strength=smoothstep(Math.min(1,(f-e.inicio)/ramp,(e.fim-f)/ramp));
    node('rect',{x:-2000,y:-2000,width:6000,height:6000,fill:'#000000',
      opacity:e.parametros.escurecimento*strength,'data-fx':'escurecimento'},layer);
  }
  function shapeLayer(defs,actor,f,primary){
    if(!enabled())return;
    let cache=defsByRoot.get(defs);
    if(!cache){
      cache=new Map();
      defsByRoot.set(defs,cache);
    }
    for(const part of actor.querySelectorAll('[data-massa]')){
      const ink=part.getAttribute('fill');
      if(!cache.has(ink)){
        const id='fx-tonal-'+next(defs);
        const gradient=node('radialGradient',{id,cx:1,cy:1,r:.62},defs);
        node('stop',{offset:.65,'stop-color':shade(ink)},gradient);
        node('stop',{offset:.76,'stop-color':shade(ink),'stop-opacity':.78},gradient);
        node('stop',{offset:.95,'stop-color':shade(ink),'stop-opacity':0},gradient);
        cache.set(ink,id);
      }
      const overlay=part.cloneNode(false);
      overlay.removeAttribute('data-massa');
      overlay.setAttribute('fill','url(#'+cache.get(ink)+')');
      overlay.setAttribute('data-fx-sombra',part.dataset.massa);
      overlay.setAttribute('pointer-events','none');
      part.after(overlay);
    }
    const id='fx-recorte-'+next(defs);
    const filter=node('filter',{id,x:'-20%',y:'-20%',width:'140%',height:'140%',
      'color-interpolation-filters':'linearRGB'},defs);
    const highlight=primary?envelope('foco_difuso',f)?.u??0:0;
    node('feDropShadow',{dx:-.012-.016*highlight,dy:-.012-.016*highlight,
      stdDeviation:.005+.008*highlight,'flood-color':api.colorMix(colors.osso,colors.acento,highlight),'flood-opacity':.075+.052*highlight},filter);
    actor.setAttribute('filter','url(#'+id+')');
  }
  function contact(layer,defs,id,x,y,head,lift=0,opacity=1){
    if(!enabled()||opacity<.04||new URLSearchParams(location.search).get('sombras')==='desligadas')return;
    return radial(layer,defs,{x,y,rx:head*(.31-.14*lift),ry:head*.071,
      ink:'#000000',alpha:(.63-.43*lift)*opacity,label:'contato:'+id});
  }
  return {enabled, illuminate, dim, shapeLayer, contact};
};
