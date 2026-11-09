"""Contratos do Ilustrado. Os prompts descrevem imagens que o usuário fornece."""
import hashlib
from pathlib import Path
import re

from cenas import ASSETS, Words, compile_plan, derive_slides, ident, number, only, string, vocabulary
from estilo_video import ensure_style_plan
from fala import normalize, paragraphs as split_paragraphs
from projeto import config, read, sha, write

LIBRARY = vocabulary(ASSETS / 'vocabulario-ilustrado.json')
PLAN = 'cenas_ilustrado.json'
FIELDS_BIBLE = ('traco', 'proporcoes', 'luz')
TRANSITIONS = ('corte', 'fusao', 'deslize')


def context(root):
    project = config(root)
    if project.get('estilo_video') != 'ilustrado':
        raise ValueError('Selecione Ilustrado antes de usar este fluxo.')
    material = root / 'material'
    ensure_style_plan(root,'ilustrado')
    ps = read(material / 'paragrafos.json')
    if project.get('roteiro_sha256'):
        clean = material / 'roteiro_limpo.txt'
        if (sha(clean) != project['roteiro_sha256']
                or [normalize(row['texto']) for row in ps]
                != [normalize(text) for text in split_paragraphs(clean.read_text(encoding='utf-8'))]):
            raise ValueError('A fala canônica foi alterada.')
    return project, material, material / 'ilustrado', ps


