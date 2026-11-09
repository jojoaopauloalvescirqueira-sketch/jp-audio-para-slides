"""Plano de luz e efeitos, e aprovação vinculada à prévia do Pictograma."""
from pathlib import Path

from cenas import number, only, string
from projeto import read, sha, write

PLAN = 'efeitos_pictograma.json'
APPROVAL = 'aprovacao_efeitos_pictograma.json'
IDENTITY = 'identidade_efeitos.json'


def compile_effects(raw, words, timeline, cues, bible, project, palette, total):
    only(raw, 'versao trechos_sensiveis efeitos', 'Plano de efeitos')
    if type(raw.get('versao')) is not int or raw['versao'] != 1:
        raise ValueError('Versão de plano de efeitos inválida.')
    sensitive = raw.get('trechos_sensiveis', [])
    if not isinstance(sensitive, list) or any(not isinstance(p, str) or p not in words.by_id for p in sensitive):
        raise ValueError('EC-074: trecho sensível fora da fala canônica.')
    sensitive = set(sensitive)
    recipe = bible['efeitos']
    spacing = number(project.get('efeitos_pictograma_intervalo_s', recipe['intervalo_s']), 'Intervalo de efeitos')
    if not 3 <= spacing <= 4:
        raise ValueError('EC-077: use intervalo entre 3 e 4 segundos.')
    effects = raw.get('efeitos')
    if not isinstance(effects, list):
        raise ValueError('O plano exige uma lista de efeitos.')
    scenes = {scene['id']: scene for scene in timeline}
    rows = []
    ids = set()
    for effect in effects:
        only(effect, 'id cena em alvo momento tipo justificativa parametros', 'Efeito')
        name = string(effect.get('id'), 'ID do efeito')
        if name in ids:
            raise ValueError(f'ID duplicado de efeito: {name}.')
        ids.add(name)
        if not isinstance(effect.get('justificativa'), str) or not effect['justificativa'].strip():
            raise ValueError(f'EC-075: {name} precisa de uma justificativa.')
        kind = effect.get('tipo')
        if not isinstance(kind, str) or kind not in recipe['repertorio']:
            raise ValueError(f'EC-074: tipo de efeito indisponível: {kind}.')
        spec = recipe['repertorio'][kind]
        cue = cues.get(spec['acao'])
        scene = scenes.get(string(effect.get('cena'), 'Cena do efeito'))
        idx = words.anchor(effect.get('em'))
        if (not cue or not scene or cue['scene'] != scene['id'] or cue['word'] != idx
                or effect.get('alvo') != spec['alvo'] or effect.get('momento') != spec['momento']
                or (words.words[idx]['p'] in sensitive and not spec['sensivel'])):
            raise ValueError(f'EC-074: {name} fora da cena, alvo, âncora ou momento permitido.')
        params = effect.get('parametros')
        only(params, 'cor intensidade antes_quadros depois_quadros escurecimento', 'Parâmetros do efeito')
        token = params.get('cor')
        if not isinstance(token, str) or token not in palette or token not in spec['cores']:
            raise ValueError(f'EC-082: {name} usa cor fora da paleta autorizada.')
        intensity = number(params.get('intensidade'), 'Intensidade')
        pre, post = params.get('antes_quadros'), params.get('depois_quadros')
        if (not 0 < intensity <= spec['max_intensidade'] or type(pre) is not int or type(post) is not int
                or min(pre, post) < 2 or not spec['duracao'][0] <= pre + post <= spec['duracao'][1]):
            raise ValueError(f'Duração ou intensidade fora da bíblia: {name}.')
        if 'escurecimento' in params:
            dim = number(params['escurecimento'], 'Escurecimento')
            if kind != 'foco_difuso' or not .11 <= dim <= .17:
                raise ValueError('O escurecimento pertence ao foco de transformação, dentro dos limites da bíblia.')
        at = cue['frame']
        if not round(scene['inicio']*30) <= at-pre < at+post <= min(total, round(scene['fim']*30)):
            raise ValueError(f'EC-074: intervalo de {name} ultrapassa a cena.')
        rows.append({**effect, 'palavra': idx, 'pouso': at, 'inicio': at-pre, 'fim': at+post})
    rows.sort(key=lambda row: row['pouso'])
    for a, b in zip(rows, rows[1:]):
        if b['pouso'] - a['pouso'] < spacing*30 or a['fim'] > b['inicio']:
            raise ValueError('EC-077: distância ou simultaneidade de efeitos fora do orçamento.')
    # A virada é a própria ação tipográfica. O foco de luz é uma camada adicional.
    for frame in range(total):
        action_count = sum(cue['start'] <= frame < cue['end'] for cue in cues.values())
        accent_count = sum(row['tipo'] != 'virada_tipografica' and row['inicio'] <= frame < row['fim'] for row in rows)
        if action_count + accent_count > recipe['max_simultaneos']:
            raise ValueError(f'EC-077: mais de dois destaques no quadro {frame}.')
    return {'destaques': rows, 'sensiveis': sorted(sensitive), 'intervalo_s': spacing}


def keys(material, preview):
    relevant = [PLAN, 'cenas_pictograma.json', 'paragrafos.json', 'marcacoes_acoes.json',
                'sincronia_fonte.json', 'sincronia_energia.json', 'sincronia_manual.json']
    bible = Path(__file__).resolve().parents[1]/'assets/biblia-pictograma.json'
    return {'previa': sha(preview), 'biblia': sha(bible),
            'material': {name: sha(material/name) for name in relevant if (material/name).is_file()}}


def register(material, preview, decision):
    if not (material/PLAN).is_file() or not preview.is_file() or not (preview.parent/IDENTITY).is_file():
        raise ValueError('Gere a prévia com efeitos antes de registrar sua decisão.')
    current = keys(material, preview)
    if read(preview.parent/IDENTITY) != current:
        raise ValueError('O plano ou a prévia mudou. Gere a prévia atual antes de registrar sua decisão.')
    write(material/APPROVAL, {'decisao': decision, 'identidade': current})


def require_approval(material, preview):
    record = read(material/APPROVAL) if (material/APPROVAL).is_file() else {}
    if record.get('decisao') not in ('aprovado', 'dispensado') or record.get('identidade') != keys(material, preview):
        raise ValueError('Aguarde aprovação ou dispensa explícita do plano de luz e efeitos desta prévia.')
