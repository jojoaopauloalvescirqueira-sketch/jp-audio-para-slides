"""Tempos de palavras, forma de onda e ajustes para animação por quadro."""
from array import array
from collections import deque
from html import unescape
import json
import os
from pathlib import Path
from importlib.util import find_spec
import math
import re
import subprocess
import sys

from ancoras import norm, stamp, tokens, word_alignment
from pictograma_tempo import final_frame
from projeto import audio, audio_files, audio_identity, binary, config, probe, read, sha, write

SOURCE='sincronia_fonte.json'
MANUAL='sincronia_manual.json'
RECOGNITION='transcricao_asr.json'
ENERGY='sincronia_energia.json'
PAUSES='marcacoes_frases.json'


def words_in(text):
    return [norm(word) for word,_ in tokens(text)]


def sec(value):
    fields=value.replace(',','.').split(':')
    return sum(float(part)*60**index for index,part in enumerate(reversed(fields)))


def subtitle_rows(path):
    content=path.read_text(encoding='utf-8-sig').replace('\r','')
    cue=[]
    inline=[]
    complete=True
    for block in re.split(r'\n\s*\n',content.strip()):
        lines=block.splitlines()
        line=next((i for i,text in enumerate(lines) if '-->' in text),None)
        if line is None:
            continue
        a,b=lines[line].split('-->',1)
        start,end=sec(a.strip()),sec(b.split()[0])
        phrase=unescape(' '.join(lines[line+1:]))
        cue.append({'texto':re.sub(r'<[^>]*>','',phrase),'inicio_s':start,'fim_s':end})
        pieces=re.split(r'<((?:\d{2}:)?\d{2}:\d{2}[.]\d{3})>',phrase)
        parts=[re.sub(r'<[^>]*>','',part).strip() for part in pieces[::2]]
        starts=[start,*map(sec,pieces[1::2]),end]
        if any(len(words_in(part))>1 for part in parts):
            complete=False
        inline.extend({'texto':part,'inicio_s':starts[i],'fim_s':starts[i+1]}
                      for i,part in enumerate(parts) if words_in(part))
    if not cue:
        raise ValueError('SRT/VTT sem legendas temporizadas.')
    return ('palavras',inline) if complete else ('frases',cue)


def json_rows(data):
    if isinstance(data,dict):
        data=data.get('normalized_alignment') or data.get('alignment') or data
    if isinstance(data,dict) and 'characters' in data:
        characters=data['characters']
        starts=data.get('character_start_times_seconds',[])
        ends=data.get('character_end_times_seconds',[])
        if (not isinstance(characters,list) or not all(isinstance(c,str) and len(c)==1 for c in characters)
                or not len(characters)==len(starts)==len(ends)):
            raise ValueError('Alinhamento por caractere inválido.')
        return [{'texto':word,'inicio_s':starts[index],'fim_s':ends[index+len(word)-1]}
                for word,index in tokens(''.join(characters))]
    rows=data.get('words',data.get('palavras')) if isinstance(data,dict) else data
    if not isinstance(rows,list) or not rows or not all(isinstance(row,dict) for row in rows):
        raise ValueError('Forneça palavras com início e fim ou alinhamento por caractere.')
    return [{'texto':row.get('word',row.get('texto')),
             'inicio_s':row.get('start',row.get('inicio_s')),
             'fim_s':row.get('end',row.get('fim_s'))} for row in rows]


def validate_rows(kind, rows, expected, duration):
    actual=[]
    previous=-1
    for row in rows:
        text,start,end=(row[key] for key in ('texto','inicio_s','fim_s'))
        if (not isinstance(text,str) or not all(type(t) in (float,int) and math.isfinite(t) for t in (start,end))
                or not 0<=start<end<=duration+.04 or start<previous):
            raise ValueError('As marcações têm texto ou intervalos inválidos para esta narração.')
        units=words_in(text)
        if not units or kind=='palavras' and len(units)!=1:
            raise ValueError('Uma marcação por palavra deve corresponder a um único token canônico.')
        actual.extend(units)
        previous=start
    if actual!=expected:
        raise ValueError('A fala das marcações diverge do roteiro canônico.')


def recording(root, project, paragraphs, ffprobe):
    files=audio_files(audio(root,project),len(paragraphs))
    durations=[]
    for file in files:
        metadata=probe(file,binary('ffprobe',ffprobe))
        if not any(s['codec_type']=='audio' for s in metadata['streams']):
            raise ValueError('O arquivo fornecido não contém áudio.')
        durations.append(float(metadata['format']['duration']))
    return files, durations