def _dictionary_rows(rows, label):
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f'{label}: informe uma lista de objetos.')
    ids = [ident(row.get('id'), label) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError(f'{label}: identificadores duplicados.')
    return rows


def authorized_names(project):
    entry = project.get('direcao_visual', {}).get('nomes_autorizados', {})
    return {name.casefold() for name in entry.get('valor', [])} if entry.get('origem') == 'usuario' else set()


def _labels(record, project):
    for key in ('nome_privado', 'rotulo_privado'):
        if key in record and string(record[key], key, 80).casefold() not in authorized_names(project):
            raise ValueError('Nome privado sem consentimento registrado.')


def title(text, project, allowed_public=()):
    if project.get('direcao_visual', {}).get('texto', {}).get('valor') == 'nenhum':
        raise ValueError('A direção visual dispensa títulos.')
    if len(string(text, 'Título', 88).split()) > 6:
        raise ValueError('Título limitado a seis palavras.')
    # Nomes no texto renderizado também passam pela lista de pessoas autorizadas.
    known = set(allowed_public) | authorized_names(project)
    labels = project.get('direcao_visual', {}).get('nomes_na_tela', {}).get('valor')
    if labels == 'nao' and any(re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)',text.casefold()) for name in known):
        raise ValueError('A direção visual dispensa nomes na tela.')
    candidate = re.compile(r'\b[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][a-záéíóúâêôãõç]+)+\b')
    if any(match.group().casefold() not in known for match in candidate.finditer(text)):
        raise ValueError('Título contém possível nome próprio sem autorização ou papel público declarado.')
    return text


def declarations(bible, cast, settings, project):
    only(bible, 'paleta traco proporcoes luz restricoes objetos', 'Bíblia visual')
    colors = bible.get('paleta')
    if (not isinstance(colors, dict) or colors.keys() != {'fundo','osso','acento','suave','linha'}
            or not all(isinstance(hexcode, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', hexcode) for hexcode in colors.values())):
        raise ValueError('A bíblia exige fundo, osso, acento, suave e linha em hexadecimal.')
    for key in FIELDS_BIBLE:
        string(bible.get(key), key, 400)
    for restriction in bible.get('restricoes', []):
        string(restriction, 'Restrição', 220)
    assets = {}

    def add(asset, kind, content, owner=None, reference=None):
        ident(asset, 'Asset')
        if asset in assets:
            raise ValueError(f'Asset duplicado: {asset}.')
        assets[asset] = dict(id=asset, tipo=kind, descricao=string(content,'Descrição',500),
                             personagem=owner, referencia=reference, alfa=kind in ('pose','objeto','meio','frente'))

    for row in _dictionary_rows(cast, 'Elenco'):
        only(row, 'id descricao roupa paleta folha poses nome_privado nome_publico', 'Personagem')
        _labels(row, project)
        if 'nome_publico' in row:
            string(row['nome_publico'], 'Nome público', 80)
        specification = ' '.join(string(row.get(key), key, 250) for key in ('descricao','roupa','paleta'))
        add(row.get('folha'), 'folha', specification, row['id'])
        for pose in _dictionary_rows(row.get('poses'), 'Poses'):
            only(pose, 'id descricao', 'Pose')
            add(pose['id'], 'pose', specification + ' ' + string(pose.get('descricao'),'Pose',180), row['id'], row['folha'])

    for row in _dictionary_rows(settings, 'Cenários'):
        only(row, 'id descricao camadas', 'Cenário')
        description = string(row.get('descricao'), 'Cenário', 250)
        for layer in _dictionary_rows(row.get('camadas'), 'Camadas'):
            only(layer, 'id tipo descricao paralaxe', 'Camada de cenário')
            kind = layer.get('tipo')
            if kind not in ('fundo','meio','frente'):
                raise ValueError('Tipo de camada de cenário inválido.')
            _unit(layer.get('paralaxe',0),'Paralaxe')
            add(layer['id'], kind, description + ' ' + string(layer.get('descricao'),'Camada',220))
            assets[layer['id']].update(cenario=row['id'], paralaxe=layer.get('paralaxe',0))
    for row in _dictionary_rows(bible.get('objetos',[]), 'Objetos'):
        only(row, 'id descricao', 'Objeto')
        add(row['id'],'objeto',row.get('descricao'))
    return assets


def _unit(value,label):
    if not 0 <= number(value,label) <= 1:
        raise ValueError(f'{label}: use posição normalizada entre zero e um.')
    return value


def _camera(value):
    only(value,'zoom centro','Câmera')
    zoom = number(value.get('zoom',1),'Zoom')
    center = value.get('centro',[.5,.5])
    if not 1 <= zoom <= 3 or not isinstance(center,list) or len(center)!=2:
        raise ValueError('Câmera exige zoom de 1 a 3 e centro normalizado.')
    return {'zoom':zoom,'centro':[_unit(v,'Centro') for v in center]}


def compile_illustrated(plan, words, assets, project, public_names=()):
    if not isinstance(plan,dict) or not isinstance(plan.get('cenas'),list):
        raise ValueError('Plano Ilustrado inválido.')
    raw = []
    for scene in plan['cenas']:
        only(scene,'id entrada camadas acoes cenario saida nota enquadramento justificativa_ritmo','Cena Ilustrado')
        layers = scene.get('camadas')
        if not isinstance(layers,list) or not layers:
            raise ValueError('Cena Ilustrado exige camadas de PNG.')
        actions = scene.get('acoes',[])
        if not isinstance(actions,list):
            raise ValueError('Ações inválidas.')
        for row in layers:
            only(row,'id asset x y escala rotacao opacidade z paralaxe nome_privado','Camada')
            _labels(row,project)
            asset=assets.get(row.get('asset'))
            if not asset or asset['tipo']=='folha' or (asset.get('cenario') and asset['cenario'] != scene.get('cenario')):
                raise ValueError('Camada usa asset não declarado, folha ou outro cenário.')
        if scene.get('saida','corte') not in TRANSITIONS:
            raise ValueError('Transição desconhecida.')
        framing = scene.get('enquadramento',{})
        only(framing,'9:16 16:9','Enquadramento')
        framing = {key:_camera(value) for key,value in framing.items()}
        raw.append({**scene,'camadas':[{**row,'tipo':'imagem'} for row in layers]+[
            {'id':'camera','tipo':'camera'}, {'id':'titulo','tipo':'titulo'}], 'enquadramento':framing})

    def layer(row):
        if row['tipo'] != 'imagem':
            return row
        result={'x':.5,'y':.5,'escala':1,'rotacao':0,'opacidade':1,'z':0,
                'paralaxe':assets[row['asset']].get('paralaxe',0),**row}
        for field in ('x','y','opacidade','paralaxe'):
            _unit(result[field],field)
        for field in ('z','rotacao'):
            number(result[field],field)
        if not 0 < number(result['escala'],'Escala') <= 2:
            raise ValueError('Escala da camada inválida.')
        return result

    def action(row,target):
        only(row,'alvo acao em asset texto zoom centro duracao_s x y escala lado modo alvos tipo','Ação Ilustrado')
        kind=row['acao']
        if 'duracao_s' in row and not 0 < number(row['duracao_s'],'Duração da ação') <= 12:
            raise ValueError('Duração de ação fora do intervalo.')
        if kind in ('trocar_pose','piscar'):
            source=assets.get(target['asset'])
            candidate=assets.get(row.get('asset'))
            if (not candidate or candidate['tipo']!='pose' or source['tipo']!='pose'
                    or candidate['personagem']!=source['personagem']):
                raise ValueError('Pose precisa existir e pertencer ao mesmo personagem.')
        if kind=='camera':
            _camera({key:row[key] for key in ('zoom','centro') if key in row})
        if kind=='titulo_entra':
            title(row.get('texto'),project,public_names)
        if kind=='transicao' and row.get('tipo') not in TRANSITIONS:
            raise ValueError('Transição desconhecida.')
        for key in ('x','y'):
            if key in row:
                _unit(row[key],key)
        if 'escala' in row and not 0 < number(row['escala'],'Escala da ação') <= 2:
            raise ValueError('Escala da ação inválida.')
        if row.get('lado','esquerda') not in ('esquerda','direita','cima','baixo'):
            raise ValueError('Lado de entrada inválido.')
        if row.get('modo','fade') not in ('lado','fade','escala'):
            raise ValueError('Modo de entrada inválido.')
        return row

    scenes=compile_plan({**plan,'cenas':raw},words,LIBRARY,layer,action)
    for scene in scenes:
        ids={item['id'] for item in scene['elementos'] if item['tipo']=='imagem'}
        for action_row in scene['acoes']:
            if action_row['acao']=='transicao':
                scene['saida']=action_row['tipo']
            if action_row['acao']=='surgir_em_grupo':
                group=action_row.get('alvos',[])
                if (not isinstance(group,list) or not group
                        or any(not isinstance(item,str) or item not in ids for item in group)):
                    raise ValueError('Grupo precisa apontar para camadas de imagem da cena.')
    return scenes


def load_design(root):
    project, material, folder, ps=context(root)
    bible, cast, settings=(read(folder/name) for name in ('biblia.json','elenco.json','cenarios.json'))
    assets=declarations(bible,cast,settings,project)
    return project, material, folder, ps, bible, cast, settings, assets


def apply_design(root, source):
    project, material, folder, ps=context(root)
    if not project.get('direcao_visual'):
        raise ValueError('Registre a direção de arte antes da bíblia.')
    only(source,'biblia elenco cenarios','Proposta Ilustrado')
    assets=declarations(source.get('biblia'),source.get('elenco'),source.get('cenarios'),project)
    for key in ('biblia','elenco','cenarios'):
        write(folder/(key+'.json'),source[key])
    return assets


def board(root, plan):
    project, material, folder, ps, _, cast, _, assets=load_design(root)
    require_review(folder,'biblia',design_hash(folder))
    words=Words(ps)
    names=[row['nome_publico'].casefold() for row in cast if 'nome_publico' in row]
    scenes=compile_illustrated(plan,words,assets,project,names)
    write(material / PLAN,plan)
    derive_slides(material,scenes,words)
    path=folder/'storyboard.md'
    lines = []
    for scene in scenes:
        layers = ', '.join(row['asset'] for row in scene['elementos'] if row['tipo']=='imagem')
        actions = ', '.join(f"{row['acao']} em «{row['em']['trecho']}»" for row in scene['acoes'])
        details = ' · '.join(part for part in (layers, actions, scene.get('nota')) if part)
        lines.append(f'- **{scene["id"]}** — {scene["fala"]} | {details}'.replace('\n',' '))
    path.write_text('# Storyboard textual\n\n'+'\n'.join(lines)+'\n',encoding='utf-8')
    return scenes


def design_hash(folder):
    values=[sha(folder/name) for name in ('biblia.json','elenco.json','cenarios.json')]
    return hashlib.sha256(''.join(values).encode()).hexdigest()


def board_hash(material, folder):
    values=[design_hash(folder),sha(material/PLAN),sha(material/'paragrafos.json')]
    return hashlib.sha256(''.join(values).encode()).hexdigest()


def require_review(folder, stage, digest):
    path=folder/('aprovacao_'+stage+'.json')
    if not path.is_file() or read(path).get('sha256') != digest:
        raise ValueError(f'Aguarde aprovação explícita de {stage}.')
