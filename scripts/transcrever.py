#!/usr/bin/env python3
"""Reconhecimento local de áudio pronto; não gera narração nem envia áudio."""
import argparse,sys
from pathlib import Path
from projeto import config,read,audio,audio_files,audio_identity,binary,probe,write

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--model',default='base');p.add_argument('--model-dir');p.add_argument('--local-only',action='store_true');p.add_argument('--threads',type=int,default=4);p.add_argument('--ffprobe');a=p.parse_args();root=a.root.resolve();c=config(root);ps=read(root/'material/paragrafos.json');files=audio_files(audio(root,c),len(ps));ffprobe=binary('ffprobe',a.ffprobe)
 try:
  import av
  from faster_whisper import WhisperModel
 except ImportError as e:raise ValueError('Instale faster-whisper em um ambiente Python compatível para transcrever localmente.') from e
 # PyAV 19 removed metadata_errors; retry only that unsupported keyword.
 original=av.open
 def compatible(*args,**kw):
  try:return original(*args,**kw)
  except TypeError as e:
   if 'metadata_errors' not in kw or 'metadata_errors' not in str(e):raise
   kw.pop('metadata_errors');return original(*args,**kw)
 av.open=compatible
 model=WhisperModel(a.model,device='cpu',compute_type='int8',cpu_threads=a.threads,download_root=a.model_dir,local_files_only=a.local_only)
 segments=[];offset=0.;paragraphs=[]
 for i,f in enumerate(files,1):
  duration=float(probe(f,ffprobe)['format']['duration']);segs,info=model.transcribe(str(f),language=c['idioma'],word_timestamps=True,beam_size=3,vad_filter=True)
  for s in segs:
   segments.append({'start':s.start+offset,'end':s.end+offset,'text':s.text,'words':[{'word':w.word,'start':w.start+offset,'end':w.end+offset,'probability':w.probability} for w in s.words]})
  if len(files)>1:paragraphs.append({'paragrafo':f'P{i:03}','inicio_s':offset,'fim_s':offset+duration})
  offset+=duration;print(f'{i}/{len(files)} · {offset:.2f}s medidos',flush=True)
 write(root/'material/transcricao_asr.json',{'audio_identidade':audio_identity(root,c,ps),'duracao_s':offset,'motor':'faster-whisper','modelo':a.model,'idioma':c['idioma'],'segmentos':segments,'paragrafos_medidos':paragraphs})
if __name__=='__main__':
 try:main()
 except ValueError as e:sys.exit(str(e))
