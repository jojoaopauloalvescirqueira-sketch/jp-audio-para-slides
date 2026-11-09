"""Consulta de projetos e sugestão de etapa, sem modificar os insumos."""
from pathlib import Path

from projeto import audio_files, config, outdir, read

LIMIT = 5
STATES = {'roteirizacao', 'aguardando_audio', 'audio_disponivel'}


def _list_file(path):
    if not path.is_file():
        return []
    data = read(path)
    if not isinstance(data, list):
        raise ValueError(f'{path.name} deveria conter uma lista.')
    return data


def _audio_files(root, audio, count):
    if not audio:
        return []
    path = root / audio
    if path.is_file():
        return [path]
    if path.is_dir() and count:
        try:
            files = audio_files(path, count)
        except ValueError:
            return []
        if all(file.is_file() for file in files):
            return files
    return []


def _next_step(material, output, video, paragraphs, scenes, audio, registered_audio):
    if not paragraphs:
        return 'Retomar — registrar o roteiro.'
    if not audio:
        if registered_audio:
            return 'Retomar — localizar ou completar o áudio registrado.'
        return 'Retomar — falta o áudio.'
    if not scenes:
        return 'Retomar — preparar o plano visual.'
    if not (material / 'marcacoes_audio.json').is_file():
        return 'Retomar — alinhar o áudio ao roteiro.'
    if not video.is_file() or not (output / 'timeline.csv').is_file():
        return 'Retomar — conferir o alinhamento e preparar a exportação.'
    return 'Retomar — revisar e entregar os materiais.'


