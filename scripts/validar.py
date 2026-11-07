#!/usr/bin/env python3
"""Valida cobertura, renderização, timeline e MP4 sem quantidades fixas."""
import argparse,csv,sys,subprocess
from pathlib import Path
from projeto import load,read,write,outdir,FORMATS,binary,probe

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',required=True,type=Path);ap.add_argument('--formato',choices=list(FORMATS));ap.add_argument('--video',action='store_true');ap.add_argument('--ffprobe');ap.add_argument('--ffmpeg');a=ap.parse_args();root=a.root.resolve();c,ps,scenes,sources=load(root);fmt=a.formato or c['formato'];out=outdir(root,fmt)
 from PIL import Image
 report={'paragrafos':len(ps),'slides':len(scenes),'figuras_referenciadas':len({str(s['figura']) for s in scenes if s['figura'] is not None}),'formato':fmt,'resolucao':FORMATS[fmt],'cobertura_roteiro':True}
 for s in scenes:
  with Image.open(out/'png'/f'{s["id"]}.png') as im:
   if im.size!=FORMATS[fmt]:raise ValueError('Dimensões incorretas: '+s['id'])
 layout=read(out/'validacao_layout.json')
 if {r['slide'] for r in layout}!={s['id'] for s in scenes} or any(r['issues'] for r in layout):raise ValueError('Validação de layout incompleta ou com problemas.')
 report['margens']=True
 if (out/'timeline.csv').exists():
  with (out/'timeline.csv').open() as f:rows=list(csv.DictReader(f))
  if [r['slide_id'] for r in rows]!=[s['id'] for s in scenes]:raise ValueError('Timeline não corresponde aos slides.')
  if float(rows[0]['inicio_s'])!=0:raise ValueError('Timeline não começa em zero.')
  for r in rows:
   if float(r['fim_s'])<=float(r['inicio_s']) or int(r['frame_fim'])<=int(r['frame_inicio']):raise ValueError('Intervalo inválido.')
  for x,y in zip(rows,rows[1:]):
   if x['fim_s']!=y['inicio_s'] or x['frame_fim']!=y['frame_inicio']:raise ValueError('Timeline descontínua.')
  report.update(timeline_continua=True,duracao_s=float(rows[-1]['fim_s']))
 if a.video:
  if not report.get('timeline_continua'):raise ValueError('Timeline ausente.')
  ff=binary('ffmpeg',a.ffmpeg);pr=binary('ffprobe',a.ffprobe);video=root/('video.mp4' if fmt=='16:9' else 'video-'+fmt.replace(':','x')+'.mp4');info=probe(video,pr);v=next(x for x in info['streams'] if x['codec_type']=='video')
  if v['codec_name']!='h264' or v['avg_frame_rate']!='30/1' or v.get('level',-1)<0 or (v['width'],v['height'])!=FORMATS[fmt] or abs(float(info['format']['duration'])-report['duracao_s'])>.1:raise ValueError('Vídeo com metadados incompatíveis.')
  subprocess.run([ff,'-v','error','-xerror','-i',str(video),'-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
  report['decodificacao_integral']=True
 write(out/'validacao.json',report);print(report)
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError,subprocess.CalledProcessError) as e:sys.exit('ERRO: '+str(e))
