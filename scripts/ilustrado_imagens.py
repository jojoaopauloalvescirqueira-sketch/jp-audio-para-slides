"""Prompts, importação local de PNGs e aprovação de arte."""
from datetime import datetime, timezone
import hashlib
import html
from pathlib import Path
import shutil
import struct
import tempfile
from urllib.parse import quote
import zlib

from direcao import update_section
from ilustrado import PLAN, board_hash, design_hash, load_design, require_review
from projeto import FORMATS, read, sha, write

ORDER = {'folha':0,'pose':1,'fundo':2,'meio':2,'frente':2,'objeto':3}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _approval(folder, stage, digest):
    write(folder/f'aprovacao_{stage}.json',{'sha256':digest,'origem':'usuario','data':_now()})


def _zoom(plan):
    values=[1]
    for scene in plan['cenas']:
        values.extend(value.get('zoom',1) for value in scene.get('enquadramento',{}).values())
        values.extend(row.get('zoom',1) for row in scene.get('acoes',[]) if row['acao']=='camera')
    return max(values)


def _ordered(assets):
    return sorted(assets.values(),key=lambda row:(ORDER[row['tipo']],row.get('personagem') or '',row['id']))


def prompts(root):
    project,material,folder,_,bible,_,_,assets=load_design(root)
    require_review(folder,'biblia',design_hash(folder))
    if project.get('direcao_visual',{}).get('storyboard',{}).get('valor')!='direto':
        require_review(folder,'storyboard',board_hash(material,folder))
    plan=read(material/PLAN)
    fmt=plan.get('formato',project['formato'])
    if fmt not in ('16:9','9:16'):
        raise ValueError('O Ilustrado usa 16:9 ou 9:16.')
    zoom=_zoom(plan)
    w,h=FORMATS[fmt]
    fixed='Ilustração vetorial chapada. '+'. '.join(bible[key] for key in ('traco','proporcoes','luz'))+'. Paleta '+', '.join(
        f'{key} {value}' for key,value in bible['paleta'].items())+'. Sem texto, sem logos e sem imitar personagens ou cenários existentes.'
    if bible.get('restricoes'):
        fixed+=' '+' '.join(bible['restricoes'])
    entries=[]
    for row in _ordered(assets):
        kind=row['tipo']
        min_width=max(3840 if fmt=='16:9' else 2160,round(w*zoom)) if kind in ('fundo','meio','frente') else None
        min_height=round(h*zoom) if min_width else 2048
        specific=row['descricao']
        if kind=='folha':
            specific+=' Folha de referência com frente, três quartos e três expressões, em fundo neutro.'
        if kind=='pose':
            specific+=f' Anexe a folha aprovada {row["referencia"]}.png como referência. Corpo inteiro e sem sombra no chão.'
        if kind=='objeto':
            specific+=' Objeto inteiro e sem sombra no chão.'
        if row['alfa']:
            specific+=' Fundo transparente com canal alfa.'
        if kind=='fundo':
            specific+=' Preencha o enquadramento de fundo.'
        dimensions=f'{min_width} × {min_height} px no mínimo' if min_width else f'altura recomendada de {min_height} px'
        filename=row['id']+'.png'
        text=f'{fixed}\n\n{specific}\n\nPNG em {dimensions}. Salve como {filename}.'
        entries.append({**row,'arquivo':filename,'largura_recomendada':min_width,'altura_recomendada':min_height,
                        'prompt':text,'prompt_sha256':hashlib.sha256(text.encode()).hexdigest()})
    record={'formato':fmt,'zoom_maximo':zoom,'proposta_sha256':board_hash(material,folder),'prompts':entries}
    write(folder/'prompts_imagens.json',record)
    text=('# Prompts de imagens · Ilustrado\n\nGere os PNGs no ChatGPT. Aprove a folha de cada personagem '
          'e anexe-a aos pedidos de pose na mesma conversa. Salve cada PNG com o nome indicado. '
          'As imagens serão creditadas como ilustração gerada por IA.\n')
    for entry in entries:
        text+=f'\n## {entry["arquivo"]}\n\n{entry["prompt"]}\n'
    (folder/'prompts_imagens.md').write_text(text,encoding='utf-8')
    return entries


