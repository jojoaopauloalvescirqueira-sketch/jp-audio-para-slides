#!/usr/bin/env python3
"""Gera HTML, manifest e PNGs a partir de material/. Requer Node + Playwright."""
import argparse,csv,html,json,re,subprocess,os
from pathlib import Path
from projeto import load, outdir, FORMATS, audio_identity, sha, read
from editorial import PROFILE, WATERMARK, MAP, ASSETS, markup, record_render


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--formato',choices=['16:9','21:9','9:16']);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--html-only',action='store_true');ap.add_argument('--node',default=os.environ.get('NODE','node'));ap.add_argument('--somente',default='');args=ap.parse_args();root=args.root.resolve();cfg,ps,scenes,sources=load(root,require_audio=False);args.formato=args.formato or cfg['formato']
 editorial=cfg['perfil_visual']==PROFILE
 vertical=args.formato=='9:16';w,h=FORMATS[args.formato];out=outdir(root,args.formato);(out/'png').mkdir(parents=True,exist_ok=True)
 marks=json.loads((root/'material/marcacoes_audio.json').read_text()) if (root/'material/marcacoes_audio.json').exists() else {'slides':[]}
 valid_marks=bool(cfg.get('audio')) and marks.get('audio_identidade')==audio_identity(root,cfg,ps) and (not marks.get('plano_sha256') or marks['plano_sha256']==sha(root/'material/slides.json'))
 if editorial and valid_marks:
  valid_marks=marks.get('plano_sha256')==sha(root/'material/slides.json') and marks.get('roteiro_sha256')==sha(root/'material/paragrafos.json')
 timings={m['slide_id']:m['inicio_s'] for m in marks.get('slides',[]) if m.get('inicio_s') is not None} if valid_marks else {}
 preview=cfg.get('audio_previa',cfg.get('audio'));preview=preview if preview and (root/preview).is_file() else ''
 audio_tag='<audio id="narracao" controls preload="metadata" src="../'+html.escape(preview)+'"></audio>' if preview else '<span>Áudio pendente ou prévia ainda não sincronizada.</span><audio id="narracao" hidden></audio>'
 source_map={str(s['id']):s for s in sources}
 editorial_notes={}
 if editorial:
  for row in read(root/MAP):editorial_notes.setdefault(row['slide_id'],[]).append(f"P{row['p']:03} · {row['trecho']}")
 E=html.escape;articles=[]
 for s in scenes:
  t=E(s['title']);b=E(s['body']);k=s['tipo'];content=''
  author=' · '.join(x for x in [cfg['autor'],cfg['marca']] if x)
  if k=='figura':
   src=source_map[str(s['figura'])];url='../'+src['arquivo'];n=s['figura']
   views=src.get('vistas',{}).get('9:16' if vertical else '21:9',[])
   if len(views)>2:raise ValueError('Use no máximo duas vistas por slide; crie outras cenas quando necessário.')
   if views:
    from PIL import Image
    original=Image.open(root/src['arquivo']);iw,ih=original.size;names=[]
    for j,box in enumerate(views):
     if len(box)!=4 or not (0<=box[0]<box[2]<=1 and 0<=box[1]<box[3]<=1):raise ValueError('Recorte normalizado inválido.')
     suffix=("-9x16" if vertical else "-21x9") if editorial else ""
     fp=root/'material/figuras'/f"F{sources.index(src)+1:03}{suffix}-vista{j+1}.png";fp.parent.mkdir(parents=True,exist_ok=True)
     original.crop((round(box[0]*iw),round(box[1]*ih),round(box[2]*iw),round(box[3]*ih))).save(fp);names.append('../'+str(fp.relative_to(root)))
    visual='<div class="figure-parts">'+''.join(f'<img src="{E(u)}" alt="Figura {E(str(n))}, vista {j+1}">' for j,u in enumerate(names))+'</div>'
   else:visual=f'<img class="chart" src="{E(url)}" alt="Figura {n} do artigo">'
   content=f'<div class="figure-image">{visual}</div><div class="caption">{t}</div><div class="note">{E(s["nota"])}</div><div class="source">Fonte: {E(src["credito"])}</div>'
  elif k=='capa':
   t=E(s['title'] or cfg['titulo']);b=E(s['body'] or cfg['subtitulo'])
   art=f'<img class="cover-art" src="../{E(cfg["capa"])}" alt="Capa do material">' if cfg['capa'] else ''
   klass='cover-copy' if art else 'cover-copy no-art'
   content=f'<div class="{klass}"><h1>{t}</h1><p class="subtitle">{b}</p><p class="author">{E(cfg["autor"])}</p></div>{art}'
  elif k=='final':
   content=f'<div class="center"><h1>{E(s["title"] or cfg["cta_rotulo"])}</h1><p class="url">{E(s["body"] or cfg["cta_url"])}</p><p class="author">{E(author)}</p></div>'
  elif k=='sintese':content='<div class="center synthesis">'+''.join(f'<p>{E(x)}</p>' for x in s['lines'])+'</div>'
  elif k=='conta':content=f'<div class="center calculation"><h2>{t}</h2>'+''.join(f'<p>{E(x)}</p>' for x in s['lines'])+'</div>'
  else:content=f'<div class="center"><h1>{t}</h1>'+ (f'<p class="definition">{b}</p>' if b else '')+'</div>'
  if editorial:content=markup(s,content,src if k=='figura' else None)
  if k!='figura' and s['fonte']:content+=f'<div class="source">{E(s["fonte"])}</div>'
  script='\n\n'.join(f"{p['id']} · {p['texto']}" for p in ps[s['p']-1:s['end']])
  if editorial:script='\n\n'.join(editorial_notes[s['id']])
  classes='slide '+k
  watermark=''
  if editorial:
   classes+=' editorial-jp'+(' vertical' if vertical else '')
   watermark='<img class="watermark" src="../'+E(cfg.get('marca_dagua',WATERMARK),quote=True)+'" alt="JP Wealth">'
  articles.append(f'<article id="{s["id"]}" class="{classes}"><div class="composition">{content}</div>{watermark}</article>')
  listen=f'<button onclick="listen({timings[s["id"]]})">Ouvir entrada</button>' if s['id'] in timings and preview else '<button disabled>Entrada ainda sem marcação</button>'
  s['notes_html']=f'<div class="narration">{listen} <strong>{s["id"]} · {s["bloco"]} · Entrada: {E(s["frase_gatilho"])}</strong><p>{E(script).replace(chr(10),"<br>")}</p></div>'
 css='''*{box-sizing:border-box}html,body{margin:0;background:#e4e5e2;color:#202725;font-family:Arial,Helvetica,sans-serif}.slide{width:2520px;height:1080px;position:relative;background:#fafaf7;overflow:hidden}.center{position:absolute;left:9%;right:9%;top:15%;bottom:15%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}h1{font-size:100px;font-weight:600;line-height:1.16;letter-spacing:-3px;max-width:2050px;margin:0;text-wrap:balance}h2{font-size:49px;font-weight:400;color:#626d68;margin:0 0 65px}.definition{font-size:49px;line-height:1.35;max-width:1900px;margin:60px 0 0;color:#58645e;text-wrap:balance}.author{font-size:38px;margin-top:64px;color:#54615a}.url{font-size:65px;color:#52705e;letter-spacing:-1px}.synthesis p{font-size:65px;line-height:1.28;margin:22px 0;max-width:2000px;text-wrap:balance}.synthesis p:first-child{color:#52705e}.calculation p{font-size:76px;line-height:1.3;margin:20px 0;font-variant-numeric:tabular-nums;letter-spacing:-1px}.calculation p:last-child{color:#52705e}.figure-image{position:absolute;top:90px;left:8%;right:8%;height:715px;display:flex;align-items:center;justify-content:center}.chart{display:block;max-width:100%;max-height:100%;object-fit:contain}.figure-parts{width:100%;height:100%;display:flex;gap:65px;align-items:center;justify-content:center}.figure-parts img{max-width:calc(50% - 33px);max-height:100%;object-fit:contain}.caption{position:absolute;top:842px;left:8%;right:8%;font-size:45px;line-height:1.2;text-align:center;letter-spacing:-.6px}.note{position:absolute;top:909px;left:8%;right:8%;font-size:27px;line-height:1.3;text-align:center;color:#626b66}.source{position:absolute;bottom:87px;left:8%;right:8%;font-size:25px;text-align:center;color:#626b66}.cover-copy{position:absolute;left:9%;top:19%;width:53%;height:65%;display:flex;flex-direction:column;justify-content:center}.cover-copy h1{font-size:91px;letter-spacing:-2.5px;line-height:1.12}.subtitle{font-size:35px;line-height:1.4;max-width:1200px;color:#626b66;margin-top:48px}.cover-copy .author{margin-top:42px}.cover-art{position:absolute;left:66%;top:20%;width:26%;height:60%;object-fit:contain}.narration{max-width:1200px;margin:15px auto 65px;font-size:17px;line-height:1.6;white-space:normal}.slide{margin:0 auto;scroll-margin-top:130px}nav{position:sticky;top:0;z-index:20;background:#202725;color:white;padding:14px;display:flex;gap:16px;justify-content:center;align-items:center;flex-wrap:wrap}nav select{max-width:45vw}nav audio{width:260px}button,select{font:inherit;padding:6px 12px}body.render{background:#fafaf7}body.render nav,body.render .narration{display:none}body.render .slide{display:none;margin:0}body.render .slide.active{display:block}body.preview .slide{zoom:var(--zoom,.4)}.render h1,.render p{orphans:2;widows:2}'''
 if vertical:css+='''.slide{width:1080px;height:1920px}.center{left:9%;right:9%;top:370px;bottom:auto;height:1060px}h1{font-size:68px;letter-spacing:-1.8px;max-width:885px}.definition{font-size:40px;margin-top:50px;max-width:880px}.author{font-size:31px}.url{font-size:35px;letter-spacing:-.5px}.synthesis p{font-size:48px;margin:24px 0}.calculation h2{font-size:37px;margin-bottom:60px}.calculation p{font-size:45px;letter-spacing:-.8px}.figure-image{top:385px;left:9%;right:9%;height:755px}.caption{top:1170px;left:9%;right:9%;font-size:35px}.note{top:1272px;left:9%;right:9%;font-size:24px}.source{bottom:auto;top:1382px;left:9%;right:9%;font-size:20px}.cover-copy{left:9%;top:370px;width:82%;height:1060px;justify-content:flex-start}.cover-copy h1{font-size:65px;letter-spacing:-1.5px;line-height:1.12}.subtitle{font-size:31px;max-width:885px;margin-top:40px}.cover-copy .author{font-size:32px;margin-top:35px}.cover-art{display:none}'''
 data=[{k:v for k,v in s.items() if k!='notes_html'} for s in scenes]
 css+=' .composition{position:absolute;left:0;top:0;width:2520px;height:1080px}.no-art{width:82%}'
 if args.formato=='16:9':css+=' .slide{width:1920px;height:1080px}.composition{top:128.571428571px;transform:scale(.761904761905);transform-origin:0 0}'
 if vertical:css+=' .composition{width:1080px;height:1920px}'
 if editorial:css+=(ASSETS/'editorial-jp.css').read_text(encoding='utf-8')
 document='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+E(cfg['titulo'])+' · apresentação</title><style>'+css+'</style><body class="preview"><nav><button onclick="step(-1)">Anterior</button><select id="selector" onchange="navigate(this.value)">'+''.join(f'<option value="{s["id"]}">{s["id"]} · {E(s["title"] or "Síntese")}</option>' for s in scenes)+'</select><button onclick="step(1)">Próximo</button><button onclick="allSlides()">Ver todos</button>'+audio_tag+'</nav>'+''.join(a+s['notes_html'] for a,s in zip(articles,scenes))+'''<script>
