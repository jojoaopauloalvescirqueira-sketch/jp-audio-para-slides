#!/usr/bin/env python3
"""Alinhamento monotônico e relatório de pontos que exigem revisão."""
import argparse,bisect,sys
from pathlib import Path
from projeto import load,audio_identity,read,write,sha
from ancoras import tokens, stamp, word_alignment

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--transcricao',type=Path);a=ap.parse_args();root=a.root.resolve();c,ps,scenes,_=load(root)
 duration, heard, expected, starts, match, identity = word_alignment(root,c,ps,a.transcricao)
 keys=sorted(match);aa=expected
 marks=[];reviews=[];global_coverage=len(match)/len(aa);long_gaps=[]
 run_start=None
 for idx in range(len(aa)+1):
  if idx<len(aa) and idx not in match:
   if run_start is None:run_start=idx
  elif run_start is not None:
   if idx-run_start>=20:long_gaps.append({'token_inicio':run_start,'tokens':idx-run_start,'texto':' '.join(expected[run_start:idx])})
   run_start=None
 for s in scenes:
  i=starts[s['p']-1]+sum(pos<s['char_start'] for _,pos in tokens(ps[s['p']-1]['texto']));t,method,gap,seconds=stamp(i,keys,match,heard,len(aa),duration);window=range(max(0,i-10),min(len(aa),i+15));coverage=sum(j in match for j in window)/len(window);reasons=[]
  if c['perfil_visual']=='editorial_jp' and s.get('conferir_audio'):reasons.append('entrada crítica indicada no plano visual')
  if t is None:reasons.append('entrada sem âncoras dos dois lados')
  if method!='reconhecido':reasons.append('entrada '+method)
  if coverage<.65:reasons.append('baixa correspondência textual local; conferir também números por extenso')
  if gap>3 or seconds>2:reasons.append('intervalo de incerteza amplo')
  k=bisect.bisect_left(keys,i);nearest=keys[min(k,len(keys)-1)];j=match.get(i,match[nearest]);context=' '.join(w['text'] for w in heard[max(0,j-3):j+18])
  if not marks:t=0.
  row={'slide_id':s['id'],'inicio_s':t,'texto_entrada':s['frase_gatilho'],'metodo':method,'cobertura_local':round(coverage,3),'tokens_incertos':gap,'intervalo_incerteza_s':seconds,'asr_contexto':context,'motivos_revisao':reasons};marks.append(row)
  if reasons:reviews.append(s['id'])
 if global_coverage<.65 or long_gaps:reviews.append('GLOBAL')
 for i,m in enumerate(marks):
  end=marks[i+1]['inicio_s'] if i+1<len(marks) else duration;m['fim_s']=end
  if m['inicio_s'] is None or end is None or not 0<=m['inicio_s']<end<=duration:reviews.append(m['slide_id']);m['motivos_revisao'].append('limites temporais inválidos')
 write(root/'material/marcacoes_audio.json',{'audio_identidade':identity,'plano_sha256':sha(root/'material/slides.json'),'roteiro_sha256':sha(root/'material/paragrafos.json'),'duracao_s':duration,'cobertura_global':global_coverage,'trechos_extensos_nao_reconhecidos':long_gaps,'slides':marks,'revisao':{'pendencias':list(dict.fromkeys(reviews)),'conferidos':[]}})
 print(f'{len(marks)} entradas; cobertura textual {global_coverage:.1%}; {len(set(reviews))} pontos para conferir. Correspondência textual não é precisão acústica.')
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError) as e:sys.exit(str(e))
