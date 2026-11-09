"""Parecer visual e barreira de exportação do Pictograma."""
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

from auditar_animacao import inspect_preview, require_pass, verify_encoded, write_report
from pictograma_plano import compile_plan
from projeto import binary, read, sha, write



def append_effects(report, result, stage):
    report.setdefault('auditoria_efeitos', {})[stage] = result
    checks = report.setdefault('checagens_catalogo', {})
    for code in ('EC-073','EC-076','EC-078','EC-079','EC-080','EC-081','EC-083','EC-084'):
        count = sum(row['codigo']==code for row in result['issues'])
        checks[code] = {'quadros':report['quadros_totais'], 'falhas':count}
    for code in sorted({row['codigo'] for row in result['issues']}):
        first = next(row for row in result['issues'] if row['codigo']==code)
        report['issues'].append({'codigo':code,'nivel':'bloqueante','quadro':first.get('quadro',0),
                                 'elemento':'luz e efeitos','correcao':f'Confira o detalhe de {code} na medição {stage}.'})


def frame_input(directory):
    return ['-framerate','30','-i',str(directory/'%06d.png')]


def audit_effects_preview(root, preview, fmt, args, report):
    from cenas import capture
    from pictograma_efeitos_pixels import audit
    from projeto import FORMATS

    out = preview.parent
    width,height = FORMATS[fmt]
    evidence = out/'efeitos'
    subprocess.run([args.node, str(Path(__file__).with_name('auditar_efeitos.mjs')),
                    str(preview), str(evidence), str(width), str(height)], check=True)
    geometry = read(evidence/'amostras-efeitos.json')
    count = report['quadros_totais']
    if len(geometry['rows'])!=count:
        raise ValueError('A medição de efeitos não cobre todos os quadros.')
    images, reference, control = (out/'.render'/name for name in ('quadros','sem-sombras','sem-efeitos'))
    capture(args.node, preview, images, fmt, count=count, pages=args.paginas)
    for folder, variable in ((reference,'JP_RENDER_SEM_SOMBRAS'),(control,'JP_RENDER_SEM_EFEITOS')):
        cmd = [args.node,str(Path(__file__).with_name('renderizar_cenas.mjs')),str(preview),str(folder),
               str(width),str(height),'video',str(count),str(args.paginas),'']
        subprocess.run(cmd,env={**os.environ,variable:'1'},check=True)
    ffmpeg = binary('ffmpeg',args.ffmpeg)
    result = audit(ffmpeg,frame_input(images),geometry,shadow_inputs=frame_input(reference),control_inputs=frame_input(control))
    append_effects(report,result,'png')
    report['efeitos_geometria_sha256'] = sha(evidence/'amostras-efeitos.json')
    report['efeitos_referencia_sha256'] = sha(reference/'render_manifest.json')
    report['efeitos_controle_sha256'] = sha(control/'render_manifest.json')
    write_report(root/'material',out,report)
    return report


def register_review(root, preview, fmt, source, words, direction, round_number, *, declarative=None):
    material = root / 'material'
    report = read(material/'auditoria_animacao.json')
    identity = {'previa_sha256':sha(preview),'formato':fmt}
    if report['identidade'] != identity:
        raise ValueError('A auditoria automática pertence a outra prévia.')
    if not 1 <= round_number <= 3:
        raise ValueError('Após três rodadas, encaminhe as pendências ao usuário.')
    review = read(source)
    fields={'resultado','ocorrencias','plano_corrigido','notas'}
    if declarative is not None:
        fields={'resultado','ocorrencias','notas','modos','evidencias'}
    if not isinstance(review, dict) or review.keys() - fields:
        raise ValueError('Parecer visual em formato inválido.')
    if review.get('resultado') not in ('aprovado','corrigir') or not isinstance(review.get('ocorrencias'),list):
        raise ValueError('O parecer exige resultado e lista de ocorrências.')
    if report.get('criterios_artisticos'):
        notes = review.get('notas')
        expected = {
            'legibilidade_da_silhueta', 'causa_e_efeito', 'peso_e_contato', 'enquadramento',
            'ritmo_e_respiracao', 'texto', 'transicoes', 'forca_da_virada'
        }
        if 'proporcoes' in report:
            expected.update(('proporcao_e_naturalidade', 'luz_e_profundidade', 'clareza_sem_som'))
        if report.get('auditoria_efeitos'):
            expected.add('efeito_ajuda_entender')
        if (not isinstance(notes, dict) or notes.keys() != expected
                or any(type(n) is not int or not 1 <= n <= 5 for n in notes.values())):
            raise ValueError(f'O parecer artístico exige {len(expected)} notas inteiras entre 1 e 5.')
        if review['resultado'] == 'aprovado' and min(notes.values()) < 4:
            raise ValueError('Uma nota abaixo de 4 exige correção e nova rodada.')
        snapshot = material/f'parecer_animacao-rodada-{round_number}.json'
    elif review['resultado'] == 'corrigir' and declarative is None:
        compile_plan(review.get('plano_corrigido'),words,direction)
    if review['resultado'] == 'aprovado':
        require_pass(report)
        if 'plano_corrigido' in review:
            raise ValueError('O parecer aprovado deve corresponder ao plano atual.')
    saved = {**review,'identidade':identity,'rodada':round_number}
    if report.get('criterios_artisticos'):
        saved['plano_sha256'] = sha(material/'cenas_pictograma.json')
        saved['render_sha256'] = sha(preview.parent/'.render/quadros/render_manifest.json')
        if snapshot.exists() and read(snapshot) != saved:
            raise ValueError('Esta rodada já foi registrada. Use a próxima rodada.')
        write(snapshot, saved)
    if declarative is not None:
        saved['vinculo_salvaguardas']=declarative
        snapshot=material/f'parecer_declarativo-rodada-{round_number}.json'
        if snapshot.exists() and read(snapshot)!=saved:
            raise ValueError('Esta rodada já foi registrada. Use a próxima rodada.')
        write(snapshot,saved)
    write(material/'parecer_animacao.json', saved)


