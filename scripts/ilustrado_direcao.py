"""Escolhas de direção de arte registradas por campo."""
from datetime import datetime, timezone

from direcao import update_section
from ilustrado import context
from projeto import write

OPTIONS = {
    'criacao': ('diretor','colaborativa','usuario'),
    'estetica': ('historica','ludica','sobria'),
    'acento_jp': ('sim','nao'),
    'elenco': ('generico','historico','autorizado'),
    'nomes_na_tela': ('sim','nao'),
    'epoca': ('generica','referenciada'),
    'ritmo': ('calmo','medio','dinamico'),
    'camera': ('contida','paralaxe','dinamica'),
    'texto': ('titulos','palavras','nenhum'),
    'legenda': ('sim','nao'),
    'storyboard': ('aprovar','direto'),
    'marca': ('sim','nao'),
}
DEFAULTS = dict(criacao='diretor',estetica='historica',acento_jp='nao',elenco='generico',
                nomes_na_tela='nao',epoca='generica',ritmo='medio',camera='paralaxe',
                texto='titulos',legenda='sim',storyboard='aprovar',marca='nao')
FREE = {'descricao_cenas','notas_epoca','paleta','cenas_por_minuto'}
FIELDS = set(OPTIONS) | FREE | {'nomes_autorizados'}


def record(root, choices, assume=False):
    project,material,_,_=context(root)
    if not isinstance(choices,dict) or choices.keys()-FIELDS:
        raise ValueError('Campos inválidos na direção de arte.')
    direction=dict(project.get('direcao_visual',{}))
    now=datetime.now(timezone.utc).isoformat(timespec='seconds')
    choices=dict(choices)
    if assume:
        for key,value in DEFAULTS.items():
            if key not in choices and key not in direction:
                choices[key]={'valor':value,'origem':'padrao_assumido'}
    for key,entry in choices.items():
        if not isinstance(entry,dict) or entry.keys()-{'valor','origem'} or 'valor' not in entry:
            raise ValueError(f'{key}: informe valor e origem.')
        value=entry['valor']
        origin=entry.get('origem','usuario')
        if origin not in ('usuario','padrao_assumido'):
            raise ValueError('Origem inválida.')
        if key in OPTIONS and value not in OPTIONS[key]:
            raise ValueError(f'{key}: opção desconhecida.')
        if key in FREE and (not isinstance(value,str) or not value.strip()):
            raise ValueError(f'{key}: informe um texto.')
        if key=='nomes_autorizados' and (origin!='usuario' or not isinstance(value,list)
                or not all(isinstance(name,str) and name.strip() and '\n' not in name for name in value)):
            raise ValueError('Nomes privados exigem consentimento explícito.')
        previous=direction.get(key,{})
        if previous.get('valor')!=value or previous.get('origem')!=origin:
            direction[key]={'valor':value,'origem':origin,'data':now}
    if OPTIONS.keys()-direction.keys():
        raise ValueError('Complete as escolhas da direção de arte.')
    if direction['criacao']['valor']!='diretor' and 'descricao_cenas' not in direction:
        raise ValueError('Informe as descrições das cenas fornecidas pelo usuário.')
    project['direcao_visual']=direction
    write(root/'projeto.json',project)
    lines=['- **'+key.replace('_',' ')+'** — '+str(entry['valor']).replace('\n',' ')+' ('+entry['origem']+').'
           for key,entry in direction.items()]
    update_section(material/'guia_producao.md','## Direção visual','\n'.join(lines))
    return direction
