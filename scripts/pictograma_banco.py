"""Banco fixo de regressão e relatório de evidências de Pictograma."""
from html import escape
from pathlib import Path
import subprocess
import sys
from time import monotonic

from projeto import read, sha, write

CASES = (
    ('P007-P008','Referência aprovada'),
    ('P001-P002','Pergunta, abertura e gancho'),
    ('P003','Enumeração com referências religiosas'),
    ('P006','Espera e repetição'),
    ('P009','Objeção e sofrimento'),
    ('P014','Versículo e conclusão hesitante'),
    ('1971-P013','História econômica, data e linha do tempo'),
)
VISUAL = ('legibilidade_da_silhueta','causa_e_efeito','peso_e_contato','enquadramento',
          'ritmo_e_respiracao','texto','transicoes','forca_da_virada','proporcao_e_naturalidade',
          'luz_e_profundidade','clareza_sem_som','efeito_ajuda_entender')
LIMITS = {'deriva_px':(0,2),'sola_px':(0,2),'interpenetracoes':(0,0),'densidade':(.85,1),
          'erro_pouso_quadros':(0,1),'lufs':(-14.5,-13.5),'pico_dbtp':(-99,-1)}


def evaluate(evidence, baseline=None):
    problems=[]
    if evidence.get('confianca')=='baixa':
        return ['Sincronia por pausas com confiança baixa. '+ '; '.join(evidence.get('divergencias',[]))]
    if not evidence.get('video') or not evidence.get('video_sha256'):
        problems.append('MP4 medido indisponível.')
    if evidence.get('encenacao'):
        problems.extend(f'{code} · {why}' for code,why in evidence['encenacao']['bloqueios'].items())
    if evidence.get('falha_execucao'):
        problems.append(evidence['falha_execucao'])
    if evidence.get('auditoria_integral') is not True or evidence.get('bloqueantes')!=0:
        problems.append('Auditoria integral sem bloqueantes ainda não demonstrada.')
    ratings=evidence.get('notas') or {}
    for criterion in VISUAL:
        value=ratings.get(criterion)
        if type(value) is not int or value<4:
            problems.append(f'Nota pendente ou abaixo de 4 em {criterion}.')
        elif baseline and value<baseline['notas'][criterion]:
            problems.append(f'Regressão na nota {criterion}.')
    metrics=evidence.get('medicoes',{})
    for metric,(low,high) in LIMITS.items():
        value=metrics.get(metric)
        if type(value) not in (int,float) or not low<=value<=high:
            problems.append(f'{metric} fora do limite ou sem evidência.')
    if metrics.get('sombra_propria') is not True or metrics.get('legenda_exata') is not True:
        problems.append('Sombra própria ou exatidão da legenda não demonstrada.')
    if baseline and evidence.get('reimplementacao_declarativa') is not True:
        problems.append('A referência aprovada ainda não foi reproduzida só pela biblioteca e pelo plano.')
    return problems


def contact_sheet(ffmpeg, video, output):
    subprocess.run([ffmpeg,'-v','error','-y','-i',str(video),'-vf',
                    'fps=1,scale=128:228:flags=lanczos,tile=5x5:padding=7:margin=8',
                    '-frames:v','1','-update','1',str(output)],check=True)


