#!/usr/bin/env python3
"""Prévia, storyboard e vídeo do estilo Pictograma."""
import argparse
import base64
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import sys

from cenas import capture, derive_slides, player as scene_player
from estilo_video import STYLES, choose, ensure_style_plan
from fala import normalize, paragraphs as speech_paragraphs
from pictograma_direcao import PALETTES, record, settings
from pictograma_coreografia import ANATOMICAL_MODEL, anchors as choreography_anchors, camera, camera_tracks, is_anatomical, is_visual, phases, storyboard_notes
from folhas_pictograma import approve as approve_sheets, render as render_sheets, require as require_sheets
from pictograma_modelo import MODEL_APPROVAL, approve_model, render_model, require_model
from pictograma_plano import TIME_PER_WORD, Words, compile_plan, schedule
from pictograma_tempo import animate_windows, extend_tail
from pictograma_efeitos import (IDENTITY as EFFECTS_IDENTITY, PLAN as EFFECTS_PLAN, compile_effects,
                                keys as effects_keys, register as register_effects,
                                require_approval as require_effects_approval)
from projeto import FORMATS, audio, audio_files, config, read, sha, write
from video_export import export_animation

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
PLAN = 'cenas_pictograma.json'
BOARD = 'storyboard_pictograma.json'
APPROVAL = 'aprovacao_storyboard.json'


def project_context(root, fmt):
    project = config(root)
    if project.get('estilo_video') != 'pictograma':
        raise ValueError('Registre o estilo pictograma antes de gerar cenas.')
    ensure_style_plan(root, 'pictograma')
    direction = settings(project)
    material = root / 'material'
    paragraphs = read(material / 'paragrafos.json')
    if project.get('roteiro_sha256'):
        clean = material / 'roteiro_limpo.txt'
        if (sha(clean) != project['roteiro_sha256']
                or [normalize(row['texto']) for row in paragraphs]
                != [normalize(text) for text in speech_paragraphs(clean.read_text(encoding='utf-8'))]):
            raise ValueError('Fala canônica alterada. Revise o projeto.')
    fmt = fmt or project['formato']
    if fmt not in ('9:16', '16:9'):
        raise ValueError('O Pictograma usa 9:16 ou 16:9.')
    return project, direction, material, paragraphs, fmt