def identity(root, project, paragraphs):
    return {'audio_identidade':audio_identity(root,project,paragraphs),
            'roteiro_sha256':sha(root/'material/paragrafos.json')}


def source_path(material):
    imported=material/SOURCE
    if imported.is_file():
        kind=read(imported)['tipo']
        if kind=='palavras':
            return imported
        if kind=='frases':
            return material/ENERGY if (material/ENERGY).is_file() else imported
    if (material/RECOGNITION).is_file():
        return material/RECOGNITION
    return material/PAUSES


def identity_for_edits(root, project, paragraphs):
    material=root/'material'
    source=material/SOURCE
    base=source_path(material)
    if not base.is_file():
        raise ValueError('Forneça marcações por palavra ou execute o reconhecimento local da narração.')
    return {**identity(root,project,paragraphs),
            'base_sha256':sha(base),
            'legenda_sha256':sha(source) if source.is_file() else None}


def import_timing(root, args):
    project=config(root)
    if project.get('estilo_video')!='pictograma':
        raise ValueError('Este editor de sincronia pertence ao Pictograma.')
    material=root/'material'
    paragraphs=read(material/'paragrafos.json')
    expected=[word for paragraph in paragraphs for word in words_in(paragraph['texto'])]
    files, durations=recording(root,project,paragraphs,args.ffprobe)
    total=sum(durations)
    interval=getattr(args,'trecho',None)
    first=getattr(args,'de',None)
    last=getattr(args,'ate',None)
    origin=getattr(args,'origem',None)
    if args.importar and (interval or first or last or origin):
        raise ValueError('Importe os ajustes separadamente da seleção do trecho.')
    if args.fonte:
        if args.fonte.suffix.lower() in ('.srt','.vtt'):
            kind,rows=subtitle_rows(args.fonte)
        else:
            kind,rows='palavras',json_rows(read(args.fonte))
        validate_rows(kind,rows,expected,total)
        saved={'identidade':identity(root,project,paragraphs),'tipo':kind,'marcacoes':rows,
               'arquivo':args.fonte.name,'sha256':sha(args.fonte),
               'origem':origin or ('srt_usuario' if args.fonte.suffix.lower() in ('.srt','.vtt') else 'usuario')}
        write(material/SOURCE,saved)
        if not (interval or first or last):
            return {'tipo':kind,'marcacoes':len(rows),'origem':saved['origem']}
    if not args.importar:
        return locate(root,project,paragraphs,files,args.ffmpeg,args.ffprobe,interval,first,last)
    baseline=identity_for_edits(root,project,paragraphs)
    imported=read(args.importar)
    if not isinstance(imported,dict) or imported.get('identidade')!=baseline:
        raise ValueError('O ajuste pertence a outro áudio, fala ou fonte de alinhamento.')
    points=parse_adjustments(imported,len(expected),total)
    # Validate the complete resulting sequence before replacing an earlier review.
    timing(root,project,paragraphs,False,args.ffmpeg,args.ffprobe,adjustments=points)
    write(material/MANUAL,{'identidade':baseline,'pontos':imported['pontos']})
    return {'palavras_conferidas':len(points)}


def use_local_recognition(root, ffprobe):
    if find_spec('faster_whisper') is None:
        return
    model=os.environ.get('JP_WHISPER_MODELO_LOCAL')
    if not model:
        cache=Path(os.environ.get('HF_HUB_CACHE',Path.home()/'.cache/huggingface/hub'))
        candidates=sorted(cache.glob('models--Systran--faster-whisper-base/snapshots/*/model.bin'))
        model=str(candidates[-1].parent) if candidates else None
    if not model or not (Path(model)/'model.bin').is_file():
        return
    subprocess.run([sys.executable,str(Path(__file__).with_name('transcrever.py')),
                    '--root',str(root),'--model',model,'--local-only','--ffprobe',binary('ffprobe',ffprobe)],
                   check=True)


