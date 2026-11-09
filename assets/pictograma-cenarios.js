/* Cenários em coordenadas de projeto. As camadas são recortadas acima da legenda. */
window.PictogramaCenarios = ({width,height,colors,node,smoothstep,colorMix}) => {
  const base=colors.fundo, green=colors.acento, cream=colors.osso;
  const tone=(amount)=>colorMix(base,green,amount);
  const light=(amount)=>colorMix(base,cream,amount);
  const rect=(g,x,y,w,h,fill,other={})=>node('rect',{x,y,width:w,height:h,fill,...other},g);
  const shape=(g,d,fill,other={})=>node('path',{d,fill,...other},g);
  const stroke=(g,d,ink,weight=2,other={})=>shape(g,d,'none',{
    stroke:ink,'stroke-width':weight,'stroke-linecap':'round','stroke-linejoin':'round',...other});
  const ellipse=(g,cx,cy,rx,ry,fill,other={})=>node('ellipse',{cx,cy,rx,ry,fill,...other},g);
  const tree=(g,x,y,size)=>{
    stroke(g,`M ${x} ${y} v ${-size*.7} m 0 ${size*.25} l ${-size*.27} ${-size*.23}`,tone(.27),3);
    ellipse(g,x,y-size*.71,size*.38,size*.38,tone(.12));
    ellipse(g,x+size*.17,y-size*.71,size*.24,size*.28,tone(.18));
    stroke(g,`M ${x} ${y-4} v ${-size*.51} l ${size*.23} ${-size*.18}`,tone(.30),3);
  };
  const block=(g,x,ground,w,h,depth,u)=>{
    const y=ground-h, side=w*.15, face=tone(depth), shade=tone(depth*.62);
    shape(g,`M ${x} ${y} l ${w*.48} ${-w*.23} l ${w*.67} ${w*.24} z`,tone(depth+.08));
    rect(g,x,y,w,h,face);
    shape(g,`M ${x+w} ${y} l ${side} ${-w*.035} v ${h} l ${-side} ${w*.035} z`,shade);
    stroke(g,`M ${x+4} ${ground-3} h ${w-9}`,tone(depth+.08));
    for(let column=0;column<3;column++){
      for(let row=0;row<Math.floor(h/40);row++){
        const bright=(column+row)%3===0;
        const xw=x+10+column*(w-13)/3, yw=y+14+row*39;
        rect(g,xw,yw,w*.11,12,bright?light(.19+.17*u):base,{rx:2});
      }
    }
    rect(g,x+w*.45,ground-26,w*.16,26,shade,{rx:2});
  };
  const distant=(g,u,glow)=>{
    ellipse(g,540,625,400+32*u,198,glow,{opacity:.30+.40*u});
    shape(g,'M 70 886 L 200 712 294 762 435 617 570 741 714 681 892 795 932 894 Z',tone(.10));
    shape(g,'M 70 935 Q 215 799 388 849 Q 599 721 776 835 L 932 915 V 1110 H 70 Z',tone(.13));
  };
  const city=(back,mid,u,street,glow)=>{
    distant(back,u,glow);
    const houses=[[96,84,123],[194,95,184],[309,88,133],[417,110,210],[551,101,157],[672,94,197],[790,92,143]];
    houses.forEach(([x,w,h],i)=>block(back,x,990+(i%2)*29,w,h,.12+(i%3)*.025,u));
    const near=[[80,130,236],[239,116,170],[669,123,181],[813,105,245]];
    near.forEach(([x,w,h],i)=>block(mid,x,street?1110:1045,w,h,.20+i*.025,u));
    if(street){
      shape(mid,'M 70 1130 H 931 V 1248 H 70 Z',tone(.095));
      stroke(mid,'M 71 1160 H 930 M 71 1190 H 930',tone(.19),2);
      tree(mid,183,1163,140);
      tree(mid,846,1173,130);
      stroke(mid,'M 733 1150 V 840 Q 733 821 752 821 H 778',tone(.29),5);
      ellipse(mid,774,848,24,31,cream,{opacity:.08+.12*u});
      rect(mid,765,824,22,9,light(.36),{rx:4});
    }else{
      ellipse(back,544,615,122,122,cream,{opacity:.035+.10*u});
      stroke(mid,'M 85 1085 Q 354 1046 522 1095 T 927 1074',tone(.24),3);
      tree(mid,137,1120,98); tree(mid,871,1117,109);
    }
  };
  const windowScene=(back,mid,u,left,shared)=>{
    const x=left?130:683, y=542, w=206;
    shape(back,'M 71 574 H 933 V 1218 H 71 Z',tone(.065));
    stroke(back,'M 71 1090 H 933 M 71 1120 H 933',tone(.21),3);
    rect(mid,x,y,w,362,tone(.24),{rx:9});
    rect(mid,x+10,y+10,w-20,342,tone(.13),{rx:5});
    shape(mid,`M ${x+11} ${y+220} l 45 -48 39 28 38 -51 61 63 v 126 h -183 z`,tone(.22));
    ellipse(mid,x+60+u*24,y+87,37,37,cream,{opacity:.14+.10*u});
    stroke(mid,`M ${x+w/2} ${y+8} v 345 m ${-w/2+9} -168 h ${w-18}`,tone(.39),5);
    rect(mid,x-10,y+356,w+20,13,tone(.36),{rx:2});
    const outer=shared?77:100, shift=36*u;
    shape(mid,`M ${x+22} ${y+370} h 160 l ${(left?1:-1)*(outer+shift)} 336 h -200 Z`,cream,
      {opacity:.035+.037*u});
    stroke(mid,`M ${left?750:109} 1110 v -196 h 81 v 196`,tone(.21),3);
  };
  const library=(back,mid,u)=>{
    rect(back,76,520,851,690,tone(.08),{rx:25});
    [104,665].forEach((x,k)=>{
      rect(mid,x,543,245,622,tone(.16),{rx:7});
      for(let row=0;row<4;row++){
        const shelf=683+row*144;
        rect(mid,x+10,shelf-127,224,126,base,{rx:3});
        for(let i=0;i<10;i++){
          const h=50+((i*19+row*13+k*7)%54), bx=x+16+i*21;
          const highlight=(i+row+k)%6===0;
          rect(mid,bx,shelf-h,14+(i%3),h,highlight?light(.22+.12*u):tone(.21+(i%4)*.045),{rx:2});
          stroke(mid,`M ${bx+3} ${shelf-h+10} h 7`,tone(.45),1.5);
        }
        rect(mid,x+3,shelf,239,9,tone(.34),{rx:2});
      }
    });
    stroke(back,'M 370 1110 V 730 Q 370 610 504 610 Q 637 610 637 730 V 1110',tone(.16),3);
  };
  const decree=(back,mid,u,left)=>{
    stroke(back,'M 72 1139 H 931 M 72 1168 H 931',tone(.18),3);
    const x=left?157:689, y=719, h=42+210*u;
    rect(mid,x+15,y+9,176,h,tone(.14),{rx:13});
    shape(mid,`M ${x+20} ${y} h 142 q 16 0 16 18 v ${h-23} q -14 -14 -28 -5 h -128 q -18 0 -18 -18 v ${-h+45} q 0 -17 16 -17 Z`,
      light(.30+.10*u),{stroke:light(.55),'stroke-width':2});
    for(let i=0;i<4;i++){
      const fraction=smoothstep(u*1.55-i*.15);
      if(fraction>0)stroke(mid,`M ${x+26} ${y+36+i*30} h ${(112-i*8)*fraction}`,light(.64),2.5);
    }
    if(u>.61)ellipse(mid,x+142,y+h-35,16,16,tone(.70),{opacity:smoothstep((u-.61)/.3)});
    stroke(mid,`M ${x+7} ${y+h-6} q -5 -13 11 -14 h 130`,light(.53),3);
  };
  const road=(back,mid,u,glow)=>{
    distant(back,u*.5,glow);
    shape(mid,'M 498 866 Q 412 997 228 1248 H 755 Q 567 986 537 866 Z',tone(.17));
    stroke(mid,'M 498 866 Q 412 997 228 1248 M 537 866 Q 567 986 755 1248',tone(.32),3);
    for(let i=0;i<6;i++){
      const z=(i+1)/7, y=883+356*z**1.52, x=520-35*z;
      const p=.14+.86*smoothstep((u-i*.12)*3.2);
      ellipse(mid,x,y,4+z*15,2+z*4,cream,{opacity:p*.46});
    }
    tree(mid,171,1184,123);tree(mid,824,1192,158);tree(back,688,1023,77);
  };
  const sideShade=light(.74);
  const restingAnimal=g=>{
    ellipse(g,-1,-3,81,9,tone(.18));
    stroke(g,'M 42 -30 Q 77 -32 77 -16 Q 76 -10 62 -11',sideShade,10);
    shape(g,'M -38 -27 Q -42 -52 -9 -64 Q 13 -73 37 -62 Q 59 -51 62 -25 Q 56 -8 39 -8 H -40 Z',cream);
    shape(g,'M 17 -49 Q 40 -61 55 -35 Q 62 -17 48 -11 H 10 Q 0 -16 15 -21 L 32 -23 Q 19 -31 17 -49 Z',sideShade);
    shape(g,'M -17 -36 Q -24 -23 -42 -18 L -62 -17 Q -73 -11 -61 -6 H -34 Q -11 -8 -7 -27 Z',cream);
    shape(g,'M -46 -53 Q -60 -64 -69 -49 L -75 -30 L -86 -25 Q -91 -17 -80 -15 H -59 Q -48 -15 -41 -24 Q -33 -34 -46 -53 Z',cream);
    shape(g,'M -49 -54 Q -36 -49 -43 -30 Q -49 -22 -57 -32 L -59 -47 Q -57 -54 -49 -54 Z',sideShade);
  };
  const seatedElder=g=>{
    ellipse(g,-8,-3,72,9,tone(.18));
    rect(g,-57,-77,82,8,light(.50),{rx:4});
    stroke(g,'M -48 -71 V -4 M 15 -71 V -4',light(.46),7);
    shape(g,'M -22 -94 Q 0 -102 17 -84 Q 31 -74 33 -60 L 31 -14 Q 33 -11 43 -9 Q 52 -7 51 0 H 16 Q 10 -2 10 -9 L 10 -49 L -28 -69 Z',sideShade);
    shape(g,'M -31 -109 Q -43 -100 -42 -83 Q -40 -72 -26 -68 L 12 -61 Q 16 -55 15 -43 L 16 -12 Q 17 -3 10 -1 H -12 Q -20 -4 -14 -11 L -5 -14 L -8 -46 L -41 -55 Q -59 -62 -58 -83 Q -58 -105 -47 -117 Z',cream);
    shape(g,'M -40 -177 Q -26 -201 -5 -179 L 10 -154 Q 14 -145 9 -137 Q -4 -124 -14 -111 L -21 -85 Q -36 -70 -53 -82 Q -56 -99 -50 -120 Q -50 -155 -40 -177 Z',cream);
    ellipse(g,10,-207,26,29,cream,{transform:'rotate(17 10 -207)'});
    shape(g,'M -7 -192 L 17 -187 L 11 -169 Q -5 -163 -18 -177 Z',cream);
    stroke(g,'M 69 -2 L 66 -119 Q 65 -129 55 -129 H 46',light(.88),6);
    stroke(g,'M -12 -157 Q 5 -139 17 -133 Q 31 -128 53 -127',sideShade,17);
    ellipse(g,54,-127,10,7,cream);
  };
  const seatedChild=g=>{
    ellipse(g,7,-4,67,9,tone(.18));
    shape(g,'M -20 -62 Q -7 -74 7 -63 L 34 -48 Q 46 -42 50 -26 L 52 -13 Q 68 -13 68 -3 L 45 0 Q 38 0 35 -8 L 25 -27 L -10 -30 Z',sideShade);
    shape(g,'M -38 -40 Q -51 -44 -49 -66 Q -51 -97 -30 -121 Q -20 -133 -3 -126 Q 7 -119 2 -101 L -2 -69 Q 5 -67 12 -67 L 23 -82 Q 29 -90 39 -86 Q 48 -84 48 -72 Q 48 -66 42 -57 L 27 -31 Q 19 -19 5 -19 L -22 -21 Q -33 -23 -38 -40 Z',cream);
    ellipse(g,-3,-155,23,24,cream,{transform:'rotate(12 -3 -155)'});
    shape(g,'M -15 -136 L 6 -136 L 3 -117 H -20 Z',cream);
    stroke(g,'M -17 -108 Q -7 -91 5 -78 Q 15 -72 30 -78',sideShade,13);
    ellipse(g,32,-79,8,6,cream);
    shape(g,'M -19 -25 L 12 -29 Q 22 -29 25 -19 L 39 -12 Q 51 -10 51 -3 H 19 Q 10 -3 3 -9 L -22 -11 Q -30 -15 -19 -25 Z',cream);
  };
  const figures={animal:restingAnimal,idoso:seatedElder,crianca:seatedChild};
  const drawFigures=(stage,scene,frame,actorX)=>{
    const {entrada_quadros,saida_inicio,saida_fim}=scene.revelacao_figuras;
    if(frame>=saida_fim)return;
    const fade=1-smoothstep((frame-saida_inicio)/(saida_fim-saida_inicio));
    const row=node('g',{transform:`scale(${width/1080} ${height/1920})`},stage);
    const start=actorX>width/2?155:570;
    for(const [i,figure] of scene.figuras.entries()){
      if(frame<figure.pouso)continue;
      const progress=smoothstep((frame-figure.pouso+1)/entrada_quadros);
      const g=node('g',{'data-figura-enumerada':figure.tipo,opacity:progress*fade,
        transform:`translate(${start+i*173} 1245)`},row);
      figures[figure.tipo](g);
    }
  };
  const paint=(stage,defs,scene,frame,actorX,figuresLayer)=>{
    if(!scene)return;
    const u=scene.continuo?1:smoothstep((frame-scene.pouso)/Math.max(1,scene.fim-scene.pouso));
    const clipId=`cenario-${scene.inicio}-${scene.tipo}`;
    const sky=node('radialGradient',{id:clipId+'-luz'},defs);
    node('stop',{offset:'0%','stop-color':green,'stop-opacity':.28},sky);
    node('stop',{offset:'100%','stop-color':green,'stop-opacity':0},sky);
    const fade=node('linearGradient',{id:clipId+'-borda',x1:'0%',x2:'100%'},defs);
    for(const [offset,ink] of [['0%','black'],['7%','white'],['93%','white'],['100%','black']])
      node('stop',{offset,'stop-color':ink},fade);
    const mask=node('mask',{id:clipId,maskUnits:'userSpaceOnUse',x:69,y:416,width:826,height:880},defs);
    rect(mask,69,416,826,880,`url(#${clipId}-borda)`);
    const group=node('g',{'data-cenario-ilustrado':scene.tipo,transform:`scale(${width/1080} ${height/1920})`,
      mask:`url(#${clipId})`},stage);
    rect(group,69,416,826,880,'none',{'data-cenario-area':'sim'});
    const glow=`url(#${clipId}-luz)`;
    const back=node('g',{'data-plano':'fundo'},group);
    const mid=node('g',{'data-plano':'intermediario'},group);
    const near=node('g',{'data-plano':'primeiro'},group);
    const left=actorX>width*.49;
    if(scene.tipo==='esperanca'||scene.tipo==='rua')city(back,mid,u,scene.tipo==='rua',glow);
    if(scene.tipo==='janela'||scene.tipo==='encontro')windowScene(back,mid,u,left,scene.tipo==='encontro');
    if(scene.tipo==='biblioteca')library(back,mid,u);
    if(scene.tipo==='decreto')decree(back,mid,u,left);
    if(scene.tipo==='caminho')road(back,mid,u,glow);
    stroke(near,'M 88 1271 h 179 m 444 0 h 197',tone(.23),2);
    shape(near,'M 92 1280 l 97 -8 39 8 z M 744 1280 l 103 -8 53 8 z',tone(.17));
    if(figuresLayer&&scene.figuras)drawFigures(figuresLayer,scene,frame,actorX);
  };
  paint.atmosfera=(stage,defs,mood,frame,opacity,{tag,x,y,floor,head,windowSide,gift})=>{
    if(!mood||opacity<=0)return;
    const type=mood.tipo;
    const safeId=tag+'-acima-da-legenda';
    const safeHeight=floor+head*.36;
    const safe=node('clipPath',{id:safeId},defs);
    rect(safe,0,0,width,safeHeight,'white');
    const group=node('g',{'data-atmosfera':type,'data-id-atmosfera':tag,opacity,
      'clip-path':`url(#${safeId})`},stage);
    rect(group,0,0,width,safeHeight,'none',{'data-area-atmosfera':'sim'});
    const glow=(name,cx,cy,rx,ry,ink,level)=>{
      if(level<=0)return;
      const key=tag+'-'+name;
      const gradient=node('radialGradient',{id:key,cx:.50,cy:.50,r:.50},defs);
      for(const [offset,a] of [[0,level],[.38,level*.78],[.71,level*.34],[1,0]])
        node('stop',{offset,'stop-color':ink,'stop-opacity':a},gradient);
      ellipse(group,cx,cy,rx,ry,`url(#${key})`);
    };
    const gold='#ead38f';
    if(type==='chuva'){
      glow('cinza',width*.47,height*.45,width*.43,height*.31,'#a0adb4',.40);
      if(windowSide!=null){
        const scaleX=width/1080, scaleY=height/1920;
        const [bx,by,w,h]=[(windowSide?140:693)*scaleX,551*scaleY,186*scaleX,341*scaleY];
        const key=tag+'-vidro';
        const clip=node('clipPath',{id:key},defs);
        rect(clip,bx,by,w,h,'white');
        const drops=node('g',{'clip-path':`url(#${key})`},group);
        rect(drops,bx,by,w,h,'#8a9aa5',{opacity:.19});
        for(let i=0;i<27;i++){
          const dx=bx+((i*31+7)%193)/193*w;
          const dy=by+((i*57+frame*(i%3+7))%349)/349*h;
          stroke(drops,`M ${dx} ${dy} l ${-head*.09} ${head*.24}`,'#d0d5d6',
            i%5===0?2.7:1.4,{opacity:.34+i%3*.07,'data-gota':'sim'});
        }
      }
      for(let i=0;i<22;i++){
        const px=width*(.12+((i*109)%742)/1000);
        const py=height*(.30+((i*71+frame*(i%3+7))%320)/1000);
        stroke(group,`M ${px} ${py} l ${-head*.11} ${head*.30}`,'#adb7bd',
          i%4===0?2:1.25,{opacity:windowSide!=null?.25:.47,'data-gota':'sim'});
      }
    }else if(type==='aura'){
      const pulse=.96+.04*Math.sin((frame-mood.pouso)*.11);
      glow('alma',x,y-head*.12,head*2.08*pulse,head*3.58,gold,.66);
      glow('centro',x,y,head*1.22,head*2.35,'#f8e9b6',.21);
      ellipse(group,x,y-head*.06,head*1.35*pulse,head*2.47,'none',
        {stroke:'#ebd9aa','stroke-width':1.6,opacity:.24,'data-aura':'sim'});
    }else if(type==='sombra'){
      glow('frio',width*.49,height*.45,width*.45,height*.35,'#788c9a',.20);
      glow('solo',width*.49,floor,width*.39,head*.45,'#8e9ba0',.11);
    }else{
      glow('aberto',width*.52,height*.39,width*.47,height*.31,gold,type==='claridade'?.36:.22);
      glow('chao',width*.47,floor-4,width*.42,head*.40,'#ddbd76',.26);
      if(gift){
        const {from,to,progress}=gift;
        const origin=glow.bind(null,'doador',from[0],from[1],head*1.33,head*1.98,gold);
        origin(.54*(1-progress));
        glow('recebe',to[0],to[1],head*(1.14+.56*progress),head*(1.65+.65*progress),
          '#ffe6a5',.76*progress);
        const path=progress*(1-progress)*4;
        if(path>0){
          const light=from.map((value,i)=>value+(to[i]-value)*progress);
          glow('trajeto',light[0],light[1]-head*.18,head*.78,head*1.12,'#fff3be',.65*path);
        }
        if(progress>.12){
          const spread=head*(.65+.63*progress);
          ellipse(group,to[0],to[1],spread,spread*1.33,'none',
            {stroke:'#f7d995','stroke-width':1.8,opacity:progress*.28});
        }
        node('g',{'data-luz-partilha':progress>=.5?'recebe':'doa','data-progresso-luz':progress},group);
      }
    }
  };
  return paint;
};