def make_report(root):
    rows=[]
    baseline_path=root/'evidencias/encenacao-antes.json'
    baseline_measures=read(baseline_path) if baseline_path.is_file() else {}
    reviews=[read(file) for file in sorted((root/'evidencias').glob('parecer-rodada-*.json'),reverse=True)]
    for case,description in CASES:
        file=root/'evidencias'/(case+'.json')
        data=read(file) if file.is_file() else {}
        for review in reviews:
            entry=review.get(case)
            if not entry:
                continue
            if data.get('folha') and (root/data['folha']).is_file() and sha(root/data['folha'])==entry.get('folha_sha256'):
                data.update(notas=entry['notas'],observacoes_visuais=entry.get('observacoes',[]))
                break
            if 'notas_rodada_anterior' not in data:
                data['notas_rodada_anterior']=entry['notas']
                data['observacoes_visuais_anteriores']=entry.get('observacoes',[])
        if case in baseline_measures:
            data['encenacao_antes']=baseline_measures[case]
        if case=='P007-P008':
            candidate=root/'trechos/P007-P008/candidato-ec086'
            if (candidate/'auditoria.json').is_file():
                data['candidata_ec086']=str((candidate/'auditoria.json').relative_to(root))
                data['mp4_candidata']=str((candidate/'candidata.mp4').relative_to(root))
            if (candidate/'quadro-247-par.png').is_file():
                data['quadro_247']=str((candidate/'quadro-247-par.png').relative_to(root))
            if (candidate/'encenacao.json').is_file():
                data['encenacao_candidata']=read(candidate/'encenacao.json')
        if case=='P009':
            review_cut=root/'trechos/P009/revisao-corte.html'
            if review_cut.is_file():
                data['forma_de_onda']=str(review_cut.relative_to(root))
        if 'encenacao' in data:
            metrics=data.get('medicoes',{})
            metrics['densidade_legada']=metrics.get('densidade')
            metrics['densidade']=data['encenacao']['pixels_acao']['fracao']
        if 'encenacao' in data and 'notas' in data:
            from pictograma_encenacao import calibrate
            data['notas_originais']=data['notas']
            data['notas']=calibrate(data['notas'],data['encenacao']['pose'])
        reference=root/'evidencias/referencia-aprovada.json'
        baseline=read(reference) if case=='P007-P008' and reference.is_file() else None
        baseline=(baseline or {}).get('metas')
        failures=evaluate(data,baseline)
        if data.get('video') and (not (root/data['video']).is_file()
                                  or sha(root/data['video'])!=data.get('video_sha256')):
            failures.append('A identidade do MP4 mudou.')
        rejected=bool(data.get('encenacao',{}).get('bloqueios')) or data.get('bloqueantes',0)>0 or any(v<4 for v in data.get('notas',{}).values())
        status=('aprovado' if not failures else 'bloqueado por sincronia' if data.get('confianca')=='baixa'
                else 'reprovado' if rejected else 'pendente')
        rows.append({'id':case,'padrao':description,**data,'problemas':failures,'resultado':status})
    complete=all(row['resultado']=='aprovado' for row in rows)
    write(root/'resultado.json',{'aprovado':complete,'trechos':rows})
    cards=[]
    for row in rows:
        findings=''.join('<li>'+escape(item)+'</li>' for item in row['problemas'])
        earlier=row.get('notas_rodada_anterior',{})
        notes=' · '.join(f'{k.replace("_"," ")} {v}' for k,v in (row.get('notas') or earlier).items())
        if notes and not row.get('notas'):
            notes='Rodada anterior · '+notes
        def coverage(result,key):
            item=(result or {}).get(key)
            return f"{item['fracao']:.1%}" if item else '—'
        prior,row_measure=row.get('encenacao_antes'),row.get('encenacao') or row.get('encenacao_candidata')
        comparative=' · '.join(f'{label} {coverage(prior,key)} → {coverage(row_measure,key)}'
                              for key,label in (('pose','pose em ação'),('corpo','corpo em ação'),('batidas','batidas com ação'),('pixels_acao','pixels de atuação')))
        metrics=' · '.join(f'{k.replace("_"," ")} {v}' for k,v in row.get('medicoes',{}).items())
        links=''
        for label,key in (('MP4','video'),('Prévia','previa'),('Storyboard','storyboard'),('Auditoria','auditoria'),('Paridade','paridade'),('Ocorrências por cena','ocorrencias'),('Corte conferido','confirmacao_corte'),('Forma de onda','forma_de_onda'),('Candidata EC-086','mp4_candidata'),('Medição EC-086','candidata_ec086'),('Quadro 247','quadro_247')):
            if row.get(key):
                links+=f'<a href="{escape(row[key],quote=True)}">{label}</a> '
        if row.get('folha'):
            sheet=escape(row['folha'],quote=True)
            links+=f'<details><summary>Folha de contato · 1 quadro/s</summary><a href="{sheet}"><img src="{sheet}" alt="Folha de contato"></a></details>'
        observations=row.get('observacoes_visuais') or row.get('observacoes_visuais_anteriores') or []
        if observations:
            links+='<details><summary>Observações da revisão visual</summary><ul>'+''.join(
                '<li>'+escape(item)+'</li>' for item in observations)+'</ul></details>'
        source=row.get('intervalo')
        time=f'{source[0]:.2f}–{source[1]:.2f} s no áudio' if source else ''
        render=f'{row["render_s"]:.1f} s' if row.get('render_s') is not None else 'sem medição'
        cards.append(f'<tr><th>{escape(row["id"])}<br><small>{escape(row["padrao"])}</small></th>'
                     f'<td>{escape(row["resultado"])}<br>{escape(time)}</td><td>{escape(notes or "Sem parecer")}</td>'
                     f'<td>{escape(metrics or "Sem medição")}<br><small>{escape(comparative)}</small><ul>{findings}</ul></td><td>{render}<br>{links}</td></tr>')
    final_links=[]
    for name,label in (('comparacao-encenacao.jpg','Montagem refeita'),('legendas-privacidade.jpg','Legendas com a substituição'),
                       ('evidencias/encenacao-antes.json','Medições antes da troca de direção')):
        if (root/name).is_file():
            final_links.append(f'<a href="{name}">{label}</a>')
    output_links='<p>'+' · '.join(final_links)+'</p>' if final_links else ''
    long_test=root/'evidencias/render-longo.json'
    long_html=''
    if long_test.is_file():
        item=read(long_test)
        long_html='<p>Ensaio de render longo · '+escape(item['resumo'])+'</p>'
    (root/'relatorio.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Banco de provas do Pictograma</title>
<style>body{font:16px system-ui;background:#131b18;color:#ece6d8;margin:24px}
a{color:#a6d9b7}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #415749}
img{max-width:340px;width:100%}small{color:#b9ccbf}ul{padding-left:18px}th{min-width:120px}</style>
<h1>Banco de provas do Pictograma</h1>
<p><a href="inventario.md">Inventário</a> · <a href="folha-acoes.html">Folha de movimento</a> · <a href="rodadas.md">Rodadas</a> · <a href="planos-diretor.json">Planos do diretor</a> · <a href="cmu.md">Experimento CMU</a></p>
<p>'''+('Banco aprovado.' if complete else 'Banco com pendências. Instalação bloqueada.')+'''</p>
<table><thead><tr><th>Trecho</th><th>Estado</th><th>Notas</th><th>Medições e pendências</th><th>Render e evidências</th></tr></thead><tbody>'''
                                      +''.join(cards)+'</tbody></table>'+output_links+long_html+'</html>',encoding='utf-8')
    return complete


def cut(ffmpeg, source, destination, start, end):
    subprocess.run([ffmpeg,'-y','-v','error','-ss',str(start),'-i',str(source),
                    '-t',str(end-start),'-vn','-c:a','pcm_s16le',str(destination)],check=True)


def stamps(words, start):
    from pictograma_tempo import final_frame
    result=[]
    for word in words:
        begin,end=(max(0,word[field]-start) for field in ('inicio_s','fim_s'))
        frame=final_frame(begin)
        result.append({**word,'inicio_s':begin,'fim_s':end,'quadro':frame,
                       'fim_quadro':max(frame+1,final_frame(end))})
    return result


def economic_timing(economy):
    from difflib import SequenceMatcher
    from ancoras import norm, tokens

    paragraphs=[p for p in read(economy/'paragrafos.json') if p['id']=='P013']
    location=next(x for x in read(economy/'marcacoes_audio.json')['paragrafos'] if x['paragrafo']=='P013')
    start,end=location['inicio_s'],location['fim_s']
    heard=[w for block in read(economy/'transcricao_asr.json') for w in block['words']
           if start<=w['start']<end]
    expected=[w for w,_ in tokens(paragraphs[0]['texto'])]
    matched=[]
    for tag,i,j,a,b in SequenceMatcher(None,list(map(norm,expected)),
                                       [norm(w['word']) for w in heard],autojunk=False).get_opcodes():
        if i==j:
            continue
        if a==b:
            raise ValueError('Há palavra da economia sem intervalo de áudio reconhecido.')
        lo,hi=heard[a]['start'],heard[b-1]['end']
        for k,word in enumerate(expected[i:j]):
            if tag=='equal':
                x,y=heard[a+k]['start'],heard[a+k]['end']
            else:
                x,y=lo+(hi-lo)*k/(j-i),lo+(hi-lo)*(k+1)/(j-i)
            matched.append({'texto':word,'inicio_s':x,'fim_s':y,
                            'metodo':'reconhecido' if tag=='equal' else 'distribuido_no_intervalo_asr',
                            'motivos_revisao':[]})
    return paragraphs,matched,start,end


def confirm_cut(project, audio_hash, alignment, words, lo, rms):
    """Reutiliza aprovação somente para os mesmos intervalos e a mesma narração."""
    from pausas_audio import word_boundaries
    approved=project.get('confirmacao_corte')
    if not approved:
        return None
    pending=[{k:row[k] for k in ('texto','inicio_s','fim_s')}
             for row in alignment['frases'] if row['confianca']=='baixa']
    if approved.get('audio_sha256')!=audio_hash or approved.get('frases')!=pending:
        raise ValueError('A confirmação do corte pertence a outra gravação ou marcação.')
    start,end=approved['inicio_s'],approved['fim_s']
    if not 0<=start<=alignment['inicio_s']<alignment['fim_s']<=end:
        raise ValueError('O corte confirmado precisa conter todas as frases selecionadas.')
    for row in alignment['frases']:
        if row['confianca']!='baixa':
            continue
        a,b=row['inicio_palavra']-lo,row['fim_palavra']-lo
        refined=word_boundaries([w['texto'] for w in words[a:b]],row['inicio_s'],row['fim_s'],rms)
        words[a:b]=refined
    return start,end


def prepare_sources(root, desktop, economy, ffmpeg):
    from pausas_audio import acoustic, aligned, phrases, selection, speech_blocks
    from pictograma_composicao import preview

    plans=read(root/'planos-diretor.json')
    material=desktop/'projeto-v7/material'
    paragraphs=read(material/'paragrafos.json')
    narration=desktop/'narracao-v7-completa.mp3'
    clauses=phrases(paragraphs,(material/'roteiro_studio.txt').read_text())
    rms,peaks=acoustic([narration],ffmpeg)
    blocks=speech_blocks(rms,peaks)
    for case,_ in CASES[1:]:
        dest=root/'trechos'/case
        dest.mkdir(parents=True,exist_ok=True)
        plan=plans[case]
        write(dest/'direcao.json',plan)
        if case=='1971-P013':
            selected,words,start,end=economic_timing(economy)
            source=economy/'narracao.mp3'
            data={'confianca':'alta','metodo':'ASR local preexistente e intervalo de P013'}
        else:
            source=narration
            lo,hi=selection(clauses,paragraphs,case)
            alignment=aligned(clauses,blocks,rms,lo,hi)
            start,end=alignment['inicio_s'],alignment['fim_s']
            data={k:alignment[k] for k in ('confianca','divergencias')}
            data['metodo']='pausas e energia acústica'
            write(dest/'alinhamento.json',{k:alignment[k] for k in ('origem','confianca','frases','divergencias')})
            words=alignment['palavras'][lo:hi]
            config=dest/'projeto.json'
            confirmation=confirm_cut(read(config),sha(source),alignment,words,lo,rms) if config.is_file() else None
            if confirmation:
                start,end=confirmation
                data.update(confianca='limites_confirmados',metodo='limites confirmados pelo usuário; palavras refinadas por energia',
                            confirmacao_corte=str(config.relative_to(root)),divergencias=[])
            lower,_,upper=case.partition('-')
            selected=[p for p in paragraphs if lower<=p['id']<=(upper or lower)]
        data['intervalo']=[start,end]
        data['audio_fonte_sha256']=sha(source)
        evidence=root/'evidencias'/(case+'.json')
        if data['confianca']=='baixa' or not 10<=end-start<=25:
            data['storyboard']=str((dest/'storyboard.html').relative_to(root))
            (dest/'storyboard.html').write_text('<!doctype html><meta charset="utf-8"><h1>'+
                escape(plan['titulo'])+'</h1><p>Storyboard textual. Sincronia bloqueada.</p>'+
                ''.join('<article><h2>'+escape(b['titulo'])+'</h2><p>'+
                         escape(b['em']['trecho'])+' · '+escape(', '.join(b['rotulos']))+'</p></article>'
                         for b in plan['batidas']),encoding='utf-8')
            write(evidence,data)
            continue
        try:
            audio=dest/'narracao.wav'
            cut(ffmpeg,source,audio,start,end)
            marks=stamps(words,start)
            total=max(round((end-start)*30),marks[-1]['fim_quadro']+1)/30
            write(dest/'marcacoes.json',{'audio_sha256':sha(audio),'palavras':marks})
            page=preview(dest,plan,selected,marks,audio,total)
            data['previa']=str(page.relative_to(root))
            data['duracao']=total
            data['quadros']=round(total*30)
        except ValueError as exc:
            data['divergencias']=[str(exc)]
            data['bloqueantes']=1
        write(evidence,data)


def reference(root,ffmpeg):
    from os.path import relpath
    reference_path=root/'evidencias/referencia-aprovada.json'
    record=read(reference_path)
    skill=root.parent
    video=skill/record['video']
    if sha(video)!=record['video_sha256']:
        raise ValueError('O MP4 aprovado do banco mudou.')
    report=read(skill/record['auditoria'])
    rating=read(skill/record['parecer'])
    if sha(skill/record['auditoria'])!=record['auditoria_sha256'] or sha(skill/record['parecer'])!=record['parecer_sha256']:
        raise ValueError('As evidências da referência aprovada mudaram.')
    old=read(skill/'outputs/piloto-p007-p008/auditoria-pixels.json')
    sheet=root/'evidencias/P007-P008-contato.jpg'
    contact_sheet(ffmpeg,video,sheet)
    pixels=report['pixels']['mp4']['ativo']
    metrics={'densidade':pixels['fracao'],'lufs':report['mixagem']['aac_lufs'],
             'pico_dbtp':report['mixagem']['aac_pico_real_dbtp'],'sombra_propria':True,
             'legenda_exata':not any('legenda' in i['codigo'] for i in report['issues'])}
    parity=root/'trechos/P007-P008/paridade.json'
    diagnosis=read(parity).get('anatomia_referencia',{}) if parity.is_file() else {}
    if diagnosis:
        metrics.update(deriva_px=diagnosis['max_deriva_px'],sola_px=diagnosis['max_altura_sola_px'],
                       interpenetracoes=sum(i['codigo'] in ('interpenetracao_mascaras','contorno_fundido_no_mp4')
                                           for i in diagnosis['issues']))
    record['metas']={'notas':rating['notas'],'medicoes':metrics}
    write(reference_path,record)
    write(root/'evidencias/P007-P008.json',{'intervalo':[0,14.4],'video':relpath(video,root),
        'video_sha256':sha(video),'folha':str(sheet.relative_to(root)),
        'auditoria':relpath(skill/record['auditoria'],root),'notas':rating['notas'],
        'auditoria_integral':report['sampled']==report['quadros_totais'],
        'bloqueantes':len(report['issues'])+len(diagnosis.get('issues',[])),'medicoes':metrics,
        **({'paridade':str(parity.relative_to(root))} if parity.is_file() else {}),
        'medicoes_rig_anterior':{'deriva_px':old['max_deriva_px'],'sola_px':old['max_altura_sola_px']}})


def audit_anatomy(node,python_pixels,preview,video,ffmpeg):
    path=preview.parent/'poses.json'
    subprocess.run([node,str(Path(__file__).with_name('medir_palco_anatomico.mjs')),
                    str(preview),str(path)],check=True)
    script=Path(__file__).with_name('auditar_mp4_anatomico.py')
    code='''import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(sys.argv[1]).parent))
from auditar_mp4_anatomico import audit
p=Path(sys.argv[4])
data=json.loads(p.read_text())
r=audit(sys.argv[2],Path(sys.argv[3]),data)
from pictograma_efeitos_pixels import measure_samples,pixels
geometry=[]
for frame in data['frames']:
    row={'shades':[],'contacts':[],'title':[]}
    for actor in frame['actors']:
        if actor.get('sombra_cabeca'):
            row['shades'].append(actor['sombra_cabeca'])
    geometry.append(row)
shadows=measure_samples(pixels(sys.argv[2],['-i',sys.argv[3]],1080,1920,len(geometry)),geometry,1080,1920)
r['sombra_propria']=shadows['sombra_propria']['amostras']>0 and not shadows['issues']
r['sombra_amostras']=shadows['sombra_propria']
r['issues']+=shadows['issues']
print(json.dumps({k:v for k,v in r.items() if k not in ('observacoes','contornos_mp4')}))
'''
    import json
    return json.loads(subprocess.check_output([python_pixels,'-c',code,str(script),ffmpeg,str(video),str(path)]))


def render_case(root,case,node,ffmpeg,python_pixels,pages):
    from auditar_animacao import inspect_preview
    from cenas import capture
    from pictograma_mix import loudness,prepare
    from pictograma_pixels import measure
    from tempfile import TemporaryDirectory
    from video_export import FX_COLOR,FX_CRF,FX_FILTER

    evidence=root/'evidencias'/(case+'.json')
    data=read(evidence)
    if data.get('confianca')=='baixa' or not data.get('previa'):
        return
    preview=root/data['previa']
    folder=preview.parent
    parent=folder.parent
    frame_dir=folder/'.render/quadros'
    video=folder/'piloto.mp4'
    dest=folder/'contato.jpg'
    duration=data['duracao']
    started=monotonic()
    earlier=root/'evidencias/rodada-2'/(case+'.json')
    typical=read(earlier).get('render_s') if earlier.is_file() else None
    estimate=typical if typical is not None else data["quadros"]*.38/pages
    print(f'{case}: {data["quadros"]} quadros; estimativa {estimate:.0f} s; retomada habilitada.',flush=True)
    capture(node,preview,frame_dir,'9:16',count=data['quadros'],pages=pages)
    audio=parent/'narracao.wav'
    words=read(parent/'marcacoes.json')['palavras']
    with TemporaryDirectory(dir=folder) as tmp:
        music=Path(__file__).resolve().parents[1]/'assets/trilhas/mozart-k545-andante.ogg'
        mixed,_=prepare(ffmpeg,audio,['-i',str(music)],duration,words,Path(tmp))
        staged=Path(tmp)/video.name
        subprocess.run([ffmpeg,'-v','error','-framerate','30','-i',str(frame_dir/'%06d.png'),
                        '-i',str(mixed),'-map','0:v:0','-map','1:a:0','-vf',FX_FILTER,
                        '-c:v','libx264','-preset','veryfast','-crf',str(FX_CRF),'-threads','3',
                        *FX_COLOR,'-c:a','aac','-b:a','192k','-t',str(duration),str(staged)],check=True)
        subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(staged),'-f','null','-'],check=True)
        staged.replace(video)
    data.pop('falha_execucao',None)
    data['render_s']=round(monotonic()-started,3)
    contact_sheet(ffmpeg,video,dest)
    data.update(video=str(video.relative_to(root)),video_sha256=sha(video),folha=str(dest.relative_to(root)))
    write(evidence,data)
    material=parent/'material';material.mkdir(exist_ok=True)
    report=inspect_preview(parent,preview,'9:16',node,integral=True)
    stats=measure(ffmpeg,['-i',str(video)],min(data['quadros'],words[-1]['fim_quadro']),data['quadros'])
    audio_metrics=loudness(ffmpeg,video)
    try:
        anatomy=audit_anatomy(node,python_pixels,preview,video,ffmpeg)
    except (ValueError,subprocess.CalledProcessError) as exc:
        anatomy={'issues':[{'codigo':'sem_evidencia_anatomica','mensagem':str(exc)}]}
    write(folder/'auditoria-anatomica.json',anatomy)
    from pictograma_encenacao import analyze, measure_stage
    if (folder/'poses.json').is_file() and any(s.get('layout') for s in read(folder/'timeline_previa.json')['cenas']):
        stage=measure_stage(node,preview,folder/'encenacao-palco.json')
        data['encenacao']=analyze(read(folder/'poses.json')['frames'],stage,ffmpeg,video,
                                  min(data['quadros'],words[-1]['fim_quadro']))
        write(folder/'encenacao.json',data['encenacao'])
        from pictograma_encenacao import append_report
        append_report(report,data['encenacao'])
        from auditar_animacao import write_report
        write_report(material,folder,report)

    metrics={'densidade':stats['ativo']['fracao'],'lufs':float(audio_metrics['input_i']),
             'pico_dbtp':float(audio_metrics['input_tp']),
             'legenda_exata':not any('legenda' in i['codigo'] for i in report['issues'])}
    for key,out in (('max_deriva_px','deriva_px'),('max_altura_sola_px','sola_px')):
        if key in anatomy:
            metrics[out]=anatomy[key]
    if 'sombra_propria' in anatomy:
        metrics['sombra_propria']=anatomy['sombra_propria']
    if 'quadros_dupla_mascaras' in anatomy:
        metrics['interpenetracoes']=sum(i['codigo'] in ('interpenetracao_mascaras','contorno_fundido_no_mp4')
                                         for i in anatomy['issues'])
    timeline=read(folder/'timeline_previa.json')['cenas']
    def timed(item):
        frame=item.get('quadro',0)
        scene=next((s['id'] for s in timeline if s['inicio']<=frame/30<s['fim']),None)
        return {**item,'quadro':frame,'segundos':round(frame/30,3),'cena':scene}
    issues=[timed(item) for item in report['issues']+anatomy['issues']]
    write(folder/'ocorrencias-por-cena.json',issues)
    data['ocorrencias']=str((folder/'ocorrencias-por-cena.json').relative_to(root))
    data.update(auditoria=str((folder/'auditoria.html').relative_to(root)),
                auditoria_integral=report['sampled']==report['quadros_totais'],
                bloqueantes=len([i for i in report['issues'] if i['nivel']=='bloqueante'])+len(anatomy['issues']),
                medicoes=metrics)
    write(evidence,data)
    return data


def render_long(root, economy, node, ffmpeg, pages):
    """Ensaio técnico com 61 s contíguos da narração real e a mesma captura."""
    from cenas import Words, capture
    from pictograma import ASSETS,player
    from pictograma_biblia import for_project
    from video_export import FX_COLOR, FX_CRF, FX_FILTER

    dest=root/'trechos/ensaio-longo'
    dest.mkdir(parents=True,exist_ok=True)
    audio=dest/'narracao.wav'
    if not audio.is_file():
        cut(ffmpeg,economy/'narracao.mp3',audio,0,61)
    preview=dest/'apresentacao.html'
    words=Words([{'id':'ensaio','texto':'Ensaio técnico de renderização.'}])
    scenes=[{'id':'ensaio','palavra':0,'fim_palavra':len(words.words),'inicio':0,'fim':61,
             'saida':'corte','padrao':'numero_data','titulo':'Ensaio de render longo','rotulos':['Linha do tempo'],
             'simbolos':['linha'],'movimento':None}]
    direction={'paleta':'escura','legenda':'nao','tom':'sobrio','marca':'nao','densidade_animacao':'abundante'}
    player(preview,{'titulo':'Ensaio técnico'},direction,'9:16',scenes,words,[],61,False,audio,61,
           composicao_declarativa={'sensivel':False},bible=for_project({}),
           rig_anatomico=read(ASSETS/'biblia-anatomica-pictograma.json'))
    frames=dest/'quadros'
    expected=1830
    print(f'Render longo: {expected} quadros. Estimativa de {expected*.18/pages:.0f} s.',flush=True)
    start=monotonic()
    capture(node,preview,frames,'9:16',count=expected,pages=pages)
    last=frames/'001829.png'
    before=last.stat().st_mtime_ns
    capture(node,preview,frames,'9:16',count=expected,pages=pages)
    if before!=last.stat().st_mtime_ns or len(list(frames.glob('*.png')))!=expected:
        raise ValueError('Retomada refez um quadro pronto ou a sequência está incompleta.')
    video=dest/'ensaio.mp4'
    subprocess.run([ffmpeg,'-v','error','-y','-framerate','30','-i',str(frames/'%06d.png'),
                    '-i',str(audio),'-map','0:v:0','-map','1:a:0','-vf',FX_FILTER,
                    '-c:v','libx264','-preset','veryfast','-crf',str(FX_CRF),
                    '-threads','3',*FX_COLOR,'-c:a','aac','-t','61',str(video)],check=True)
    subprocess.run([ffmpeg,'-v','error','-xerror','-i',str(video),'-f','null','-'],check=True)
    elapsed=monotonic()-start
    write(root/'evidencias/render-longo.json',{
        'duracao_s':61,'quadros':expected,'retomada_sem_refazer':True,
        'tempo_s':round(elapsed,3),'video':str(video.relative_to(root)),
        'resumo':f'61 s de áudio fornecido, {expected} quadros, retomada sem refazer e decodificação integral. {elapsed:.1f} s de execução.'})


def cmu_adoption(native, candidate):
    """Barreira do teste opcional, independente do download ou da importação."""
    for side in (native,candidate):
        score=side.get('naturalidade_movimento')
        if type(score) is not int or not 1<=score<=5 or not side.get('prova_sha256'):
            raise ValueError('O A/B precisa de notas de movimento e evidências de ambos os renders.')
    if native['prova_sha256']==candidate['prova_sha256']:
        raise ValueError('O A/B precisa de dois renders distintos.')
    return (not evaluate(candidate) and
            candidate['naturalidade_movimento']>native['naturalidade_movimento'])