def prepare_export(root, preview, fmt, args, coreografia=False, mix_report=None, effects=False):
    material = root/'material'
    path = material/'auditoria_animacao.json'
    identity = {'previa_sha256':sha(preview),'formato':fmt}
    report = read(path) if path.is_file() else None
    if (not report or report['identidade']!=identity or report.get('modo')!='integral'
            or report.get('sampled')!=report.get('quadros_totais')
            or (coreografia and report.get('versao_catalogo') != 2)):
        report=inspect_preview(root,preview,fmt,args.node,integral=True)
    if effects and not report.get('auditoria_efeitos', {}).get('png'):
        report=audit_effects_preview(root,preview,fmt,args,report)
    require_pass(report)
    review_path = material/'parecer_animacao.json'
    review = read(review_path) if review_path.is_file() else {}
    if (review.get('identidade') != identity or review.get('resultado') != 'aprovado'
            or not 1 <= review.get('rodada',0) <= 3
            or (coreografia and review.get('plano_sha256') != sha(material/'cenas_pictograma.json'))):
        raise ValueError('Registre o parecer visual aprovado da prévia medida antes da exportação.')
    ffmpeg = binary('ffmpeg',args.ffmpeg)
    frame_check = None
    if coreografia:
        from pictograma_pixels import check, measure
        def frame_check(directory, binary_path):
            if review.get('render_sha256') != sha(directory/'render_manifest.json'):
                raise ValueError('O parecer visual pertence a outra renderização.')
            stats = measure(binary_path, ['-framerate', '30', '-i', str(directory/'%06d.png')],
                            report['quadros_ativos'], report['quadros_totais'])
            check(report, 'png', stats)
            write_report(material, preview.parent, report)
            require_pass(report)

    def verify_video(staged):
        if effects:
            from pictograma_efeitos_pixels import audit
            geometry_path = preview.parent/'efeitos/amostras-efeitos.json'
            reference = preview.parent/'.render/sem-sombras'
            control = preview.parent/'.render/sem-efeitos'
            if (report['efeitos_geometria_sha256'] != sha(geometry_path)
                    or report['efeitos_referencia_sha256'] != sha(reference/'render_manifest.json')
                    or report['efeitos_controle_sha256'] != sha(control/'render_manifest.json')):
                raise ValueError('As medições dos efeitos pertencem a outra prévia.')
            from video_export import FX_COLOR, FX_CRF, FX_FILTER
            with TemporaryDirectory(prefix='pictograma-controles-') as temporary:
                controls = []
                for folder in (reference,control):
                    target = str(Path(temporary)/(folder.name+'.mp4'))
                    subprocess.run([ffmpeg,'-v','error',*frame_input(folder),'-an','-vf',FX_FILTER,
                                    '-c:v','libx264','-preset','veryfast','-crf',str(FX_CRF),
                                    '-threads',str(args.threads),*FX_COLOR,target],check=True)
                    controls.append(['-i',target])
                measured = audit(ffmpeg,['-i',str(staged)],read(geometry_path),
                                 shadow_inputs=controls[0],control_inputs=controls[1])
            append_effects(report,measured,'mp4')
            write_report(material,preview.parent,report)
            require_pass(report)
        if mix_report and 'mixagem' in mix_report:
            report['mixagem'] = mix_report['mixagem']
        return verify_encoded(staged,ffmpeg,report,material,preview.parent)

    return verify_video, frame_check
