"""Contrato declarativo e resolução de palavras para Pictograma."""
from pathlib import Path

from cenas import Words, compile_plan as compile_scenes, ident, number, only, schedule, string, validate_box, vocabulary

LIBRARY = vocabulary(Path(__file__).resolve().parents[1] / 'assets/vocabulario-pictograma.json')
ROLES = {'EU', 'VOCÊ', 'OUTRO', 'O OUTRO', 'NARRADOR', 'INTERLOCUTOR', 'PÚBLICO'}
COLORS = {'osso', 'acento', 'suave'}
POSES = {'em_pe', 'sentado', 'ajoelhado'}
BOX = (64, 440, 892, 1320)
TIME_PER_WORD = 60 / 140


def element(source, direction):
    only(source, 'id tipo x y w h cor estado texto anotacao rotulo visivel direcao acento estilo_texto pontos apoio de para persistir z piso legenda_de', 'Elemento')
    row = dict(source)
    element_id = ident(row.get('id'), 'Elemento')
    kind = row.get('tipo')
    if kind not in LIBRARY:
        raise ValueError(f'{element_id}: tipo fora da biblioteca.')
    validate_box(row, BOX)
    if row['w'] < 12 or row['h'] < 8:
        raise ValueError(f'{element_id}: dimensão muito pequena.')
    if row.get('cor', 'osso') not in COLORS or row.get('estado', 'em_pe') not in POSES:
        raise ValueError(f'{element_id}: cor ou postura desconhecida.')
    if type(row.get('visivel', True)) is not bool or row.get('direcao', 'direita') not in (
            'direita', 'esquerda', 'cima', 'baixo'):
        raise ValueError(f'{element_id}: visibilidade ou direção inválida.')
    for key in ('apoio', 'de', 'para', 'legenda_de'):
        if key in row:
            ident(row[key], key)
    if 'legenda_de' in row and kind != 'texto':
        raise ValueError('O rótulo deve ser um elemento de texto.')
    if 'persistir' in row and type(row['persistir']) is not bool:
        raise ValueError('Persistência deve ser booleana.')
    if 'z' in row:
        number(row['z'], 'Camada')
    if 'pontos' in row and (kind not in ('seta','linha','braco','divisoria') or
            not isinstance(row['pontos'], list) or len(row['pontos']) != 4 or
            any(not 0 <= number(coord, 'Ponto') <= 100 for coord in row['pontos'])):
        raise ValueError('Traço exige quatro coordenadas entre 0 e 100.')
    if 'piso' in row and (kind != 'linha' or type(row['piso']) is not bool or
                          row.get('pontos',[0,50,100,50])[1] != row.get('pontos',[0,50,100,50])[3]):
        raise ValueError('O piso deve ser uma linha horizontal.')
    if kind == 'texto':
        string(row.get('texto'), element_id, 100)
        if 'acento' in row:
            string(row['acento'], 'Palavra de acento', 30)
        if row.get('estilo_texto', 'display') not in ('display', 'auxiliar'):
            raise ValueError('Estilo de texto desconhecido.')
    if 'anotacao' in row:
        string(row['anotacao'], element_id, 45)
    if direction['texto'] == 'nenhum' and (kind == 'texto' or 'anotacao' in row):
        raise ValueError(f'{element_id}: a direção visual dispensa texto editorial.')
    if 'rotulo' in row:
        label = string(row['rotulo'], element_id, 44)
        allowed_names = {name.casefold() for name in direction['nomes_autorizados']}
        if (direction['personagens'] == 'genericos'
                or (label.upper() not in ROLES and label.casefold() not in allowed_names)):
            raise ValueError(f'{element_id}: rótulo de pessoa sem autorização: {label}.')
    return row


