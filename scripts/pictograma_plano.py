"""Contrato declarativo e resolução de palavras para Pictograma."""
import math
import re
from bisect import bisect_right

from alinha_audio import tokens

LIBRARY = {
    'figura': {'aparecer', 'sumir', 'sentar', 'levantar', 'andar', 'destacar', 'mudar_cor'},
    'banco': {'aparecer', 'sumir'},
    'relogio': {'aparecer', 'sumir', 'girar'},
    'reticencias': {'aparecer', 'sumir', 'pulsar'},
    'linha': {'aparecer', 'sumir', 'desenhar'},
    'braco': {'aparecer', 'sumir', 'desenhar'},
    'seta': {'aparecer', 'sumir', 'desenhar'},
    'divisoria': {'aparecer', 'sumir', 'desenhar'},
    'coluna': {'aparecer', 'sumir'},
    'texto': {'aparecer', 'sumir', 'palavra', 'trocar_letra', 'anotar'},
}
ROLES = {'EU', 'VOCÊ', 'OUTRO', 'O OUTRO', 'NARRADOR', 'INTERLOCUTOR', 'PÚBLICO'}
COLORS = {'osso', 'acento', 'suave'}
POSES = {'em_pe', 'sentado'}
BOX = (64, 440, 892, 1320)
TIME_PER_WORD = 60 / 140


def string(value, label, maximum=160):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum or '\n' in value:
        raise ValueError(f'{label}: texto curto obrigatório.')
    return value


def number(value, label):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f'{label}: número inválido.')
    return value


def ident(value, label):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}', value):
        raise ValueError(f'{label}: identificador inválido.')
    return value


def only(record, keys, label):
    if not isinstance(record, dict) or record.keys() - set(keys.split()):
        raise ValueError(f'{label}: campos inválidos. Tempos em segundos são derivados da fala.')


class Words:
    def __init__(self, paragraphs):
        self.words = []
        self.by_id = {}
        self.positions = []
        for paragraph in paragraphs:
            pid = paragraph['id']
            text = paragraph['texto']
            units = tokens(text)
            if not units or pid in self.by_id:
                raise ValueError(f'Parágrafo vazio ou duplicado: {pid}.')
            self.by_id[pid] = (len(self.words), text, dict((pos, i) for i, (_, pos) in enumerate(units)))
            self.positions.extend((pid, pos) for _, pos in units)
            self.words.extend({'p': pid, 'texto': word} for word, _ in units)
        if not self.words:
            raise ValueError('Registre a fala canônica antes de planejar o Pictograma.')

    def anchor(self, anchor):
        only(anchor, 'p trecho ocorrencia', 'Âncora')
        p = anchor.get('p')
        pid = f'P{p:03}' if type(p) is int and p > 0 else p
        if not isinstance(pid, str) or pid not in self.by_id:
            raise ValueError(f'Parágrafo de âncora desconhecido: {p}.')
        offset, text, word_positions = self.by_id[pid]
        excerpt = string(anchor.get('trecho'), 'Trecho da âncora')
        hits = [m.start() for m in re.finditer(r'(?<!\w)' + re.escape(excerpt) + r'(?!\w)', text)
                if m.start() in word_positions]
        if not hits:
            raise ValueError(f'Âncora ausente em {pid}: {excerpt}.')
        if len(hits) > 1 and 'ocorrencia' not in anchor:
            raise ValueError(f'Âncora ambígua em {pid}: {excerpt}. Informe ocorrencia.')
        occurrence = anchor.get('ocorrencia', 1)
        if type(occurrence) is not int or not 1 <= occurrence <= len(hits):
            raise ValueError(f'Ocorrência inválida em {pid}: {excerpt}.')
        return offset + word_positions[hits[occurrence - 1]]


    def excerpt(self, start, end):
        parts = []
        for pid, (_, text, _) in self.by_id.items():
            positions = [pos for word_pid, pos in self.positions[start:end] if word_pid == pid]
            if not positions:
                continue
            cutoff = self.positions[end][1] if end < len(self.positions) and self.positions[end][0] == pid else len(text)
            parts.append(text[positions[0]:cutoff].strip())
        return ' '.join(parts)


def element(source, direction):
    only(source, 'id tipo x y w h cor estado texto anotacao rotulo visivel direcao', 'Elemento')
    row = dict(source)
    element_id = ident(row.get('id'), 'Elemento')
    kind = row.get('tipo')
    if kind not in LIBRARY:
        raise ValueError(f'{element_id}: tipo fora da biblioteca.')
    x, y, w, h = (number(row.get(field), field) for field in ('x', 'y', 'w', 'h'))
    if not (w >= 12 and h >= 8 and BOX[0] <= x <= BOX[2] - w and BOX[1] <= y <= BOX[3] - h):
        raise ValueError(f'{element_id}: elemento fora da área segura.')
    if row.get('cor', 'osso') not in COLORS or row.get('estado', 'em_pe') not in POSES:
        raise ValueError(f'{element_id}: cor ou postura desconhecida.')
    if type(row.get('visivel', True)) is not bool or row.get('direcao', 'direita') not in (
            'direita', 'esquerda', 'cima', 'baixo'):
        raise ValueError(f'{element_id}: visibilidade ou direção inválida.')
    if kind == 'texto':
        string(row.get('texto'), element_id, 100)
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


