"""Valida a proposta do diretor e prepara inserções na fala canônica."""
import re

from fala import BRACKET, paragraphs
from tags_voz import CATALOG, DENSITIES, allowed_categories, preference, tag_key

QUOTES = re.compile(r'“[^”]*”|«[^»]*»|"[^"]*"|‘[^’]*’|(?<!\w)\'[^\n\']+\'(?!\w)|^\s*—[^\n]*', re.M)
HEADING = '## Plano de tags aplicado'


def render(canonical, plan, direction, literals):
    if preference(direction, 'tags') != 'skill':
        raise ValueError('Aplicar tags exige direção registrada no modo skill.')
    language = preference(direction, 'idioma_tags')
    density = preference(direction, 'densidade_tags')
    if (not isinstance(plan, dict) or type(plan.get('versao')) is not int or plan['versao'] != 1
            or language not in ('pt', 'en') or density not in DENSITIES
            or plan.get('idioma') != language or plan.get('densidade') != density):
        raise ValueError('Plano incompatível com a versão, o idioma ou a densidade da direção registrada.')
    for field in ('curva', 'tags', 'testes'):
        if not isinstance(plan.get(field), list):
            raise ValueError(f'O plano precisa de uma lista em {field}.')
    if not plan['curva'] or any(
        not isinstance(row, dict) or type(row.get('intensidade')) is not int
        or not 1 <= row['intensidade'] <= 5 or not _text(row.get('bloco')) or not _text(row.get('funcao'))
        for row in plan['curva']
    ):
        raise ValueError('Informe a curva por bloco com função e intensidade entre 1 e 5.')
    if any(not _text(item) for item in plan['testes']) or (plan['tags'] and not plan['testes']):
        raise ValueError('Informe testes de escuta para as tags propostas.')

    offsets = {}
    end = 0
    for index, paragraph in enumerate(paragraphs(canonical), 1):
        start = canonical.index(paragraph, end)
        offsets[f'P{index:03}'] = (start, paragraph)
        end = start + len(paragraph)

    categories = allowed_categories(direction)
    blocked = {tag_key(item) for item in literals}
    insertions = {}
    applied = []
    controls = []
    for row in plan['tags']:
        if not isinstance(row, dict) or not all(_text(row.get(field)) for field in
                ('p', 'antes_de', 'tag', 'categoria', 'intencao', 'alcance', 'risco')):
            raise ValueError('Entrada de tag incompleta.')
        if not isinstance(row.get('alternativa'), str):
            raise ValueError('A entrada precisa do campo alternativa.')
        p = row['p']
        if p not in offsets:
            raise ValueError(f'Parágrafo inexistente: {p}.')
        match = BRACKET.fullmatch(row['tag'])
        key = tag_key(match[1]) if match else ''
        tag = CATALOG.get(key)
        if not tag or key in blocked or tag['idioma'] != language:
            raise ValueError(f'Tag ausente do catálogo, literal ou de outro idioma em {p}.')
        if tag['categoria'] != row['categoria'] or tag['categoria'] not in categories:
            raise ValueError(f'Categoria da tag incompatível ou sem autorização em {p}.')

        offset, paragraph = offsets[p]
        anchor = row['antes_de']
        hits = [m.start() for m in re.finditer(r'(?=' + re.escape(anchor) + ')', paragraph)]
        if not hits:
            raise ValueError(f'Âncora ausente em {p}: {anchor}')
        if len(hits) > 1 and 'ocorrencia' not in row:
            raise ValueError(f'Âncora ambígua em {p}; informe ocorrencia.')
        occurrence = row.get('ocorrencia', 1)
        if type(occurrence) is not int or not 1 <= occurrence <= len(hits):
            raise ValueError(f'Ocorrência inválida em {p}.')
        pos = hits[occurrence - 1]
        before = paragraph[:pos].rstrip()
        if before and not re.search(r'[.!?…]["”»’\']?$', before):
            raise ValueError(f'A âncora precisa começar em uma fronteira de frase em {p}.')
        if any(q.start() < pos < q.end() for q in QUOTES.finditer(paragraph)):
            raise ValueError(f'A inserção interromperia uma citação em {p}.')
        if offset + pos in insertions:
            raise ValueError(f'Posição de tag duplicada em {p}.')
        insertions[offset + pos] = row['tag'] + ' '
        applied.append((offset + pos, row, occurrence))
        controls.append(key)

    pieces = []
    cursor = 0
    for pos, value in sorted(insertions.items()):
        pieces.extend((canonical[cursor:pos], value))
        cursor = pos
    pieces.append(canonical[cursor:])
    return ''.join(pieces), list(dict.fromkeys(controls)), guide(plan, applied)


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def guide(plan, applied):
    def cell(text):
        return ' '.join(text.split()).replace('|', '\\|')

    lines = ['| P | Tag | Antes de | Intenção |', '| --- | --- | --- | --- |']
    for _, row, occurrence in sorted(applied):
        anchor = cell(row['antes_de']) + f' (ocorrência {occurrence})'
        lines.append(f"| {row['p']} | `{row['tag']}` | {anchor} | {cell(row['intencao'])} |")
    if not applied:
        lines = ['O diretor propôs gravar a fala sem tags.']
    if plan['testes']:
        lines.extend(['', '### Testes de escuta', ''])
        lines.extend('- ' + cell(test) for test in plan['testes'])
    return '\n'.join(lines)
