"""Preparação e retomada sem síntese de voz ou dependência de outra skill."""
import argparse,json,shutil,sys
from pathlib import Path
import direcao
import estado_projetos
import plano_tags
from editorial import initialize, PROFILE
from fala import BRACKET, KNOWN, clean_paragraphs, compare_speech, normalize, paragraphs
from projeto import read,write,sha,audio_files,binary,probe,config
from validar_roteiro import validate
from tags_voz import preference, tag_key

def iniciar(root,titulo,artigo=None,autor='',perfil_visual=PROFILE):
 root=Path(root)
 if not titulo.strip():raise ValueError('Título ausente.')
 if (root/'projeto.json').exists():raise ValueError('Projeto existente; use registrar_roteiro ou anexar_audio para retomar.')
 if artigo and not Path(artigo).is_file():raise ValueError('Artigo ausente.')
 mat=root/'material';mat.mkdir(parents=True,exist_ok=True)
 visual=initialize(root) if perfil_visual==PROFILE else {'perfil_visual':'legado'}
 visual['trilha_obrigatoria']=True
 c={**visual,'titulo':titulo,'autor':autor,'subtitulo':'','audio':None,'formato':'16:9','estilo_video':None,'fps':30,'idioma':'pt','estado':'roteirizacao'}
 if artigo:
  artigo=Path(artigo);dest=mat/('artigo'+artigo.suffix);shutil.copy2(artigo,dest)
  c['artigo']={'arquivo':dest.relative_to(root).as_posix(),'sha256':sha(dest)}
 write(root/'projeto.json',c)
 for name in ('slides','fontes_figuras'):write(mat/(name+'.json'),[])
 return c

def registrar(root,limpo,studio=None,model='eleven_v4',audio_tags=(),literal_tags=()):
 root=Path(root);limpo=Path(limpo)
 if not limpo.is_file() or (studio and not Path(studio).is_file()):raise ValueError('Roteiro ausente.')
 text=limpo.read_text(encoding='utf-8-sig');marked=Path(studio).read_text(encoding='utf-8-sig') if studio else text
 return registrar_textos(root,config(root),text,marked,model,audio_tags,literal_tags)


def canonical_state(root, project, literal_tags=()):
    dest = root / 'material/roteiro_limpo.txt'
    literals = {tag_key(tag) for tag in (*project.get('colchetes_literais', []), *literal_tags)}
    if not dest.is_file():
        if project.get('roteiro_sha256'):
            raise ValueError('Fala canônica registrada está ausente.')
        return None, sorted(literals)
    if project.get('roteiro_sha256') and sha(dest) != project['roteiro_sha256']:
        raise ValueError('A fala canônica existente foi alterada.')
    existing = dest.read_bytes().decode('utf-8')
    # A fala já registrada é autoridade sobre colchetes que passaram a integrar o catálogo.
    literals.update(tag_key(match[1]) for match in BRACKET.finditer(existing) if tag_key(match[1]) in KNOWN)
    return existing, sorted(literals)


def registrar_textos(root, project, clean, studio, model, audio_tags, literal_tags, tag_guide=''):
    mat = root / 'material'
    dest = mat / 'roteiro_limpo.txt'
    existing, literals = canonical_state(root, project, literal_tags)
    paras = clean_paragraphs(clean, (), literals)
    if existing is not None:
        if [normalize(p) for p in paragraphs(existing)] != [normalize(p) for p in paragraphs(clean)]:
            raise ValueError('Fala canônica existente difere; crie nova revisão do projeto antes de substituir.')
        canonical = existing
    else:
        canonical = '\n\n'.join(paras) + '\n'
    direction = project.get('direcao_narrativa')
    mode = preference(direction, 'tags')
    if mode in ('elevenlabs', 'nenhuma'):
        studio, audio_tags = canonical, ()
    report = validate(studio, model, clean if existing is None else canonical, audio_tags=audio_tags, literal_tags=literals, direction=direction)
    if report['errors']:
        raise ValueError('Roteiro incompatível: ' + '; '.join(report['errors']))
    if not paras or not compare_speech(studio, canonical, audio_tags, literals):
        raise ValueError('Fala ou parágrafos divergentes.')

    par_path = mat / 'paragrafos.json'
    if existing is not None and par_path.is_file():
        stored = read(par_path)
        expected = [(f'P{i:03}', normalize(p)) for i, p in enumerate(paragraphs(existing), 1)]
        if [(p['id'], normalize(p['texto'])) for p in stored] != expected:
            raise ValueError('Parágrafos existentes incompatíveis com a fala canônica.')
    if direction:
        direcao.update_guide(root, direction)
    else:
        warning = 'Direção narrativa ausente. O registro da fala pode prosseguir.'
        report['warnings'].append(warning)
        report['status'] = 'apto_com_avisos'
        print('Aviso: ' + warning, file=sys.stderr)
    if existing is None:
        dest.write_text(canonical, encoding='utf-8')
    if existing is None or not par_path.exists():
        write(par_path, [{'id': f'P{i:03}', 'texto': p} for i, p in enumerate(paragraphs(canonical), 1)])
    (mat / 'roteiro_studio.txt').write_text(studio, encoding='utf-8')
    write(mat / 'validacao_roteiro.json', report)
    direcao.update_section(mat / 'guia_producao.md', plano_tags.HEADING, tag_guide)
    project.update(estado='audio_disponivel' if project.get('audio') else 'aguardando_audio',
                   roteiro_sha256=sha(dest), modelo_recomendado=model,
                   controles_vocais=list(audio_tags), colchetes_literais=literals)
    write(root / 'projeto.json', project)
    return report


