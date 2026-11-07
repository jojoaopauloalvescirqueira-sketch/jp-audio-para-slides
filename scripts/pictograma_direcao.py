"""Registro das escolhas do diretor de animação e do usuário."""
from datetime import datetime, timezone
import re

from direcao import update_section
from projeto import config, write

PALETTES = {
    'escura': dict(fundo='#0B0F0D', osso='#ECE6D8', acento='#9CC6A6', suave='#89978F', linha='#2C3631'),
    'clara': dict(fundo='#F1EEE5', osso='#15231C', acento='#346249', suave='#536459', linha='#CCD6CE'),
}
OPTIONS = {
    'criacao': ('diretor', 'colaborativa', 'usuario'),
    'tom': ('sobrio', 'didatico', 'energetico'),
    'metafora': ('literal', 'ilustrativa', 'metaforica'),
    'personagens': ('genericos', 'papeis', 'nomes'),
    'texto': ('palavras', 'frases', 'nenhum'),
    'legenda': ('sim', 'nao'),
    'paleta': ('escura', 'clara', 'personalizada'),
    'aprovacao': ('storyboard', 'direta'),
    'marca': ('sim', 'nao'),
}
DEFAULTS = dict(criacao='diretor', tom='didatico', metafora='ilustrativa', personagens='genericos',
                texto='palavras', legenda='sim', paleta='escura', aprovacao='storyboard', marca='nao')
FIELDS = (*OPTIONS, 'cores', 'nomes_autorizados', 'descricoes')
LABELS = {
    'criacao': 'Criação de cenas', 'tom': 'Tom visual', 'metafora': 'Metáfora',
    'personagens': 'Personagens', 'texto': 'Texto na tela', 'legenda': 'Legenda palavra a palavra',
    'paleta': 'Paleta', 'aprovacao': 'Aprovação', 'marca': 'Marca d’água', 'cores': 'Cores personalizadas',
    'nomes_autorizados': 'Nomes autorizados', 'descricoes': 'Descrições fornecidas',
}


def checked_value(field, value):
    if field in OPTIONS:
        if value not in OPTIONS[field]:
            raise ValueError(f'{field}: escolha fora das opções.')
    elif field == 'cores':
        if not isinstance(value, dict) or value.keys() != PALETTES['escura'].keys() or not all(
                isinstance(color, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', color) for color in value.values()):
            raise ValueError('Use os cinco tokens de paleta em hexadecimal #RRGGBB.')
    elif field == 'nomes_autorizados':
        if not isinstance(value, list) or not all(
                isinstance(name, str) and name.strip() and '\n' not in name and len(name) <= 44 for name in value):
            raise ValueError('Forneça uma lista de nomes explicitamente autorizados.')
        value = [name.strip() for name in value]
    elif not isinstance(value, str) or not value.strip():
        raise ValueError('Descreva as cenas fornecidas como texto.')
    return value


def record(root, choices, assume=False):
    project = config(root)
    if not isinstance(choices, dict) or choices.keys() - set(FIELDS):
        raise ValueError('Escolhas de direção visual inválidas.')
    current = dict(project.get('direcao_visual', {}))
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    supplied = dict(choices)
    if assume:
        for name, default in DEFAULTS.items():
            if name not in current and name not in supplied:
                supplied[name] = {'valor': default, 'origem': 'padrao_assumido'}
    for field, entry in supplied.items():
        if not isinstance(entry, dict) or entry.keys() - {'valor', 'origem'} or 'valor' not in entry:
            raise ValueError(f'{field}: informe valor e origem.')
        source = entry.get('origem', 'usuario')
        if source not in ('usuario', 'padrao_assumido'):
            raise ValueError(f'{field}: origem inválida.')
        if field == 'nomes_autorizados' and source != 'usuario':
            raise ValueError('Nomes reais exigem autorização explícita do usuário.')
        value = checked_value(field, entry['valor'])
        previous = current.get(field)
        if not previous or previous.get('valor') != value or previous.get('origem') != source:
            current[field] = {'valor': value, 'origem': source, 'data': stamp}
    project['direcao_visual'] = current
    settings(project)
    write(root / 'projeto.json', project)
    lines = []
    for field, entry in current.items():
        value = entry['valor']
        if isinstance(value, list):
            value = ', '.join(value)
        elif isinstance(value, dict):
            value = ', '.join(f'{key} {color}' for key, color in value.items())
        lines.append(f'- **{LABELS[field]}** — {" ".join(value.split())} ({entry["origem"]}).')
    update_section(root / 'material/guia_producao.md', '## Direção visual', '\n'.join(lines))
    return current


def settings(project):
    choices = project.get('direcao_visual', {})
    missing = set(OPTIONS) - choices.keys() - {'marca'}
    if missing:
        raise ValueError('Complete a direção visual antes de propor cenas: ' + ', '.join(sorted(missing)))
    values = {key: checked_value(key, entry['valor']) for key, entry in choices.items()}
    values.setdefault('marca', 'nao')
    if values['paleta'] == 'personalizada' and 'cores' not in values:
        raise ValueError('Informe os tokens da paleta personalizada.')
    if values['criacao'] != 'diretor' and 'descricoes' not in values:
        raise ValueError('Registre as descrições livres das cenas fornecidas pelo usuário.')
    names = values.get('nomes_autorizados', [])
    if values['personagens'] == 'nomes' and (
            not names or choices['nomes_autorizados'].get('origem') != 'usuario'):
        raise ValueError('Registre a autorização explícita dos nomes reais.')
    values['nomes_autorizados'] = names if values['personagens'] == 'nomes' else []
    return values
