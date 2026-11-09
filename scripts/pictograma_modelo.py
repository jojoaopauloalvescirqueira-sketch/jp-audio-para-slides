"""Gera a folha de modelo SVG em HTML para o cânone selecionado."""
from html import escape
import json
from pathlib import Path
import subprocess

from pictograma_biblia import for_project
from pictograma_direcao import PALETTES
from projeto import read, sha, write

ASSETS = Path(__file__).resolve().parents[1] / 'assets'


def write_sheet(path, project, palette=None):
    bible = for_project(project)
    colors = palette or PALETTES['escura']
    data = json.dumps({'bible': bible, 'colors': colors}, ensure_ascii=False).replace('</', '<\\/')
    js = '\n'.join((ASSETS / name).read_text(encoding='utf-8')
                   for name in ('pictograma-figura.js', 'pictograma-palco.js', 'pictograma-modelo.js'))
    html = """<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Folha de modelo · Pictograma</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#101714;color:#eee9db;font:15px system-ui}main{padding:24px 26px;max-width:1520px;margin:auto}
h1{font-size:38px;margin:0}p{color:#bdcbc2;margin:5px 0 16px}
section{margin-top:17px}h2{font-size:16px;margin:0 0 8px;color:#cbd8cf;letter-spacing:.08em;text-transform:uppercase}
.grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}
figure{margin:0;background:#18221d;border:1px solid #2d4036;border-radius:10px;overflow:hidden}
svg{display:block;width:100%;height:auto}figcaption{padding:8px 11px;min-height:57px}
strong{display:block;font-size:15px}small{font-size:11px;color:#baccc1;font-variant-numeric:tabular-nums}
@media(max-width:850px){.grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:470px){.grid{grid-template-columns:repeat(2,1fr)}}
</style><main><h1>Pictograma · Folha de modelo</h1><p>""" + escape(project.get('titulo', 'Projeto')) + """
 · Grade em unidades de cabeça · Luz a 45° de cima à esquerda</p>
<div id="poses"></div></main>"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html + f'<script id="modelo" type="application/json">{data}</script><script>{js}</script>',
                    encoding='utf-8')


MODEL_APPROVAL = 'aprovacao_modelo_pictograma.json'
MODEL_ASSETS = ('biblia-pictograma.json', 'pictograma-figura.js', 'pictograma-palco.js', 'pictograma-modelo.js')


def model_dir(root):
    return root / 'material' / 'modelo_pictograma'


def model_identity(root, project, palette):
    folder = model_dir(root)
    return {'biblia': for_project(project), 'paleta': palette,
            'assets': {name: sha(ASSETS/name) for name in MODEL_ASSETS},
            'artefatos': {name: sha(folder/name) for name in
                          ('folha-de-modelo.html', 'folha-de-modelo.png', 'medicoes-modelo.json')}}


def render_model(root, project, palette, node):
    folder = model_dir(root)
    sheet = folder / 'folha-de-modelo.html'
    write_sheet(sheet, project, palette)
    script = Path(__file__).with_name('capturar_modelo_pictograma.mjs')
    subprocess.run([node, str(script), str(sheet), str(folder/'folha-de-modelo.png'),
                    str(folder/'medicoes-modelo.json')], check=True)
    current = model_identity(root, project, palette)
    write(folder/'identidade.json', current)
    return sheet


def approve_model(root, project, palette):
    folder = model_dir(root)
    identity = model_identity(root, project, palette)
    if read(folder/'identidade.json') != identity:
        raise ValueError('A bíblia ou a folha de modelo mudou. Gere a folha atual antes da aprovação.')
    if read(folder/'medicoes-modelo.json')['issues']:
        raise ValueError('A folha de modelo ainda tem bloqueantes de proporções.')
    write(root/'material'/MODEL_APPROVAL, identity)


def require_model(root, project, palette):
    path = root/'material'/MODEL_APPROVAL
    if not path.is_file():
        raise ValueError('Apresente a folha de modelo e aguarde aprovação antes do storyboard.')
    if read(path) != model_identity(root, project, palette):
        raise ValueError('A folha de modelo ou o cânone mudou. Solicite aprovação da folha atual.')
