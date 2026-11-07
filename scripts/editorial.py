"""Contratos, composição e controle de renderização do perfil Editorial JP."""
import html
import re
import shutil
from pathlib import Path

PROFILE = 'editorial_jp'
WATERMARK = 'material/marca-dagua-jp-wealth.png'
MAP = 'material/mapa_visual.json'
FRAME_COUNT = 8
KINDS = {'comparacao', 'diagrama'}
EFFECTS = {'revelar', 'realcar', 'aproximar'}
ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def initialize(root):
    from projeto import write
    logo = Path(root) / WATERMARK
    logo.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / 'jp-wealth-logo.png', logo)
    write(Path(root) / MAP, [])
    return {'perfil_visual': PROFILE, 'marca_dagua': WATERMARK}


def project_file(root, relative, label):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError(f'{label}: use caminho relativo ao projeto.')
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'{label}: arquivo ausente ou fora do projeto: {relative}')
    return path


def targets(scene):
    kind = scene['tipo']
    if kind == 'comparacao':
        return {f'item-{i}' for i in range(1, len(scene['itens']) + 1)}
    if kind in {'conta', 'sintese', 'diagrama'}:
        return {f'linha-{i}' for i in range(1, len(scene['lines']) + 1)}
    return {'vista'} if kind == 'figura' else set()


def validate(root, config, paragraphs, scenes, sources):
    from projeto import read
    project_file(root, config.get('marca_dagua', WATERMARK), 'Marca d’água')
    source_map = {str(s['id']): s for s in sources}
    for scene in scenes:
        kind = scene['tipo']
        name = scene['id']
        if not isinstance(scene.get('conferir_audio', False), bool):
            raise ValueError(f'{name}: conferir_audio precisa ser booleano.')
        if kind == 'comparacao':
            items = scene.get('itens')
            if not isinstance(items, list) or not 1 <= len(items) <= 3:
                raise ValueError(f'{name}: use de um a três itens para a comparação.')
            for item in items:
                if not isinstance(item, dict) or any(
                    not isinstance(item.get(key), str) or not item[key].strip()
                    for key in ('rotulo', 'valor')
                ):
                    raise ValueError(f'{name}: cada item precisa de rótulo e valor com unidade.')
        if kind == 'diagrama' and not 2 <= len(scene['lines']) <= 4:
            raise ValueError(f'{name}: diagrama precisa de duas a quatro etapas.')
        if kind == 'figura':
            src = source_map[str(scene['figura'])]
            project_file(root, src['arquivo'], 'Figura')
            if src.get('natureza', 'evidencia') not in {'evidencia', 'ilustracao'}:
                raise ValueError(f'{name}: natureza da figura inválida.')
        if 'movimento' not in scene:
            continue
        motion = scene['movimento']
        if not isinstance(motion, dict):
            raise ValueError(f'{name}: movimento inválido.')
        effect, target = motion.get('tipo'), motion.get('alvo')
        if not isinstance(effect, str) or not isinstance(target, str) or effect not in EFFECTS or target not in targets(scene):
            raise ValueError(f'{name}: efeito ou alvo incompatível com o modelo.')
        if effect == 'revelar' and target == 'vista':
            raise ValueError(f'{name}: preserve a evidência visível e use realce ou aproximação.')
        if effect == 'aproximar' and (
            target != 'vista' or not source_map[str(scene['figura'])].get('vistas')
        ):
            raise ValueError(f'{name}: aproximação exige uma vista preparada.')

    rows = read(project_file(root, MAP, 'Mapa visual'))
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('O mapa visual deve ser uma lista ordenada.')
    index = 0
    for number, paragraph in enumerate(paragraphs, 1):
        text = paragraph['texto']
        cursor = 0
        while index < len(rows) and rows[index].get('p') == number:
            row = rows[index]
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
            phrase = row.get('trecho')
            if not isinstance(phrase, str) or not phrase.strip() or not text.startswith(phrase, cursor):
                raise ValueError(f'Mapa visual linha {index + 1}: trecho diverge da fala.')
            end = cursor + len(phrase)
            if end < len(text) and not text[end].isspace():
                raise ValueError(f'Mapa visual linha {index + 1}: trecho termina dentro de palavra.')
            active = next((s for s in reversed(scenes)
                           if (s['p'], s['char_start']) <= (number, cursor)), None)
            if not active or row.get('slide_id') != active['id']:
                raise ValueError(f'Mapa visual linha {index + 1}: estado ativo incompatível.')
            if any((s['p'] == number and cursor < s['char_start'] < end) for s in scenes):
                raise ValueError(f'Mapa visual linha {index + 1}: trecho atravessa uma entrada.')
            is_entry = (active['p'], active['char_start']) == (number, cursor)
            allowed = {'nova', 'revelar'} if is_entry else {'manter'}
            if row.get('decisao') not in allowed or not str(row.get('motivo', '')).strip():
                raise ValueError(f'Mapa visual linha {index + 1}: decisão ou motivo inválido.')
            cursor = end
            index += 1
        if text[cursor:].strip():
            raise ValueError(f'Mapa visual incompleto em {paragraph["id"]}.')
    if index != len(rows):
        raise ValueError('Mapa visual contém linhas extras ou fora da ordem.')


