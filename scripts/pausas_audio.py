"""Alinhamento local por pausas e ritmo silábico, sem reconhecimento de fala."""
from array import array
from dataclasses import dataclass
from math import log, sqrt
from pathlib import Path
import re
import subprocess
import tempfile
import sys

from ancoras import tokens, norm
from tags_voz import tag_key
from projeto import read, sha, write

STEP = .01
MIN_GAP = 12
FALLBACK = 'Use marcações do ElevenLabs, recorte manual ou autorize o Whisper.'
VOICE = re.compile(r'\[([^\[\]\n]+)\]')


@dataclass(frozen=True)
class Phrase:
    paragraph: str
    text: str
    words: tuple
    start: int
    weight: int
    boundary: str
    tags: tuple


def syllables(word):
    value = norm(word).replace('qu', 'q').replace('gue', 'ge').replace('gui', 'gi')
    nuclei = re.findall(r'[aeiouy]+', value)
    return max(1, len(nuclei) + sum(max(0, len(re.findall('[aeo]', group))-1) for group in nuclei))


def phrases(paragraphs, studio=None):
    marked = re.split(r'\n\s*\n', studio.strip()) if studio else []
    if studio and len(marked) != len(paragraphs):
        raise ValueError('O Studio precisa ter os mesmos parágrafos da fala canônica.')
    offset = 0
    result = []
    for index, paragraph in enumerate(paragraphs):
        clean = paragraph['texto']
        source = marked[index] if studio else clean
        # Only controls removed in the canonical text are controls in this comparison.
        clean_tags = {tag_key(x) for x in VOICE.findall(clean)}
        text = ''
        controls = {}
        pos = 0
        for m in VOICE.finditer(source):
            key = tag_key(m[1])
            if key in clean_tags:
                continue
            text += source[pos:m.start()]
            controls.setdefault(len(tokens(text)), []).append(key)
            pos = m.end()
        text += source[pos:]
        words = tokens(text)
        if [norm(w) for w,_ in words] != [norm(w) for w,_ in tokens(clean)]:
            raise ValueError(f'O Studio diverge da fala canônica em {paragraph["id"]}.')
        begin = 0
        for i,(word,start) in enumerate(words):
            end = start+len(word)
            next_word = words[i+1][1] if i+1 < len(words) else len(text)
            between = text[end:next_word]
            trailing = re.match(r'\s*[,;:.?!…]+', between)
            punctuation = trailing[0].strip()[-1] if trailing else ''
            last = i+1 == len(words)
            if not (punctuation or 'pausa' in controls.get(i+1,[]) or last):
                continue
            clause = tuple(w for w,_ in words[begin:i+1])
            strength = ('pausa' if 'pausa' in controls.get(i+1,[]) else
                        'paragrafo' if last else 'forte' if punctuation in '.?!…' and punctuation else 'leve')
            found_tags = tuple((offset+j,key) for j in range(begin,i+1) for key in controls.get(j,[]))
            result.append(Phrase(paragraph['id'],text[words[begin][1]:next_word].strip(),
                                 clause,offset+begin,sum(map(syllables,clause)),strength,found_tags))
            begin = i+1
        offset += len(words)
    return result


def acoustic(files, ffmpeg):
    rms, peaks = [], []
    for file in files:
        command = [ffmpeg,'-v','error','-i',str(file),'-vn','-ac','1','-ar','16000','-f','s16le','-']
        with subprocess.Popen(command,stdout=subprocess.PIPE) as child:
            while True:
                chunk=child.stdout.read(320)
                if not chunk:
                    break
                values=array('h')
                values.frombytes(chunk)
                if sys.byteorder!='little':
                    values.byteswap()
                rms.append(sqrt(sum(v*v for v in values)/len(values)))
                peaks.append(max(abs(v) for v in values))
            if child.wait():
                raise ValueError('O FFmpeg não conseguiu ler a narração.')
    return rms, peaks


def speech_blocks(rms, peaks):
    if len(rms) != len(peaks) or not rms:
        raise ValueError('Não foi possível medir energia da narração.')
    level=sorted(rms)[round(.93*(len(rms)-1))]
    if level<=0:
        raise ValueError('Não há fala distinguível. '+FALLBACK)
    peak_limit=max(14,level*.142)
    rms_limit=max(7,level*.060)
    gaps=[]
    start=None
    for i,(value,peak) in enumerate(zip(rms+[float('inf')],peaks+[float('inf')])):
        if value < rms_limit and peak < peak_limit:
            if start is None: start=i
        elif start is not None:
            if i-start>=MIN_GAP: gaps.append((start,i))
            start=None
    blocks=[]
    begin=0
    for low,high in gaps:
        if low>begin: blocks.append((begin,low))
        begin=high
    if begin<len(rms): blocks.append((begin,len(rms)))
    return blocks


