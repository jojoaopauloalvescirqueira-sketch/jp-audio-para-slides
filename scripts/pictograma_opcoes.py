"""Triagem e registro de opções de storyboard por batida."""
from collections import Counter
from datetime import date
from hashlib import sha256
import re

from ancoras import norm
from pictograma_encenacao import pose_changes
from pictograma_verbos import PAIRED, find_cue

SENSITIVE = re.compile(r'\b(?:deus|oracao|orar|salmo|jesus|sofre|crianca|idoso|morre|morte|cruz|pai nosso)\b')


def signature(scene):
    return sha256(scene['fala'].encode('utf-8')).hexdigest()


def options(scenes, duration, poses):
    moved={}
    totals=Counter()
    active=Counter()
    if poses:
        _,moved=pose_changes(poses,len(poses),body_only=True)
    for row in poses:
        totals[row['scene']]+=len(row['actors'])
        active[row['scene']]+=len(moved[row['f']])
    patterns=Counter((s.get('layout'),s['padrao'],(s.get('movimento') or {}).get('tipo')) for s in scenes)
    output=[]
    for scene in scenes:
        name=scene['id']
        action=scene.get('movimento') or {}
        kind=action.get('tipo')
        cue=scene.get('verbo_chave') or find_cue(scene['fala'])
        key=(scene.get('layout'),scene['padrao'],kind)
        body=active[name]/totals[name] if totals[name] else None
        reasons=[]
        if body is not None and body<.05:
            reasons.append('pouca ação de corpo')
        if cue and (cue['precisa_opcoes'] or cue['acao']!=kind):
            reasons.append('modalidade do verbo' if cue['precisa_opcoes'] else 'verbo-chave divergente')
        if kind in PAIRED and action.get('alvo')!='outro':
            reasons.append('relação sem segundo ator')
        if patterns[key]>2:
            reasons.append('molde repetido')
        if action.get('figura') or kind=='mao_presente' or SENSITIVE.search(norm(scene['fala'])):
            reasons.append('passagem sensível ou religiosa')
        if not reasons:
            continue
        variants=[
            {'id':'A','leitura':'Conservar a intenção da ação, com o gesto no quadro da fala.','recomendada':True},
            {'id':'B','leitura':'Manter a mesma intenção com gesto mais contido e postura mais aberta.'}]
        if kind=='tentar_levantar':
            variants[0]['leitura']='A figura faz uma tentativa mais alta e cede ao banco.'
            variants[1]['leitura']='A figura faz uma tentativa curta e cede ao banco.'
        if kind=='oferecer_e_recusar':
            variants[0]['leitura']='A palma se abre para a amiga. O gesto no peito dura um instante e é retirado.'
            variants[1]['leitura']='A palma se abre para a amiga. A referência a si mesmo é ainda mais breve.'
        if kind=='sentar_juntos' and action.get('figura')=='idoso':
            variants[0]['leitura']='O protagonista encontra o idoso de pé, com apoio da bengala.'
            variants[1]['leitura']='Os dois se sentam no banco. O idoso conserva a bengala.'
        output.append({'numero':len(output)+1,'batida':name,'assinatura':signature(scene),
                       'motivos':reasons,'corpo':body,'opcoes':variants})
    limit=max(0,int(duration*6/60))
    return {'limite':limit,'candidatas':output,'falha':len(output)>limit}


def resolve_choices(project, proposal, response=None, automatic=False):
    """Resolve uma seleção curta, preservando escolhas com a mesma fala."""
    known={row['numero']:row for row in proposal['candidatas']}
    explicit={}
    if response:
        if proposal['falha']:
            raise ValueError('O diretor precisa reduzir as batidas frágeis antes de pedir escolhas.')
        for part in re.split(r'\s*[,;]\s*|\s+',response.strip().upper()):
            match=re.fullmatch(r'(\d+)([AB])',part)
            if not match or int(match[1]) not in known or int(match[1]) in explicit:
                raise ValueError('Escolha inválida ou repetida. Use 1A, 2B.')
            explicit[int(match[1])]=match[2]
    saved=project.setdefault('escolhas_storyboard',{})
    selected={}
    for row in proposal['candidatas']:
        name=row['batida']
        previous=saved.get(name,{})
        if row['numero'] in explicit:
            value,origin=explicit[row['numero']],'usuario'
        elif not automatic and previous.get('assinatura')==row['assinatura'] and previous.get('opcao') in ('A','B'):
            selected[name]=previous
            continue
        else:
            value,origin='A','padrao_assumido'
        selected[name]={'opcao':value,'origem':origin,'data':date.today().isoformat(),
                        'assinatura':row['assinatura']}
    if not automatic:
        saved.update(selected)
    return selected


def stage_choices(scenes, choices):
    for scene in scenes:
        chosen=choices.get(scene['id'],{})
        if not scene.get('movimento') or chosen.get('assinatura')!=signature(scene):
            continue
        scene['movimento']['variacao']=chosen['opcao']


def storyboard_project(root, response=None):
    """Triagem reutilizável da prévia declarativa; só grava escolhas a pedido."""
    from projeto import read, write

    folder=root/'pictograma-9x16'
    timeline=read(folder/'timeline_previa.json')
    poses=read(folder/'poses.json')['frames']
    active=round(timeline['fim_fala_s']*30)
    proposal=options(timeline['cenas'],timeline['duracao_s'],poses[:active])
    project_path=root/'projeto.json'
    project=read(project_path)
    selected=resolve_choices(project,proposal,response)
    if response is not None:
        write(project_path,project)
    return {**proposal,'escolhas':selected}


def main():
    from argparse import ArgumentParser
    import json
    from pathlib import Path

    parser=ArgumentParser(description='Triar opções da prévia declarativa do Pictograma.')
    parser.add_argument('--root',required=True,type=Path)
    choice=parser.add_mutually_exclusive_group()
    choice.add_argument('--resposta',help='Escolhas explícitas, como 1A, 2B.')
    choice.add_argument('--assumir',action='store_true',help='Registrar recomendações nas batidas sem escolha.')
    args=parser.parse_args()
    try:
        result=storyboard_project(args.root,args.resposta if not args.assumir else '')
    except (OSError,ValueError,KeyError) as exc:
        parser.error(str(exc))
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
