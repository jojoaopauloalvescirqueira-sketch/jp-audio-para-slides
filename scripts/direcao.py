"""Registro das escolhas editoriais do projeto e da seção correspondente no guia."""
import math
import re
from datetime import datetime, timezone
from pathlib import Path

from projeto import FORMATS, config, write
from tags_voz import CATEGORIES, DENSITIES, REQUIRES_PERMISSION, TAG_FIELDS, preference


OPTIONS = {
    'tags': {
        'skill': 'O diretor vocal propõe as tags e a skill valida e aplica o plano.',
        'elevenlabs': 'O Studio parte da fala limpa para receber sugestões no site.',
        'nenhuma': 'O Studio parte da fala limpa para gravação direta.',
    },
    'idioma_tags': {'pt': 'Usar controles em português.', 'en': 'Usar controles em inglês.'},
    'densidade_tags': {name: f'Até uma tag por {words} palavras.' for name, words in DENSITIES.items()},
    'perspectiva': {
        'externa': 'Narração em terceira pessoa com atribuição explícita.',
        'personagem': 'Primeira pessoa ancorada em posição ou vivência identificável.',
    },
    'estilo': {
        'didatico': 'Frases diretas e exemplos concretos com as ressalvas da fonte.',
        'professor': 'Premissas, método, objeções e limites explicitados.',
        'professor-didatico': 'Estrutura de professor com linguagem de explicador.',
    },
    'registro': {
        'culto': 'Sintaxe formal adaptada para leitura em voz alta.',
        'falado': 'Linguagem de conversa com marcas orais coerentes com a voz.',
        'intermediario': 'Cadência oral com vocabulário preciso e coloquialidade moderada.',
    },
    'cobertura': {
        'integral': 'Preservar as referências e a sustentação do argumento.',
        'essencial': 'Priorizar as referências essenciais na fala e documentar os cortes autorizados.',
    },
    'formato': {name: 'Orientar o planejamento visual e a saída padrão do projeto.'
                for name in FORMATS},
    'falas_terceiros': {
        'literal': 'Reproduzir as palavras verificáveis com atribuição explícita.',
        'indireto': 'Atribuir a fala sem aspas e conservar os termos relevantes do interlocutor.',
        'parafrase': 'Explicar com formulação própria e atribuir a ideia à fonte.',
    },
    'sensiveis': {
        'manter': 'Manter formulação e contexto conforme a fonte.',
        'oferecer-alternativa': 'Apresentar uma alternativa para decisão explícita antes de trocar a formulação.',
    },
}

LABELS = {
    'perspectiva': 'Perspectiva', 'estilo': 'Estilo', 'registro': 'Registro',
    'voz': 'Voz', 'destino': 'Destino', 'vivencia': 'Base da primeira pessoa',
    'cobertura': 'Cobertura', 'duracao_alvo': 'Duração-alvo', 'formato': 'Formato',
    'falas_terceiros': 'Falas de terceiros', 'sensiveis': 'Trechos sensíveis',
    'tags': 'Quem posiciona as tags', 'idioma_tags': 'Idioma das tags',
    'densidade_tags': 'Densidade das tags', 'categorias_tags': 'Categorias das tags',
}

TEXT_EFFECTS = {
    'voz': 'Orientar pronomes, atribuição e interpretação.',
    'destino': 'Orientar a abertura e o encerramento para o público indicado.',
    'vivencia': 'Delimitar a experiência ou posição que sustenta a primeira pessoa.',
}

HEADING = '## Direção narrativa'


def duration(value):
    if value == 'livre':
        return value
    try:
        seconds = float(value)
    except (ValueError, TypeError):
        raise ValueError('Duração-alvo deve ser positiva em segundos ou livre.') from None
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('Duração-alvo deve ser positiva em segundos ou livre.')
    return seconds


def block(value):
    parts = value.split(':')
    if len(parts) != 3 or not re.fullmatch(r'[\w-]+', parts[0]) or not any(parts[1:]):
        raise ValueError('Use --bloco ID:PERSPECTIVA:ESTILO, deixando vazio o campo herdado.')
    name, perspective, style = parts
    choices = {'perspectiva': perspective, 'estilo': style}
    overrides = {key: choice for key, choice in choices.items() if choice}
    if any(choice not in OPTIONS[key] for key, choice in overrides.items()):
        raise ValueError('Perspectiva ou estilo de bloco desconhecido.')
    return name, overrides


def arguments(parser):
    for field in LABELS:
        kwargs = {'choices': OPTIONS[field]} if field in OPTIONS else {}
        if field == 'categorias_tags':
            kwargs = {'action': 'append', 'choices': CATEGORIES}
        parser.add_argument('--' + field.replace('_', '-'), **kwargs)
    parser.add_argument('--bloco', action='append', default=[], metavar='ID:PERSPECTIVA:ESTILO')
    parser.add_argument('--assumir', action='append', default=[], choices=[*LABELS, 'blocos'],
                        help='Marcar o campo fornecido como padrão assumido. Repetir por campo.')


