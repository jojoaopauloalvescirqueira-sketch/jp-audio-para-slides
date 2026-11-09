"""Geração e aprovação das folhas do rig anatômico, com testes sem narração."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ASSETS = Path(__file__).resolve().parents[1] / 'assets'
RUNNER = Path(__file__).with_name('capturar_folhas_pictograma.mjs')
NAMES = ('folha-anatomica', 'folha-movimento')
SOURCES = ('biblia-anatomica-pictograma.json', 'pictograma-figura.js', 'pictograma-rig.js')
APPROVAL = 'aprovacao_folhas_anatomicas.json'


def identity(folder):
    def digest(path):
        return sha256(path.read_bytes()).hexdigest()
    return {'rig': {name: digest(ASSETS / name) for name in SOURCES},
            'ferramentas': {p.name: digest(p) for p in (
                Path(__file__), RUNNER, ASSETS/'pictograma-folhas.js',
                Path(__file__).with_name('auditoria_anatomica.js'))},
            'folhas': {name: digest(folder / name) for name in (
                *(base + ext for base in NAMES for ext in ('.html', '.png')), 'medicoes.json', 'poses-ensaio.json')}}


def approve(folder, confirmed):
    if not confirmed:
        raise ValueError('Registre a aprovação explícita das duas folhas.')
    if json.loads((folder/'medicoes.json').read_text())['issues']:
        raise ValueError('As folhas têm bloqueantes na auditoria anatômica.')
    current = identity(folder)
    if current != json.loads((folder/'identidade.json').read_text()):
        raise ValueError('O rig ou as folhas mudaram. Apresente as folhas atuais.')
    (folder/APPROVAL).write_text(json.dumps(current, indent=2)+'\n')


def require(folder):
    try:
        approved = json.loads((folder/APPROVAL).read_text())
        matches = approved == identity(folder)
    except (OSError, ValueError):
        matches = False
    if not matches:
        raise ValueError('Aguarde aprovação das duas folhas atuais antes de renderizar a cena.')


def render(folder, node, mutations=False):
    folder.mkdir(parents=True, exist_ok=True)
    b = (ASSETS/SOURCES[0]).read_text()
    js = '\n'.join((ASSETS/name).read_text() for name in (*SOURCES[1:], 'pictograma-folhas.js'))
    for name in NAMES:
        title = 'Folha anatômica' if name == NAMES[0] else 'Folha de movimento'
        (folder/(name+'.html')).write_text(
            f'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>{title}</title>'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<style>:root{color-scheme:dark;background:#121b18;color:#f3ecdc;font:15px system-ui}*{box-sizing:border-box}'
            'body{margin:0}main{padding:28px;margin:auto;max-width:1510px}h1{font-size:35px;margin:4px 0}'
            'header p{color:#c2d3c9;margin:8px 0 13px}button{padding:.5rem 1rem;border:1px solid #688578;'
            'border-radius:8px;background:#23382e;color:#fff}section{margin-top:19px}'
            'h2{font-size:20px;margin:0 0 7px}figure{margin:0;background:#1a2822;border:1px solid #354d40;'
            'border-radius:10px;overflow:hidden}svg{display:block;width:100%;height:auto}'
            'figcaption{padding:8px 10px;color:#dce7dc;font-size:13px;min-height:50px}small{display:block;color:#aec4b6}'
            '.cards{display:grid;grid-template-columns:repeat(var(--cols),minmax(0,1fr));gap:8px}'
            'body.hide-diagnostic [data-diagnostico]{display:none}.legend{color:#bcd3c5}'
            '@media(max-width:780px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}</style>'
            f'<main><header><h1>{title} · Pictograma 1.8</h1>'
            '<p>Ensaios do rig em escala de seis cabeças · 30 quadros por segundo</p>'
            '<button id="diagnostico" aria-pressed="true">Ocultar diagnóstico</button>'
            '<p class="legend">Âmbar · ossos &nbsp; Ciano · centro de massa &nbsp; Verde claro · base e contatos</p>'
            f'</header><div id="cartoes"></div></main><script id="biblia" type="application/json">{b}</script>'
            f'<script>{js}</script><script>window.prepararFolha({json.dumps(name)});</script>',encoding='utf-8')
    subprocess.run([node,str(RUNNER),str(folder), *(['--testar'] if mutations else [])],check=True)
    (folder/'identidade.json').write_text(json.dumps(identity(folder),indent=2)+'\n')
