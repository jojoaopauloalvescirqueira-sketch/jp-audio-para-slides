(async () => {
  const source=document.querySelector('#modelo');
  if(!source)return;
  const {bible,colors}=JSON.parse(source.textContent);
  const {anatomy,pose,draw,svg,contour}=PictogramaFigura;
  const {environment,bench,contact}=PictogramaPalco;
  const names={em_pe:'Em pé',inclinado:'Inclinado',andando:'Passo',sentado:'Banco',
    sentado_no_chao:'Chão',ajoelhado:'Ajoelhado'};
  const height=190,floor=228,width=222,frame=245;
  const create=(parent,tag,value)=>{
    const el=document.createElement(tag);
    if(value)el.textContent=value;
    parent.append(el);
    return el;
  };
  const metrics=[];
  for(const [role,color,expression] of [['Agente',colors.acento,'disposto'],['Outra figura',colors.osso,'neutro']]){
    const section=create(document.querySelector('#poses'),'section');
    create(section,'h2',role);
    const grid=create(section,'div');
    grid.className='grid';
    for(const [name,title] of Object.entries(names)){
      const card=create(grid,'figure');
      const stage=svg(card,'svg',{viewBox:`0 0 ${width} ${frame}`,'aria-label':title});
      const defs=svg(stage,'defs');
      const background=svg(stage,'g');
      stage.dataset.poseModelo=name;
      const a=anatomy(bible,height);
      environment(background,defs,bible,colors,{width,height:frame,floor,focus:109,head:a.head});
      for(let i=0;i<=Math.floor(height/a.head);i++){
        const y=floor-i*a.head;
        svg(stage,'line',{x1:17,y1:y,x2:214,y2:y,stroke:colors.suave,'stroke-opacity':i===0?.45:.18,...(i===0?{'data-parte':'piso'}:{})});
        svg(stage,'text',{x:4,y:y+3,'font-size':9,fill:colors.suave}).textContent=i;
      }
      const x=['sentado','sentado_no_chao'].includes(name)?77:106;
      const id=role==='Agente'?'agente':'outro';
      let seat;
      if(name==='sentado')seat=bench(stage,defs,bible,{x:x-height*.18,floor,height,colors}).top;
      const state=pose(bible,a,name,x,floor,{seat,phase:.16});
      const actor=draw(stage,defs,bible,{id,paintId:id+'-'+name,height,pose:state,color,expression});
      for(const [footX,footY] of actor.soles){
        const shadow=contact(stage,defs,bible,id,footX,floor,a.foot*.64,a.head*.11,Math.max(0,(floor-footY)/15));
        stage.insertBefore(shadow,actor.g);
      }
      const outline=await contour(actor.g);
      const head=Number(actor.face.getAttribute('ry'))*2;
      const ratio=outline.height/height;
      const caption=create(card,'figcaption');
      create(caption,'strong',title);
      const detail=name==='em_pe'?`${(outline.height/head).toFixed(2)} cabeças · pernas ${(100*a.hip/height).toFixed(0)}%`:
        `${(100*ratio).toFixed(1)}% da altura em pé`;
      create(caption,'small',detail);
      metrics.push({personagem:role,pose:name,altura_px:outline.height,altura_em_cabecas:outline.height/head,
        altura_relativa:ratio,quadril_ao_chao:a.hip/height,joelho_ao_chao:a.knee/height,
        tronco_relativo:(a.torso+a.head*.30)/height,apoio_y:floor,solas:actor.soles,
        topo_contorno_px:state.y+outline.top,base_contorno_px:state.y+outline.bottom});
    }
  }
  window.medidasModelo=metrics;
})();