def _inspect(root):
    project = config(root)
    material = root / 'material'
    paragraphs = _list_file(material / 'paragrafos.json')
    scenes = _list_file(material / 'slides.json')
    recorded_audio = project.get('audio')
    if recorded_audio is not None and not isinstance(recorded_audio, str):
        raise ValueError('Caminho do áudio inválido.')
    audio = _audio_files(root, recorded_audio, len(paragraphs))
    has_script = bool(paragraphs) or (material / 'roteiro_limpo.txt').is_file()
    stored = project.get('estado')
    if audio:
        state = 'audio_disponivel'
    elif stored in STATES and stored != 'audio_disponivel':
        state = stored
    else:
        state = 'aguardando_audio' if has_script or recorded_audio else 'roteirizacao'

    fmt = project['formato']
    output = outdir(root, fmt)
    video = root / ('video.mp4' if fmt == '16:9' else f"video-{fmt.replace(':', 'x')}.mp4")
    next_step = _next_step(material, output, video, paragraphs, scenes, audio, recorded_audio)
    animated_artifacts = []
    if project.get('estilo_video') == 'pictograma':
        plan = material / 'cenas_pictograma.json'
        board = material / 'storyboard_pictograma.json'
        approval = material / 'aprovacao_storyboard.json'
        if paragraphs and not project.get('direcao_visual'):
            next_step = 'Retomar — definir a direção de animação.'
        elif board.is_file() and not approval.is_file() and not plan.is_file():
            next_step = 'Retomar — aguardar aprovação do storyboard.'
        elif paragraphs and not plan.is_file():
            next_step = 'Retomar — preparar o plano de cenas Pictograma.'
        elif plan.is_file() and audio:
            rendered = root / ('pictograma-' + fmt.replace(':', 'x')) / 'video.mp4'
            next_step = ('Retomar — revisar e entregar o Pictograma.' if rendered.is_file()
                         else 'Retomar — alinhar as palavras e renderizar o Pictograma.')
        animated_artifacts = [plan, board, approval]
        for format_key in ('9x16', '16x9'):
            folder = root / ('pictograma-' + format_key)
            animated_artifacts.extend(folder / name for name in (
                'apresentacao.html', 'timeline_pictograma.json', 'video.mp4', 'storyboard/index.html'))
    if project.get('estilo_video') == 'ilustrado' and paragraphs:
        folder = material / 'ilustrado'
        plan = material / 'cenas_ilustrado.json'
        status = folder / 'assets.json'
        prompts = folder / 'prompts_imagens.json'
        board = folder / 'aprovacao_storyboard.json'
        bible = folder / 'aprovacao_biblia.json'
        output = root / 'ilustrado' / fmt.replace(':','x')
        animated_artifacts = [plan, status, prompts, board, bible, folder/'storyboard.md',
                              folder/'biblia.json', folder/'elenco.json', folder/'cenarios.json',
                              root/'ilustrado/folha_contato.html']
        for key in ('9x16','16x9'):
            animated_artifacts.extend(root/'ilustrado'/key/name for name in
                                      ('apresentacao.html','timeline_ilustrado.json','video.mp4','validacao.json'))
        if not project.get('direcao_visual'):
            next_step = 'Retomar — definir a direção de arte.'
        elif not (folder/'biblia.json').is_file():
            next_step = 'Retomar — preparar a bíblia visual e o elenco.'
        elif not bible.is_file():
            next_step = 'Retomar — aprovar a bíblia visual.'
        elif not plan.is_file():
            next_step = 'Retomar — preparar o storyboard textual.'
        elif not board.is_file() and project['direcao_visual'].get('storyboard',{}).get('valor')!='direto':
            next_step = 'Retomar — aprovar o storyboard textual.'
        elif not prompts.is_file():
            next_step = 'Retomar — gerar os prompts de imagens.'
        else:
            requested = read(prompts)['prompts']
            inventory = read(status)['assets'] if status.is_file() else []
            by_id = {row['id']:row for row in inventory}
            missing = []
            for request in requested:
                row = by_id.get(request['id'],{})
                if (row.get('status') not in ('recebida','aprovada')
                        or row.get('prompt_sha256') != request['prompt_sha256']
                        or not (folder/'imagens'/request['arquivo']).is_file()):
                    missing.append(request['id'])
            if missing:
                next_step = f'Retomar — faltam {len(missing)} imagens: '+', '.join(missing)+'.'
            elif any(row['status']=='recebida' for row in inventory):
                next_step = 'Retomar — aprovar a folha de contato.'
            elif not audio:
                next_step = 'Retomar — localizar ou completar o áudio registrado.' if recorded_audio else 'Retomar — falta o áudio.'
            else:
                next_step = ('Retomar — revisar e entregar o Ilustrado.' if (output/'video.mp4').is_file()
                             else 'Retomar — alinhar as palavras e renderizar o Ilustrado.')
    activity = [root / 'projeto.json', *audio, *animated_artifacts]
    activity.extend(material / name for name in (
        'roteiro_limpo.txt', 'roteiro_studio.txt', 'guia_producao.md', 'mapa_didatico.md',
        'fidelidade.md', 'paragrafos.json', 'slides.json', 'fontes_figuras.json',
        'mapa_visual.json', 'plano_tags.json', 'transcricao_asr.json',
        'divergencias_asr.json', 'marcacoes_audio.json',
    ))
    for format_key in ('16:9', '21:9', '9:16'):
        slides = outdir(root, format_key)
        activity.extend(slides / name for name in (
            'apresentacao.html', 'manifest.csv', 'render_manifest.json',
            'timeline.csv', 'sincronizacao.json', 'validacao.json',
        ))
        filename = 'video.mp4' if format_key == '16:9' else f"video-{format_key.replace(':', 'x')}.mp4"
        activity.append(root / filename)
    newest = max(path.stat().st_mtime_ns for path in activity if path.is_file())
    return newest, {
        'titulo': ' '.join(project['titulo'].split()),
        'pasta': str(root),
        'estado': state,
        'formato': fmt,
        'audio_disponivel': bool(audio),
        'proximo_passo': next_step,
    }


def scan(roots):
    projects = set()
    notices = []
    for path in roots:
        root = Path(path).expanduser().resolve()
        if root.name == 'projeto.json':
            root = root.parent
        try:
            if not root.is_dir():
                notices.append({'pasta': str(root), 'motivo': 'Pasta indisponível.'})
                continue
            if (root / 'projeto.json').exists():
                projects.add(root)
            for child in root.iterdir():
                if (not child.name.startswith('.') and not child.is_symlink()
                        and child.is_dir() and (child / 'projeto.json').exists()):
                    projects.add(child)
        except OSError:
            notices.append({'pasta': str(root), 'motivo': 'Não foi possível consultar a pasta.'})

    rows = []
    for root in sorted(projects):
        try:
            rows.append(_inspect(root))
        except (OSError, ValueError, TypeError, AttributeError):
            notices.append({'pasta': str(root), 'motivo': 'Manifesto ou artefatos do projeto ilegíveis.'})
    rows.sort(key=lambda row: (-row[0], row[1]['pasta']))
    return {'projetos': [row for _, row in rows[:LIMIT]], 'avisos': notices}
