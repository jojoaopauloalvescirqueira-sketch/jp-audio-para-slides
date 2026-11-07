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
import tempfile
from urllib.parse import quote

from alinha_audio import word_alignment
from estilo_video import STYLES, resolve, save
from fala import normalize, paragraphs as speech_paragraphs
from pictograma_direcao import PALETTES, record, settings
from pictograma_plano import TIME_PER_WORD, Words, compile_plan, measured_times, schedule
from projeto import FORMATS, audio, audio_files, binary, config, probe, read, sha, write
from trilha import select as select_music
from video_export import export

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
PLAN = 'cenas_pictograma.json'
BOARD = 'storyboard_pictograma.json'
APPROVAL = 'aprovacao_storyboard.json'


def project_context(root, fmt):
    project = config(root)
    if project.get('estilo_video') != 'pictograma':
        raise ValueError('Registre o estilo pictograma antes de gerar cenas.')
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
    return {'storyboard_sha256': sha(material / BOARD), 'roteiro_sha256': sha(material / 'paragrafos.json'),
            'direcao_sha256': digest, 'formato': fmt}


def require_approval(material, direction, fmt, scenes, words):
    if direction['aprovacao'] != 'storyboard':
        return
    path = material / APPROVAL
    if not path.is_file() or not (material / BOARD).is_file():
        raise ValueError('Aguarde a aprovação explícita do storyboard antes de aplicar o plano completo.')
    review = read(path)
    if any(review.get(key) != value for key, value in approval_keys(material, fmt, direction).items()):
        raise ValueError('Storyboard, fala, formato ou direção alterados. Solicite nova aprovação.')
    board = compile_plan(read(material / BOARD), words, direction, storyboard=True)
    if [(item['id'], item['palavra']) for item in board] != [(item['id'], item['palavra']) for item in scenes]:
        raise ValueError('As cenas e entradas do plano precisam corresponder ao storyboard aprovado.')


