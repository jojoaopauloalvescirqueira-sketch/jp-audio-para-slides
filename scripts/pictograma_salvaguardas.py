"""Aplicabilidade e evidências de liberação do Pictograma declarativo."""
import hashlib
import json
from pathlib import Path
import re

from catalogo_erros import catalogo
from projeto import sha

ROOT = Path(__file__).resolve().parent
NOTAS = frozenset(('legibilidade_da_silhueta', 'causa_e_efeito', 'peso_e_contato',
                   'enquadramento', 'ritmo_e_respiracao', 'texto', 'transicoes', 'forca_da_virada'))
# Verificações obrigatórias no percurso declarativo. As regras do catálogo
# específicas de outro percurso mantêm seu próprio escopo e testes.
PLAN = ('EC-088', 'EC-097', 'EC-098', 'EC-102')
DOM = ('EC-028', 'EC-033', 'EC-084', 'EC-096', 'EC-099')
MP4 = ('EC-036', 'EC-086', 'EC-094', 'legenda_codificada', 'identidade_render')
ENUMERATION = {
    'animal': re.compile(r'\b(?:bichinhos?|animais|animal)\b'),
    'idoso': re.compile(r'\bidos[oa]s?\b'),
    'crianca': re.compile(r'\bcrianças?\b'),
}
NEGATION = re.compile(r'\b(?:não|nunca|seria|em vez de)\b')
CONDITIONAL = re.compile(r'^\s*se\s+(?:eu|você|ele|ela|a gente|nós|eles|elas|for|fosse|pudesse|houver|fizer|tiver)\b')
AFFIRMATIVE = {'sentar', 'levantar', 'entregar', 'receber', 'andar_ate', 'carregar', 'apontar'}


def digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def identity(plan, preview, sync, track):
    engine = ('pictograma_salvaguardas.py', 'pictograma_declarativo.py', 'pictograma_verificacao.py',
              'pictograma_auditoria.py', 'video_export.py', 'renderizar_cenas.mjs',
              'pictograma_composicao.py', 'auditar_animacao.mjs', 'auditoria_catalogo.js',
              'pictograma_gestos.py', 'pictograma_mix.py', 'pictograma_legenda.py')
    return {'direcao_sha256': sha(plan), 'previa_sha256': sha(preview), 'formato': '9:16',
            'sincronia_sha256': digest(sync), 'audio_identidade': sync['identidade']['audio_identidade'],
            'trilha': track, 'regras_sha256': digest({
                **{name: sha(ROOT/name) for name in engine},
                'catalogo': sha(ROOT.parent/'assets/erros_conhecidos.json')})}


def expected_ownership(scenes):
    """Derive the ownership contract from the staging, independently of the SVG."""
    previous=None
    for scene in scenes:
        action=scene.get('movimento') or {}
        kind=action.get('tipo')
        if scene.get('manter_posse'):
            scene['posse_esperada']=previous or {'objeto':'ausente','pouso':0,'antes':-1,'depois':-1}
        elif kind in ('entregar','receber') and action.get('alvo')=='outro' and action.get('objeto'):
            continuous=kind=='receber' and action.get('relacao')=='segurado'
            giver=int(kind=='receber' and not continuous)
            scene['posse_esperada']={'objeto':action['objeto'],'pouso':0 if continuous else action['pouso'],
                                    'antes':giver,'depois':1-giver}
        current=scene.get('posse_esperada')
        previous={**current,'pouso':0} if current else None