def markup(scene, content, source=None):
    """Reaproveita o HTML legado de figuras e acrescenta modelos editoriais."""
    e = html.escape
    kind = scene['tipo']
    title, body = e(scene['title']), e(scene['body'])
    subtitle = f'<p class="editorial-subtitle">{body}</p>' if body else ''
    if kind == 'comparacao':
        cards = ''.join(
            f'<div class="editorial-item" data-alvo="item-{i}">'
            f'<p class="editorial-label">{e(item["rotulo"])}</p>'
            f'<p class="editorial-value">{e(item["valor"])}</p></div>'
            for i, item in enumerate(scene['itens'], 1)
        )
        if len(scene['itens']) == 1:
            cards += '<div class="editorial-item editorial-placeholder" aria-hidden="true"></div>'
        return (f'<div class="editorial-center"><h1>{title}</h1>'
                f'<div class="editorial-items">{cards}</div>{subtitle}</div>')
    if kind in {'diagrama', 'conta', 'sintese'}:
        steps = ''.join(
            f'<div class="editorial-step" data-alvo="linha-{i}"><p>{e(line)}</p></div>'
            for i, line in enumerate(scene['lines'], 1)
        )
        if kind == 'conta' and len(scene['lines']) == 1:
            steps += '<div class="editorial-step editorial-placeholder" aria-hidden="true"><p>0</p></div>'
        return (f'<div class="editorial-center"><h1>{title}</h1>'
                f'<div class="editorial-steps">{steps}</div>{subtitle}</div>')
    if kind == 'figura':
        if source.get('natureza') == 'ilustracao':
            label = 'Ilustração conceitual'
        elif scene.get('vistas', source.get('vistas')):
            label = 'Detalhe do gráfico'
        else:
            label = 'Gráfico de referência'
        return (content.replace('class="figure-image"', 'class="figure-image" data-alvo="vista"', 1)
                + f'<div class="editorial-eyebrow">{label}</div>')
    return content


def render_inputs(root, cfg, fmt, scenes, sources):
    from projeto import sha
    files = ['material/paragrafos.json', 'material/slides.json',
             'material/fontes_figuras.json', MAP, cfg.get('marca_dagua', WATERMARK)]
    used = {str(scene['figura']) for scene in scenes if scene['tipo'] == 'figura'}
    files.extend(source['arquivo'] for source in sources if str(source['id']) in used)
    if cfg['capa']:
        files.append(cfg['capa'])
    return {
        'formato': fmt,
        'perfil': PROFILE,
        'tema_sha256': sha(ASSETS / 'editorial-jp.css'),
        'projeto': {key: cfg[key] for key in
                    ('titulo', 'subtitulo', 'autor', 'marca', 'cta_rotulo', 'cta_url', 'capa')},
        'arquivos': {path: sha(project_file(root, path, 'Entrada visual')) for path in sorted(set(files))},
    }


def frame_paths(scene):
    name = scene['id']
    transition = [f'movimento/{name}-{i:02}.png' for i in range(1, FRAME_COUNT)] if scene.get('movimento') else []
    return transition + [f'png/{name}.png']


def record_render(root, cfg, fmt, scenes, sources, out):
    from projeto import sha, write
    write(out / 'render_manifest.json', {
        'entradas': render_inputs(root, cfg, fmt, scenes, sources),
        'quadros': {scene['id']: {path: sha(out / path) for path in frame_paths(scene)} for scene in scenes},
    })


def check_render(root, cfg, fmt, scenes, sources, out):
    from projeto import read, sha
    path = out / 'render_manifest.json'
    if not path.is_file():
        raise ValueError('Renderização Editorial JP ausente ou parcial; gere todos os quadros.')
    manifest = read(path)
    if manifest.get('entradas') != render_inputs(root, cfg, fmt, scenes, sources):
        raise ValueError('Plano ou recurso visual mudou desde a renderização; gere os quadros novamente.')
    for scene in scenes:
        expected = manifest.get('quadros', {}).get(scene['id'], {})
        for frame in frame_paths(scene):
            file = out / frame
            if not file.is_file() or expected.get(frame) != sha(file):
                raise ValueError(f'Quadro ausente ou alterado: {frame}; renderize novamente.')
