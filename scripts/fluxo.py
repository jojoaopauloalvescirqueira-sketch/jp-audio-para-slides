"""Preparação e retomada sem síntese de voz ou dependência de outra skill."""
import argparse,shutil,sys
from pathlib import Path
from editorial import initialize, PROFILE
from fala import clean_paragraphs,compare_speech
from projeto import read,write,sha,audio_files,binary,probe,config
from validar_roteiro import validate

def iniciar(root,titulo,artigo=None,autor='',perfil_visual=PROFILE):
 root=Path(root)
 if not titulo.strip():raise ValueError('Título ausente.')
 if (root/'projeto.json').exists():raise ValueError('Projeto existente; use registrar_roteiro ou anexar_audio para retomar.')
 if artigo and not Path(artigo).is_file():raise ValueError('Artigo ausente.')
 mat=root/'material';mat.mkdir(parents=True,exist_ok=True)
 visual=initialize(root) if perfil_visual==PROFILE else {'perfil_visual':'legado'}
 visual['trilha_obrigatoria']=True
 c={**visual,'titulo':titulo,'autor':autor,'subtitulo':'','audio':None,'formato':'16:9','fps':30,'idioma':'pt','estado':'roteirizacao'}
 if artigo:
  artigo=Path(artigo);dest=mat/('artigo'+artigo.suffix);shutil.copy2(artigo,dest)
  c['artigo']={'arquivo':dest.relative_to(root).as_posix(),'sha256':sha(dest)}
 write(root/'projeto.json',c)
 for name in ('slides','fontes_figuras'):write(mat/(name+'.json'),[])
 return c

def registrar(root,limpo,studio=None,model='eleven_v4',audio_tags=(),literal_tags=()):
 root=Path(root);c=config(root);mat=root/'material';limpo=Path(limpo)
 if not limpo.is_file() or (studio and not Path(studio).is_file()):raise ValueError('Roteiro ausente.')
 text=limpo.read_text(encoding='utf-8-sig');marked=Path(studio).read_text(encoding='utf-8-sig') if studio else text
 report=validate(marked,model,text,audio_tags=audio_tags,literal_tags=literal_tags)
 if report['errors']:raise ValueError('Roteiro incompatível: '+'; '.join(report['errors']))
 paras=clean_paragraphs(text,(),literal_tags)
 if not paras or not compare_speech(marked,text,audio_tags,literal_tags):raise ValueError('Fala ou parágrafos divergentes.')
 canonical='\n\n'.join(paras)+'\n';dest=mat/'roteiro_limpo.txt'
 if dest.exists() and dest.read_text()!=canonical:raise ValueError('Fala canônica existente difere; crie nova revisão do projeto antes de substituir.')
 dest.write_text(canonical,encoding='utf-8');(mat/'roteiro_studio.txt').write_text(marked,encoding='utf-8')
 write(mat/'paragrafos.json',[{'id':f'P{i:03}','texto':p} for i,p in enumerate(paras,1)])
 write(mat/'validacao_roteiro.json',report)
 c.update(estado='audio_disponivel' if c.get('audio') else 'aguardando_audio',roteiro_sha256=sha(dest),modelo_recomendado=model,controles_vocais=list(audio_tags),colchetes_literais=list(literal_tags))
 write(root/'projeto.json',c);return report

def anexar(root,source,ffprobe=None):
 root=Path(root);c=config(root);mat=root/'material';ps=read(mat/'paragrafos.json')
 if not ps:raise ValueError('Registre a fala canônica antes do áudio.')
 source=Path(source);files=audio_files(source,len(ps));ffprobe=binary('ffprobe',ffprobe)
 measures=[]
 for f in files:
  data=probe(f,ffprobe)
  if not any(s.get('codec_type')=='audio' for s in data['streams']):raise ValueError('Arquivo não contém faixa de áudio.')
  measures.append({'arquivo':f.name,'duracao_s':float(data['format']['duration']),'sha256':sha(f)})
 if c.get('audio'):
  old=audio_files(root/c['audio'],len(ps))
  if [sha(f) for f in old]!=[m['sha256'] for m in measures]:raise ValueError('Áudio existente diferente; preserve-o e crie uma revisão explícita.')
  return measures
 if source.is_dir():
  dest=mat/'audios';dest.mkdir(exist_ok=True)
  for i,f in enumerate(files,1):shutil.copy2(f,dest/f'P{i:03}{f.suffix.lower()}')
 else:
  dest=mat/('narracao'+source.suffix.lower());shutil.copy2(source,dest)
 write(mat/'entradas.json',measures);c.update(audio=dest.relative_to(root).as_posix(),estado='audio_disponivel');write(root/'projeto.json',c)
 return measures

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='acao',required=True)
 a=sub.add_parser('iniciar');a.add_argument('--root',required=True,type=Path);a.add_argument('--titulo',required=True);a.add_argument('--autor',default='');a.add_argument('--artigo',type=Path);a.add_argument('--perfil-visual',choices=[PROFILE,'legado'],default=PROFILE)
 a=sub.add_parser('registrar_roteiro');a.add_argument('--root',required=True,type=Path);a.add_argument('--limpo',required=True,type=Path);a.add_argument('--studio',type=Path);a.add_argument('--model',default='eleven_v4');a.add_argument('--audio-tag',action='append',default=[]);a.add_argument('--literal-tag',action='append',default=[])
 a=sub.add_parser('anexar_audio');a.add_argument('--root',required=True,type=Path);a.add_argument('--audio',required=True,type=Path);a.add_argument('--ffprobe')
 a=p.parse_args()
 if a.acao=='iniciar':iniciar(a.root,a.titulo,a.artigo,a.autor,a.perfil_visual)
 elif a.acao=='registrar_roteiro':registrar(a.root,a.limpo,a.studio,a.model,a.audio_tag,a.literal_tag)
 else:anexar(a.root,a.audio,a.ffprobe)
 print('Etapa concluída. Consulte projeto.json; sincronização exige áudio e marcações verificadas.')
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError) as e:sys.exit(str(e))
