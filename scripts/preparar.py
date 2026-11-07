#!/usr/bin/env python3
"""Copia entradas prontas, preserva originais e cria o projeto editorial vazio."""
import argparse,re,shutil,sys
from pathlib import Path
from editorial import initialize, PROFILE
from projeto import audio_files,binary,probe,sha,write
from fala import clean_paragraphs
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--audio',required=True,type=Path);p.add_argument('--roteiro',required=True,type=Path);p.add_argument('--titulo',required=True);p.add_argument('--autor',default='');p.add_argument('--subtitulo',default='');p.add_argument('--artigo',type=Path);p.add_argument('--perfil-visual',choices=[PROFILE,'legado'],default=PROFILE);p.add_argument('--ffprobe');p.add_argument('--audio-tag',action='append',default=[]);p.add_argument('--literal-tag',action='append',default=[]);a=p.parse_args()
 if (a.root/'projeto.json').exists():raise ValueError('Projeto existente; não será sobrescrito.')
 if not a.roteiro.is_file():raise ValueError('Roteiro ausente.')
 raw=a.roteiro.read_text(encoding='utf-8-sig');paras=clean_paragraphs(raw,a.audio_tag,a.literal_tag)
 if not paras:raise ValueError('Roteiro vazio.')
 files=audio_files(a.audio,len(paras));ffprobe=binary('ffprobe',a.ffprobe)
 measurements=[{'arquivo':f.name,'duracao_s':float(probe(f,ffprobe)['format']['duration']),'sha256':sha(f)} for f in files]
 if a.artigo and not a.artigo.is_file():raise ValueError('Artigo ausente.')
 mat=a.root/'material';mat.mkdir(parents=True,exist_ok=True);shutil.copy2(a.roteiro,mat/'roteiro_original.txt');(mat/'roteiro_limpo.txt').write_text('\n\n'.join(paras)+'\n',encoding='utf-8')
 if a.audio.is_dir():
  dest=mat/'audios';dest.mkdir()
  for i,f in enumerate(files,1):shutil.copy2(f,dest/f'P{i:03}{f.suffix.lower()}')
 else:dest=mat/('narracao'+a.audio.suffix.lower());shutil.copy2(a.audio,dest)
 if a.artigo:shutil.copy2(a.artigo,mat/('artigo'+a.artigo.suffix))
 write(mat/'paragrafos.json',[{'id':f'P{i:03}','texto':t} for i,t in enumerate(paras,1)]);write(mat/'slides.json',[]);write(mat/'fontes_figuras.json',[]);write(mat/'entradas.json',measurements)
 visual=initialize(a.root) if a.perfil_visual==PROFILE else {'perfil_visual':'legado'}
 visual['trilha_obrigatoria']=True
 write(a.root/'projeto.json',{**visual,'titulo':a.titulo,'subtitulo':a.subtitulo,'autor':a.autor,'marca':'','cta_rotulo':'','cta_url':'','capa':'','audio':dest.relative_to(a.root).as_posix(),'formato':'16:9','estilo_video':None,'idioma':'pt','fps':30})
 print(f'{len(paras)} parágrafos preparados. Preencha material/slides.json com o plano editorial.')
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError) as e:sys.exit(str(e))
