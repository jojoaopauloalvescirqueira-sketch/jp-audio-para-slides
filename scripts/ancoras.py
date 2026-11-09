"""Tokenização, correspondência e tempo das âncoras da fala."""
import bisect, difflib, math, re, unicodedata
from projeto import audio_identity, read, write, sha, config
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


def stamp(i, keys, match, heard, count, duration):
  if i in match:return heard[match[i]]['start'],'reconhecido',0,0.
  k=bisect.bisect_left(keys,i);lo=keys[k-1] if k else None;hi=keys[k] if k<len(keys) else None
  if lo is None or hi is None:return None,'sem_ancoras',count,duration
  gap=hi-lo-1;t0=heard[match[lo]]['end'];t1=heard[match[hi]]['start']
  if gap==1 and match[hi]-match[lo]==2:return heard[match[lo]+1]['start'],'variacao_lexical',1,max(0,t1-t0)
  return t0+(t1-t0)*(i-lo)/(hi-lo),'interpolado',gap,max(0,t1-t0)


def tempos_ancoras(root, ancoras, paragraphs=None, estimar=False):
    """Retorna e registra tempos por índice de token, incluindo motivos de revisão."""
    from pathlib import Path
    root = Path(root)
    material = root / 'material'
    project = config(root)
    paragraphs = paragraphs if paragraphs is not None else read(material / 'paragrafos.json')
    count = sum(len(tokens(item['texto'])) for item in paragraphs)
    indices = sorted(set(ancoras))
    if not indices or any(type(i) is not int or not 0 <= i < count for i in indices):
        raise ValueError('Índice de âncora inválido.')
    estimated = estimar or not project.get('audio')
    identity = None
    if estimated:
        duration = count * 60 / 140
        times = [i * 60 / 140 for i in range(count)]
        rows = [dict(palavra=i, tempo=times[i], metodo='estimado', motivos_revisao=[]) for i in indices]
    else:
        duration, heard, expected, _, matched, identity = word_alignment(root, project, paragraphs)
        keys = sorted(matched)
        stamps = [stamp(i, keys, matched, heard, count, duration) for i in range(count)]
        times = [item[0] for item in stamps]
        # Legendas de borda herdam a primeira/última posição conhecida.
        times = [t if t is not None else heard[matched[keys[0] if i < keys[0] else keys[-1]]]['start']
                 for i, t in enumerate(times)]
        rows = []
        for i in indices:
            time, method, _, uncertainty = stamps[i]
            window = range(max(0, i - 10), min(count, i + 15))
            coverage = sum(j in matched for j in window) / len(window)
            reasons = []
            if method != 'reconhecido':
                reasons.append(method)
            if coverage < .65:
                reasons.append('baixa cobertura local')
            if uncertainty > 2:
                reasons.append('incerteza acima de 2 s')
            rows.append(dict(palavra=i, tempo=time, metodo=method, cobertura_local=round(coverage, 3),
                             incerteza_s=uncertainty, motivos_revisao=reasons))
    report = dict(estimado=estimated, duracao_s=duration, audio_identidade=identity, ancoras=rows)
    write(material / 'marcacoes_acoes.json', report)
    return times, report


def require_reviewed_anchors(root, report):
    """Uma marca incerta exige confirmação vinculada ao arquivo atual."""
    pending = {row['palavra'] for row in report['ancoras'] if row['motivos_revisao']}
    if not pending:
        return
    material = root / 'material'
    review_file = material / 'revisao_acoes.json'
    if review_file.is_file():
        review = read(review_file)
        if review.get('marcacoes_sha256') == sha(material / 'marcacoes_acoes.json'):
            checked = {row['palavra'] for row in review.get('conferidos', [])
                       if isinstance(row.get('motivo'), str) and row['motivo'].strip()}
            pending -= checked
    if pending:
        raise ValueError('Revise as âncoras de ações em material/marcacoes_acoes.json.')
