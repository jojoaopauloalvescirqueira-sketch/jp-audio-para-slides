"""Compilação e geometria de cenas declarativas."""
import html
import json
import os
import math
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from ancoras import tokens, tempos_ancoras
from projeto import FORMATS, write

ASSETS = Path(__file__).resolve().parents[1] / "assets"


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
            raise ValueError('Registre a fala canônica antes de planejar as cenas.')

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


def vocabulary(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data.get('tipos'), dict):
        raise ValueError('Vocabulário sem tipos declarados.')
    return data['tipos']


def validate_box(row, bounds):
    left, top, right, bottom = bounds
    x, y, w, h = (number(row.get(field), field) for field in ('x', 'y', 'w', 'h'))
    if not (w > 0 and h > 0 and left <= x <= right - w and top <= y <= bottom - h):
        raise ValueError(f'{row.get("id")}: elemento fora da área segura.')
    return x, y, w, h


def compile_plan(plan, words, types, prepare_layer, prepare_action, storyboard=False):
    only(plan, 'versao formato cenas', 'Plano')
    if type(plan.get('versao')) is not int or plan['versao'] != 1:
        raise ValueError('Versão do plano inválida.')
    if not isinstance(plan.get('cenas'), list) or not plan['cenas']:
        raise ValueError('Informe pelo menos uma cena.')
    scenes = []
    names = set()
    for source in plan['cenas']:
        if not isinstance(source, dict):
            raise ValueError('Cena inválida.')
        name = ident(source.get('id'), 'Cena')
        if name in names:
            raise ValueError(f'Cena duplicada: {name}.')
        names.add(name)
        entrance = source.get('entrada', source.get('inicio'))
        start = words.anchor(entrance)
        if (not scenes and start != 0) or (scenes and start <= scenes[-1]['palavra']):
            raise ValueError('As cenas devem cobrir a fala desde a primeira palavra e avançar sem sobreposição.')
        raw_layers = source.get('elementos', source.get('camadas'))
        if not isinstance(raw_layers, list) or not raw_layers:
            raise ValueError(f'{name}: cena sem camadas.')
        layers = [prepare_layer(row) for row in raw_layers]
        targets = {ident(row.get('id'), 'Camada'): row for row in layers}
        if len(targets) != len(layers):
            raise ValueError(f'{name}: elemento duplicado.')
        for row in layers:
            if row.get('tipo') not in types:
                raise ValueError(f'{row["id"]}: tipo fora do vocabulário.')
        actions = source.get('acoes', [])
        if not isinstance(actions, list) or (storyboard and actions):
            raise ValueError(f'{name}: storyboard aceita somente elementos estáticos.')
        resolved = []
        for item in actions:
            if not isinstance(item, dict) or not isinstance(item.get('alvo'), str) or item['alvo'] not in targets:
                raise ValueError(f'{name}: ação aponta para alvo inexistente.')
            target = targets[item['alvo']]
            if item.get('acao') not in types[target['tipo']]:
                raise ValueError(f'{name}: ação fora da biblioteca para {target["tipo"]}.')
            resolved.append({**prepare_action(item, target), 'palavra': words.anchor(item.get('em'))})
        order = [(item['palavra'], item['alvo'], item['acao']) for item in resolved]
        if len(set(order)) != len(order):
            raise ValueError(f'{name}: ação duplicada na mesma palavra.')
        scenes.append({
            'id': name, 'entrada': entrance, 'palavra': start, 'elementos': layers,
            'acoes': sorted(resolved, key=lambda item: item['palavra']),
            'enquadramento': source.get('enquadramento', {}),
            'saida': source.get('saida', 'corte'),
            'justificativa_ritmo': source.get('justificativa_ritmo', ''),
        })
    for index, scene in enumerate(scenes):
        end = scenes[index + 1]['palavra'] if index + 1 < len(scenes) else len(words.words)
        if any(not scene['palavra'] <= item['palavra'] < end for item in scene['acoes']):
            raise ValueError(f'{scene["id"]}: ação fora do trecho da cena.')
        scene['fim_palavra'] = end
        scene['fala'] = words.excerpt(scene['palavra'], end)
    return scenes


def derive_slides(material, scenes, words):
    order = {pid: index for index, pid in enumerate(words.by_id, 1)}
    slides = []
    for scene in scenes:
        entry = scene['entrada']
        slides.append({'id': scene['id'], 'tipo': 'ideia', 'p': order[words.words[scene['palavra']]['p']],
                       'frase_gatilho': entry['trecho'], **({'ocorrencia': entry['ocorrencia']}
                                                           if 'ocorrencia' in entry else {})})
    write(Path(material) / 'slides.json', slides)