def aplicar_tags(root, path):
    root = Path(root)
    project = config(root)
    canonical, literals = canonical_state(root, project)
    if canonical is None:
        raise ValueError('Registre a fala canônica antes de aplicar tags.')
    studio, controls, tag_guide = plano_tags.render(canonical, read(path), project.get('direcao_narrativa'), literals)
    model = project.get('modelo_recomendado', 'eleven_v4')
    return registrar_textos(root, project, canonical, studio, model, controls, literals, tag_guide)

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

def visual_command(a):
 from estilo_video import choose
 if a.acao=='estilo':
  return choose(a.root,a.estilo,a.salvar,a.formato,a.confirmar_troca)
 root=a.root.resolve()
 if a.acao=='sincronia':
  from pictograma_sincronia import import_timing
  return import_timing(root,a)
 if a.acao=='marca_dagua':
  from editorial import set_watermark
  return set_watermark(root,a.estado=='ligada')
 if a.acao=='cenas':
  from animado import prepare
  return prepare(root,a)
 if a.acao=='direcao_ilustrado':
  from ilustrado_direcao import record
  if not a.respostas and not a.assumir:
   raise ValueError('Informe as respostas ou a delegação do usuário.')
  return record(root,read(a.respostas) if a.respostas else {},a.assumir)
 if a.acao=='dados_ilustrado':
  from ilustrado import apply_design
  return apply_design(root,read(a.proposta))
 from ilustrado_imagens import approve,import_images,prompts
 if a.acao=='aprovar_ilustrado':
  if not a.confirmado:
   raise ValueError('Registre a decisão somente após confirmação explícita do usuário.')
  if (a.asset or a.refazer) and a.etapa!='imagens':
   raise ValueError('Seleção por asset e refação valem para a etapa imagens.')
  return approve(root,a.etapa,a.asset,a.refazer)
 if a.acao=='prompts_imagens':
  return prompts(root)
 return import_images(root,a.pasta)


