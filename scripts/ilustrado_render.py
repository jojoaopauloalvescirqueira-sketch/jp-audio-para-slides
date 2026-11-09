"""Compilação e prévia do Ilustrado com PNGs importados."""
import base64
import os
from pathlib import Path
from urllib.parse import quote

from cenas import ASSETS, Words, compile_timeline, derive_slides, player
from ilustrado import PLAN, compile_illustrated, load_design
from ilustrado_imagens import usable_images
from projeto import FORMATS, audio, audio_files, read, sha, write


def render_preview(root, fmt=None, estimated=False, final=False):
    project,material,folder,paragraphs,bible,cast,_,declarations=load_design(root)
    plan=read(material/PLAN)
    fmt=fmt or plan.get('formato') or project['formato']
    if fmt not in ('16:9','9:16'):
        raise ValueError('O Ilustrado usa 16:9 ou 9:16.')
    words=Words(paragraphs)
    public=[row['nome_publico'].casefold() for row in cast if 'nome_publico' in row]
    scenes=compile_illustrated(plan,words,declarations,project,public)
    if fmt=='9:16' and any(fmt not in scene['enquadramento'] for scene in scenes):
        raise ValueError('Informe o enquadramento 9:16 de cada cena.')
    images=usable_images(root,final)
    if final and (estimated or not project.get('audio')):
        raise ValueError('A exportação exige palavras medidas e áudio.')
    times,report=compile_timeline(root,scenes,paragraphs,estimated)
    derive_slides(material,scenes,words)
    out=root/'ilustrado'/fmt.replace(':','x')
    preview=out/'apresentacao.html'
    audio_path=None
    if not report['estimado']:
        files=audio_files(audio(root,project),len(paragraphs))
        unified=material/'narracao-unificada.m4a'
        audio_path=files[0] if len(files)==1 else unified if unified.is_file() else None
    direction=project.get('direcao_visual',{})
    logo=None
    if direction.get('marca',{}).get('valor')=='sim':
        logo='data:image/png;base64,'+base64.b64encode((ASSETS/'jp-wealth-logo.png').read_bytes()).decode()
    data=dict(kit='ilustrado',formato=fmt,dimensoes=FORMATS[fmt],paleta=bible['paleta'],
              estimado=report['estimado'],duracao=report['duracao_s'],cenas=report['cenas'],
              interface_cena=False,legenda=direction.get('legenda',{}).get('valor')=='sim',marca=logo,
              palavras=[{**row,'tempo':t} for row,t in zip(words.words,times)],
              pendente=any(row['status']!='aprovada' for row in images.values()),
              imagens={name:{'url':quote(os.path.relpath(root/row['arquivo'],out)), 'tipo':row['tipo']}
                       for name,row in images.items() if row['tipo']!='folha'})
    player(preview,project['titulo'],fmt,data,(ASSETS/'kit-ilustrado.js').read_text(encoding='utf-8'),audio_path,
           css=(ASSETS/'ilustrado.css').read_text(encoding='utf-8'),
           notes='<p class="credito-ilustracao">Ilustração conceitual. Créditos em FONTES.md.</p>')
    report.update(estilo_video='ilustrado',formato=fmt,plano_sha256=sha(material/PLAN),
                  roteiro_sha256=sha(material/'paragrafos.json'))
    write(out/'timeline_previa.json',report)
    return preview,fmt,report,images


def render_video(root, args):
    from animado import export_identity, image_identity
    from video_export import export_animation

    preview,fmt,report,images=render_preview(root,args.formato,final=True)
    project,material,_,paragraphs,_,_,_,_=load_design(root)
    out=preview.parent
    digest=image_identity(images)
    report.update(export_identity(material,project,PLAN),assets_sha256=digest)
    target=out/'video.mp4'
    export_animation(root,preview,target,out/'quadros',fmt,project,paragraphs,report,args,digest)
    write(out/'timeline_ilustrado.json',report)
    if len(audio_files(audio(root,project),len(paragraphs)))>1:
        render_preview(root,fmt,final=True)
    return target
