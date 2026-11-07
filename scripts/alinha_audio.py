#!/usr/bin/env python3
"""Alinhamento monotônico e relatório de pontos que exigem revisão."""
import argparse,bisect,difflib,re,sys,unicodedata,math
from pathlib import Path
from projeto import load,audio_identity,read,write,sha
from tags_voz import preference

def tokens(s):return [(m.group(),m.start()) for m in re.finditer(r'\w+(?:[.,]\d+)*',s)]
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))
def check_external_speech(material, matcher, expected, heard, paragraphs, starts, transcript_hash):
    script_hash = sha(material / 'paragrafos.json')
    differences = []
    for op, a, b, c, d in matcher.get_opcodes():
        if op == 'equal':
            continue
        index = bisect.bisect_right(starts, min(a, len(expected) - 1)) - 1
        first = heard[min(c, len(heard) - 1)]
        start = first['start'] if c < d else (heard[c - 1]['end'] if c else first['start'])
        differences.append({
            'tipo': op, 'p_inicio': paragraphs[index]['id'],
            'esperado': ' '.join(expected[a:b]),
            'reconhecido': ' '.join(word['text'] for word in heard[c:d]),
            'inicio_s': start, 'fim_s': heard[d - 1]['end'] if c < d else start,
        })

    identity = {'transcricao_sha256': transcript_hash, 'roteiro_sha256': script_hash}
    review_path = material / 'revisao_fala_asr.json'
    reviewed = False
    if differences and review_path.is_file():
        review = read(review_path)
        reviewed = (all(review.get(key) == value for key, value in identity.items())
                    and review.get('resultado') == 'variacao_asr'
                    and isinstance(review.get('justificativa'), str)
                    and bool(review['justificativa'].strip()))
    write(material / 'divergencias_asr.json', {
        **identity, 'divergencias': differences,
        'estado': 'conferido' if reviewed or not differences else 'pendente',
    })
    if differences and not reviewed:
        raise ValueError(f'{len(differences)} divergências na fala reconhecida. Confira material/divergencias_asr.json antes de alinhar.')


def word_alignment(root,c,ps,transcript=None):
 """Mapeia cada token canônico ao timestamp reconhecido, quando há correspondência."""
 material=root/'material';tr_path=transcript or material/'transcricao_asr.json';tr=read(tr_path)
 if not isinstance(tr,dict) or tr.get('audio_identidade')!=audio_identity(root,c,ps):raise ValueError('Transcrição sem identidade válida para os áudios atuais.')
 duration=float(tr['duracao_s']);heard=[]
 if not math.isfinite(duration) or duration<=0:raise ValueError('Duração da transcrição inválida.')
 for seg in tr['segmentos']:
  for w in seg['words']:
   if not (math.isfinite(w['start']) and math.isfinite(w['end']) and 0<=w['start']<=w['end']<=duration+.15):raise ValueError('Timestamp ASR inválido.')
   ts=tokens(w['word'])
   for k,(t,_) in enumerate(ts):heard.append({'text':t,'start':w['start']+(w['end']-w['start'])*k/len(ts),'end':w['start']+(w['end']-w['start'])*(k+1)/len(ts)})
 if not heard:raise ValueError('Alinhamento insuficiente: não há palavras reconhecidas.')
 if any(v['start']<u['start'] for u,v in zip(heard,heard[1:])):raise ValueError('Timestamps ASR não monotônicos.')
 expected=[];starts=[]
 for p in ps:starts.append(len(expected));expected.extend(t for t,_ in tokens(p['texto']))
 aa=[norm(t) for t in expected];bb=[norm(w['text']) for w in heard];match={}
 matcher=difflib.SequenceMatcher(None,aa,bb,autojunk=False)
 if preference(c.get('direcao_narrativa'),'tags')=='elevenlabs':
  check_external_speech(material,matcher,expected,heard,ps,starts,sha(tr_path))
 for block in matcher.get_matching_blocks():
  for k in range(block.size):match[block.a+k]=block.b+k
 keys=sorted(match)
 if not keys:raise ValueError('Alinhamento insuficiente: não há correspondências com o roteiro.')
 return duration,heard,expected,starts,match,tr['audio_identidade']


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--transcricao',type=Path);a=ap.parse_args();root=a.root.resolve();c,ps,scenes,_=load(root)
 duration, heard, expected, starts, match, identity = word_alignment(root,c,ps,a.transcricao)
 keys=sorted(match);aa=[norm(t) for t in expected]
 def stamp(i):
  if i in match:return heard[match[i]]['start'],'reconhecido',0,0.
  k=bisect.bisect_left(keys,i);lo=keys[k-1] if k else None;hi=keys[k] if k<len(keys) else None
  if lo is None or hi is None:return None,'sem_ancoras',len(aa),duration
  gap=hi-lo-1;t0=heard[match[lo]]['end'];t1=heard[match[hi]]['start']
  if gap==1 and match[hi]-match[lo]==2:return heard[match[lo]+1]['start'],'variacao_lexical',1,max(0,t1-t0)
  return t0+(t1-t0)*(i-lo)/(hi-lo),'interpolado',gap,max(0,t1-t0)
 marks=[];reviews=[];global_coverage=len(match)/len(aa);long_gaps=[]
 run_start=None
 for idx in range(len(aa)+1):
  if idx<len(aa) and idx not in match:
   if run_start is None:run_start=idx
  elif run_start is not None:
   if idx-run_start>=20:long_gaps.append({'token_inicio':run_start,'tokens':idx-run_start,'texto':' '.join(expected[run_start:idx])})
   run_start=None
 for s in scenes:
  i=starts[s['p']-1]+sum(pos<s['char_start'] for _,pos in tokens(ps[s['p']-1]['texto']));t,method,gap,seconds=stamp(i);window=range(max(0,i-10),min(len(aa),i+15));coverage=sum(j in match for j in window)/len(window);reasons=[]
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