def action(source, row, direction):
    only(source, 'alvo acao em valor grupo pousar antecipacao_quadros fim_em', 'Ação')
    target = row['id']
    kind = source['acao']
    value = source.get('valor')
    if source.get('pousar','inicio') not in ('inicio','pico'):
        raise ValueError('O pouso deve ser inicio ou pico.')
    anticipation=source.get('antecipacao_quadros',3)
    if type(anticipation) is not int or not 0<=anticipation<=30 or (
            source.get('pousar')=='pico' and anticipation<1):
        raise ValueError('Antecipação exige 0–30 quadros, com pelo menos um para pouso no pico.')
    if 'grupo' in source:
        ident(source['grupo'], 'Grupo de movimento')
    if kind in ('andar_ate', 'apontar', 'ajudar_a_levantar', 'abracar'):
        ident(value, 'Outra figura')
    elif kind == 'entregar':
        only(value, 'de para', 'Entrega')
        ident(value.get('de'), 'Origem da entrega')
        ident(value.get('para'), 'Destino da entrega')
    elif kind == 'contar':
        if type(value) is not int or not -999999 <= value <= 999999 or direction['texto'] == 'nenhum':
            raise ValueError('Contagem exige inteiro entre -999999 e 999999 e texto autorizado.')
    elif kind == 'andar':
        x = number(value, 'Destino do movimento')
        if not BOX[0] <= x <= BOX[2] - row['w']:
            raise ValueError(f'{target}: o destino ultrapassa a área segura.')
    elif kind == 'mudar_cor' and value not in COLORS:
        raise ValueError(f'{target}: cor de ação desconhecida.')
    elif kind in ('palavra', 'trocar_letra', 'anotar'):
        string(value, target, 100 if kind != 'anotar' else 45)
        if direction['texto'] == 'nenhum':
            raise ValueError(f'{target}: ação textual contraria a direção.')
    elif kind not in ('mudar_cor', 'palavra', 'trocar_letra', 'anotar') and value is not None:
        raise ValueError(f'{target}: a ação não recebe valor.')
    return source


def compile_plan(plan, words, direction, storyboard=False):
    if isinstance(plan, dict) and isinstance(plan.get('cenas'), list):
        for scene in plan['cenas']:
            only(scene, 'id inicio entrada elementos acoes justificativa_ritmo saida', 'Cena')
            if scene.get('saida', 'fusao') not in ('fusao','deslize','corte'):
                raise ValueError('Transição desconhecida.')
    base = plan
    if isinstance(plan, dict) and 'coreografia' in plan:
        base = {key: value for key, value in plan.items() if key != 'coreografia'}
    scenes = compile_scenes(base, words, LIBRARY, lambda row: element(row, direction),
                            lambda row, target: action(row, target, direction), storyboard)
    for scene, source in zip(scenes, plan['cenas']):
        scene['saida'] = source.get('saida','fusao')
        elements = {item['id']:item for item in scene['elementos']}
        types = {key:item['tipo'] for key,item in elements.items()}
        for row in scene['acoes']:
            action_type = row['acao']
            if 'fim_em' in row:
                end=words.anchor(row['fim_em'])
                if action_type not in ('andar','andar_ate','entregar') or not row['palavra']<end<scene['fim_palavra']:
                    raise ValueError('A âncora final deve suceder o gesto na mesma cena.')
                row['palavra_fim']=end
            if action_type in ('andar_ate','apontar','ajudar_a_levantar','abracar','entregar'):
                peers = list(row['valor'].values()) if action_type=='entregar' else [row['valor']]
                if any(types.get(peer) != 'figura' for peer in peers) or len(set(peers+[row['alvo']])) != len(peers)+1:
                    raise ValueError('O gesto exige figuras distintas da mesma cena.')
                if action_type == 'andar_ate':
                    actor, peer = elements[row['alvo']], elements[peers[0]]
                    row['destino_x'] = max(BOX[0], min(BOX[2]-actor['w'],
                        peer['x']-actor['w']-20 if actor['x']<peer['x'] else peer['x']+peer['w']+20))
        groups = {}
        for row in scene['acoes']:
            if 'grupo' in row:
                groups.setdefault(row['grupo'], set()).add(row['palavra'])
        if any(len(points)>1 for points in groups.values()):
            raise ValueError('Um grupo de destaque deve compartilhar a mesma palavra.')
        for row in scene['elementos']:
            for key, kind in (('apoio','banco'),('de','figura'),('para','figura'),('legenda_de','figura')):
                if key in row and types.get(row[key]) != kind:
                    raise ValueError(f'{row["id"]}: {key} exige um alvo do tipo {kind}.')
            if ('de' in row) != ('para' in row) or ('de' in row and row['tipo'] != 'braco'):
                raise ValueError('Braço dinâmico exige duas figuras.')
    if 'coreografia' in plan:
        from pictograma_coreografia import anchors
        if storyboard or any(scene['acoes'] or scene['saida'] != 'corte' for scene in scenes):
            raise ValueError('A coreografia usa seus próprios gestos e cortes casados.')
        anchors(plan['coreografia'], words, scenes, direction)
    return scenes

def measured_times(heard, matches, count, required):
    from ancoras import stamp
    if required - matches.keys():
        raise ValueError('Âncora sem palavra reconhecida.')
    known = sorted(matches)
    result = []
    for index in range(count):
        moment = stamp(index, known, matches, heard, count, heard[matches[known[-1]]]['start'])[0]
        result.append(moment if moment is not None else heard[matches[known[0] if index < known[0] else known[-1]]]['start'])
    return result