def match(clauses, blocks):
    """Costura monotônica com estados alternativos para detectar ambiguidade."""
    n,m=len(clauses),len(blocks)
    if not n or not m:
        raise ValueError('Não há frases ou pausas suficientes. '+FALLBACK)
    spoken=[0]
    for a,b in blocks: spoken.append(spoken[-1]+b-a)
    weights=[0]
    for phrase in clauses: weights.append(weights[-1]+phrase.weight)
    pace=spoken[-1]*STEP/weights[-1]
    states={(0,0):[(0.,None)]}
    missed={'leve':.39,'forte':2.0,'pausa':2.5,'paragrafo':2.3}
    for i in range(n):
        for j in range(m):
            current=states.get((i,j),())
            if not current: continue
            missing=0.
            for a in range(i+1,min(n,i+6)+1):
                if a>i+1: missing+=missed[clauses[a-2].boundary]
                ideal=(weights[a]-weights[i])*pace
                for b in range(j+1,min(m,j+5)+1):
                    if (a==n)!=(b==m): continue
                    duration=(spoken[b]-spoken[j])*STEP
                    mismatch=log((duration+.06)/(ideal+.06))
                    gap=(blocks[b][0]-blocks[b-1][1])*STEP if b<m else .6
                    strength=clauses[a-1].boundary
                    penalty=2.8*mismatch*mismatch+missing+.37*(b-j-1)
                    if strength=='leve': penalty+=.65*max(0,gap-.19)
                    else: penalty+=1.2*max(0,.26-gap)
                    if strength=='pausa': penalty+=.6*max(0,.4-gap)
                    key=(a,b)
                    bucket=states.setdefault(key,[])
                    for rank,(cost,_) in enumerate(current):
                        bucket.append((cost+penalty,(i,j,rank,mismatch)))
                    bucket.sort(key=lambda x:x[0])
                    del bucket[2:]
    final=states.get((n,m))
    if not final:
        raise ValueError('Não foi possível casar o roteiro à gravação. '+FALLBACK)

    def path(rank):
        a,b=n,m
        out=[]
        while a or b:
            _,(i,j,rank,residual)=states[a,b][rank]
            out.append((i,a,j,b,residual))
            a,b=i,j
        return out[::-1]

    return path(0), path(1) if len(final)>1 and final[1][0]-final[0][0]<.22 else []


def word_boundaries(words, start, end, rms):
    from pictograma_sincronia import refine

    weights=[syllables(w) for w in words]
    total=sum(weights)
    rows=[]
    elapsed=0
    for i,word in enumerate(words):
        expected=start+(end-start)*elapsed/total
        elapsed+=weights[i]
        if i==0:
            point=start
            method='ancora_frase'
        else:
            previous=rows[-1]['inicio_s']
            upcoming=start+(end-start)*elapsed/total
            onset=refine(expected,rms,max(previous+.03,expected-.15),
                         min(end-.025,(expected+upcoming)/2+.02))
            method='estimativa_energia_baixa'
            point=expected
            bin_=round(onset/STEP)
            before=sum(rms[max(0,bin_-3):bin_])/3
            after=sum(rms[bin_:bin_+3])/3
            if onset!=expected or (after>=max(150,before*2.25) and rms[bin_]>before*1.35):
                a=max(round((previous+.025)/STEP),bin_-3)
                if a<=bin_:
                    point=min(range(a,bin_+1),key=lambda k:rms[k])*STEP
                    method='refinado_energia'
            point=max(previous+.001,min(end-.001,point))
        rows.append({'texto':word,'inicio_s':round(point,4),'metodo':method,
                     'motivos_revisao':[]})
    for i,row in enumerate(rows):
        row['fim_s']=rows[i+1]['inicio_s'] if i+1<len(rows) else end
    return rows


def selection(clauses, paragraphs, interval=None, first=None, last=None):
    from cenas import Words
    words=Words(paragraphs)
    if not interval:
        if first or last: raise ValueError('Use --trecho ao informar âncoras literais.')
        return 0,len(words.words)
    ids=list(words.by_id)
    parts=interval.upper().split('-')
    if len(parts)==1: parts*=2
    if len(parts)!=2 or any(p not in ids for p in parts) or ids.index(parts[0])>ids.index(parts[1]):
        raise ValueError('Informe um intervalo crescente, como P007-P008.')
    a=words.anchor({'p':parts[0],'trecho':first}) if first else words.by_id[parts[0]][0]
    if last:
        b=words.anchor({'p':parts[1],'trecho':last})+len(tokens(last))
    else:
        nxt=ids.index(parts[1])+1
        b=words.by_id[ids[nxt]][0] if nxt<len(ids) else len(words.words)
    if a>=b:
        raise ValueError('As âncoras do recorte estão invertidas.')
    return a,b


