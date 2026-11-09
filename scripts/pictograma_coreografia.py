"""Âncoras e fases da composição coreografada de virada, banco e ajuda."""
from cenas import number, only, string

CUES = {
    'negacao': (0, 12), 'conceito': (0, 12), 'virada': (-17, 10),
    'sentar': (-16, 12), 'esperar': (0, 13), 'levantar': (-13, 13),
    'ajudar': (-7, 29), 'receber': (0, 17), 'fazer': (0, 17),
}
ROLES = (0, 0, 0, 1, 1, 1, 1, 2, 2)


VISUAL_MODEL = 'virada_banco_ajuda_v2'
ANATOMICAL_MODEL = 'sequencia_de_padroes'
ANATOMICAL_MODELS = (ANATOMICAL_MODEL, 'virada_banco_ajuda_v3')


def is_anatomical(plan):
    return plan.get('modelo') in ANATOMICAL_MODELS


def is_visual(plan):
    return isinstance(plan, dict) and isinstance(plan.get('coreografia'), dict) and (
        plan['coreografia'].get('modelo') in (VISUAL_MODEL, *ANATOMICAL_MODELS))


def anchors(plan, words, scenes, direction):
    keys = 'modelo ancoras'
    if isinstance(plan, dict) and plan.get('modelo') in (VISUAL_MODEL, *ANATOMICAL_MODELS):
        keys += ' enquadramento storyboard encenacao padroes'
    only(plan, keys, 'Coreografia')
    if plan.get('modelo') not in ('virada_banco_ajuda_v1', VISUAL_MODEL, *ANATOMICAL_MODELS) or len(scenes) != 3:
        raise ValueError('A coreografia de virada, banco e ajuda exige três cenas.')
    if plan['modelo'] in (VISUAL_MODEL, *ANATOMICAL_MODELS):
        camera(plan)
        storyboard_notes(plan, words)
    if direction['texto'] == 'nenhum':
        raise ValueError('Esta coreografia exige palavras de conceito no palco.')
    raw = plan.get('ancoras')
    only(raw, ' '.join(CUES), 'Âncoras da coreografia')
    indexes = [words.anchor(raw.get(name)) for name in CUES]
    if indexes != sorted(set(indexes)):
        raise ValueError('Os gestos precisam avançar na ordem da fala.')
    for index, role in zip(indexes, ROLES):
        if not scenes[role]['palavra'] <= index < scenes[role]['fim_palavra']:
            raise ValueError('Uma âncora da coreografia está fora da cena do gesto.')
    return dict(zip(CUES, indexes))


def phases(indexes, sync, timeline, hold):
    cues = {}
    for (name, (before, after)), scene_index in zip(CUES.items(), ROLES):
        word = indexes[name]
        frame = sync['palavras'][word]['quadro']
        cues[name] = {'frame': frame, 'word': word, 'start': max(0, frame + before),
                      'end': frame + after, 'minimum': 24 if name == 'virada' else 5,
                      'scene': timeline[scene_index]['id']}
    for first, second in (('conceito', 'virada'), ('sentar', 'esperar'), ('levantar', 'ajudar')):
        if cues[first]['end'] > cues[second]['start']:
            raise ValueError(f'As fases {first} e {second} não cabem no intervalo medido.')
    if cues['ajudar']['end'] > cues['receber']['end'] or cues['fazer']['end'] > round(hold * 30) + 10:
        raise ValueError('A atuação final não cabe na fala e na cauda disponíveis.')
    return {'cues': cues, 'corte': round(timeline[1]['inicio'] * 30),
            'comparacao': round(timeline[2]['inicio'] * 30)}


def camera(plan):
    raw = plan.get('enquadramento')
    only(raw, 'altura chao', 'Enquadramento')
    h, floor = [number(raw.get(key), key) for key in ('altura', 'chao')]
    if not 760 <= h <= 820 or not 1180 <= floor <= 1270 or floor - h < 375:
        raise ValueError('Enquadramento fora da área prevista para esta composição.')
    return {'altura': h, 'chao': floor}


STORY_FACTS = {
    'maos_em_contato': ('as mãos se encontram', 'mão com mão', 'encontra a mão e sustenta'),
    'pes_no_chao': ('planta os pés', 'pés apoiados', 'pés no chão'),
    'sentado_no_banco': ('assenta o quadril na borda do banco', 'sentado no banco'),
    'palmas_no_peito': ('palmas até o peito', 'palmas creme, na altura do peito'),
    'coracao_nas_maos': ('coração pousa', 'coração termina apoiado'),
    'agente_a_esquerda': ('ajudante à esquerda',),
}


