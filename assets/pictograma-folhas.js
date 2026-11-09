/* Ensaios independentes de roteiro e áudio para as duas folhas de aprovação. */
window.prepararFolha = name => {
  const b=JSON.parse(document.querySelector('#biblia').textContent);
  const rig=window.PictogramaRig;
  const {svg}=window.PictogramaFigura;
  const colors=['#9cc6a6','#efe5cf'];
  const target=document.querySelector('#cartoes');
  const c=document.querySelector('#diagnostico');
  c.onclick=()=>{
    const hidden=document.body.classList.toggle('hide-diagnostic');
    c.setAttribute('aria-pressed',String(!hidden));
    c.textContent=hidden?'Mostrar diagnóstico':'Ocultar diagnóstico';
  };
  const draw=(parent,spec)=>{
    const figure=document.createElement('figure');
    parent.append(figure);
    const stage=svg(figure,'svg',{viewBox:spec.box,role:'img','aria-label':spec.title});
    const [x,y,w]=spec.box.split(' ').map(Number);
    svg(stage,'line',{x1:x+.1,y1:0,x2:x+w-.1,y2:0,stroke:'#6d8c7c','stroke-width':.027});
    if(spec.frame!==undefined){stage.dataset.ensaio=spec.ensaio;stage.dataset.quadro=spec.frame;}
    if(spec.seat){
      svg(stage,'path',{d:'M -1.58 -1.48 H -.07 V -1.35 H -1.58Z M -1.44 -1.36 H -1.33 V 0 H -1.44Z M -.23 -1.36 H -.12 V 0 H -.23Z',fill:'#587266'});
    }
    if(spec.grid){
      for(let i=0;i<=6;i++){
        svg(stage,'line',{x1:x+.13,x2:x+w-.13,y1:-i,y2:-i,stroke:'#526c5f','stroke-width':.012});
        const tick=svg(stage,'text',{x:x+.17,y:-i-.035,fill:'#a8c5b5','font-size':.16});
        tick.textContent=i+' h';
      }
    }
    if(spec.grid){stage.dataset.ensaio='anatomia';stage.dataset.yaw=spec.yaw;stage.dataset.personagem=spec.index;}
    spec.poses.forEach((pose,i)=>rig.draw(stage,pose,b,{
      yaw:spec.yaw??82,color:colors[spec.index??i],diagnostic:true
    }));
    const caption=document.createElement('figcaption');
    caption.textContent=spec.title;
    const details=document.createElement('small');details.textContent=spec.subtitle;
    caption.append(details);figure.append(caption);
    return stage;
  };
  function row(title,count){
    const section=document.createElement('section'), h=document.createElement('h2'), cards=document.createElement('div');
    h.textContent=title; cards.className='cards';cards.style.setProperty('--cols',count);
    section.append(h,cards);target.append(section);return cards;
  }
  const neutral=[rig.neutral(b),rig.neutral(b,-1)];
  const sequences={
    repouso:[neutral],
    marcha:Array.from({length:32},(_,f)=>[rig.walk(b,f)]),
    sentar:Array.from({length:31},(_,f)=>[rig.chair(b,f,false)]),
    levantar:Array.from({length:31},(_,f)=>[rig.chair(b,f,true)]),
    ajuda:Array.from({length:b.ajuda.fim+1},(_,f)=>rig.help(b,f))
  };
  if(name==='folha-anatomica'){
    const headings=['Frente','Perfil','Três quartos'];
    for(const [i,pose] of neutral.entries()){
      const label=i===0?'Ajudante':'Ajudado';
      const g=row(label,3);
      for(const [view,yaw] of [0,90,45].entries())
        draw(g,{poses:[pose],yaw,index:i,box:'-2.3 -6.25 4.6 6.6',
          grid:true,title:headings[view],subtitle:'6 h · coxa 1,49 h · canela 1,30 h · antebraço 0,85 h'});
    }
    const footer=document.createElement('p');
    footer.className='legend';
    const names={lombar:'Lombar',toracica:'torácica',cervical:'cervical',cabeca:'base da cabeça ao centro',
      clavicula:'clavícula',braco:'braço',antebraco:'antebraço',mao:'mão',coxa:'coxa',canela:'canela',
      calcanhar_planta:'calcanhar–planta',planta_ponta:'planta–ponta'};
    footer.textContent=Object.entries(b.ossos).map(([key,v])=>names[key]+' '+String(v).replace('.',',')+' h').join(' · ');
    target.append(footer);
  }else{
    const layout=[
      ['Caminhada · dois passos','marcha',[0,4,8,12,16,20,24,28]],
      ['Sentar','sentar',[0,5,10,15,20,26,30]],
      ['Levantar','levantar',[0,4,8,12,17,23,30]],
      ['Ajudar a levantar · 2 segundos','ajuda',[0,8,14,23,30,39,49,59]]
    ];
    for(const [label,key,frames] of layout){
      const g=row(label,frames.length);
      for(const f of frames){
        const poses=sequences[key][f];
        const multi=key==='ajuda';
        const box=multi?'-3.15 -6.25 6.25 6.60':key==='marcha'?'-1.65 -6.25 5.35 6.6':'-2.05 -6.25 4.1 6.6';
        draw(g,{poses,box,frame:f,ensaio:key,
          seat:key==='sentar'||key==='levantar',title:poses[0].phase,
          subtitle:`Q${String(f).padStart(2,'0')} · ${(f/30).toFixed(2).replace('.',',')} s`});
      }
    }
  }
  window.ensaioRig={neutral,sequences,bible:b};
};
