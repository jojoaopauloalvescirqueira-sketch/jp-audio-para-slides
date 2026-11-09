MotorCenas.registrarKit('ilustrado', ({data,width,height,landscape,colors,node,set,text,layer,sample,
  smoothstep,cameraLayer}) => {
  const artwork=data.imagens;
  window.assetsReady=Promise.all(Object.values(artwork).map(asset=>{
    const image=new Image();
    image.src=asset.url;
    return image.decode();
  }));
  // A rejected asset is propagated to the headless renderer and kept visible in the player.
  window.assetsReady.catch(error=>{
    const status=document.getElementById('estado-previa');
    if(status) status.textContent='Falha ao decodificar um PNG: '+error.message;
  });
  const startState=row=>({x:row.x,y:row.y,scale:row.escala,rotation:row.rotacao,opacity:row.opacidade,glow:0});
  const offset={esquerda:[-.18,0],direita:[.18,0],cima:[0,-.14],baixo:[0,.14]};
  const tracks=values=>Object.fromEntries(Object.entries(values).map(([key,value])=>[key,[[-1,value]]]));
  const at=(state,t)=>Object.fromEntries(Object.entries(state).map(([key,track])=>[key,sample(track,t,key)]));
  function tween(state,key,t,duration,value,initial) {
    const track=state[key];
    const from=initial ?? sample(track,t,key);
    while(track.length>1 && track.at(-1)[0]>=t) track.pop();
    track.push([t,from],[t+duration,value]);
  }
  function image(parent,id,opacity) {
    if(opacity<=0) return;
    const asset=artwork[id];
    if(!asset) throw Error('PNG não encontrado: '+id);
    node('image',{href:asset.url,x:-width/2,y:-height/2,width,height,opacity,
      preserveAspectRatio:asset.tipo==='fundo'?'xMidYMid slice':'xMidYMid meet'},parent);
  }
  function compile(scene) {
    const pictures=scene.elementos.filter(row=>row.tipo==='imagem').sort((a,b)=>a.z-b.z);
    const states=new Map(pictures.map(row=>[row.id,{row,channels:tracks(startState(row)),poses:[],breaths:[],blinks:[]}]));
    const framing=scene.enquadramento?.[data.formato] || {};
    const [cx,cy]=framing.centro || [.5,.5];
    const camera=tracks({zoom:framing.zoom || 1,x:cx,y:cy});
    const title=tracks({word:'',opacity:0,y:0});
    const enter=(item,t,dt,action) => {
      const state=item.channels;
      const base=startState(item.row);
      tween(state,'opacity',t,dt,base.opacity,0);
      if(action.modo==='escala') tween(state,'scale',t,dt,base.scale,base.scale*.75);
      if(action.modo==='lado') {
        const [dx,dy]=offset[action.lado || 'esquerda'];
        tween(state,'x',t,dt,base.x,base.x+dx);
        tween(state,'y',t,dt,base.y,base.y+dy);
      }
    };
    for(const action of scene.acoes) {
      if(action.acao==='entrar' || action.acao==='surgir_em_grupo') {
        for(const id of action.alvos || [action.alvo]) states.get(id).channels.opacity[0][1]=0;
      }
    }
    for(const action of scene.acoes) {
      const t=action.tempo, dt=action.duracao_s || (action.acao==='trocar_pose'?.25:.4);
      const item=states.get(action.alvo);
      const state=item?.channels;
      switch(action.acao) {
        case 'entrar': enter(item,t,dt,action); break;
        case 'sair': {
          tween(state,'opacity',t,dt,0);
          if(action.modo==='lado') {
            const [dx,dy]=offset[action.lado || 'esquerda'];
            tween(state,'x',t,dt,sample(state.x,t,'x')+dx);
            tween(state,'y',t,dt,sample(state.y,t,'y')+dy);
          }
          break;
        }
        case 'mover':
          for(const [source,key] of [['x','x'],['y','y'],['escala','scale']])
            if(action[source]!==undefined) tween(state,key,t,dt,action[source]);
          break;
        case 'trocar_pose': item.poses.push({t,dt,id:action.asset}); break;
        case 'piscar': item.blinks.push({t,dt:action.duracao_s || .17,id:action.asset}); break;
        case 'respirar': item.breaths.push(t); break;
        case 'destacar':
          tween(state,'glow',t,dt/2,1);
          tween(state,'glow',t+dt/2,dt/2,0);
          break;
        case 'surgir_em_grupo':
          action.alvos.forEach((id,i)=>enter(states.get(id),t+i*.12,dt,action));
          break;
        case 'camera': {
          const [x,y]=action.centro || [.5,.5];
          tween(camera,'x',t,dt,x);
          tween(camera,'y',t,dt,y);
          tween(camera,'zoom',t,dt,action.zoom || 1);
          break;
        }
        case 'titulo_entra':
          tween(title,'word',t,0,action.texto);
          tween(title,'opacity',t,dt,1,0);
          tween(title,'y',t,dt,0,-22);
          break;
        case 'titulo_sai':
          tween(title,'opacity',t,dt,0);
          tween(title,'y',t,dt,22);
          break;
      }
    }

    return (world,defs,t,showOverlay) => {
      const shot=at(camera,t);
      const view=cameraLayer(world,shot);
      for(const item of states.values()) {
        const {row,channels}=item;
        const state=at(channels,t);
        if(state.opacity<=0) continue;
        const breathe=item.breaths.find(start=>start<=t);
        if(breathe!==undefined) state.scale*=1+.012*(1-Math.cos((t-breathe)*3))/2;
        const group=layer(view,{'data-elemento':row.id},{...state,x:state.x*width,y:state.y*height,parallax:row.paralaxe},
          {x:shot.x*width,y:shot.y*height});
        if(state.glow) set(group,{style:`filter:drop-shadow(0 0 ${20*state.glow}px ${colors.acento})`});
        let current=row.asset, overlay=null;
        for(const pose of item.poses) {
          if(pose.t>t) break;
          const u=smoothstep((t-pose.t)/pose.dt);
          if(u<1) overlay={id:pose.id,weight:u}; else {current=pose.id;overlay=null;}
        }
        const blink=item.blinks.find(pose=>pose.t<=t && t<pose.t+pose.dt);
        if(blink) current=blink.id;
        image(group,current,overlay?1-overlay.weight:1);
        if(overlay) image(group,overlay.id,overlay.weight);
      }
      const heading=at(title,t);
      if(showOverlay && heading.word && heading.opacity>0) {
        const titleNode=text(world,heading.word,landscape?width/2:480,
          (landscape?183:575)+heading.y,landscape?width*.8:790,landscape?92:78,
          {fill:colors.osso,weight:800});
        set(titleNode,{opacity:heading.opacity,'data-seguro':'texto'});
      }
      if(showOverlay && data.pendente) {
        const label=text(world,'ARTE PENDENTE DE APROVAÇÃO',landscape?width/2:480,
          landscape?1050:1420,790,landscape?23:25,{fill:colors.suave});
        set(label,{'data-seguro':'texto'});
      }
    };
  }
  return compile;
});
