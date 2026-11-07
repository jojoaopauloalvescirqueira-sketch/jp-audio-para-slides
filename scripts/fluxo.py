"""Preparação e retomada sem síntese de voz ou dependência de outra skill."""
import argparse,shutil,sys
from pathlib import Path
import direcao
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
 c={**visual,'titulo':titulo,'autor':autor,'subtitulo':'','audio':None,'formato':'16:9','fps':30,'idioma':'pt','estado':'roteirizacao'}
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

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='acao',required=True)
 a=sub.add_parser('iniciar');a.add_argument('--root',required=True,type=Path);a.add_argument('--titulo',required=True);a.add_argument('--autor',default='');a.add_argument('--artigo',type=Path);a.add_argument('--perfil-visual',choices=[PROFILE,'legado'],default=PROFILE)
 a=sub.add_parser('direcao');a.add_argument('--root',required=True,type=Path);direcao.arguments(a)
 a=sub.add_parser('registrar_roteiro');a.add_argument('--root',required=True,type=Path);a.add_argument('--limpo',required=True,type=Path);a.add_argument('--studio',type=Path);a.add_argument('--model',default='eleven_v4');a.add_argument('--audio-tag',action='append',default=[]);a.add_argument('--literal-tag',action='append',default=[])
 a=sub.add_parser('aplicar_tags');a.add_argument('--root',required=True,type=Path);a.add_argument('--plano',required=True,type=Path)
 a=sub.add_parser('anexar_audio');a.add_argument('--root',required=True,type=Path);a.add_argument('--audio',required=True,type=Path);a.add_argument('--ffprobe')
 a=p.parse_args()
 if a.acao=='iniciar':iniciar(a.root,a.titulo,a.artigo,a.autor,a.perfil_visual)
 elif a.acao=='direcao':direcao.record(a.root,a)
 elif a.acao=='registrar_roteiro':registrar(a.root,a.limpo,a.studio,a.model,a.audio_tag,a.literal_tag)
 elif a.acao=='aplicar_tags':aplicar_tags(a.root,a.plano)
 else:anexar(a.root,a.audio,a.ffprobe)
 print('Etapa concluída. Consulte projeto.json; sincronização exige áudio e marcações verificadas.')
if __name__=='__main__':
 try:main()
 except (ValueError,FileNotFoundError) as e:sys.exit(str(e))