def storyboard_notes(plan, words):
    rows = plan.get('storyboard')
    if not isinstance(rows, list) or len(rows) < 3:
        raise ValueError('Informe as batidas e as notas de direção do storyboard.')
    result = []
    for row in rows:
        only(row, 'em quadros nota leitura afirmacoes', 'Batida do storyboard')
        index = words.anchor(row.get('em'))
        offset = row.get('quadros', 0)
        if type(offset) is not int or not -30 <= offset <= 30:
            raise ValueError('O quadro de storyboard pode deslocar até 30 quadros da âncora.')
        note = string(row.get('nota'), 'Nota de direção', 350)
        claims = row.get('afirmacoes', [])
        if (not isinstance(claims, list) or any(not isinstance(item, str) or item not in STORY_FACTS for item in claims)
                or len(set(claims)) != len(claims)):
            raise ValueError('Afirmação de storyboard inválida.')
        inferred = [key for key, patterns in STORY_FACTS.items()
                    if any(term in note.casefold() for term in patterns)]
        result.append({'palavra': index, 'quadros': offset,
                       'afirmacoes': list(dict.fromkeys(claims + inferred)),
                       'nota': note,
                       'leitura': string(row.get('leitura'), 'Leitura sem som', 200)})
    return result


def camera_tracks(choreography):
    cues = choreography['cues']
    raise_frame = cues['levantar']['frame']
    help_frame = cues['ajudar']['frame']
    comparison = choreography['comparacao']
    return {
        'base_horizontal': .70,
        'respiracao': {'zoom': .009, 'velocidade': .052},
        'impulsos': [{'inicio': raise_frame-11, 'fim': raise_frame+22, 'delta': .017},
                     {'inicio': help_frame-12, 'fim': help_frame+35, 'delta': .023}],
        'abertura': {'inicio': comparison+3, 'fim': comparison+37, 'delta': -.016},
    }


def library_sequence(choreography, rig):
    """Compila blocagem em intervalos que a biblioteca de ações executa."""
    marks=choreography['encenacao']['marcas']
    cues={name:row['frame'] for name,row in choreography['cues'].items()}
    cut=choreography['corte']
    sit, rise=cues['sentar']-16,cues['levantar']-29
    help_start=cues['ajudar']-rig['ajuda']['pega']
    help_end=help_start+rig['ajuda']['fim']
    starts=[cut,cut+16,sit,rise,rise+30,help_start+8,help_end+1]
    if starts!=sorted(set(starts)) or sit<cut+20 or rise<sit+30 or help_start<rise+30 or cues['receber']<help_end+5:
        raise ValueError('A sequência anatômica não cabe nos intervalos medidos.')
    types=('marcha','transicao_assento','sentar','levantar','aproximar','ajudar','comparar')
    return {'intervalos':[{'tipo':kind,'de':a,'ate':b}
                          for kind,a,b in zip(types,starts,starts[1:]+[None])],
            'distancias':{'assento':marks['cadeira'],'marcha':marks['marcha']},
            'gestos':{'inicio_ajuda':help_start,'fim_ajuda':help_end,
                      'receber':cues['receber'],'oferecer':cues['fazer']}}


def library_preview_data(data):
    """Seleciona o compositor anatômico e seus blocos a partir do plano."""
    from cenas import ASSETS
    from projeto import read

    choreography=data['coreografia']
    defaults=read(ASSETS/'pictograma-parametros-padroes.json')
    configured=choreography.get('parametros',{})
    choreography['parametros']={name:{**values,**configured.get(name,{})}
                                for name,values in defaults.items()}
    rig=data['rig_anatomico']
    data['kit']='pictograma-biblioteca'
    choreography['sequencia']=library_sequence(choreography,rig)
    choreography['blocos']=[
        {'tipo':'virada_tipografica','de':0,'ate':choreography['corte']},
        {'tipo':'atuacao_anatomica','de':choreography['corte'],'ate':None},
    ]
    return ('pictograma-figura.js','pictograma-palco.js','pictograma-rig.js',
            'pictograma-acoes.js','pictograma-efeitos.js','pictograma-virada.js','pictograma-blocos.js',
            'kit-pictograma-biblioteca.js')
