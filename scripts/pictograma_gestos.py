"""Contrato e auditoria da atuação expressiva declarativa."""
from math import dist

from cenas import only, string

PROFILE = 'expressivo_intencional'
QUIET = frozenset(('olhar_para','pensar','esperar','virar','acompanhar_espera',
                   'curvar','agachar','ajoelhar','sentar_no_chao'))
BODY = frozenset(('andar_ate','aproximar','afastar','sentar','levantar','tentar_levantar',
                  'sentar_juntos','ajudar_a_levantar'))
OBJECTS = frozenset(('ler','carregar','entregar','receber','romper'))
PAIR = frozenset(('conversar','oferecer_e_recusar','ajudar_a_levantar','entregar','receber','amparar'))
HOLD = frozenset(('ler','carregar','receber','orar'))


def validate_gesture(action):
    g = action.get('gesto')
    only(g, 'intencao mao alvo saida', 'EC-099 · Gesto')
    for field in ('intencao','alvo'):
        string(g.get(field), f'EC-099 · {field}', 140)
    if g.get('mao') not in ('E','D','ambas','nenhuma') or g.get('saida') not in ('repouso','apoio','continua'):
        raise ValueError('EC-099 · Declare mão e saída do gesto.')
    kind=action['tipo']
    if kind in QUIET and g['mao']!='nenhuma':
        raise ValueError('EC-099 · A ação de repouso deve manter as mãos relaxadas.')
    if kind not in QUIET|BODY and g['mao']=='nenhuma':
        raise ValueError('EC-099 · A ação manual precisa declarar a mão.')
    if kind in OBJECTS and not action.get('objeto'):
        raise ValueError('EC-099 · A ação precisa de um objeto visível.')
    if kind in PAIR and action.get('alvo')!='outro':
        raise ValueError('EC-099 · A ação precisa de um interlocutor.')
    if kind=='apontar' and not action.get('objeto') and action.get('alvo')!='outro':
        raise ValueError('EC-099 · O alvo de apontar precisa estar no palco.')
    if kind in ('ler','orar','sentar','levantar','sentar_juntos','tentar_levantar','ajudar_a_levantar') and g['mao']!='ambas':
        raise ValueError('EC-099 · A ação exige as duas mãos.')
    return g


def schedule(action, start, end):
    validate_gesture(action)
    kind=action['tipo']
    pre,post=({
        'sentar':(25,5),'levantar':(23,8),'tentar_levantar':(24,18),
        'ajudar_a_levantar':(25,40),'sentar_juntos':(22,8),
        'andar_ate':(12,22),'aproximar':(10,22),'afastar':(10,22),
        'agachar':(12,22),'acompanhar_espera':(0,8),'mao_presente':(10,65),
        'oferecer_e_recusar':(12,26),
    }).get(kind,(10,15))
    landing=action['pouso']
    action['inicio']=max(start,landing-pre)
    last=action.get('segundo_pouso',landing)
    action['fim']=min(end,max(last+post,action['inicio']+8))
    if kind=='mao_presente':
        finish=action['fim']-1
        reach=min(landing+15,finish-19)
        hold=min(landing+31,finish-11)
        if reach<=landing or hold-reach<8:
            raise ValueError('EC-101 · Reserve tempo para apresentar, sustentar e recolher a mão.')
        action['presenca']={'olhar':max(action['inicio'],landing-6),'alcance':reach,'sustenta_ate':hold}
    if kind in HOLD or kind in ('acompanhar_espera','esperar','virar'):
        action['fim']=end
    if kind in HOLD:
        action['sustentar']=True
    if kind=='orar':
        finish=action['fim']-1
        palms=min(landing+24,finish-19)
        release=finish-13
        if palms<=action['inicio'] or release-palms<5:
            raise ValueError('EC-107 · Reserve tempo para juntar e recolher as mãos.')
        action['oracao']={'palmas':palms,'recolher':release}


def auditar_gestos(sample, previous=None):
    """Audita mãos medidas em pixels e contatos esperados no quadro."""
    issues=[]
    def flag(actor, hand, reason):
        issues.append({'codigo':'EC-099','nivel':'bloqueante','quadro':sample['f'],
                       'cena':sample['scene'],'elemento':f'figura-{actor}/mão-{hand}',
                       'correcao':reason})
    action=sample.get('action')
    for index, actor in enumerate(sample['actors']):
        old=None
        if previous and previous['scene']==sample['scene'] and index<len(previous['actors']):
            old=previous['actors'][index]
        elif previous and sample.get('transicao') and index<len(sample.get('ids', ())):
            actor_id=sample['ids'][index]
            previous_ids=previous.get('ids', ())
            if actor_id in previous_ids:
                old=previous['actors'][previous_ids.index(actor_id)]
        for hand,info in actor.items():
            if info['excesso']>9:
                flag(index,hand,'A mão não alcança o alvo com a pose atual.')
            if info['contato'] is not None and info['contato']>9:
                flag(index,hand,'O apoio declarado se soltou durante a ação.')
            if info['ativa'] and (not action or not info['autorizada']):
                flag(index,hand,'A mão executa um gesto sem intenção ou fora da janela.')
            if old:
                if dist(old[hand]['posicao'],info['posicao'])>40:
                    where='na transição' if sample.get('transicao') else 'dentro da batida'
                    flag(index,hand,f'O pulso salta mais de 40 px {where}.')
    if sample.get('encontro') is not None and sample['encontro']>12:
        flag(0,'D','As palmas não se encontram durante a transferência ou pega.')
    if sample.get('contato_esperado') and sample.get('encontro') is None:
        flag(0,'D','A fase de contato perdeu a pega declarada.')
    return issues