def locate(root, project, paragraphs, files, ffmpeg, ffprobe, interval=None, first=None, last=None):
    from pausas_audio import from_project, phrases, render_excerpt, selection, write_srt, FALLBACK

    material=root/'material'
    imported=material/SOURCE
    if not imported.is_file() and not (material/RECOGNITION).is_file():
        use_local_recognition(root,ffprobe)
    if not imported.is_file() and not (material/RECOGNITION).is_file():
        report=from_project(root,project,paragraphs,files,binary('ffmpeg',ffmpeg),interval,first,last)
        result={key:report[key] for key in ('origem','confianca','inicio_s','fim_s','frases')}
        if interval and len(files)==1:
            result['audio_recortado']=render_excerpt(material,files,report,binary('ffmpeg',ffmpeg))
        return result
    lo,hi=selection([],paragraphs,interval,first,last)
    sync=timing(root,project,paragraphs,False,ffmpeg,ffprobe)
    words=sync['palavras']
    selected=words[lo:hi]
    start,end=selected[0]['inicio_s'],selected[-1]['fim_s']
    rows=[]
    all_units=[]
    cursor=0
    if imported.is_file() and read(imported)['tipo']=='frases':
        source=read(imported)
        units=[]
        for cue in source['marcacoes']:
            count=len(words_in(cue['texto']))
            units.append((cursor,cursor+count,cue['texto']))
            cursor+=count
    else:
        units=[(clause.start,clause.start+len(clause.words),clause.text) for clause in phrases(paragraphs)]
    studio=material/'roteiro_studio.txt'
    tagged=phrases(paragraphs,studio.read_text(encoding='utf-8-sig')) if studio.is_file() else []
    for a,b,text in units:
        t0,t1=words[a]['inicio_s'],words[b-1]['fim_s']
        clause=next((part for part in tagged if part.start<=a<part.start+len(part.words)),None)
        all_units.append({'texto':text,'inicio_s':t0,'fim_s':t1,'inicio_palavra':a,'fim_palavra':b,
                          'paragrafo':clause.paragraph if clause else '',
                          'confianca':'baixa' if any(w['motivos_revisao'] for w in words[a:b]) else 'alta',
                          'tags':[{'tag':tag,'palavra':idx} for part in tagged
                                  for idx,tag in part.tags if a<=idx<b]})
        left,right=max(a,lo),min(b,hi)
        if left>=right: continue
        t0,t1=words[left]['inicio_s'],words[right-1]['fim_s']
        rows.append({'texto':text if (a,b)==(left,right) else ' '.join(row['texto'] for row in words[left:right]),
                     'inicio_s':t0,'fim_s':t1,'inicio_palavra':left,'fim_palavra':right,
                     'inicio_relativo_s':round(t0-start,4),'fim_relativo_s':round(t1-start,4)})
    uncertain=[row['texto'] for row in selected if row['motivos_revisao']]
    report={'origem':read(imported).get('origem','usuario') if imported.is_file() else 'whisper_local',
            'identidade':identity(root,project,paragraphs),'inicio_s':start,'fim_s':end,
            'confianca':'baixa' if uncertain else 'alta','frases':rows,'divergencias':uncertain}
    write(material/PAUSES,report)
    if uncertain:
        raise ValueError('Confiança baixa em '+', '.join(uncertain)+'. '+FALLBACK)
    write_srt(material/'marcacoes_frases.srt',rows)
    if tagged:
        from efeito_tags import register_effects
        register_effects(material,{**report,'frases_completas':all_units,'palavras':words,'studio_sha256':sha(studio)})
    if interval and len(files)==1:
        report['audio_recortado']=render_excerpt(material,files,report,binary('ffmpeg',ffmpeg))
    return report


def parse_adjustments(payload, count, total):
    points=payload.get('pontos')
    if not isinstance(points,list) or not points:
        raise ValueError('O ajuste precisa listar os quadros conferidos.')
    result={}
    for point in points:
        if not isinstance(point,dict) or point.keys()!={'palavra','quadro'}:
            raise ValueError('Cada ajuste exige índice de palavra e quadro.')
        index,frame=point['palavra'],point['quadro']
        if (type(index) is not int or type(frame) is not int or not 0<=index<count
                or not 0<=frame<final_frame(total) or index in result):
            raise ValueError('Ajuste duplicado ou fora da narração.')
        result[index]=frame
    return result


def envelope(files, ffmpeg):
    """RMS mono em blocos de 10 ms, com leitura limitada a um bloco por vez."""
    result=[]
    for file in files:
        command=[ffmpeg,'-v','error','-i',str(file),'-vn','-ac','1','-ar','16000','-f','s16le','-']
        with subprocess.Popen(command,stdout=subprocess.PIPE) as child:
            while True:
                chunk=child.stdout.read(320)
                if not chunk:
                    break
                samples=array('h')
                samples.frombytes(chunk)
                if sys.byteorder!='little':
                    samples.byteswap()
                result.append(math.sqrt(sum(sample*sample for sample in samples)/len(samples)))
            if child.wait():
                raise ValueError('Não foi possível medir a forma de onda.')
    return result


