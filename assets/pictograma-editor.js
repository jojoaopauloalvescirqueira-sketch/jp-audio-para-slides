document.addEventListener('DOMContentLoaded', () => {
  const data=JSON.parse(document.getElementById('dados').textContent);
  const sync=data.sincronia;
  const graph=document.getElementById('onda-sincronia');
  const select=document.getElementById('ancora-sincronia');
  const output=document.getElementById('quadro-sincronia');
  const edits=new Map();
  const ctx=graph.getContext('2d');
  const frameAt=(word)=>edits.get(word.palavra) ?? word.quadro;
  function draw() {
    const w=graph.width,h=graph.height;
    ctx.clearRect(0,0,w,h);
    ctx.fillStyle='#52705E';
    sync.onda.forEach((amplitude,i)=>{
      const bar=2+amplitude*h*.8;
      ctx.fillRect(i*w/sync.onda.length,(h-bar)/2,Math.ceil(w/sync.onda.length),bar);
    });
    for(const word of sync.palavras) {
      ctx.fillStyle=word.palavra===Number(select.value)?'#ECE6D8':'#9CC6A6';
      ctx.fillRect(frameAt(word)/30/sync.duracao_s*w,0,1,h);
    }
    const word=sync.palavras[Number(select.value)];
    output.textContent='Quadro '+frameAt(word)+' · '+(frameAt(word)/30).toFixed(3)+' s';
  }
  function step(delta) {
    const index=Number(select.value);
    const word=sync.palavras[index];
    const lower=index ? frameAt(sync.palavras[index-1]) : 0;
    const upper=index+1<sync.palavras.length ? frameAt(sync.palavras[index+1]) : Math.ceil(sync.duracao_s*30)-1;
    const next=Math.max(lower,Math.min(upper,frameAt(word)+delta));
    edits.set(index,next);
    window.seek(next/30);
    draw();
  }
  for(const word of sync.palavras){
    const label=document.createElement('option');
    label.value=word.palavra;
    label.textContent=word.texto+' · '+word.metodo;
    select.append(label);
    if(word.metodo==='conferido_manual') edits.set(word.palavra,word.quadro);
  }
  select.addEventListener('change',()=>{
    window.seek(frameAt(sync.palavras[Number(select.value)])/30);
    draw();
  });
  document.getElementById('ancora-menos').addEventListener('click',()=>step(-1));
  document.getElementById('ancora-mais').addEventListener('click',()=>step(1));
  document.getElementById('editor-sincronia').addEventListener('keydown',event=>{
    if(event.key==='ArrowLeft'||event.key==='ArrowRight'){
      event.preventDefault();
      step(event.key==='ArrowLeft'?-1:1);
    }
  });
  document.getElementById('baixar-sincronia').addEventListener('click',()=>{
    if(!edits.size) {output.textContent='Ajuste ou confirme um quadro primeiro.';return;}
    const payload={identidade:sync.identidade,pontos:[...edits].sort(([a],[b])=>a-b)
      .map(([palavra,quadro])=>({palavra,quadro}))};
    const link=document.createElement('a');
    link.href=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));
    link.download='marcacoes_ajustadas.json';
    link.click();
    setTimeout(()=>URL.revokeObjectURL(link.href),1000);
  });
  draw();
});