def compile_timeline(root, scenes, paragraphs, estimar=False):
    indices = {scene['palavra'] for scene in scenes}
    indices.update(action['palavra'] for scene in scenes for action in scene['acoes'])
    times, report = tempos_ancoras(root, indices, paragraphs, estimar)
    if not report['estimado'] and any(row['tempo'] is None for row in report['ancoras']):
        raise ValueError('Âncoras sem tempo. Revise as marcações de ações.')
    timeline = schedule(scenes, times, report['duracao_s'])
    report['cenas'] = timeline
    write(Path(root) / 'material/timeline_cenas.json', report)
    return times, report


def player(path, title, fmt, data, kit_source, narration=None, css="", notes=""):
    dimensions = FORMATS[fmt]
    palette = data['paleta']
    scenes = data['cenas']
    estimated = data['estimado']
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    title = html.escape(title)
    status = 'Prévia estimada · 140 palavras/min' if estimated else 'Prévia sincronizada · áudio medido'
    shortcuts = ''.join(f'<button data-cena="{i}">{html.escape(scene["id"])}</button>'
                        for i, scene in enumerate(scenes))
    audio_tag = f'<audio id="narracao" preload="metadata" src="{quote(os.path.relpath(narration, path.parent))}"></audio>' if narration else ''
    width, height = dimensions
    motor = (ASSETS / 'motor-cenas.js').read_text(encoding='utf-8')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'''<!doctype html>
<html lang="pt-BR"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Prévia animada</title>
<style>
:root {{ color-scheme:dark; background:#121715; color:#ECE6D8; font:16px system-ui, sans-serif }}
body {{ margin:0; padding:16px; }}
{css}
main {{ max-width:1000px; margin:auto; display:flex; flex-wrap:wrap; gap:24px; justify-content:center }}
figure {{ width:min(100%, max(280px, calc(72vh * {width}/{height}))); margin:0 }}
#palco {{ display:block; width:100%; height:auto; background:{palette['fundo']}; font-family:Arial, sans-serif }}
section {{ max-width:440px; flex:1 1 250px }}
.controls, nav {{ display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 }}
button {{ font:inherit; padding:8px 14px; border:1px solid #536459; border-radius:20px; background:#16241c; color:#ECE6D8 }}
button:focus-visible, input:focus-visible {{ outline:2px solid #9CC6A6 }}
label {{ display:flex; gap:10px; align-items:center }} input {{ width:100%; accent-color:#9CC6A6 }}
html.render, html.render body {{ margin:0; padding:0; overflow:hidden }}
html.render main, html.render figure {{ display:block; margin:0; width:100vw; max-width:none }}
html.render .controls, html.render label, html.render section {{ display:none }}
</style>
<script>if (new URLSearchParams(location.search).has('render')) document.documentElement.classList.add('render');</script>
<main data-estilo="{html.escape(data["kit"], quote=True)}"><figure><svg id="palco" viewBox="0 0 {width} {height}" role="img" aria-label="Palco animado"></svg>
<div class="controls"><button id="assistir">Assistir</button><button id="recomecar">Recomeçar</button></div>
<label>Tempo <input id="tempo" type="range" min="0" step="0.001" aria-label="Posição na animação"><output id="posicao"></output></label>
{audio_tag}</figure><section><p id="estado-previa">{status}</p><h1>{title}</h1>{notes}<nav aria-label="Ir para cena">{shortcuts}</nav></section></main>
<script id="dados" type="application/json">{payload}</script><script>{motor}</script><script>{kit_source}</script>
<script>MotorCenas.iniciar(JSON.parse(document.getElementById('dados').textContent));</script></html>''', encoding='utf-8')



def capture(node, page, output, fmt, requests=None, count=None, pages=4, assets_hash=''):
    width, height = FORMATS[fmt]
    script = Path(__file__).with_name('renderizar_cenas.mjs')
    with tempfile.TemporaryDirectory(prefix='.pedidos-cenas-', dir=page.parent) as scratch:
        mode = 'video' if count is not None else 'quadros'
        argument = str(count)
        if requests is not None:
            path = Path(scratch) / 'quadros.json'
            write(path, requests)
            argument = str(path)
        subprocess.run([node, str(script), str(page), str(output), str(width), str(height), mode,
                        argument, str(pages), assets_hash], check=True)