def png_info(path):
    with path.open('rb') as stream:
        header=stream.read(33)
        stream.seek(-12,2) if path.stat().st_size>=45 else None
        end=stream.read(12)
    if (len(header)!=33 or header[:16]!=b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR'
            or end!=b'\x00\x00\x00\x00IEND\xaeB\x60\x82'
            or zlib.crc32(header[12:29])!=struct.unpack('>I',header[29:33])[0]):
        raise ValueError('arquivo PNG inválido ou incompleto')
    width,height,depth,kind,compression,filtering,interlace=struct.unpack('>IIBBBBB',header[16:29])
    if not (1<=width<=20000 and 1<=height<=20000 and kind in (0,2,3,4,6)
            and depth in (1,2,4,8,16) and compression==filtering==0 and interlace in (0,1)):
        raise ValueError('cabeçalho PNG inválido')
    return width,height,kind in (4,6)


def inspect_png(path, entry):
    width,height,alpha=png_info(path)
    if entry['alfa'] and not alpha:
        raise ValueError('canal alfa obrigatório')
    warnings=[]
    min_width=entry['largura_recomendada']
    if (min_width and width<min_width) or height<entry['altura_recomendada']:
        warnings.append('Resolução abaixo da recomendação. Pode haver ampliação superior a 100%.')
    return width,height,alpha,warnings