def main():
 import os
 from estilo_video import STYLES
 from projeto import FORMATS
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='acao',required=True)
 a=sub.add_parser('iniciar');a.add_argument('--root',required=True,type=Path);a.add_argument('--titulo',required=True);a.add_argument('--autor',default='');a.add_argument('--artigo',type=Path);a.add_argument('--perfil-visual',choices=[PROFILE,'legado'],default=PROFILE)
 a=sub.add_parser('direcao');a.add_argument('--root',required=True,type=Path);direcao.arguments(a)
 a=sub.add_parser('registrar_roteiro');a.add_argument('--root',required=True,type=Path);a.add_argument('--limpo',required=True,type=Path);a.add_argument('--studio',type=Path);a.add_argument('--model',default='eleven_v4');a.add_argument('--audio-tag',action='append',default=[]);a.add_argument('--literal-tag',action='append',default=[])
 a=sub.add_parser('aplicar_tags');a.add_argument('--root',required=True,type=Path);a.add_argument('--plano',required=True,type=Path)
 a=sub.add_parser('anexar_audio');a.add_argument('--root',required=True,type=Path);a.add_argument('--audio',required=True,type=Path);a.add_argument('--ffprobe')
 a=sub.add_parser('estado',help='Consultar projetos locais sem modificar arquivos.')
 a.add_argument('--root',action='append',type=Path,default=[],metavar='PASTA',
                help='Pasta ou projeto.json adicional. Pode ser repetido.')
 style=sub.add_parser('estilo',help='Consultar ou registrar o estilo de vídeo.')
 style.add_argument('--root',type=Path)
 style.add_argument('--estilo',choices=STYLES)
 style.add_argument('--salvar',action='store_true')
 style.add_argument('--formato',choices=FORMATS)
 style.add_argument('--confirmar-troca',action='store_true')
 visual={
  'sincronia':sub.add_parser('sincronia',help='Importar tempos de palavras ou revisão por quadro.'),
  'marca_dagua':sub.add_parser('marca_dagua',help='Ligar ou desligar a marca do Editorial JP.'),
  'cenas':sub.add_parser('cenas',help='Preparar a prévia ou o plano de cenas animadas.'),
  'direcao_ilustrado':sub.add_parser('direcao_ilustrado',help='Registrar a direção de arte.'),
  'dados_ilustrado':sub.add_parser('dados_ilustrado',help='Validar e registrar bíblia, elenco e cenários.'),
  'aprovar_ilustrado':sub.add_parser('aprovar_ilustrado',help='Registrar a revisão de uma etapa do Ilustrado.'),
  'prompts_imagens':sub.add_parser('prompts_imagens',help='Preparar prompts após aprovação do storyboard.'),
  'importar_imagens':sub.add_parser('importar_imagens',help='Importar PNGs fornecidos pelo usuário.'),
 }
 for command in visual.values():
  command.add_argument('--root',required=True,type=Path)
 visual['marca_dagua'].add_argument('--estado',required=True,choices=('ligada','desligada'))
 v=visual['cenas']
 v.add_argument('--plano',type=Path)
 v.add_argument('--formato',choices=('9:16','16:9'))
 v.add_argument('--estimar',action='store_true')
 v.add_argument('--node',default=os.environ.get('NODE','node'))
 v.add_argument('--ffmpeg',default=os.environ.get('FFMPEG'))
 v.add_argument('--ffprobe',default=os.environ.get('FFPROBE'))
 v=visual['sincronia']
 v.add_argument('--ffprobe',default=os.environ.get('FFPROBE'))
 v.add_argument('--ffmpeg',default=os.environ.get('FFMPEG'))
 inputs=v.add_mutually_exclusive_group()
 inputs.add_argument('--fonte',type=Path)
 inputs.add_argument('--importar',type=Path)
 v.add_argument('--trecho',help='Parágrafo ou intervalo, por exemplo P007-P008.')
 v.add_argument('--de',help='Trecho literal da primeira palavra do recorte.')
 v.add_argument('--ate',help='Trecho literal que termina na última palavra do recorte.')
 v.add_argument('--origem',choices=('elevenlabs','srt_usuario','usuario'))
 v=visual['direcao_ilustrado']
 v.add_argument('--respostas',type=Path)
 v.add_argument('--assumir',action='store_true')
 visual['dados_ilustrado'].add_argument('--proposta',required=True,type=Path)
 v=visual['aprovar_ilustrado']
 v.add_argument('--etapa',required=True,choices=('biblia','storyboard','imagens'))
 v.add_argument('--confirmado',action='store_true')
 v.add_argument('--asset',action='append',default=[])
 v.add_argument('--refazer',action='store_true')
 visual['importar_imagens'].add_argument('--pasta',required=True,type=Path)
 a=p.parse_args()
 if a.acao=='estilo' or a.acao in visual:
  result=visual_command(a)
  if result is not None:
   print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
  return
 if a.acao=='estado':
  print(json.dumps(estado_projetos.scan([Path.cwd(),*a.root]),ensure_ascii=False,indent=2))
  return
 if a.acao=='iniciar':iniciar(a.root,a.titulo,a.artigo,a.autor,a.perfil_visual)
 elif a.acao=='direcao':direcao.record(a.root,a)
 elif a.acao=='registrar_roteiro':registrar(a.root,a.limpo,a.studio,a.model,a.audio_tag,a.literal_tag)
 elif a.acao=='aplicar_tags':aplicar_tags(a.root,a.plano)
 else:anexar(a.root,a.audio,a.ffprobe)
 print('Etapa concluída. Consulte projeto.json; sincronização exige áudio e marcações verificadas.')
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError,KeyError,TypeError) as e:sys.exit(str(e))
