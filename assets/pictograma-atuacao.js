/* Blocagem do piloto. O solver aprovado mantém os comprimentos e recalcula os apoios. */
window.PictogramaAtuacao=(b,cues,corte,marks)=>{
  const rig=window.PictogramaRig,library=window.PictogramaAcoes;
  const clamp=(x)=>Math.min(1,Math.max(0,x));
  const smooth=x=>{x=clamp(x);return x*x*(3-2*x);};
  const mix=(a,z,t)=>a+(z-a)*t;
  const vec=(a,z,t)=>a.map((v,i)=>mix(v,z[i],t));
  const chairOffset=marks.cadeira,walkOffset=marks.marcha;
  const sentar=cues.sentar.frame-16, levantar=cues.levantar.frame-29;
  const aproximar=levantar+30;
  const ajuda=cues.ajudar.frame-b.ajuda.pega;
  const fimAjuda=ajuda+b.ajuda.fim;
  if(sentar<corte+20 || levantar<sentar+30 || ajuda<aproximar || cues.receber.frame<fimAjuda+5)
    throw Error('A atuação anatômica não cabe nos intervalos desta narração.');
  const walk=f=>library.walk(b,f,walkOffset);
  const chair=(f,up)=>library.chair(b,f,up,chairOffset);
  const lastStep=walk(16),firstSit=chair(0,false),lastRise=chair(30,true);
  const firstHelp=library.help(b,0);
  const finalHelp=library.help(b,b.ajuda.fim);
  function upright(c){
    const [a,z]=c.feet.map((foot,i)=>[foot.ankle[0]+(i?-.35:.35),foot.ankle[1],foot.ankle[2]]);
    const knee=4*Math.PI/180,{coxa,canela}=b.ossos;
    const span2=coxa**2+canela**2+2*coxa*canela*Math.cos(knee);
    const mid=vec(a,z,.5);
    mid[1]-=Math.sqrt(span2-rig.distance(a,z)**2/4);
    return mid;
  }
  const bridge=(a,z,t,phase)=>library.bridge(b,a,z,t,phase);
  function comparison(f,index){
    const actor=finalHelp[index],c=actor.control;
    const reach=smooth((f-(cues.receber.frame-13))/13);
    const offer=smooth((f-cues.fazer.frame)/12)*(1-smooth((f-cues.fazer.frame-26)/13));
    const rest=smooth((f-fimAjuda)/14);
    const pelvis=vec(c.pelvis,upright(c),rest);
    const [x,y,z]=pelvis;
    const calm=(index?.018:.025)*Math.sin(f*.17+index);
    const near=[-.32,y-1.25,z-.43],far=[.31,y-1.17,z-.18];
    const hands=index?[vec([-.64,y+.20,z],near,reach),vec([.64,y+.20,z],far,reach)]:
      [null,vec([.68,y+.22,z],[.38,y-1.02,z+.82],offer)];
    return rig.pose(b,{...c,pelvis,hands,handContacts:null,groundSeat:false,
      handDirections:index?[[0,-.03,-1],[0,-.03,-1]]:[[0,1,0],[0,-.15,1]],
      spine:[c.spine[0]*(1-rest)+calm,c.spine[1]*(1-rest),c.spine[2]*(1-rest)],headPitch:0,phase:'Comparação',mode:'comparacao'});
  }
  function at(frame){
    const f=Math.round(frame);
    if(f<corte)return [];
    const walkEnd=corte+16;
    if(f<walkEnd)return [walk(f-corte)];
    if(f<sentar)return [bridge(lastStep,firstSit,(f-walkEnd)/(sentar-walkEnd),'Plantar para sentar')];
    if(f<levantar)return [chair(Math.min(30,f-sentar),false)];
    if(f<aproximar)return [chair(f-levantar,true)];
    if(f<ajuda+8){
      const t=clamp((f-aproximar)/(ajuda+8-aproximar));
      const actors=library.help(b,Math.max(0,f-ajuda));
      return [bridge(lastRise,actors[0]??firstHelp[0],t,'Dar um passo para ajudar'),actors[1]];
    }
    if(f<=fimAjuda)return library.help(b,f-ajuda,{contatoDesenhado:true});
    return [comparison(f,0),comparison(f,1)];
  }
  return {at,ajuda,fimAjuda};
};