def _atomic_copy(source, target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent,delete=False) as handle:
        temporary=Path(handle.name)
    try:
        shutil.copyfile(source,temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def expected_prompts(root):
    project,material,folder,_,_,_,_,_=load_design(root)
    expected=read(folder/'prompts_imagens.json')
    if expected['proposta_sha256']!=board_hash(material,folder):
        raise ValueError('A bíblia ou o storyboard mudou. Aprove a revisão e gere novos prompts.')
    return material,folder,expected


def import_images(root, source, fixture=False):
    material,folder,expected=expected_prompts(root)
    if not source.is_dir():
        raise ValueError('Pasta de imagens indisponível.')
    manifest=folder/'assets.json'
    previous={item['id']:item for item in read(manifest)['assets']} if manifest.is_file() else {}
    rows=[]
    for prompt in expected['prompts']:
        name=prompt['arquivo']
        incoming=source/name
        target=folder/'imagens'/name
        old=previous.get(prompt['id'],{})
        item={**prompt,'arquivo':target.relative_to(root).as_posix(),'status':'pendente'}
        path=incoming if incoming.is_file() else target
        if not path.is_file():
            rows.append(item)
            continue
        try:
            if path==target and old.get('prompt_sha256')!=prompt['prompt_sha256']:
                raise ValueError('PNG de uma revisão anterior. Importe a versão atual.')
            width,height,alpha,warnings=inspect_png(path,prompt)
            digest=sha(path)
            unchanged=(old.get('sha256')==digest and old.get('prompt_sha256')==prompt['prompt_sha256'])
            if path!=target:
                _atomic_copy(path,target)
            item.update(status=old['status'] if unchanged and old['status'] in ('aprovada','refazer') else 'recebida',
                        sha256=digest,largura=width,altura=height,alfa_detectado=alpha,avisos=warnings,
                        origem=old.get('origem') if unchanged else ('fixture sintética' if fixture else
                                f'Gerada pelo usuário no ChatGPT, importada em {_now()} para o prompt {prompt["id"]}.'),
                        credito='fixture de teste' if fixture else 'ilustração gerada por IA')
        except ValueError as error:
            item.update(status='refazer',erro=str(error))
        rows.append(item)
    write(manifest,{'proposta_sha256':expected['proposta_sha256'],'assets':rows})
    contact(root,rows)
    return rows


def contact(root, rows):
    out=root/'ilustrado'
    out.mkdir(exist_ok=True)
    groups={}
    for row in rows:
        groups.setdefault(row.get('personagem') or 'Cenários e objetos',[]).append(row)
    html_rows=[]
    for group,entries in groups.items():
        html_rows.append(f'<h2>{html.escape(group)}</h2><section>')
        for row in entries:
            label=html.escape(row['id'])
            image=''
            if row.get('sha256'):
                relative='../'+row['arquivo']
                image=f'<img src="{quote(relative)}" alt="{label}">'
            notes=' '.join([row.get('erro',''),*row.get('avisos',[])])
            html_rows.append(f'<figure>{image}<figcaption>{label} · {row["status"]}<p>{html.escape(notes)}</p></figcaption></figure>')
        html_rows.append('</section>')
    (out/'folha_contato.html').write_text('''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Folha de contato · Ilustrado</title><style>body{background:#162321;color:#ecf5ef;margin:2rem;font:16px system-ui}
section{display:flex;flex-wrap:wrap;gap:1rem}figure{width:240px;background:#223331;margin:0;padding:12px}
img{display:block;width:100%;height:168px;object-fit:contain;background:repeating-conic-gradient(#293b39 0% 25%,#253532 0% 50%) 0 / 20px 20px}
figcaption{padding-top:10px}p{font-size:13px;color:#c3d6cb}</style>
<h1>Folha de contato · Ilustrado</h1><p>Confira a consistência das folhas, poses, cenários e objetos.</p>'''
      +''.join(html_rows)+'</html>',encoding='utf-8')


def approve(root, stage, assets=(), redo=False):
    project,material,folder,_,_,_,_,_=load_design(root)
    if stage=='biblia':
        _approval(folder,stage,design_hash(folder))
    elif stage=='storyboard':
        require_review(folder,'biblia',design_hash(folder))
        _approval(folder,stage,board_hash(material,folder))
    elif stage=='imagens':
        _,_,expected=expected_prompts(root)
        path=folder/'assets.json'
        stored=read(path)
        if stored['proposta_sha256']!=expected['proposta_sha256']:
            raise ValueError('As imagens pertencem a uma proposta anterior.')
        rows=stored['assets']
        chosen=set(assets) if assets else {row['id'] for row in rows}
        if not chosen <= {row['id'] for row in rows}:
            raise ValueError('Asset desconhecido.')
        for row in rows:
            if row['id'] not in chosen:
                continue
            if (not redo and (row['status'] not in ('recebida','aprovada')
                    or sha(root/row['arquivo'])!=row['sha256'])):
                raise ValueError(f'Importe o PNG atual antes de aprovar {row["id"]}.')
            row.update(status='refazer' if redo else 'aprovada', revisao_em=_now())
        write(path,stored)
        contact(root,rows)
        credits=[f'- {row["id"]} · {row["credito"]} · {row["origem"]}'
                 for row in rows if row['status']=='aprovada']
        update_section(root/'FONTES.md','## Imagens do Ilustrado',
                       'Imagens de representação visual. Seu crédito acompanha cada arquivo.\n\n'+'\n'.join(credits))
    else:
        raise ValueError('Etapa de aprovação desconhecida.')


def usable_images(root, final=False):
    material,folder,expected=expected_prompts(root)
    path=folder/'assets.json'
    stored=read(path) if path.is_file() else {'proposta_sha256':'','assets':[]}
    if stored['proposta_sha256']!=expected['proposta_sha256']:
        raise ValueError('Importe as imagens da proposta atual.')
    rows={row['id']:row for row in stored['assets']}
    needed={entry['id'] for entry in expected['prompts']}
    statuses={'aprovada'} if final else {'aprovada','recebida'}
    missing=sorted(name for name in needed if rows.get(name,{}).get('status') not in statuses)
    if missing:
        raise ValueError(f'Faltam {len(missing)} imagens ou aprovações: '+', '.join(missing))
    if rows.keys()!=needed:
        raise ValueError('O inventário contém PNGs fora da proposta.')
    for key,row in rows.items():
        file=folder/'imagens'/(key+'.png')
        if row['arquivo']!=file.relative_to(root).as_posix() or file.is_symlink() or not file.is_file() or sha(file)!=row['sha256']:
            raise ValueError(f'PNG alterado após importação: {key}.')
    return rows
