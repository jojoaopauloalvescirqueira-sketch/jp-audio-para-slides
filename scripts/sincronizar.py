#!/usr/bin/env python3
"""Timeline e MP4 a partir de durações medidas e entradas verificáveis."""
import argparse,csv,math,subprocess,sys,tempfile
from pathlib import Path
from projeto import load,audio,audio_files,audio_identity,binary,probe,read,write,sha,outdir,ffquote,FORMATS

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--marcacoes',type=Path);ap.add_argument('--formato',choices=list(FORMATS));ap.add_argument('--ffprobe');ap.add_argument('--ffmpeg');ap.add_argument('--renderizar',action='store_true');ap.add_argument('--threads',type=int,default=4);a=ap.parse_args();root=a.root.resolve();c,ps,scenes,_=load(root);fmt=a.formato or c['formato'];out=outdir(root,fmt);ffprobe=binary('ffprobe',a.ffprobe);files=audio_files(audio(root,c),len(ps));infos=[probe(p,ffprobe) for p in files];durations=[float(i['format']['duration']) for i in infos];total=sum(durations);times=[];methods=[]
 mp=a.marcacoes or root/'material/marcacoes_audio.json'
 if mp.is_file():
  m=read(mp)
  if m.get('audio_identidade')!=audio_identity(root,c,ps):raise ValueError('Marcações pertencem a outro áudio; SHA-256 incompatível.')
  for key,file in [('plano_sha256','slides.json'),('roteiro_sha256','paragrafos.json')]:
   if m.get(key) and m[key]!=sha(root/'material'/file):raise ValueError(f'{file} mudou; refaça o alinhamento.')
  if not math.isfinite(float(m['duracao_s'])) or abs(m['duracao_s']-total)>.15:raise ValueError('Duração das marcações não corresponde aos áudios medidos.')
  rev=m.get('revisao',{});checked={x['slide_id']:x for x in rev.get('conferidos',[]) if isinstance(x,dict) and x.get('motivo','').strip()};by={x['slide_id']:x for x in m.get('slides',[])}
  pending=[]
  for key in rev.get('pendencias',[]):
   row=checked.get(key);t=by.get(key,{}).get('inicio_s')
   if not row or row.get('inicio_s')!=t:pending.append(key)
  if pending:raise ValueError('Alinhamento exige revisão documentada: '+', '.join(pending))
  if 'slides' in m:
   if len(by)!=len(m['slides']):raise ValueError('Marcações duplicadas.')
   for s in scenes:
    if s['id'] not in by:raise ValueError('Marcação ausente: '+s['id'])
    row=by[s['id']]
    if row.get('texto_entrada')!=s['frase_gatilho']:raise ValueError('Frase-gatilho mudou: '+s['id'])
    times.append(row['inicio_s']);methods.append(row.get('metodo','marcacao_fornecida'))
  else:
   rows=m.get('paragrafos',[]);pm={r['paragrafo']:r for r in rows}
   if len(pm)!=len(rows):raise ValueError('Marcações de parágrafos duplicadas.')
   previous=0.
   for p in ps:
    if p['id'] not in pm:raise ValueError('Marcação ausente para '+p['id'])
    row=pm[p['id']];start=row['inicio_s'];end=row['fim_s']
    if not (math.isfinite(start) and math.isfinite(end) and abs(start-previous)<.01 and start<end<=total+.01):raise ValueError('Marcações por parágrafo inválidas ou descontínuas.')
    previous=end
   if abs(previous-total)>.15:raise ValueError('Marcações por parágrafo não cobrem o áudio.')
   for s in scenes:
    row=pm[f'P{s["p"]:03}'];ratio=len(ps[s['p']-1]['texto'][:s['char_start']].split())/len(ps[s['p']-1]['texto'].split());times.append(row['inicio_s']+(row['fim_s']-row['inicio_s'])*ratio);methods.append('posicao_interna_proporcional_estimada')
 elif audio(root,c).is_dir():
  starts=[0.]
  for d in durations:starts.append(starts[-1]+d)
  for s in scenes:
   ratio=len(ps[s['p']-1]['texto'][:s['char_start']].split())/len(ps[s['p']-1]['texto'].split());times.append(starts[s['p']-1]+durations[s['p']-1]*ratio);methods.append('duracao_paragrafo_medida_posicao_interna_estimada')
 else:raise ValueError('Áudio único exige marcações. Rode transcrever.py e alinha_audio.py ou forneça marcações verificadas.')
 if not times or any(not isinstance(t,(int,float)) or not math.isfinite(t) or t<0 or t>=total for t in times):raise ValueError('Entradas inválidas ou fora da duração do áudio.')
 if abs(times[0])>.01:raise ValueError('A primeira entrada precisa ser zero.')
 times[0]=0.
 if any(y<=x for x,y in zip(times,times[1:])):raise ValueError('Entradas não crescentes.')
 rows=[];concat=['ffconcat version 1.0'];ends=times[1:]+[total]
 for s,start,end,method in zip(scenes,times,ends,methods):
  png=out/'png'/f'{s["id"]}.png'
  if not png.is_file():raise ValueError('Slide ausente: '+str(png))
  f0=round(start*30);f1=round(end*30)
  if f1<=f0:raise ValueError('Slide com menos de um quadro: '+s['id'])
  rows.append({'slide_id':s['id'],'arquivo_png':f'png/{s["id"]}.png','inicio_s':f'{start:.6f}','fim_s':f'{end:.6f}','duracao_s':f'{end-start:.6f}','frame_inicio':f0,'frame_fim':f1,'metodo':method});concat+=['file '+ffquote(png),f'duration {(f1-f0)/30:.9f}','option framerate 30']
 concat+=['file '+ffquote(out/'png'/f'{scenes[-1]["id"]}.png'),'option framerate 30']
 out.mkdir(parents=True,exist_ok=True)
 with (out/'timeline.csv').open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 (out/'concat.ffconcat').write_text('\n'.join(concat)+'\n',encoding='utf-8');(out/'audios.ffconcat').write_text('ffconcat version 1.0\n'+'\n'.join('file '+ffquote(f) for f in files)+'\n',encoding='utf-8')
 report={'formato':fmt,'duracao_audio_s':total,'quadros':round(total*30),'fps':30,'slides':len(rows),'metodos':sorted(set(methods)),'audio_identidade':audio_identity(root,c,ps)}
 if a.renderizar:
  ff=binary('ffmpeg',a.ffmpeg);target=root/('video.mp4' if fmt=='16:9' else 'video-'+fmt.replace(':','x')+'.mp4');audio_input=['-i',str(files[0])] if len(files)==1 else ['-f','concat','-safe','0','-i',str(out/'audios.ffconcat')]
  codecs=[next(s['codec_name'] for s in i['streams'] if s['codec_type']=='audio') for i in infos];copy_audio=len(files)==1 and codecs[0]=='aac'
  codec=['-c:a','copy'] if copy_audio else ['-c:a','aac','-b:a','192k']
  if len(files)>1:
   # Normalize derived copies: concat demuxing original files with mixed codecs/rates is unsafe.
   preview=root/'material/narracao-unificada.m4a'
   with tempfile.TemporaryDirectory(prefix='.audio-normalizada-',dir=root) as directory:
    directory=Path(directory);normalized=[];channels=max(int(next(s for s in i['streams'] if s['codec_type']=='audio').get('channels',1)) for i in infos)
    for index,file in enumerate(files):
     dest=directory/f'{index:06}.wav';subprocess.run([ff,'-y','-v','error','-i',str(file),'-vn','-ar','48000','-ac',str(channels),'-c:a','pcm_s16le',str(dest)],check=True);normalized.append(dest)
    tracklist=directory/'audio.ffconcat';tracklist.write_text('ffconcat version 1.0\n'+'\n'.join('file '+ffquote(x) for x in normalized)+'\n',encoding='utf-8')
    derived=directory/'unificada.m4a';subprocess.run([ff,'-y','-v','error','-f','concat','-safe','0','-i',str(tracklist),'-c:a','aac','-b:a','192k',str(derived)],check=True);derived.replace(preview)
   if abs(float(probe(preview,ffprobe)['format']['duration'])-total)>.15:raise ValueError('A unificação dos áudios mudou a duração total.')
   audio_input=['-i',str(preview)];codec=['-c:a','copy']
  handle=tempfile.NamedTemporaryFile(prefix='.render-',suffix='.mp4',dir=root,delete=False);stage=Path(handle.name);handle.close()
  try:
   subprocess.run([ff,'-y','-hide_banner','-loglevel','warning','-f','concat','-safe','0','-i',str(out/'concat.ffconcat'),*audio_input,'-map','0:v:0','-map','1:a:0','-vf','fps=30','-c:v','libx264','-preset','veryfast','-tune','stillimage','-crf','20','-threads',str(a.threads),'-pix_fmt','yuv420p',*codec,'-t',f'{total:.6f}','-movflags','+faststart',str(stage)],check=True)
   vi=probe(stage,ffprobe);v=next(s for s in vi['streams'] if s['codec_type']=='video')
   if (v['width'],v['height'])!=FORMATS[fmt] or v['avg_frame_rate']!='30/1' or int(v['nb_frames'])!=round(total*30) or abs(float(vi['format']['duration'])-total)>.1:raise ValueError('Metadados do vídeo não conferem.')
   subprocess.run([ff,'-v','error','-xerror','-i',str(stage),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
   if copy_audio and len(files)==1:
    def ahash(p):return subprocess.run([ff,'-v','error','-i',str(p),'-map','0:a:0','-c:a','copy','-f','hash','-hash','sha256','-'],check=True,capture_output=True,text=True).stdout.strip()
    if ahash(files[0])!=ahash(stage):raise ValueError('O áudio copiado não corresponde ao original.')
   stage.replace(target)
  finally:stage.unlink(missing_ok=True)
  report.update(video=target.name,decodificacao_integral=True,audio_sem_recompressao=copy_audio)
  if len(files)>1:
   preview=root/'material/narracao-unificada.m4a';c['audio_previa']=preview.relative_to(root).as_posix();write(root/'projeto.json',c)
 write(out/'sincronizacao.json',report);print(f'{len(rows)} slides; {total:.6f}s medidos; formato {fmt}.')
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,FileNotFoundError,subprocess.CalledProcessError) as e:sys.exit('ERRO: '+str(e))