def refine(start, signal, lower, upper):
    center=round(start*100)
    left=max(3,math.ceil(lower*100),center-15)
    right=min(len(signal)-3,math.floor(upper*100),center+15)
    choices=[]
    for i in range(left,right+1):
        before=sum(signal[i-3:i])/3
        after=sum(signal[i:i+3])/3
        if after>=max(150,before*2.25) and signal[i]>before*1.35:
            strength=(after-before)/(after+100)/(1+abs(i-center)*.07)
            choices.append((strength,-abs(i-center),i))
    return max(choices)[2]/100 if choices else start


def cue_ranges(cues):
    result=[]
    for row in cues:
        result.extend([(row['inicio_s'],row['fim_s'])]*len(words_in(row['texto'])))
    return result


def measured_rows(root, project, paragraphs, duration, signal, imported):
    if imported and imported['tipo']=='palavras':
        return [{**row,'metodo':'exportado','motivos_revisao':[]} for row in imported['marcacoes']]
    material=root/'material'
    if imported and imported['tipo']=='frases' and (material/ENERGY).is_file():
        analysis=read(material/ENERGY)
        if (analysis['identidade']!=identity(root,project,paragraphs)
                or analysis['srt_sha256']!=sha(material/SOURCE)):
            raise ValueError('O refinamento de energia pertence a outro áudio, roteiro ou SRT.')
        rows=analysis['palavras']
        expected=[word for paragraph in paragraphs for word in words_in(paragraph['texto'])]
        validate_rows('palavras',rows,expected,duration)
        for row,(low,high) in zip(rows,cue_ranges(imported['marcacoes'])):
            if not low<=row['inicio_s']<row['fim_s']<=high+.0001:
                raise ValueError('O refinamento ultrapassa a frase do SRT.')
        return rows
    if imported and imported['tipo']=='frases':
        from pausas_audio import word_boundaries
        return [{**row,'metodo':('ancora_frase_srt' if row['metodo']=='ancora_frase' else row['metodo'])}
                for cue in imported['marcacoes']
                for row in word_boundaries([w for w,_ in tokens(cue['texto'])],cue['inicio_s'],cue['fim_s'],signal)]
    if not (material/RECOGNITION).is_file() and (material/PAUSES).is_file():
        report=read(material/PAUSES)
        studio=material/'roteiro_studio.txt'
        if (report.get('origem')!='pausas_do_audio' or report.get('identidade')!=identity(root,project,paragraphs)
                or report.get('studio_sha256')!=(sha(studio) if studio.is_file() else None)):
            raise ValueError('As pausas pertencem a outro áudio, Studio ou roteiro. Rode sincronia novamente.')
        if (report['confianca']!='alta' or report['frases'][0]['inicio_palavra']!=0
                or report['frases'][-1]['fim_palavra']!=len(report['palavras'])):
            raise ValueError('Gere a sincronia confiável do projeto inteiro antes de exportá-lo.')
        return report['palavras']
    if not (material/RECOGNITION).is_file():
        raise ValueError('Forneça marcações por palavra ou execute o reconhecimento local da narração.')
    asr_duration,heard,expected,_,matched,_=word_alignment(root,project,paragraphs)
    if abs(asr_duration-duration)>.06:
        raise ValueError('Duração da transcrição difere da narração.')
    keys=sorted(matched)
    cues=cue_ranges(imported['marcacoes']) if imported else [(0.,duration)]*len(expected)
    result=[]
    for i, word in enumerate(expected):
        low,high=cues[i]
        start,method,_,_=stamp(i,keys,matched,heard,len(expected),duration)
        if start is None:
            first,last=keys[0],keys[-1]
            if i<first:
                start=heard[matched[first]]['start']*i/first
            else:
                a=heard[matched[last]]['end']
                start=a+(duration-a)*(i-last-1)/max(1,len(expected)-last-1)
            method='interpolado'
        if method=='reconhecido':
            end=heard[matched[i]]['end']
            refined=refine(start,signal,max(low,start-.15,result[-1]['inicio_s'] if result else 0),
                           min(high,end,start+.15))
            if refined!=start:
                method='refinado'
        else:
            end=start+.08
            refined=start
        reasons=[] if method in ('reconhecido','refinado') else ['revisar '+method]
        if not low-.07<=refined<=high+.07:
            reasons.append('fora da frase exportada')
        result.append({'texto':word,'inicio_s':refined,'fim_s':min(duration,max(end,refined)),
                       'inicio_original_s':start,'ajuste_s':round(refined-start,4),
                       'metodo':method,'motivos_revisao':reasons})
    return result


