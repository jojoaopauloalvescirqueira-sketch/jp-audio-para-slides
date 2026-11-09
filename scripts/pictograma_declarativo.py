"""Percurso oficial de auditoria, parecer e exportação da direção declarativa."""
from pathlib import Path
import shutil
import tempfile

from ancoras import require_reviewed_anchors
from auditar_animacao import inspect_preview, require_pass, write_report
from pictograma_auditoria import prepare_export, register_review
from pictograma_composicao import preview as compose
from pictograma_mix import GAP, prepare, verify as verify_mix
from pictograma_salvaguardas import identity, matrix, plan_checks, require_matrix, validate_review
from pictograma_sincronia import ENERGY, MANUAL, PAUSES, RECOGNITION, SOURCE, timing
from pictograma_verificacao import render_identity, verify_frames, verify_media
from projeto import audio, audio_files, binary, read, sha, write
from trilha import select
from video_export import _audio_hash, export_animation


def run(args, root, project, direction, material, paragraphs, words, fmt):
    if fmt!='9:16':
        raise ValueError('A direção declarativa anatômica usa 9:16.')
    if args.estimar or not project.get('audio'):
        raise ValueError('O aceite declarativo exige narração fornecida e marcações medidas. Use compor para estimar.')
    source_files=[root/'projeto.json',args.direcao,material/'paragrafos.json',material/'roteiro_limpo.txt',
                  *(material/name for name in (ENERGY,MANUAL,PAUSES,RECOGNITION,SOURCE,'revisao_acoes.json'))]
    def hashes(paths):
        return [sha(path) if path.is_file() else None for path in paths]

    source_snapshot=hashes(source_files)
    plan=read(args.direcao)
    if plan.get('gestual')!='expressivo_intencional':
        raise ValueError('O aceite declarativo exige o perfil expressivo com intenção.')
    files=audio_files(audio(root,project),len(paragraphs))
    if len(files)!=1:
        raise ValueError('Use a narração unificada para exportar a direção declarativa.')
    ff,fp=binary('ffmpeg',args.ffmpeg),binary('ffprobe',args.ffprobe)
    sync=timing(root,project,paragraphs,False,ff,fp)
    total=max(round(sync['duracao_s']*30),sync['palavras'][-1]['fim_quadro']+1)/30
    preview,timeline=compose(root,plan,paragraphs,sync['palavras'],files[0],total,safeguards=True)
    track=select(root,{**project,'trilha_obrigatoria':True},Path(args.trilha) if args.trilha else None,
                 args.nivel_trilha_db,fp,args.atmosfera,args.motivo_trilha,total)
    gap=GAP if args.nivel_trilha_db is None else -args.nivel_trilha_db
    if not 12<=gap<=15:
        raise ValueError('O Pictograma aceita nível de trilha explícito entre -15 e -12 dB.')

    def seal():
        result=identity(args.direcao,preview,sync,[
            {'sha256':sha(path),'nivel_db':level} for path,level,*_ in track])
        return {**result,'voz_sha256':sha(files[0]),'roteiro_sha256':sha(material/'paragrafos.json'),
                'diferenca_alvo_db':gap}

    current=seal()
    if hashes(source_files)!=source_snapshot:
        raise ValueError('Os insumos mudaram durante a preparação da prévia.')
    report={'estilo_video':'pictograma','formato':fmt,'estimado':False,'duracao_s':total,
            'duracao_narracao_s':sync['duracao_s'],'audio_identidade':sync['identidade']['audio_identidade'],
            'ancoras':[{'palavra':item['palavra'],'tempo':item['inicio_s'],
                        'metodo':item['metodo'],'motivos_revisao':item['motivos_revisao']} for item in sync['palavras']],
            'previa_sha256':current['previa_sha256'],'direcao_sha256':current['direcao_sha256'],
            'cenas':timeline['cenas']}
    write(material/'marcacoes_acoes.json',{'estimado':False,'audio_identidade':report['audio_identidade'],
                                         'duracao_s':sync['duracao_s'],'ancoras':report['ancoras']})
    require_reviewed_anchors(root,report)
    audit_path=material/'auditoria_animacao.json'
    audit=read(audit_path) if audit_path.is_file() else {}

    def persist(phase):
        rows=matrix(audit,timeline,phase)
        audit['vinculo_salvaguardas']=current
        audit['salvaguardas']=rows
        write_report(material,preview.parent,audit)
        write(material/'salvaguardas.json',{'fase':phase,'identidade':current,'regras':rows,
                                          'render_sha256':audit.get('render_sha256'),
                                          'mp4_sha256':audit.get('mp4_sha256')})
        require_pass(audit)
        require_matrix(rows,phase)

    if args.acao=='auditar' or audit.get('vinculo_salvaguardas')!=current or 'checagens_previa' not in audit:
        audit=inspect_preview(root,preview,fmt,args.node,integral=True)
        checks,issues=plan_checks(timeline)
        audit.setdefault('checagens_catalogo',{}).update(checks)
        audit['issues'].extend(issues)
        audit['checagens_catalogo']['EC-033']={'quadros':audit['sampled'],'falhas':0}
        audit['checagens_previa']=dict(audit['checagens_catalogo'])
    if (audit.get('modo')!='integral' or audit['sampled']!=round(total*30)
            or len(audit.get('geometria_export',[]))!=round(total*30)):
        raise ValueError('A auditoria declarativa precisa cobrir todos os quadros.')
    # A retry starts with the preview evidence. A new MP4 must prove itself.
    audit['checagens_catalogo']=dict(audit['checagens_previa'])
    if any(row['supports'] or row['crossing'] for row in audit['geometria_export']):
        if not audit['checagens_catalogo'].get('EC-094',{}).get('quadros'):
            raise ValueError('O banco declarado exige evidência visual na prévia.')
    audit['issues']=[issue for issue in audit['issues'] if issue.get('etapa')!='mp4']
    audit.pop('render_sha256',None)
    audit.pop('mp4_sha256',None)
    audit.pop('mixagem',None)
    audit.pop('video',None)
    persist('previa')
    if args.acao=='auditar':
        print(preview.parent/'auditoria.html')
        return
    if args.acao=='parecer':
        review=read(args.parecer)
        validate_review(review,timeline)
        register_review(root,preview,fmt,args.parecer,words,direction,args.rodada,declarative=current)
        print(material/'parecer_animacao.json')
        return

    saved=material/'parecer_animacao.json'
    review=read(saved) if saved.is_file() else {}
    if review.get('vinculo_salvaguardas')!=current:
        raise ValueError('O parecer visual está ausente ou pertence a outros insumos.')
    validate_review(review,timeline)
    shared_verify,_=prepare_export(root,preview,fmt,args,mix_report=report)
    frames=preview.parent/'.render/quadros'
    count=round(total*30)
    target=preview.parent/'video.mp4'
    if args.candidato and args.candidato.resolve()==target.resolve():
        raise ValueError('Indique um candidato separado do vídeo final.')

    def check_frames(folder,_):
        audit['render_sha256']=render_identity(folder,count)

    def check_video(file):
        verify_media(fp,file,count)
        audit['video']=read(audit_path).get('video',{'quadros':count})
        checks,failures=verify_frames(ff,file,frames,audit['geometria_export'],count)
        audit['checagens_catalogo'].update(checks)
        audit['checagens_catalogo']['EC-036']={'quadros':count,'falhas':0}
        for code,frame in failures.items():
            audit['issues'].append({'etapa':'mp4','codigo':code,'nivel':'bloqueante','quadro':frame,'elemento':'MP4',
                'correcao':'Confira o quadro decodificado contra o render e o apoio planejado.'})
        audit['mp4_sha256']=sha(file)
        audit['mixagem']=report['mixagem']
        if (hashes(source_files)!=source_snapshot or seal()!=current
                or render_identity(frames,count)!=audit['render_sha256']):
            raise ValueError('Os insumos ou o render mudaram durante a exportação.')
        persist('mp4')

    def verify_stage(stage):
        if args.candidato:
            # Verify a private snapshot to avoid validating one version and
            # promoting another. The candidate must carry the measured mix.
            with tempfile.TemporaryDirectory(dir=stage.parent,prefix='.candidato-') as tmp:
                copy=Path(tmp)/'video.mp4'
                shutil.copyfile(args.candidato,copy)
                if _audio_hash(ff,copy)!=_audio_hash(ff,stage):
                    raise ValueError('A faixa do candidato difere da mixagem medida.')
                shared_verify(copy)
                check_video(copy)
                copy.replace(stage)
        else:
            shared_verify(stage)
            check_video(stage)

    def mix_audio(ffmpeg,narration,music_input,duration,scratch):
        mixed,metrics=prepare(ffmpeg,narration,music_input,duration,sync['palavras'],scratch,gap)
        report['mixagem']=metrics
        return mixed,lambda stage:verify_mix(ffmpeg,stage,metrics)

    # The renderer's general cache validates metadata, not individual PNGs.
    # The audited path starts with a fresh capture before trusting any pixels.
    (frames/'render_manifest.json').unlink(missing_ok=True)
    export_animation(root,preview,target,frames,fmt,project,paragraphs,report,args,
                     assets_hash=current['regras_sha256'],verify=verify_stage,
                     verify_frames=check_frames,mix_audio=mix_audio,fidelity=True,music_selection=track)
    report.update(render_sha256=audit['render_sha256'],mp4_sha256=audit['mp4_sha256'])
    write(preview.parent/'timeline_pictograma.json',report)
    print(target)
