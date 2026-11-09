"""Seleção local de estilo, migração e arquivo dos planos anteriores."""
import os
import shutil
import tempfile
from pathlib import Path

from editorial import ASSETS, MAP, PROFILE, WATERMARK
from projeto import FORMATS, config, read, write

STYLES = ('editorial_jp', 'pictograma', 'ilustrado', 'legado')
ANIMATED = {'pictograma', 'ilustrado'}
DEFAULT_VAR = 'JP_ESTILO_VIDEO_PADRAO'
DEFAULT_FORMATS = {'pictograma': '9:16', 'ilustrado': '16:9'}


def resolve(project=None, explicit=None, environ=None):
    project = project or {}
    environ = os.environ if environ is None else environ
    inherited = project.get('perfil_visual', 'legado') if project and 'estilo_video' not in project else None
    for style, source in (
        (explicit, 'pedido'), (project.get('estilo_video'), 'projeto'),
        (inherited, 'projeto_anterior'), (environ.get(DEFAULT_VAR), 'ambiente'),
    ):
        if style is not None:
            if style not in STYLES:
                raise ValueError(f'Estilo de vídeo inválido em {source}: {style}.')
            return {'estilo': style, 'origem': source}
    return {'estilo': None, 'origem': 'perguntar'}


def ensure_style_plan(root, style, source=None):
    other = 'ilustrado' if style == 'pictograma' else 'pictograma'
    wrong = f'cenas_{other}.json'
    if (root / 'material' / wrong).exists() or (source and Path(source).name == wrong):
        raise ValueError(f'O projeto {style} recusa {wrong}. Use a troca de estilo para arquivar o plano.')


def _artifacts(root, style):
    shared = ['material/slides.json','material/timeline_cenas.json','material/marcacoes_acoes.json',
              'material/revisao_acoes.json','material/marcacoes_audio.json']
    paths = {
        'pictograma': ['material/cenas_pictograma.json','material/storyboard_pictograma.json',
                       'material/aprovacao_storyboard.json','pictograma-9x16','pictograma-16x9'],
        'ilustrado': ['material/cenas_ilustrado.json','material/ilustrado','ilustrado'],
    }
    static = [MAP,'slides','slides-21x9','slides-9x16','video.mp4','video-21x9.mp4','video-9x16.mp4']
    return [name for name in shared + paths.get(style,static) if (root/name).exists()]


def save(root, style, fmt=None, confirm=False, origin='pedido'):
    if style not in STYLES:
        raise ValueError(f'Estilo de vídeo inválido: {style}.')
    root = Path(root)
    manifest = root/'projeto.json'
    raw = read(manifest)
    project = config(root)
    previous = resolve(raw,environ={})['estilo']
    material = root/'material'
    slides = material/'slides.json'
    planned = (any((material/name).is_file() for name in (
                   'cenas_pictograma.json','storyboard_pictograma.json','cenas_ilustrado.json',
                   'ilustrado/biblia.json'))
               or (slides.is_file() and bool(read(slides))))
    if previous is None and planned:
        previous = raw.get('perfil_visual','legado')
    changing = previous is not None and previous != style
    if changing and planned and not confirm:
        raise ValueError('O projeto já tem plano. Confirme a troca com --confirmar-troca para arquivar o plano anterior.')
    if fmt is not None:
        project['formato'] = fmt
    elif raw.get('estilo_video') != style and style in DEFAULT_FORMATS:
        project['formato'] = DEFAULT_FORMATS[style]
    if project['formato'] not in FORMATS or (style in ANIMATED and project['formato'] not in ('9:16','16:9')):
        raise ValueError(f'Formato inválido para {style}.')

    if not changing and style in ANIMATED:
        ensure_style_plan(root,style)
    archive = None
    moves = []
    created = []
    try:
        if changing:
            history=material/'historico'
            history.mkdir(parents=True,exist_ok=True)
            archive=Path(tempfile.mkdtemp(prefix=previous+'-',dir=history))
            shutil.copy2(manifest,archive/'projeto.json')
            guide=material/'guia_producao.md'
            if guide.is_file():
                shutil.copy2(guide,archive/'guia_producao.md')
            for name in _artifacts(root,previous):
                source,destination=root/name,archive/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                source.rename(destination)
                moves.append((source,destination))
            project.pop('direcao_visual',None)
            project['historico_estilo']=archive.relative_to(root).as_posix()
            if style in ANIMATED:
                ensure_style_plan(root,style)
        if not slides.is_file():
            write(slides,[])
            created.append(slides)
        if style == PROFILE:
            if not (root/MAP).is_file():
                write(root/MAP,[])
                created.append(root/MAP)
            if not project.get('marca_dagua'):
                logo=root/WATERMARK
                if not logo.is_file():
                    shutil.copy2(ASSETS/'jp-wealth-logo.png',logo)
                    created.append(logo)
                project['marca_dagua']=WATERMARK
        project['perfil_visual']=PROFILE if style==PROFILE else 'legado'
        project.update(estilo_video=style,origem_estilo_video=origin)
        with tempfile.NamedTemporaryFile(dir=root,delete=False) as handle:
            staged=Path(handle.name)
        try:
            write(staged,project)
            staged.replace(manifest)
        finally:
            staged.unlink(missing_ok=True)
    except BaseException:
        for file in created:
            file.unlink(missing_ok=True)
        for source,destination in reversed(moves):
            destination.rename(source)
        raise
    if changing:
        from direcao import update_section
        if guide.is_file():
            update_section(guide,'## Direção visual','')
        sources = root/'FONTES.md'
        if previous == 'ilustrado' and sources.is_file():
            shutil.copy2(sources,archive/'FONTES.md')
            update_section(sources,'## Imagens do Ilustrado','')
    return project


def choose(root=None, explicit=None, store=False, fmt=None, confirm=False):
    root = Path(root) if root else None
    manifest = root / 'projeto.json' if root else None
    choice = resolve(read(manifest) if manifest and manifest.is_file() else None, explicit)
    if store:
        if not root or not choice['estilo']:
            raise ValueError('Informe a pasta e escolha o estilo antes de registrar.')
        save(root,choice['estilo'],fmt,confirm,choice['origem'])
    return choice