def context(timeline):
    scenes = timeline['cenas']
    actions = [s.get('movimento') or {} for s in scenes]
    result = set(PLAN+DOM+MP4)
    if not any(s.get('posse_esperada') for s in scenes):
        result.discard('EC-084')
    if not any((a.get('tipo') in ('sentar','levantar','sentar_juntos','acompanhar_espera',
                                 'tentar_levantar') or s.get('assento')) and not (
                    a.get('tipo')=='sentar_juntos' and a.get('figura')=='idoso' and a.get('variacao')=='A')
               for s,a in zip(scenes,actions)):
        result.discard('EC-094')
    for s,a in zip(scenes,actions):
        kind = a.get('tipo')
        if (s.get('cenario_ilustrado') or {}).get('figuras'):
            result.add('EC-100')
        if kind=='mao_presente':
            result.update(('EC-101','EC-104'))
        if kind=='ler' and a.get('objeto')=='livro':
            result.update(('EC-103','EC-106'))
        if kind=='orar':
            result.add('EC-107')
        if s.get('manter_elenco'):
            result.add('EC-113')
        if a.get('passo_final'):
            result.add('EC-114')
        if a.get('cuidado'):
            result.add('EC-115')
        atmosphere = (s.get('atmosfera') or {}).get('tipo')
        if atmosphere:
            result.add({'sombra':'EC-108','aura':'EC-109','chuva':'EC-110',
                        'claridade':'EC-111','partilha':'EC-112'}[atmosphere])
    if not timeline.get('figuras_com_apoio'):
        result.discard('EC-086')
    if timeline.get('pessoas_privadas'):
        result.add('EC-092')
    if not any(s.get('rotulos') or s.get('titulo') or s.get('grafico') for s in scenes):
        result.discard('EC-096')
    return result


def plan_checks(timeline):
    """Checks decided before looking at DOM markers. Narrow literal triggers."""
    counts={code:{'quadros':0,'falhas':0} for code in PLAN}
    issues=[]
    def check(code, scene, ok, message):
        counts[code]['quadros']+=1
        if not ok:
            counts[code]['falhas']+=1
            issues.append({'codigo':code,'nivel':'bloqueante','quadro':round(scene['inicio']*30),
                           'elemento':scene['id'],'correcao':message})
    for scene in timeline['cenas']:
        a=scene.get('movimento') or {}
        g=a.get('gesto') or {}
        speech=scene['fala'].casefold()
        kind=a.get('tipo')
        check('EC-088',scene,bool(g.get('intencao') and g.get('alvo') and g.get('saida')
                                  and a.get('em')) or bool(scene.get('pausa')),
              'Declare gesto, alvo, âncora e saída, ou justifique o repouso.')
        if a.get('acentos'):
            check('EC-102',scene,len({entry['tipo'] for entry in a['acentos']})==len(a['acentos']),
                  'Separe acentos de conversa com intenções diferentes.')
        concepts=sorted((match.start(),kind) for kind,pattern in ENUMERATION.items()
                        if (match:=pattern.search(speech)))
        if len(concepts)>=2:
            figures=(scene.get('cenario_ilustrado') or {}).get('figuras') or []
            check('EC-097',scene,[item['tipo'] for item in figures]==[kind for _,kind in concepts],
                  'Mostre os grupos que a narração enumera, com suas próprias âncoras.')
        for pattern, action in ((r'\b(?:rezou|rezar|o pai nosso pedindo)\b','orar'),
                                (r'\b(?:leu em voz alta|abriu o livro para ler)\b','ler'),
                                (r'\b(?:entregou|entrega) (?:um|o) coração\b','entregar')):
            if re.search(pattern,speech) and not NEGATION.search(speech):
                check('EC-097',scene,kind==action,'Encene a ação explícita da fala.')
        if kind in AFFIRMATIVE:
            cue=(a.get('em') or {}).get('trecho','').casefold()
            start=speech.find(cue) if cue else -1
            prefix=speech[:max(0,start)].rsplit('.',1)[-1].rsplit(',',1)[-1]
            modal=bool(NEGATION.search(cue) or CONDITIONAL.match(prefix+cue)
                       or re.search(r'\b(?:não|nunca|seria|em vez de)\s+(?:\w+\s+){0,2}$',prefix))
            check('EC-098',scene,not modal,'Encene a recusa, a tentativa ou a hipótese.')
    for code in PLAN:
        if not counts[code]['quadros']:
            counts[code]={'quadros':len(timeline['cenas']),'falhas':0,'triagem':True}
    return counts,issues


