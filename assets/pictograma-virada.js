/* Virada de um glifo, com cabeçalho e varredura opcionais. */
window.PictogramaVirada=api=>{
  const {colors,node,set,text,line,smoothstep,mix}=api;
  const ease=(f,s,e)=>smoothstep((f-s)/(e-s));
  const wave=(f,s,e)=>Math.sin(Math.PI*ease(f,s,e));
  const group=(p,id,attrs={})=>node('g',{'data-elemento':id,...attrs},p);
  function label(p,id,value,x,y,available,size,fill,opacity=1){
    if(opacity<=0)return;
    const g=group(p,id,{opacity});
    const el=text(g,value,x,y,available,size,{fill});
    el.classList.add('picto-display');
    el.dataset.titulo='sim';
    return el;
  }
  function shape(parent,p,q,color,width,attrs={}){
    return set(line(parent,...p,...q,color,width),attrs);
  }
  return (stage,f,{cues,corte,words,marks,effects=false,floor})=>{
    const frame=name=>cues[name].frame;
    const turn=cues.virada;
    const face=ease(f,turn.frame-7,turn.frame+6);
    const show=ease(f,0,9);
    const reveal=.56+.44*ease(f,frame('conceito')-2,frame('conceito')+10);
    const exit=ease(f,corte-11,corte);
    const newLetter=face>=.5;
    const scaleX=Math.max(.028,Math.abs(Math.cos(face*Math.PI)));
    const settle=1+.052*wave(f,turn.frame+4,turn.frame+13);
    const y=marks.linha_conceito-36*ease(f,corte-5,corte);
    const token=node('g',{opacity:show*reveal*(1-exit),'data-virada':'sim'},stage);
    const dropStart=turn.frame+6, dropEnd=turn.frame+17;
    const drop=effects?ease(f,dropStart,dropEnd):0;
    const negationExit=effects?drop:ease(f,turn.frame+6,turn.frame+35);
    const leadSize=marks.tamanho_cabecalho;
    const header=words.sujeito!=null&&words.copula!=null&&words.negacao!=null;
    const subject=header?label(token,'sujeito',words.sujeito,0,marks.linha_superior,marks.largura_sujeito,leadSize,colors.osso):null;
    const copula=header?label(token,'verbo-titulo',words.copula,0,marks.linha_superior,marks.largura_copula,leadSize,colors.osso):null;
    const prefix=label(token,'prefixo',words.prefixo,0,y,marks.largura_palavra,marks.tamanho_palavra,colors.osso);
    const suffix=label(token,'sufixo',words.sufixo,0,y,marks.largura_palavra,marks.tamanho_palavra,colors.osso);
    const glyph=group(token,'letra',{'data-letra':newLetter?words.depois:words.antes});
    const letter=text(glyph,words.antes,0,0,marks.largura_palavra,marks.tamanho_palavra,{fill:newLetter?colors.acento:colors.osso});
    letter.classList.add('picto-display');
    const oldWidth=letter.getComputedTextLength();
    letter.textContent=words.depois;
    const slot=Math.max(oldWidth,letter.getComputedTextLength());
    if(!newLetter)letter.textContent=words.antes;
    const start=marks.centro_tipo-(prefix.getComputedTextLength()+slot+suffix.getComputedTextLength())/2;
    const advance=start+prefix.getComputedTextLength();
    set(prefix,{x:start,'text-anchor':'start'});
    set(suffix,{x:advance+slot,'text-anchor':'start'});
    set(glyph,{transform:`translate(${advance+slot/2} ${y}) scale(${scaleX*settle} ${settle})`});
    if(header){
    const release=effects?0:negationExit;
    const pulse=1+.14*wave(f,frame('negacao')-2,frame('negacao')+12);
    const negAlpha=show*(1-negationExit)*(1-exit);
    const neg=group(stage,'negacao',{'data-negacao':'sim',opacity:negAlpha});
    const negative=text(neg,words.negacao,0,0,marks.largura_negacao,leadSize,{fill:colors.osso});
    negative.classList.add('picto-display');
    negative.dataset.titulo='sim';
    const subjectWidth=subject.getComputedTextLength(), copulaWidth=copula.getComputedTextLength();
    const negativeWidth=negative.getComputedTextLength(), space=24;
    const full=subjectWidth+negativeWidth+copulaWidth+space*2;
    const compact=subjectWidth+space+copulaWidth;
    const firstX=marks.centro_tipo-full/2, compactX=marks.centro_tipo-compact/2;
    set(subject,{x:mix(firstX,compactX,release)+subjectWidth/2});
    set(copula,{x:mix(firstX+full,compactX+compact,release)-copulaWidth/2});
    if(effects){
      set(neg,{transform:`translate(${firstX+subjectWidth+space+negativeWidth/2} ${marks.linha_superior+25*drop}) scale(${pulse})`,
        'data-queda':f>dropStart&&f<dropEnd?'sim':'nao'});
    }else{
      const shrink=ease(f,turn.frame+6,turn.frame+10);
      const drift=ease(f,turn.frame+10,turn.frame+30);
      const fall=ease(f,turn.frame+30,turn.frame+35);
      const xpos=mix(firstX+subjectWidth+space+negativeWidth/2,marks.saida_negacao_x,drift);
      set(neg,{transform:`translate(${xpos} ${marks.linha_superior+35*shrink+92*fall})
        scale(${pulse*(1-.76*shrink)})`,'data-queda':shrink>0?'sim':'nao'});
    }
    const strike=ease(f,turn.start,effects?turn.frame+5:turn.frame-10);
    if(strike>0){
      neg.dataset.riscoCompleto=String(strike===1);
      const [x,y,length,slope]=marks.risco;
      const point=[x+length*strike,y-slope*strike];
      shape(neg,[x,y],point,colors.acento,8,{'data-risco':'sim'});
      const flash=wave(f,turn.start,turn.frame-9);
      if(flash>0&&!effects)node('circle',{cx:point[0],cy:point[1],r:10+8*flash,fill:colors.acento,opacity:flash*.33},neg);
    }
    if(effects&&f>=dropEnd)neg.remove();
    }
    if(words.classe_antes&&words.classe_depois)label(token,'classe',newLetter?words.classe_depois:words.classe_antes,marks.centro_tipo,marks.linha_classe+12*Math.sin(face*Math.PI),marks.largura_classe,marks.tamanho_classe,
      newLetter?colors.acento:colors.osso);
    if(marks.varredura&&f>=corte-16){
      const u=ease(f,corte-16,corte);
      const sweep=group(stage,'linha-de-palco',{opacity:u*.69});
      const xx=marks.varredura.esquerda+(1-u)*marks.varredura.recuo, yy=mix(marks.varredura.y,floor,u);
      shape(sweep,[xx,yy],[marks.varredura.extensao-xx,yy],colors.acento,3);
    }
  };
};