def aligned(clauses, blocks, rms, lo, hi):
    route, alternate=match(clauses,blocks)
    alternates={i:(j,b) for a,z,j,b,_ in alternate for i in range(a,z)}
    full=[]
    words=[]
    missing=[]
    for a,z,j,b,residual in route:
        group=clauses[a:z]
        start,end=blocks[j][0]*STEP,blocks[b-1][1]*STEP
        row_words=[w for phrase in group for w in phrase.words]
        base=group[0].start
        measured=word_boundaries(row_words,start,end,rms)
        words.extend(measured)
        soft=[{'texto':c.text,'paragrafo':c.paragraph,'tipo':c.boundary} for c in group[:-1]]
        missing.extend(soft)
        weak=abs(residual)>log(2.15) or any(c.boundary!='leve' for c in group[:-1])
        ambiguous=any(alternates.get(k,(j,b))!=(j,b) for k in range(a,z))
        full.append({'texto':' '.join(c.text for c in group),'paragrafo':group[0].paragraph,
                     'inicio_palavra':base,'fim_palavra':base+len(row_words),
                     'inicio_s':round(start,3),'fim_s':round(end,3),'pontuacao_final':group[-1].boundary,
                     'tags':[{'palavra':idx,'tag':tag} for c in group for idx,tag in c.tags],
                     'sem_pausa':soft,'confianca':'baixa' if weak or ambiguous else 'alta',
                     'desvio_log_duracao':round(residual,4)})

    selected=[]
    warnings=[]
    for row in full:
        a,b=row['inicio_palavra'],row['fim_palavra']
        if max(a,lo)>=min(b,hi): continue
        item=dict(row)
        if a<lo or hi<b:
            if a<lo:
                item['inicio_s']=words[lo]['inicio_s']
                item['inicio_palavra']=lo
            if hi<b:
                item['fim_s']=words[hi]['inicio_s']
                item['fim_palavra']=hi
            item['texto']=' '.join(w['texto'] for w in words[max(a,lo):min(b,hi)])
            if item['fim_palavra']==b:
                item['texto']+=row['texto'][-1] if row['texto'][-1] in '.?!,;:' else ''
            for boundary in ([lo] if a<lo else [])+([hi] if hi<b else []):
                if words[boundary]['metodo']=='estimativa_energia_baixa':
                    item['confianca']='baixa'
        if item['confianca']=='baixa':
            warnings.append(f'{item["paragrafo"]} · {item["texto"]}')
        selected.append(item)
    if not selected:
        raise ValueError('O intervalo não tem frases alinhadas.')
    start=selected[0]['inicio_s']
    for row in selected:
        row['inicio_relativo_s']=round(row['inicio_s']-start,4)
        row['fim_relativo_s']=round(row['fim_s']-start,4)
    return {'origem':'pausas_do_audio','confianca':'baixa' if warnings else 'alta',
            'inicio_s':start,'fim_s':selected[-1]['fim_s'],'frases':selected,
            'frases_completas':full,'palavras':words,'pontuacoes_sem_silencio':missing,
            'divergencias':warnings}


def stamp_srt(seconds):
    ms=round(seconds*1000)
    h,ms=divmod(ms,3600000)
    m,ms=divmod(ms,60000)
    s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'


def write_srt(path, rows):
    path.write_text('\n\n'.join(f'{i}\n{stamp_srt(row["inicio_relativo_s"])} --> '
                                 f'{stamp_srt(row["fim_relativo_s"])}\n{row["texto"]}'
                                 for i,row in enumerate(rows,1))+'\n',encoding='utf-8')


def from_project(root, project, paragraphs, files, ffmpeg, interval=None, first=None, last=None):
    from pictograma_sincronia import identity

    material=root/'material'
    studio_path=material/'roteiro_studio.txt'
    studio=studio_path.read_text(encoding='utf-8-sig') if studio_path.is_file() else None
    clauses=phrases(paragraphs,studio)
    lo,hi=selection(clauses,paragraphs,interval,first,last)
    rms,peaks=acoustic(files,ffmpeg)
    report=aligned(clauses,speech_blocks(rms,peaks),rms,lo,hi)
    report['identidade']=identity(root,project,paragraphs)
    report['studio_sha256']=sha(studio_path) if studio else None
    write(material/'marcacoes_frases.json',report)
    if report['divergencias']:
        raise ValueError('Confiança baixa em '+ '; '.join(report['divergencias'])+'. '+FALLBACK)
    write_srt(material/'marcacoes_frases.srt',report['frases'])
    if studio:
        from efeito_tags import register_effects
        register_effects(material,report)
    return report


def render_excerpt(material, files, report, ffmpeg):
    if len(files)!=1:
        raise ValueError('O recorte automático requer uma narração completa em um só arquivo.')
    start,end=report['inicio_s'],report['fim_s']
    target=material/'trecho_narracao.wav'
    with tempfile.TemporaryDirectory(dir=material) as temporary:
        staged=Path(temporary)/target.name
        subprocess.run([ffmpeg,'-v','error','-ss',f'{start:.4f}','-i',str(files[0]),
                        '-t',f'{end-start:.4f}','-map','0:a:0','-c:a','pcm_s16le',str(staged)],check=True)
        staged.replace(target)
    return target.name