const params=new URLSearchParams(location.search);let current=0;const slides=[...document.querySelectorAll('.slide')];window.sceneData='''+json.dumps(data,ensure_ascii=False).replace('<',chr(92)+'u003c')+''';window.sceneSize='''+json.dumps([w,h])+''';
for(const scene of window.sceneData) {
 if(!scene.movimento)continue;
 const target=document.getElementById(scene.id).querySelector('[data-alvo="'+scene.movimento.alvo+'"]');
 if(target)target.classList.add('movimento-'+scene.movimento.tipo);
}
function zoom(){document.documentElement.style.setProperty('--zoom',Math.min((innerWidth-30)/window.sceneSize[0],.75))}zoom();addEventListener('resize',zoom);
window.show=function(id){current=slides.findIndex(s=>s.id===id);document.body.classList.add('render');document.body.classList.remove('preview');slides.forEach(s=>s.classList.toggle('active',s.id===id));document.getElementById('selector').value=id;window.scrollTo(0,0)};
window.navigate=id=>{document.body.className='preview';current=slides.findIndex(s=>s.id===id);document.getElementById(id).scrollIntoView();document.getElementById('selector').value=id};
window.listen=t=>{const a=document.getElementById('narracao');a.currentTime=t;a.play().catch(()=>{})};
addEventListener('keydown',e=>{if(!['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)&&['ArrowRight','ArrowLeft'].includes(e.key))step(e.key==='ArrowRight'?1:-1)});
window.step=d=>{const i=Math.max(0,Math.min(slides.length-1,current+d));if(!params.has('render')){document.body.className='preview';document.getElementById(slides[i].id).scrollIntoView();current=i;document.getElementById('selector').value=slides[i].id}else show(slides[i].id)};
window.allSlides=()=>{document.body.className='preview';zoom()};if(params.has('render'))show(params.get('render')||slides[0].id);
</script></body></html>'''
 (out/'apresentacao.html').write_text(document)
 with (out/'manifest.csv').open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=['slide_id','arquivo_png','paragrafo_inicio','paragrafo_fim','frase_gatilho','tipo','figura_artigo','duracao_estimada_s']);writer.writeheader()
  for s in scenes:writer.writerow(dict(slide_id=s['id'],arquivo_png=f'png/{s["id"]}.png',paragrafo_inicio=f'P{s["p"]:03}',paragrafo_fim=f'P{s["end"]:03}',frase_gatilho=s['frase_gatilho'],tipo=s['tipo'],figura_artigo=f'Figura {s["figura"]}' if s['figura'] is not None else '',duracao_estimada_s=f'{s["estimativa_s"]:.6f}'))
 (out/'intervalos_roteiro.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
 if not args.html_only:
  if editorial:(out/'render_manifest.json').unlink(missing_ok=True)
  subprocess.run([args.node,str(Path(__file__).with_name('renderizar.mjs')),str(out),args.somente],check=True)
  if editorial and not args.somente:record_render(root,cfg,args.formato,scenes,sources,out)
 print(f'{len(scenes)} slides · {w}×{h} · {out}')
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError) as exc:raise SystemExit(str(exc))