def player(path, project, direction, fmt, scenes, words, times, duration, estimated, narration=None):
    dimensions = FORMATS[fmt]
    palette = direction['cores'] if direction['paleta'] == 'personalizada' else PALETTES[direction['paleta']]
    logo = None
    if direction['marca'] == 'sim':
        logo = 'data:image/png;base64,' + base64.b64encode((ASSETS / 'jp-wealth-logo.png').read_bytes()).decode()
    data = {'dimensoes': dimensions, 'paleta': palette, 'legenda': direction['legenda'] == 'sim',
            'tom': direction['tom'], 'marca': logo, 'cenas': scenes, 'duracao': duration,
            'palavras': [{**word, 'tempo': t} for word, t in zip(words.words, times)]}
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    title = html.escape(project['titulo'])
    status = 'Prévia estimada · 140 palavras/min' if estimated else 'Prévia sincronizada · áudio medido'
    shortcuts = ''.join(f'<button data-cena="{i}">{html.escape(scene["id"])}</button>'
                        for i, scene in enumerate(scenes))
    audio_tag = f'<audio id="narracao" preload="metadata" src="{quote(os.path.relpath(narration, path.parent))}"></audio>' if narration else ''
    width, height = dimensions
    motor = (ASSETS / 'pictograma/motor.js').read_text(encoding='utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Pictograma</title>
<style>
:root {{ color-scheme:dark; background:#121715; color:#ECE6D8; font:16px system-ui, sans-serif }}
body {{ margin:0; padding:16px; }}
main {{ max-width:1000px; margin:auto; display:flex; flex-wrap:wrap; gap:24px; justify-content:center }}
figure {{ width:min(100%, max(280px, calc(72vh * {width}/{height}))); margin:0 }}
#palco {{ display:block; width:100%; height:auto; background:{palette['fundo']}; font-family:Arial, sans-serif }}
section {{ max-width:440px; flex:1 1 250px }}
.controls, nav {{ display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 }}
button {{ font:inherit; padding:8px 14px; border:1px solid #536459; border-radius:20px; background:#16241c; color:#ECE6D8 }}
button:focus-visible, input:focus-visible {{ outline:2px solid #9CC6A6 }}
label {{ display:flex; gap:10px; align-items:center }} input {{ width:100%; accent-color:#9CC6A6 }}
html.render, html.render body {{ margin:0; padding:0; overflow:hidden }}
html.render main, html.render figure {{ display:block; margin:0; width:100vw; max-width:none }}
html.render .controls, html.render label, html.render section {{ display:none }}
</style>
<script>if (new URLSearchParams(location.search).has('render')) document.documentElement.classList.add('render');</script>
<main><figure><svg id="palco" viewBox="0 0 {width} {height}" role="img" aria-label="Palco Pictograma"></svg>
<div class="controls"><button id="assistir">Assistir</button><button id="recomecar">Recomeçar</button></div>
<label>Tempo <input id="tempo" type="range" min="0" step="0.001" aria-label="Posição na animação"><output id="posicao"></output></label>
{audio_tag}</figure><section><p>{status}</p><h1>{title}</h1><nav aria-label="Ir para cena">{shortcuts}</nav></section></main>
<script id="dados" type="application/json">{payload}</script><script>{motor}</script></html>''', encoding='utf-8')


def capture(node, page, output, fmt, requests=None, count=None):
    width, height = FORMATS[fmt]
    script = Path(__file__).with_name('renderizar_pictograma.mjs')
    with tempfile.TemporaryDirectory(prefix='.pedidos-pictograma-', dir=page.parent) as scratch:
        mode = 'video' if count is not None else 'quadros'
        argument = str(count)
        if requests is not None:
            path = Path(scratch) / 'quadros.json'
            write(path, requests)
            argument = str(path)
        subprocess.run([node, str(script), str(page), str(output), str(width), str(height), mode, argument], check=True)


def storyboard(args, root, project, direction, material, words, fmt):
    if direction['aprovacao'] != 'storyboard':
        raise ValueError('A direção atual escolhe animação direta.')
    source = read(args.plano)
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


def animate(args, root, project, direction, material, paragraphs, words, fmt):
    source = read(args.plano or material / PLAN)
    scenes = compile_plan(source, words, direction)
    require_approval(material, direction, fmt, scenes, words)
    estimated = args.estimar or not project.get('audio')
    if args.acao == 'video' and estimated:
        raise ValueError('O MP4 exige áudio e palavras medidas.')
    files = []
    if estimated:
        duration = len(words.words) * TIME_PER_WORD
        times = [index * TIME_PER_WORD for index in range(len(words.words))]
        identity = None
    else:
        files = audio_files(audio(root, project), len(paragraphs))
        duration, heard, expected, _, matches, identity = word_alignment(root, project, paragraphs)
        required = {scene['palavra'] for scene in scenes}
        required.update(item['palavra'] for scene in scenes for item in scene['acoes'])
        times = measured_times(heard, matches, len(expected), required)
    timeline = schedule(scenes, times, duration)
    out = root / ('pictograma-' + fmt.replace(':', 'x'))
    preview = out / 'apresentacao.html'
    unified = material / 'narracao-unificada.m4a'
    narration = files[0] if len(files) == 1 else None
    player(preview, project, direction, fmt, timeline, words, times, duration, estimated, narration)
    write(material / PLAN, source)
    report = {'estilo_video': 'pictograma', 'formato': fmt, 'estimado': estimated, 'duracao_s': duration,
              'audio_identidade': identity, 'cenas': timeline, 'palavras_alinhadas': len(matches) if not estimated else 0}
    if not estimated:
        report['fonte_tempos'] = read(material / 'transcricao_asr.json').get('motor', 'transcrição fornecida')
    if args.acao == 'quadros':
        requests = [(f'quadro-{index:02}', moment) for index, moment in enumerate(args.tempo, 1)]
        if any(not 0 <= moment < duration for _, moment in requests):
            raise ValueError('Tempo do quadro fora da prévia.')
        capture(args.node, preview, out / 'quadros', fmt, requests)
    if args.acao == 'video':
        ffmpeg = binary('ffmpeg', args.ffmpeg)
        ffprobe = binary('ffprobe', args.ffprobe)
        infos = [probe(file, ffprobe) for file in files]
        measured_duration = sum(float(info['format']['duration']) for info in infos)
        if abs(measured_duration - duration) > .06 or round(measured_duration * 30) != round(duration * 30):
            raise ValueError('Duração da transcrição difere da narração medida.')
        music_project = {**project, 'trilha_obrigatoria': True}
        music = select_music(root, music_project, args.trilha, args.nivel_trilha_db, ffprobe,
                             args.atmosfera, args.motivo_trilha, duration)
        target = out / 'video.mp4'
        with tempfile.TemporaryDirectory(prefix='.quadros-', dir=out) as scratch:
            capture(args.node, preview, Path(scratch), fmt, count=round(duration * 30))
            export(root, target, fmt, files, infos, duration, ffmpeg, ffprobe, music, report, project,
                   ['-framerate', '30', '-i', str(Path(scratch) / '%08d.png')], args.threads)
        report['quadros'] = round(duration * 30)
        if len(files) > 1:
            player(preview, project, direction, fmt, timeline, words, times, duration, False, unified)
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
    direction = modes.add_parser('direcao')
    direction.add_argument('--root', type=Path, required=True)
    direction.add_argument('--respostas', type=Path)
    direction.add_argument('--assumir', action='store_true')
    visual_commands = {
        'storyboard': modes.add_parser('storyboard'),
        'aprovar-storyboard': modes.add_parser('aprovar-storyboard'),
        'previa': modes.add_parser('previa'),
        'quadros': modes.add_parser('quadros'),
        'video': modes.add_parser('video'),
    }
    for name, sub in visual_commands.items():
        sub.add_argument('--root', required=True, type=Path)
        sub.add_argument('--formato', choices=('9:16', '16:9'))
        if name == 'aprovar-storyboard':
            sub.add_argument('--confirmado', action='store_true')
            continue
        sub.add_argument('--plano', type=Path, required=name == 'storyboard')
        sub.add_argument('--node', default=os.environ.get('NODE', 'node'))
        sub.add_argument('--estimar', action='store_true')
        if name == 'quadros':
            sub.add_argument('--tempo', type=float, action='append', required=True)
        if name == 'video':
            sub.add_argument('--ffmpeg')
            sub.add_argument('--ffprobe')
            sub.add_argument('--trilha')
            sub.add_argument('--nivel-trilha-db', type=float)
            sub.add_argument('--atmosfera')
            sub.add_argument('--motivo-trilha')
            sub.add_argument('--threads', type=int, default=4)
    args = parser.parse_args()
    root = args.root.resolve() if args.root else None
    if args.acao == 'estilo':
        manifest = root / 'projeto.json' if root else None
        chosen = resolve(read(manifest) if manifest and manifest.exists() else None, args.estilo)
        if args.salvar:
            if not root or not chosen['estilo']:
                raise ValueError('Informe um projeto e escolha o estilo antes de registrar.')
            save(root, chosen['estilo'], args.formato)
        print(json.dumps(chosen, ensure_ascii=False))
        return
    if args.acao == 'direcao':
        if config(root).get('estilo_video') != 'pictograma':
            raise ValueError('Selecione pictograma antes de registrar a direção visual.')
        if not args.respostas and not args.assumir:
            raise ValueError('Informe as respostas ou a delegação do usuário.')
        print(json.dumps(record(root, read(args.respostas) if args.respostas else {}, args.assumir), ensure_ascii=False))
        return

    project, direction, material, paragraphs, fmt = project_context(root, args.formato)
    words = Words(paragraphs)
    if args.acao == 'storyboard':
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
