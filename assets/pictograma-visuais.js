/* Elementos gráficos independentes da pose. O quadro sempre vem da fala. */
window.PictogramaVisuais=({width,height,colors,node,text,rectangle,line,circle,smoothstep,colorMix})=>{
  const canvas=780;
  const x0=72, y0=386;
  const ink=colors.osso, accent=colors.acento, dim=colors.suave, rule=colors.linha;
  const paper=colorMix(colors.fundo,accent,.07);
  const clamp=u=>Math.max(0,Math.min(1,u));
  const easing=u=>1-(1-clamp(u))**3;
  const title=(g,value,x,y,max,size,fill=ink)=>{
    const el=text(g,value,x,y,max,size,{fill});
    el.classList.add('picto-display');
    return el;
  };
  const panel=(g,x,y,w,h,emphasis=0)=>node('rect',{
    x,y,width:w,height:h,rx:19,fill:paper,
    stroke:colorMix(rule,accent,.55*emphasis),'stroke-width':2
  },g);
  const path=(g,d,attributes={})=>node('path',{d,fill:'none',stroke:accent,
    'stroke-width':3,'stroke-linecap':'round','stroke-linejoin':'round',...attributes},g);
  const reveal=(g,opacity,dy=0)=>node('g',{opacity,transform:`translate(0 ${dy})`},g);
  const arrow=(g,start,end,y,u)=>{
    const x=start+(end-start)*u;
    line(g,start,y,x,y,accent,3);
    if(u>.86)path(g,`M ${x-10} ${y-6} L ${x} ${y} L ${x-10} ${y+6}`,{opacity:(u-.86)/.14});
  };
  return (parent,graphic,frame)=>{
    if(!graphic || frame<graphic.inicio)return;
    const {tipo,textos,pouso,fim}=graphic;
    const t=frame-pouso;
    const prepare=easing((frame-graphic.inicio)/Math.max(1,pouso-graphic.inicio));
    const u=smoothstep((t+2)/Math.max(8,fim-pouso+2));
    const opacity=easing((frame-graphic.inicio+1)/8);
    const g=node('g',{'data-elemento':'grafico','data-grafico':tipo,
      transform:`translate(${x0*width/1080} ${y0*height/1920}) scale(${width/1080} ${height/1920})`,
      opacity},parent);
    if(tipo==='contraste'){
      const left=panel(g,4,10,323,100,prepare*(1-u)*.55);
      left.setAttribute('opacity',Math.min(1,.45+prepare));
      panel(g,457,10,319,100,u);
      title(g,textos[0],165,74,277,48,colorMix(ink,dim,.24*u));
      title(reveal(g,.22+.78*u,8*(1-u)),textos[1],616,74,279,48,colorMix(ink,accent,u));
      arrow(g,351,431,60,u);
    }else if(tipo==='fonte'){
      panel(g,25,8,730,108,.42*u);
      const book=node('g',{transform:'translate(103 61)'},g);
      path(book,'M -38 -23 Q -18 -28 0 -17 Q 18 -28 38 -23 V 24 Q 18 18 0 30 Q -18 18 -38 24 Z',
        {stroke:ink,fill:colorMix(paper,accent,.14)});
      path(book,'M 0 -17 V 29',{stroke:accent,'stroke-width':2});
      for(let i=0;i<3;i++){
        const p=easing((t+3-i*3)/9), y=-12+i*10;
        line(book,-30,y,-30+19*p,y+3,dim,2);
        line(book,10,y+3,10+19*p,y,accent,2);
      }
      title(reveal(g,.36+.64*u,6*(1-u)),textos[0],425,72,540,42);
    }else if(tipo==='relogio'){
      panel(g,35,9,710,104,.55*u);
      const cx=108,cy=61,r=31;
      node('circle',{cx,cy,r,fill:'none',stroke:rule,'stroke-width':3},g);
      const length=2*Math.PI*r;
      node('circle',{cx,cy,r,fill:'none',stroke:accent,'stroke-width':4,
        'stroke-dasharray':`${u*length} ${length}`,transform:`rotate(-90 ${cx} ${cy})`},g);
      const a=(u*.86-.25)*Math.PI*2;
      line(g,cx,cy,cx+Math.cos(a)*22,cy+Math.sin(a)*22,ink,3);
      line(g,cx,cy,cx-11,cy-7,dim,3);
      circle(g,cx,cy,3,accent);
      title(g,textos[0],443,72,545,43);
    }else if(tipo==='rede'){
      const items=textos.length;
      const spacing=canvas/items;
      const cy=93;
      for(let i=0;i<items;i++){
        const x=(i+.5)*spacing;
        const p=easing((t+5-i*5)/12);
        if(i)line(g,x-spacing+14,cy,x-spacing+14+(spacing-28)*p,cy,rule,4);
        const group=reveal(g,.24+.76*p,9*(1-p));
        title(group,textos[i],x,62,spacing-24,36,colorMix(ink,accent,p*.72));
        circle(group,x,cy,4+4*p,colorMix(rule,accent,p));
      }
    }else if(tipo==='enfase'){
      const w=590*u;
      line(g,canvas/2-w/2,104,canvas/2+w/2,104,accent,3);
      circle(g,canvas/2+w/2,104,3,accent);
      title(reveal(g,.30+.70*u,14*(1-u)),textos[0],canvas/2,81,690,63,colorMix(ink,accent,u*.54));
    }
  };
};