def _entry(previous, value, assumed, stamp):
    entry = {'valor': value, 'origem': 'padrao_assumido' if assumed else 'usuario'}
    if previous and all(previous.get(key) == val for key, val in entry.items()):
        return previous
    return {**entry, 'data': stamp}


def record(root, args):
    root = Path(root)
    project = config(root)
    direction = project.get('direcao_narrativa', {}).copy()
    fields = {key: getattr(args, key) for key in LABELS if getattr(args, key) is not None}
    for key in fields.keys() & TEXT_EFFECTS.keys():
        fields[key] = ' '.join(fields[key].split())
        if not fields[key]:
            raise ValueError(f'{LABELS[key]} deve ter um valor.')
    if 'duracao_alvo' in fields:
        fields['duracao_alvo'] = duration(fields['duracao_alvo'])
    blocks = dict(block(value) for value in args.bloco)
    if len(blocks) != len(args.bloco):
        raise ValueError('Informe cada bloco uma vez por execução.')
    supplied = set(fields)
    if blocks:
        supplied.add('blocos')
    assumed = set(args.assumir)
    if not supplied or assumed - supplied:
        raise ValueError('Informe escolhas e use --assumir somente para campos fornecidos.')
    if 'categorias_tags' in fields:
        fields['categorias_tags'] = list(dict.fromkeys(fields['categorias_tags']))
        if 'categorias_tags' in assumed and REQUIRES_PERMISSION.intersection(fields['categorias_tags']):
            raise ValueError('Voz e efeitos sonoros exigem autorização explícita.')
    mode = fields.get('tags', preference(direction, 'tags'))
    if mode != 'skill':
        if fields.keys() & set(TAG_FIELDS):
            raise ValueError('Idioma, densidade e categorias exigem o modo skill.')
        for key in TAG_FIELDS:
            direction.pop(key, None)
    stamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    for key, value in fields.items():
        direction[key] = _entry(direction.get(key), value, key in assumed, stamp)
    if blocks:
        existing = direction.get('blocos', {}).copy()
        for name, overrides in blocks.items():
            choices = existing.get(name, {}).copy()
            for key, value in overrides.items():
                choices[key] = _entry(choices.get(key), value, 'blocos' in assumed, stamp)
            existing[name] = choices
        direction['blocos'] = existing
    if 'formato' in fields:
        project['formato'] = fields['formato']
    project['direcao_narrativa'] = direction
    write(root / 'projeto.json', project)
    update_guide(root, direction)
    return direction


def _item(field, entry):
    value = entry['valor']
    effect = OPTIONS[field][value] if field in OPTIONS else TEXT_EFFECTS.get(field)
    if field == 'categorias_tags':
        value = ', '.join(value)
        effect = 'Limitar a proposta às categorias autorizadas.'
    if field == 'duracao_alvo':
        if value == 'livre':
            effect = 'Deixar o tempo decorrer da cobertura e da explicação necessária.'
        else:
            value = f'{value:g} s'
            effect = 'Orientar o ritmo e a estimativa de palavras. Conflitos de cobertura exigem decisão.'
    return f'- **{LABELS[field]}** — {value} ({entry["origem"]}). {effect}'


def update_guide(root, direction):
    path = Path(root) / 'material/guia_producao.md'
    lines = [_item(field, direction[field]) for field in LABELS if field in direction]
    for name, choices in direction.get('blocos', {}).items():
        lines.append(f'- **Bloco {name}**')
        lines.extend('  ' + _item(field, entry) for field, entry in choices.items())
    if preference(direction, 'tags') == 'elevenlabs':
        lines.extend(['', '1. Abra uma cópia da fala limpa no Studio e confira voz e modelo.',
                      '2. Selecione a narração e procure **AI Tools → Enhance text**. Se o recurso não estiver disponível no Studio, use **v4 Enhance** no Text to Speech com Eleven v4.',
                      '3. Compare as sugestões com a fala limpa. Retenha apenas as tags desejadas e restaure palavras, pontuação e parágrafos antes de gerar.',
                      '4. Ao receber o áudio, confira as diferenças que o reconhecimento indicar antes de alinhar.'])
    update_section(path, HEADING, '\n'.join(lines))


def update_section(path, heading, content):
    """Atualiza somente a seção gerada do guia."""
    text = path.read_text(encoding='utf-8') if path.exists() else '# Guia de produção\n'
    section = re.compile(r'^' + re.escape(heading) + r'[ \t]*(?:\n|\Z).*?(?=^#{1,2}[ \t]|\Z)', re.M | re.S)
    replacement = heading + '\n\n' + content + '\n' if content else ''
    if section.search(text):
        updated = section.sub(lambda match: replacement + ('\n' if replacement and match.end() < len(text) else ''), text, count=1)
    elif replacement:
        separator = '\n' if text.endswith('\n') else '\n\n'
        updated = text + separator + replacement if text else replacement
    else:
        return
    if updated != text:
        path.write_text(updated, encoding='utf-8')