SCOPES = {
    'EC-037':'A fonte de marcações deste percurso é verificada na sincronia.',
    'EC-038':'Efeito de controles vocais pertence à preparação da locução.',
    'EC-039':'O renderizador deste percurso é o navegador.',
    'EC-041':'A regra pertence ao Ilustrado.',
    'EC-085':'A exportação utiliza o relógio local da narração unificada.',
    'EC-105':'Ponte raster de cartela exige uma montagem de referência específica.',
    'EC-116':'Revelação em segmento raster exige uma montagem de referência específica.',
}


def matrix(report, timeline, phase):
    required=context(timeline)
    definitions=catalogo()+[{'id':code,'titulo':title} for code,title in (
        ('legenda_codificada','Correspondência das legendas no vídeo'),
        ('identidade_render','Correspondência dos quadros e dos insumos no vídeo'))]
    counts=report.get('checagens_catalogo',{})
    rows=[]
    for row in definitions:
        code=row['id']
        evidence=counts.get(code)
        if evidence and evidence.get('quadros',0)>0:
            status='reprovada' if evidence.get('falhas') else 'aprovada'
            reason='Triagem de aplicabilidade executada.' if evidence.get('triagem') else 'Medição executada.'
        elif code in required:
            status='sem_evidencia'
            reason='Medição do MP4 pendente.' if code in MP4 and phase!='mp4' else 'Falta medição neste percurso.'
        elif code in SCOPES or code in DOM+MP4 or (code.startswith('EC-') and 100<=int(code[3:])<=115):
            status='nao_aplicavel'
            reason=SCOPES.get(code,'O plano não contém a ação, o objeto ou o efeito que dispara a checagem.')
        else:
            status='sem_evidencia'
            reason='A cobertura depende de medição especializada ou de parecer. A execução atual não demonstrou a regra.'
        rows.append({'id':code,'titulo':row['titulo'],'estado':status,'motivo':reason,
                     'obrigatoria':code in required,'medicao':evidence})
    return rows


def require_matrix(rows, phase):
    missing=[row['id'] for row in rows if row['obrigatoria'] and row['estado']!='aprovada'
             and (phase=='mp4' or row['id'] not in MP4)]
    if missing:
        raise ValueError('Salvaguardas obrigatórias sem aprovação: '+', '.join(missing))


def validate_review(review, timeline):
    if not isinstance(review,dict) or review.get('resultado') not in ('aprovado','corrigir'):
        raise ValueError('Registre o resultado do parecer.')
    notes=review.get('notas')
    if (not isinstance(notes,dict) or notes.keys()!=NOTAS or
            any(type(n) is not int or not 1<=n<=5 for n in notes.values())):
        raise ValueError('Registre as oito notas de revisão entre 1 e 5.')
    if review.get('resultado')=='aprovado' and min(notes.values())<4:
        raise ValueError('Uma nota abaixo de 4 exige correção.')
    scenes={s['id']:s for s in timeline['cenas']}
    covered=set()
    evidence=review.get('evidencias',[])
    if not isinstance(evidence,list) or any(not isinstance(item,dict) for item in evidence):
        raise ValueError('Registre as evidências do parecer por cena.')
    for item in evidence:
        scene=scenes.get(item.get('cena'))
        frames=item.get('quadros')
        if (not scene or not isinstance(frames,list) or len(frames)<min(2,round(scene['fim']*30)-round(scene['inicio']*30)) or
                any(type(f) is not int or not round(scene['inicio']*30)<=f<round(scene['fim']*30) for f in frames)
                or frames!=sorted(set(frames)) or
                not isinstance(item.get('observacao'),str) or not item['observacao'].strip()):
            raise ValueError('O parecer exige quadros válidos e observação da cena.')
        covered.add(item['cena'])
    if review.get('resultado')=='aprovado' and (
            covered!=scenes.keys() or review.get('modos')!={'com_som':True,'sem_som':True,'celular':True}):
        raise ValueError('Revise todas as cenas em sequência com som, sem som e no tamanho de celular.')