def action(source, targets, words, direction):
    only(source, 'alvo acao em valor', 'Ação')
    target = source.get('alvo')
    if not isinstance(target, str) or target not in targets:
        raise ValueError('Ação aponta para elemento inexistente.')
    row = targets[target]
    kind = source.get('acao')
    if kind not in LIBRARY[row['tipo']]:
        raise ValueError(f'{target}: ação fora da biblioteca para {row["tipo"]}.')
    value = source.get('valor')
    if kind == 'andar':
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
    return {**source, 'palavra': words.anchor(source.get('em'))}


def compile_plan(plan, words, direction, storyboard=False):
    only(plan, 'versao cenas', 'Plano')
    if type(plan.get('versao')) is not int or plan['versao'] != 1:
        raise ValueError('Versão do plano Pictograma inválida.')
    if not isinstance(plan.get('cenas'), list) or not plan['cenas']:
        raise ValueError('Informe pelo menos uma cena.')
    scenes = []
    names = set()
    for source in plan['cenas']:
        only(source, 'id inicio elementos acoes justificativa_ritmo', 'Cena')
        name = ident(source.get('id'), 'Cena')
        if name in names:
            raise ValueError(f'Cena duplicada: {name}.')
        names.add(name)
        start = words.anchor(source.get('inicio'))
        if (not scenes and start != 0) or (scenes and start <= scenes[-1]['palavra']):
            raise ValueError('As cenas devem cobrir a fala desde a primeira palavra e avançar sem sobreposição.')
        if not isinstance(source.get('elementos'), list) or not source['elementos']:
            raise ValueError(f'{name}: cena sem elementos.')
        items = [element(item, direction) for item in source['elementos']]
        targets = {item['id']: item for item in items}
        if len(targets) != len(items):
            raise ValueError(f'{name}: elemento duplicado.')
        actions = source.get('acoes', [])
        if not isinstance(actions, list) or (storyboard and actions):
            raise ValueError(f'{name}: storyboard aceita somente elementos estáticos.')
        actions = [action(item, targets, words, direction) for item in actions]
        order = [(item['palavra'], item['alvo'], item['acao']) for item in actions]
        if len(set(order)) != len(order):
            raise ValueError(f'{name}: ação duplicada na mesma palavra.')
        scenes.append({
            'id': name, 'palavra': start, 'elementos': items,
            'acoes': sorted(actions, key=lambda item: item['palavra']),
            'justificativa_ritmo': source.get('justificativa_ritmo', ''),
        })
    for index, scene in enumerate(scenes):
        end = scenes[index + 1]['palavra'] if index + 1 < len(scenes) else len(words.words)
        if any(not scene['palavra'] <= item['palavra'] < end for item in scene['acoes']):
            raise ValueError(f'{scene["id"]}: ação fora do trecho da cena.')
        scene['fim_palavra'] = end
        scene['fala'] = words.excerpt(scene['palavra'], end)
    return scenes


def measured_times(heard, matches, count, required):
    """Retorna tempos exatos para âncoras. Só legendas podem interpolar lacunas."""
    missing = sorted(required - matches.keys())
    if missing:
        raise ValueError('Âncoras sem palavra reconhecida. Confira o áudio e a transcrição: '
                         + ', '.join(str(index + 1) for index in missing))
    known = sorted(matches)
    result = []
    for index in range(count):
        if index in matches:
            result.append(heard[matches[index]]['start'])
            continue
        position = bisect_right(known, index)
        left = known[max(0, position - 1)]
        right = known[min(position, len(known) - 1)]
        start = heard[matches[left]]['start']
        end = heard[matches[right]]['start']
        result.append(start if left == right else start + (end - start) * (index - left) / (right - left))
    return result


def schedule(scenes, times, duration, check_rhythm=True):
    timeline = []
    for index, scene in enumerate(scenes):
        start = times[scene['palavra']] if index else 0
        end = times[scenes[index + 1]['palavra']] if index + 1 < len(scenes) else duration
        if not start < end:
            raise ValueError(f'{scene["id"]}: cena sem duração válida.')
        if check_rhythm and not 2 <= end - start <= 12:
            reason = scene['justificativa_ritmo']
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f'{scene["id"]}: cena com {end - start:.2f} s. Informe justificativa_ritmo.')
        actions = [{**item, 'tempo': times[item['palavra']]} for item in scene['acoes']]
        if any(not start <= item['tempo'] < end for item in actions):
            raise ValueError(f'{scene["id"]}: palavra medida fora do intervalo da cena.')
        timeline.append({**scene, 'inicio': start, 'fim': end, 'acoes': actions})
    return timeline
