"""Seleção local de estilo e compatibilidade com projetos anteriores."""
import os
import shutil
from pathlib import Path

from editorial import ASSETS, MAP, PROFILE, WATERMARK
from projeto import config, read, write

STYLES = ('editorial_jp', 'pictograma', 'legado')
DEFAULT_VAR = 'JP_ESTILO_VIDEO_PADRAO'


def resolve(project=None, explicit=None, environ=None):
    project = project or {}
    environ = os.environ if environ is None else environ
    inherited = project.get('perfil_visual', 'legado') if project and 'estilo_video' not in project else None
    choices = (
        (explicit, 'pedido'),
        (project.get('estilo_video'), 'projeto'),
        (inherited, 'projeto_anterior'),
        (environ.get(DEFAULT_VAR), 'ambiente'),
    )
    for style, source in choices:
        if style is not None:
            if style not in STYLES:
                raise ValueError(f'Estilo de vídeo inválido em {source}: {style}.')
            return {'estilo': style, 'origem': source}
    return {'estilo': None, 'origem': 'perguntar'}


def save(root, style, fmt=None):
    if style not in STYLES:
        raise ValueError(f'Estilo de vídeo inválido: {style}.')
    root = Path(root)
    project = config(root)
    raw = read(root / 'projeto.json')
    if fmt is not None:
        project['formato'] = fmt
    elif style == 'pictograma' and raw.get('estilo_video') != style:
        project['formato'] = '9:16'
    if style == 'pictograma' and project['formato'] not in ('9:16', '16:9'):
        raise ValueError('O Pictograma usa formato 9:16 ou 16:9.')
    if style == PROFILE:
        if not (root / MAP).is_file():
            write(root / MAP, [])
        if not project.get('marca_dagua'):
            logo = root / WATERMARK
            if not logo.is_file():
                shutil.copy2(ASSETS / 'jp-wealth-logo.png', logo)
            project['marca_dagua'] = WATERMARK
        project['perfil_visual'] = PROFILE
    elif style == 'legado':
        project['perfil_visual'] = 'legado'
    project['estilo_video'] = style
    write(root / 'projeto.json', project)
    return project
