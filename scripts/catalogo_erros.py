"""Catálogo de regressões do Pictograma e projeção Markdown."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def catalogo():
    return json.loads((ROOT / 'assets/erros_conhecidos.json').read_text(encoding='utf-8'))


def markdown(rows):
    lines = ['# Erros conhecidos do Pictograma', '',
             'Fonte: `assets/erros_conhecidos.json`. Registre exemplo, regra, checagem e teste antes de corrigir.',
             'Exemplos sem quadro histórico comprovado são fichas de reprodução. Abra as imagens para conferir a origem.',
             'O auditor usa os exemplos como contraexemplos e os compara com o quadro corrigido, quando disponível.', '',
             '| ID | Erro | Categoria | Estado | Exemplo |',
             '| --- | --- | --- | --- | --- |']
    for row in rows:
        lines.append('| {id} | {titulo} | {categoria} | {estado} | [PNG](erros/{id}.png) |'.format(**row))
    for row in rows:
        check = row['checagem'] or {}
        lines.extend(['', '## {id} · {titulo}'.format(**row), '', row['regra'], '',
                      'Registro: ' + row['encontrado_em'] + '. Exemplo: ' + row['origem_exemplo'] + '.',
                      'Checagem: ' + check.get('funcao', 'a implementar') +
                      ('. Bloqueia o MP4: ' + ('sim' if check['bloqueia_mp4'] else 'não') if check else '') + '.',
                      'Teste: ' + (row['teste'] or 'a implementar') + '.'])
    return '\n'.join(lines) + '\n'


def resumo(report):
    """Não atribui aprovação a uma checagem ausente ou sem aplicação comprovada."""
    flags = {row['codigo'] for row in report['issues']}
    dom = report.get('checagens_catalogo', {})
    active = report.get('catalogo_evidencias', {})
    result = []
    for row in catalogo():
        code = row['id']
        check = row['checagem'] or {}
        present = flags.intersection(check.get('codigos', []) + [code])
        if present:
            status = 'reprovado' if check.get('bloqueia_mp4') else 'aviso'
        elif code in dom and dom[code]['quadros']:
            status = 'conferido' if report['modo'] == 'integral' else 'conferido_em_amostra'
        elif code in active:
            status = active[code]
        elif row['estado'] == 'fora_de_escopo':
            status = 'fora_de_escopo'
        else:
            status = 'não aferido nesta auditoria'
        result.append({'id': code, 'titulo': row['titulo'], 'resultado': status,
                       **({'medicoes': dom[code]} if code in dom else {})})
    return result


def fixture(path):
    """Prévia muda com tempos congelados para testes de geometria."""
    from types import SimpleNamespace
    from pictograma import player
    from pictograma_biblia import for_project
    data = json.loads((ROOT/'assets/referencia-pictograma/fixture-catalogo.json').read_text(encoding='utf-8'))
    direction = {'paleta':'personalizada','cores':data.pop('paleta'), 'legenda':'sim',
                 'marca':'nao', 'tom':'didatico', 'densidade_animacao':'abundante'}
    return player(path, {'titulo':'Fixture muda do catálogo'}, direction, '9:16', data.pop('cenas'),
                  SimpleNamespace(words=[]), [], data.pop('duracao'), True,
                  hold=data.pop('repouso'), bible=for_project({}), **data)