def caption_groups(words, raw_tokens, width=32, replacements=()):
    from pictograma_legenda import display_tokens
    visible,_=display_tokens(raw_tokens,replacements)
    groups=[]
    lines=[[]]
    length=0
    def flush():
        if lines[0]:
            groups.append([line for line in lines if line])
    for index,(entry,raw) in enumerate(zip(words,raw_tokens)):
        entry['texto']=raw
        shown=visible[index]
        if shown!=raw:
            entry['exibicao']=shown
        needed=len(shown)+(1 if lines[-1] else 0)
        if lines[-1] and length+needed>width:
            if len(lines)==2:
                flush()
                lines=[[]]
            else:
                lines.append([])
            length=0
            needed=len(shown)
        lines[-1].append(index)
        length+=needed
        if re.search(r'[.!?;:]$',raw):
            flush()
            lines=[[]]
            length=0
    flush()
    return [{'linhas':lines,'inicio':words[lines[0][0]]['quadro'],
             'fim':words[lines[-1][-1]]['fim_quadro']+6} for lines in groups]


def timing(root, project, paragraphs, estimated, ffmpeg=None, ffprobe=None, adjustments=None):
    material=root/'material'
    raw=[]
    for paragraph in paragraphs:
        text=paragraph['texto']
        units=tokens(text)
        for i,(word,offset) in enumerate(units):
            cutoff=units[i+1][1] if i+1<len(units) else len(text)
            raw.append(word+''.join(c for c in text[offset+len(word):cutoff] if c in ',.;:!?…'))
    wave=[]
    base=None
    if estimated:
        duration=len(raw)*60/140
        rows=[{'texto':word,'inicio_s':i*60/140,'fim_s':(i+1)*60/140,'metodo':'estimado',
               'motivos_revisao':[]} for i,word in enumerate(raw)]
    else:
        files,durations=recording(root,project,paragraphs,ffprobe)
        duration=sum(durations)
        if not source_path(material).is_file():
            locate(root,project,paragraphs,files,ffmpeg,ffprobe)
        base=identity_for_edits(root,project,paragraphs)
        source=material/SOURCE
        imported=read(source) if source.is_file() else None
        if imported:
            if imported['identidade']!=identity(root,project,paragraphs):
                raise ValueError('Marcações exportadas pertencem a outro áudio ou roteiro.')
            validate_rows(imported['tipo'],imported['marcacoes'],
                          [word for p in paragraphs for word in words_in(p['texto'])],duration)
        signal=envelope(files,binary('ffmpeg',ffmpeg))
        block=max(1,math.ceil(len(signal)/1800))
        peak=max(signal,default=1) or 1
        wave=[round(max(signal[i:i+block])/peak,4) for i in range(0,len(signal),block)]
        rows=measured_rows(root,project,paragraphs,duration,signal,imported)
        if adjustments is None and (material/MANUAL).is_file():
            reviewed=read(material/MANUAL)
            if reviewed['identidade']!=base:
                raise ValueError('Os ajustes manuais pertencem a outra fonte de sincronia.')
            adjustments=parse_adjustments(reviewed,len(rows),duration)
    for index,row in enumerate(rows):
        frame=final_frame(row['inicio_s'])
        if adjustments and index in adjustments:
            frame=adjustments[index]
            row.update(inicio_s=frame/30,metodo='conferido_manual',motivos_revisao=[])
        row['fim_s']=max(row['inicio_s'],row['fim_s'])
        row.update(palavra=index,quadro=frame,
                   fim_quadro=max(frame+1,final_frame(row['fim_s'])))
        if index and row['inicio_s']<rows[index-1]['inicio_s']:
            raise ValueError('Os inícios das palavras não podem inverter a ordem do roteiro.')
    from pictograma_legenda import rules, display_tokens
    replacements,names=rules(project)
    groups=caption_groups(rows,raw,replacements=replacements)
    return {'duracao_s':duration,'palavras':rows,'legendas':groups,'onda':wave,'identidade':base,
            'substituicoes_legenda':display_tokens(raw,replacements)[1],'pessoas_privadas':names,
            'fim_fala_s':min(duration,max(max(row['inicio_s'],row['fim_s']) for row in rows))}