def approval_keys(material, fmt, direction):
    digest = hashlib.sha256(json.dumps(direction, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
    keys = {'storyboard_sha256': sha(material / BOARD), 'roteiro_sha256': sha(material / 'paragrafos.json'),
            'direcao_sha256': digest, 'formato': fmt}
    if is_visual(read(material/BOARD)):
        keys['modelo_aprovado_sha256'] = sha(material/MODEL_APPROVAL)
    return keys


def require_approval(material, direction, fmt, scenes, words):
    if direction['aprovacao'] != 'storyboard':
        return
    path = material / APPROVAL
    if not path.is_file() or not (material / BOARD).is_file():
        raise ValueError('Aguarde a aprovação explícita do storyboard antes de aplicar o plano completo.')
    review = read(path)
    if any(review.get(key) != value for key, value in approval_keys(material, fmt, direction).items()):
        raise ValueError('Storyboard, fala, formato ou direção alterados. Solicite nova aprovação.')
    source = read(material / BOARD)
    board = compile_plan(source, words, direction, storyboard=not is_visual(source))
    if [(item['id'], item['palavra']) for item in board] != [(item['id'], item['palavra']) for item in scenes]:
        raise ValueError('As cenas e entradas do plano precisam corresponder ao storyboard aprovado.')


def get_palette(direction):
    return direction['cores'] if direction['paleta'] == 'personalizada' else PALETTES[direction['paleta']]


def player(path, project, direction, fmt, scenes, words, times, duration, estimated, narration=None, hold=None, **extra):
    dimensions = FORMATS[fmt]
    palette = get_palette(direction)
    logo = None
    if direction['marca'] == 'sim':
        logo = 'data:image/png;base64,' + base64.b64encode((ASSETS / 'jp-wealth-logo.png').read_bytes()).decode()
    data = {'dimensoes': dimensions, 'paleta': palette, 'legenda': direction['legenda'] == 'sim',
            'tom': direction['tom'], 'marca': logo, 'cenas': scenes, 'duracao': duration,
            'palavras': [{**word, 'tempo': t} for word, t in zip(words.words, times)]}
    fonts = ASSETS / 'pictograma-fontes'
    archivo = base64.b64encode((fonts / 'Archivo.ttf').read_bytes()).decode('ascii')
    atkinson = base64.b64encode((fonts / 'Atkinson-Bold.ttf').read_bytes()).decode('ascii')
    css = (
        '@font-face{font-family:Archivo;src:url(data:font/ttf;base64,' + archivo +
        ') format("truetype");font-weight:400 900;font-stretch:62% 125%}'
        '@font-face{font-family:Atkinson;src:url(data:font/ttf;base64,' + atkinson +
        ') format("truetype");font-weight:700}'
        '#palco{font-family:Atkinson,Arial,sans-serif}.picto-display{font-family:Archivo,"Arial Narrow",Arial,sans-serif;'
        'font-weight:800;font-stretch:80%}.picto-auxiliar{font-family:Atkinson,Arial,sans-serif;font-weight:700}'
    )
    data.update(kit='pictograma', estimado=estimated, repouso=hold,
                densidade=direction['densidade_animacao'], rotulo_cena=False, **extra)
    notes = ''
    if not estimated and 'sincronia' in data:
        from pictograma_relatorio import editor
        notes = editor()
    asset = 'kit-pictograma.js'
    if 'composicao_declarativa' in data:
        data.update(kit='pictograma-declarativo', interface_cena=False)
        names = ('pictograma-figura.js','pictograma-palco.js','pictograma-rig.js',
                 'pictograma-acoes.js','pictograma-efeitos.js','pictograma-virada.js',
                 'pictograma-visuais.js','pictograma-cenarios.js','kit-pictograma-declarativo.js')
    elif 'bible' in data:
        data.update(kit='pictograma-cinematico', interface_cena=False)
        if 'encenacao' not in data['coreografia']:
            data['coreografia']['encenacao'] = read(ASSETS/'pictograma-legado-cinematico.json')
        names = ('pictograma-figura.js', 'pictograma-palco.js')
        if 'rig_anatomico' in data:
            names += ('pictograma-rig.js', 'pictograma-acoes.js', 'pictograma-atuacao.js')
            notes += '<button id="ver-diagnostico" type="button" aria-pressed="false">Mostrar diagnóstico</button>'
        if 'efeitos_pictograma' in data:
            names += ('pictograma-efeitos.js',)
            notes += '<button id="alternar-efeitos" type="button" aria-pressed="true">Luz e efeitos</button>'
        if 'rig_anatomico' in data and not data.get('piloto_godot'):
            from pictograma_coreografia import library_preview_data
            names = library_preview_data(data)
        else:
            names += ('kit-pictograma-cinematico.js',)
    elif 'coreografia' in data:
        data.update(kit='pictograma-coreografia', interface_cena=False)
        names = ('kit-pictograma-coreografia.js',)
    else:
        names = (asset,)
    source = '\n'.join((ASSETS/name).read_text(encoding='utf-8') for name in names)
    return scene_player(path, project['titulo'], fmt, data, source, narration, css=css, notes=notes)


def gate_anatomical(source, root):
    if is_anatomical(source.get('coreografia', {})):
        require_sheets(root / 'folhas')


def storyboard(args, root, project, direction, material, words, fmt):
    ensure_style_plan(root, 'pictograma', args.plano)
    source = read(args.plano)
    gate_anatomical(source, root)
    if is_visual(source):
        visual_storyboard(args, root, project, direction, material, words, fmt, source)
        return
    if direction['aprovacao'] != 'storyboard':
        raise ValueError('A direção atual escolhe animação direta.')
    scenes = compile_plan(source, words, direction, storyboard=True)
    times = [index * TIME_PER_WORD for index in range(len(words.words))]
    duration = len(times) * TIME_PER_WORD
    timeline = schedule(scenes, times, duration, check_rhythm=False)
    out = root / ('pictograma-' + fmt.replace(':', 'x')) / 'storyboard'
    render_direction = {**direction, 'legenda': 'nao'}
    player(out / 'palco.html', project, render_direction, fmt, timeline, words, times, duration, True)
    capture(args.node, out / 'palco.html', out, fmt, [(scene['id'], scene['inicio']) for scene in timeline])
    cards = ''.join(f'<figure><img src="{scene["id"]}.png" alt="Quadro {scene["id"]}">'
                    f'<figcaption>{scene["id"]} · {html.escape(scene["fala"])}</figcaption></figure>'
                    for scene in timeline)
    (out / 'index.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Storyboard Pictograma</title><style>body{background:#121715;color:#ECE6D8;font:16px system-ui;margin:24px}
main{display:flex;gap:16px;flex-wrap:wrap}figure{margin:0;width:230px}img{width:100%;display:block}
figcaption{padding:8px 0 18px}</style><h1>Storyboard Pictograma</h1>'''
                                   + '<main>' + cards + '</main></html>', encoding='utf-8')
    write(material / BOARD, source)
    write(out / 'identidade.json', approval_keys(material, fmt, direction))
    print(out / 'index.html')


def visual_options(project, source, words, scenes, direction, sync, timeline, hold):
    from pictograma_biblia import for_project

    plan = source['coreografia']
    choreography = phases(choreography_anchors(plan, words, scenes, direction), sync, timeline, hold)
    choreography['enquadramento'] = camera(plan)
    if plan['modelo'] == ANATOMICAL_MODEL:
        from pictograma_composicao import pattern_scene_data
        choreography['encenacao'] = pattern_scene_data(plan.get('encenacao'))
    elif 'encenacao' in plan:
        from pictograma_composicao import legacy_scene_data
        choreography['encenacao'] = legacy_scene_data(plan['encenacao'], ASSETS)
    choreography['camera'] = camera_tracks(choreography)
    choreography['parametros'] = plan.get('padroes', {})
    claims = []
    if 'storyboard' in plan:
        for row in storyboard_notes(plan, words):
            frame = min(round(timeline[-1]['fim']*30)-1,
                        max(0, sync['palavras'][row['palavra']]['quadro']+row['quadros']))
            claims.extend({'quadro': frame, 'tipo': value} for value in row['afirmacoes'])
    extra = {'coreografia': choreography, 'bible': for_project(project),
             'afirmacoes_storyboard': claims, 'legenda_a_partir': choreography['corte']}
    if is_anatomical(plan):
        extra['rig_anatomico'] = read(ASSETS/'biblia-anatomica-pictograma.json')
    return extra


def visual_storyboard(args, root, project, direction, material, words, fmt, source):
    from pictograma_sincronia import timing
    if not is_anatomical(source['coreografia']):
        require_model(root, project, get_palette(direction))
    scenes = compile_plan(source, words, direction)
    estimated = args.estimar or not project.get('audio')
    sync = timing(root, project, read(material/'paragrafos.json'), estimated, args.ffmpeg, args.ffprobe)
    times = [row['quadro']/30 for row in sync['palavras']]
    timeline = schedule(scenes, times, max(sync['duracao_s'], times[-1]+1/30))
    hold = sync['fim_fala_s']
    duration = extend_tail(timeline, max(sync['duracao_s'], hold), hold, direction['cauda_s'])
    extra = visual_options(project, source, words, scenes, direction, sync, timeline, hold)
    out = root/('pictograma-'+fmt.replace(':','x'))/'storyboard'
    player(out/'palco.html', project, {**direction, 'legenda':'nao'}, fmt, timeline, words, times,
           duration, estimated, **extra)
    rows = storyboard_notes(source['coreografia'], words)
    requests = [(f'batida-{i:02}', min(duration-1/30, max(0, times[row['palavra']]+row['quadros']/30)))
                for i, row in enumerate(rows, 1)]
    capture(args.node, out/'palco.html', out, fmt, requests)
    if extra['afirmacoes_storyboard']:
        from auditar_animacao import inspect_preview, require_pass
        report = inspect_preview(out, out/'palco.html', fmt, args.node, integral=True)
        require_pass({'issues': [issue for issue in report['issues'] if issue['codigo'] == 'EC-017']})
    cards = ''.join(f'<figure><img src="{key}.png" alt="Batida {i}">'
                    f'<figcaption><strong>{i:02} · {moment:.2f} s</strong>'
                    f'<p>{html.escape(row["nota"])}</p><p>Leitura sem som · {html.escape(row["leitura"])}</p>'
                    '</figcaption></figure>'
                    for i, (row, (key, moment)) in enumerate(zip(rows, requests), 1))
    (out/'index.html').write_text("""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Storyboard do Pictograma</title><style>body{background:#121b16;color:#eee9db;font:16px system-ui;margin:2rem}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:1rem}
figure{margin:0;background:#17231b;padding:.6rem}img{display:block;width:100%}figcaption{padding:.7rem}
</style><h1>Storyboard · Pictograma</h1><main>"""+cards+'</main>', encoding='utf-8')
    write(material/BOARD, source)
    write(out/'identidade.json', approval_keys(material, fmt, direction))
    print(out/'index.html')


def animate(args, root, project, direction, material, paragraphs, words, fmt):
    ensure_style_plan(root, 'pictograma', args.plano)
    source = read(args.plano or material / PLAN)
    gate_anatomical(source, root)
    scenes = compile_plan(source, words, direction)
    if is_visual(source) and not is_anatomical(source['coreografia']):
        require_model(root, project, get_palette(direction))
    require_approval(material, direction, fmt, scenes, words)
    if is_visual(source) and direction['aprovacao']=='storyboard' and read(material/BOARD)!=source:
        raise ValueError('A versão coreografada mudou desde o storyboard aprovado.')
    estimated = args.estimar or not project.get('audio')
    if args.acao == 'video' and estimated:
        raise ValueError('O MP4 exige o arquivo de narração fornecido pelo usuário e tempos medidos.')
    files = [] if estimated else audio_files(audio(root, project), len(paragraphs))
    from pictograma_sincronia import timing

    sync = timing(root,project,paragraphs,estimated,getattr(args,'ffmpeg',None),getattr(args,'ffprobe',None))
    narration_duration = sync['duracao_s']
    times = [item['quadro']/30 for item in sync['palavras']]
    timeline = schedule(scenes,times,max(narration_duration,times[-1]+1/30))
    motion_end = animate_windows(timeline,sync['palavras'],direction['tom'])
    speech_end = sync['fim_fala_s']
    hold = max(speech_end,motion_end)
    duration = extend_tail(timeline,max(narration_duration,hold),speech_end,direction['cauda_s'])
    identity = sync['identidade']['audio_identidade'] if sync['identidade'] else None
    anchors = [{'palavra':row['palavra'],'tempo':row['inicio_s'],'metodo':row['metodo'],
                'motivos_revisao':row['motivos_revisao']} for row in sync['palavras']]
    write(material/'marcacoes_acoes.json',{'estimado':estimated,'audio_identidade':identity,
          'duracao_s':narration_duration,'ancoras':anchors})
    derive_slides(material, scenes, words)
    out = root / ('pictograma-' + fmt.replace(':', 'x'))
    preview = out / 'apresentacao.html'
    unified = material / 'narracao-unificada.m4a'
    narration = files[0] if len(files) == 1 else None
    if not narration and unified.is_file() and not estimated:
        narration = unified
    extra = {'palavras':sync['palavras'],'legendas':sync['legendas'],
             'sincronia':sync,'auditoria_sincronia':True,
             'pessoas_privadas':sync['pessoas_privadas'],'substituicoes_legenda':sync['substituicoes_legenda']}
    if is_visual(source):
        extra.update(visual_options(project, source, words, scenes, direction, sync, timeline, hold))
    elif 'coreografia' in source:
        extra['coreografia'] = phases(choreography_anchors(source['coreografia'], words, scenes, direction),
                                      sync, timeline, hold)
    if (material/EFFECTS_PLAN).is_file():
        if 'rig_anatomico' not in extra:
            raise ValueError('O plano de efeitos requer a composição Pictograma com rig anatômico no navegador.')
        extra['efeitos_pictograma'] = compile_effects(
            read(material/EFFECTS_PLAN), words, timeline, extra['coreografia']['cues'],
            extra['bible'], project, get_palette(direction), round(duration*30))
    player(preview, project, direction, fmt, timeline, words, times, duration, estimated, narration, hold, **extra)
    from pictograma_relatorio import sync_report
    sync_report(out/'sincronia.html',sync,timeline,estimated,extra.get('coreografia'))
    write(material / PLAN, source)
    if 'efeitos_pictograma' in extra:
        write(out/EFFECTS_IDENTITY, effects_keys(material, preview))
    report = {'estilo_video': 'pictograma', 'formato': fmt, 'estimado': estimated, 'duracao_s': duration,
              'audio_identidade': identity, 'cenas': timeline,
              'duracao_narracao_s': narration_duration, 'fim_fala_s': speech_end, 'ancoras': anchors,
              'plano_sha256': sha(material / PLAN), 'roteiro_sha256': sha(material / 'paragrafos.json')}
    if 'coreografia' in extra:
        report['coreografia'] = extra['coreografia']
    if not estimated:
        report['fonte_tempos'] = sorted({row['metodo'] for row in sync['palavras']})
    if args.acao == 'auditar':
        from auditar_animacao import inspect_preview, require_pass
        has_effects = 'efeitos_pictograma' in extra
        audit = inspect_preview(root, preview, fmt, args.node, args.integral or has_effects)
        if has_effects:
            from pictograma_auditoria import audit_effects_preview
            audit = audit_effects_preview(root, preview, fmt, args, audit)
        print(out / 'auditoria.html')
        require_pass(audit)
    if args.acao == 'parecer':
        from pictograma_auditoria import register_review
        register_review(root, preview, fmt, args.parecer, words, direction, args.rodada)
    if args.acao == 'quadros':
        requests = [(f'quadro-{index:02}', moment) for index, moment in enumerate(args.tempo, 1)]
        if any(not 0 <= moment < duration for _, moment in requests):
            raise ValueError('Tempo do quadro fora da prévia.')
        capture(args.node, preview, out / 'quadros', fmt, requests)
    if args.acao == 'video':
        if 'efeitos_pictograma' in extra:
            require_effects_approval(material, preview)
        from animado import export_identity
        from pictograma_sincronia import source_path, MANUAL
        from pictograma_auditoria import prepare_export

        report.update(export_identity(material,project,PLAN,source_path(material)))
        if (material/MANUAL).is_file():
            report['ajustes_sha256'] = sha(material/MANUAL)
        report['previa_sha256'] = sha(preview)
        report['legenda_fonte_sha256'] = sync['identidade']['legenda_sha256']
        target = out / 'video.mp4'
        verify, verify_frames = prepare_export(root, preview, fmt, args, coreografia='coreografia' in extra,
                                               mix_report=report, effects='efeitos_pictograma' in extra)
        from pictograma_mix import GAP, prepare, verify as verify_mix
        level = GAP if args.nivel_trilha_db is None else -args.nivel_trilha_db
        if not 12 <= level <= 15:
            raise ValueError('O Pictograma aceita nível de trilha explícito entre -15 e -12 dB.')

        def mix_audio(ffmpeg, narration, music_input, total, scratch):
            mixed, metrics = prepare(ffmpeg, narration, music_input, total, sync['palavras'], scratch, level)
            report['mixagem'] = metrics
            return mixed, lambda staged: verify_mix(ffmpeg, staged, metrics)

        export_animation(root, preview, target, out / '.render/quadros', fmt, project, paragraphs, report, args,
                         verify=verify, verify_frames=verify_frames, mix_audio=mix_audio,
                         fidelity='efeitos_pictograma' in extra)
        if len(files) > 1:
            player(preview, project, direction, fmt, timeline, words, times, duration, False, unified, hold, **extra)
        print(target)
    report_name = 'timeline_pictograma.json' if args.acao == 'video' else 'timeline_previa.json'
    write(out / report_name, report)
    print(preview)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='acao', required=True)
    style = modes.add_parser('estilo')
    style.add_argument('--root', type=Path)
    style.add_argument('--estilo', choices=STYLES)
    style.add_argument('--salvar', action='store_true', help='Registra somente em projeto.json.')
    style.add_argument('--formato', choices=FORMATS)
    style.add_argument('--confirmar-troca', action='store_true')
    direction = modes.add_parser('direcao')
    direction.add_argument('--root', type=Path, required=True)
    direction.add_argument('--respostas', type=Path)
    direction.add_argument('--assumir', action='store_true')
    sheets = modes.add_parser('folhas')
    sheets.add_argument('--root', required=True, type=Path)
    sheets.add_argument('--node', default=os.environ.get('JP_NODE', 'node'))
    approve = modes.add_parser('aprovar-folhas')
    approve.add_argument('--root', required=True, type=Path)
    approve.add_argument('--confirmado', action='store_true')
    effect_approval = modes.add_parser('aprovar-efeitos')
    effect_approval.add_argument('--root', required=True, type=Path)
    effect_approval.add_argument('--formato', choices=('9:16', '16:9'))
    decision = effect_approval.add_mutually_exclusive_group(required=True)
    decision.add_argument('--confirmado', action='store_true')
    decision.add_argument('--dispensar', action='store_true')
    compose = modes.add_parser('compor')
    compose.add_argument('--root',required=True,type=Path)
    compose.add_argument('--direcao',required=True,type=Path)
    compose.add_argument('--ffmpeg',default=os.environ.get('JP_FFMPEG'))
    compose.add_argument('--ffprobe',default=os.environ.get('JP_FFPROBE'))
    bank = modes.add_parser('banco-de-provas')
    bank.add_argument('--root', type=Path, default=ASSETS.parent/'banco_de_provas')
    bank.add_argument('--preparar', action='store_true')
    bank.add_argument('--renderizar', action='store_true')
    bank.add_argument('--render-longo', action='store_true')
    bank.add_argument('--trecho', action='append')
    bank.add_argument('--fontes-v7', type=Path)
    bank.add_argument('--economia', type=Path)
    bank.add_argument('--ffmpeg', default=os.environ.get('JP_FFMPEG','ffmpeg'))
    bank.add_argument('--node', default=os.environ.get('JP_NODE','node'))
    bank.add_argument('--python-pixels', default=sys.executable)
    bank.add_argument('--paginas', type=int, default=4)
    visual_commands = {
        'modelo': modes.add_parser('modelo'),
        'aprovar-modelo': modes.add_parser('aprovar-modelo'),
        'storyboard': modes.add_parser('storyboard'),
        'aprovar-storyboard': modes.add_parser('aprovar-storyboard'),
        'previa': modes.add_parser('previa'),
        'quadros': modes.add_parser('quadros'),
        'auditar': modes.add_parser('auditar'),
        'parecer': modes.add_parser('parecer'),
        'video': modes.add_parser('video'),
    }
    for name, sub in visual_commands.items():
        sub.add_argument('--root', required=True, type=Path)
        sub.add_argument('--formato', choices=('9:16', '16:9'))
        if name in ('aprovar-storyboard','aprovar-modelo'):
            sub.add_argument('--confirmado', action='store_true')
            continue
        sub.add_argument('--plano', type=Path, required=name == 'storyboard')
        sub.add_argument('--node', default=os.environ.get('JP_NODE') or os.environ.get('NODE','node'))
        sub.add_argument('--estimar', action='store_true')
        sub.add_argument('--paginas', type=int, default=4)
        if name == 'auditar':
            sub.add_argument('--integral', action='store_true')
        if name == 'parecer':
            sub.add_argument('--parecer',type=Path,required=True)
            sub.add_argument('--rodada',type=int,required=True)
        if name == 'quadros':
            sub.add_argument('--tempo', type=float, action='append', required=True)
        sub.add_argument('--ffmpeg',default=os.environ.get('JP_FFMPEG') or os.environ.get('FFMPEG'))
        sub.add_argument('--ffprobe',default=os.environ.get('JP_FFPROBE') or os.environ.get('FFPROBE'))
        if name in ('auditar','parecer','video'):
            sub.add_argument('--direcao',type=Path,help='plano da direção declarativa')
            sub.add_argument('--trilha')
            sub.add_argument('--nivel-trilha-db', type=float)
            sub.add_argument('--atmosfera')
            sub.add_argument('--motivo-trilha')
        if name=='video':
            sub.add_argument('--candidato',type=Path,help='montagem externa a validar contra o render declarativo')
            sub.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    root = args.root.resolve() if args.root else None
    if args.acao == 'compor':
        from pictograma_composicao import preview
        from pictograma_sincronia import timing
        project,direction,material,paragraphs,fmt=project_context(root,None)
        if fmt!='9:16':
            raise ValueError('A composição declarativa anatômica desta versão requer 9:16.')
        estimate=not project.get('audio')
        tracks=[] if estimate else audio_files(audio(root,project),len(paragraphs))
        if len(tracks)>1:
            raise ValueError('Use a narração unificada para a prévia declarativa.')
        sync=timing(root,project,paragraphs,estimate,args.ffmpeg,args.ffprobe)
        total=max(round(sync['duracao_s']*30),sync['palavras'][-1]['fim_quadro']+1)/30
        print(preview(root,read(args.direcao),paragraphs,sync['palavras'],
                      tracks[0] if tracks else None,total,estimate))
        return
    if args.acao == 'banco-de-provas':
        from pictograma_banco import CASES, make_report, prepare_sources, reference, render_case, render_long
        cases = {case for case,_ in CASES}
        if args.trecho and not set(args.trecho)<=cases:
            raise ValueError('Trecho desconhecido no banco de provas.')
        if args.preparar:
            if not args.fontes_v7 or not args.economia:
                raise ValueError('Indique --fontes-v7 e --economia para preparar os recortes.')
            reference(root,args.ffmpeg)
            prepare_sources(root,args.fontes_v7,args.economia,args.ffmpeg)
        if args.renderizar:
            for case,_ in CASES[1:]:
                if args.trecho and case not in args.trecho:
                    continue
                try:
                    render_case(root,case,args.node,args.ffmpeg,args.python_pixels,args.paginas)
                except (ValueError, OSError, subprocess.CalledProcessError) as exc:
                    evidence=root/'evidencias'/(case+'.json')
                    data=read(evidence) if evidence.is_file() else {}
                    data['falha_execucao']=str(exc)
                    data['bloqueantes']=max(1,data.get('bloqueantes',0))
                    write(evidence,data)
                    print(f'{case}: {exc}',file=sys.stderr)
        if args.render_longo:
            if not args.economia:
                raise ValueError('Indique --economia para o ensaio de render longo.')
            render_long(root,args.economia,args.node,args.ffmpeg,args.paginas)
        passed=make_report(root)
        print(root/'relatorio.html')
        if not passed:
            raise SystemExit(1)
        return
    if args.acao == 'estilo':
        print(json.dumps(choose(root,args.estilo,args.salvar,args.formato,args.confirmar_troca),ensure_ascii=False))
        return
    if args.acao == 'direcao':
        if config(root).get('estilo_video') != 'pictograma':
            raise ValueError('Selecione pictograma antes de registrar a direção visual.')
        if not args.respostas and not args.assumir:
            raise ValueError('Informe as respostas ou a delegação do usuário.')
        print(json.dumps(record(root, read(args.respostas) if args.respostas else {}, args.assumir), ensure_ascii=False))
        return

    if args.acao == 'folhas':
        render_sheets(root/'folhas',args.node)
        print(root/'folhas')
        return
    if args.acao == 'aprovar-folhas':
        approve_sheets(root/'folhas',args.confirmado)
        print('Aprovação das duas folhas registrada.')
        return
    project, direction, material, paragraphs, fmt = project_context(root, args.formato)
    words = Words(paragraphs)
    if getattr(args,'direcao',None):
        if args.plano:
            parser.error('Use --direcao para o plano declarativo ou --plano para cenas coreografadas.')
        from pictograma_declarativo import run
        run(args,root,project,direction,material,paragraphs,words,fmt)
        return
    if getattr(args,'candidato',None):
        parser.error('--candidato requer --direcao.')
    if args.acao == 'aprovar-efeitos':
        preview = root/('pictograma-'+fmt.replace(':','x'))/'apresentacao.html'
        register_effects(material, preview, 'aprovado' if args.confirmado else 'dispensado')
        print('Decisão sobre luz e efeitos registrada.')
    elif args.acao == 'modelo':
        print(render_model(root, project, get_palette(direction), args.node))
    elif args.acao == 'aprovar-modelo':
        if not args.confirmado:
            raise ValueError('Registre a aprovação somente após confirmação explícita do usuário.')
        approve_model(root, project, get_palette(direction))
        print('Folha de modelo aprovada.')
    elif args.acao == 'storyboard':
        storyboard(args, root, project, direction, material, words, fmt)
    elif args.acao == 'aprovar-storyboard':
        if not args.confirmado or direction['aprovacao'] != 'storyboard':
            raise ValueError('Registre a aprovação somente após confirmação explícita do usuário.')
        out = root / ('pictograma-' + fmt.replace(':', 'x')) / 'storyboard'
        keys = approval_keys(material, fmt, direction)
        if not (out / 'index.html').is_file() or read(out / 'identidade.json') != keys:
            raise ValueError('Gere o storyboard atual antes da aprovação.')
        write(material / APPROVAL, keys)
        print('Aprovação registrada.')
    else:
        animate(args, root, project, direction, material, paragraphs, words, fmt)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
