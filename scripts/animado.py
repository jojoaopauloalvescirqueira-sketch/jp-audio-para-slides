"""Encaminhamento dos projetos animados para seus respectivos adaptadores."""
from argparse import Namespace
from hashlib import sha256
import json
import subprocess

from estilo_video import ensure_style_plan
from projeto import FORMATS, audio_identity, binary, config, probe, read, sha, write


def pictogram(root, args):
    from pictograma import Words, animate, project_context

    project, direction, material, paragraphs, fmt = project_context(root, args.formato)
    return animate(args, root, project, direction, material, paragraphs, Words(paragraphs), fmt)


def prepare(root, args):
    style = config(root).get('estilo_video')
    if style == 'pictograma':
        return pictogram(root, Namespace(**{**vars(args), 'acao': 'previa'}))
    if style == 'ilustrado':
        from ilustrado import board
        from ilustrado_render import render_preview

        ensure_style_plan(root, style, args.plano)
        if args.plano:
            return board(root, read(args.plano))
        return render_preview(root, args.formato, args.estimar)[0]
    raise ValueError('Escolha um estilo animado antes de preparar as cenas.')


def synchronize(root, args, style):
    if args.marcacoes:
        raise ValueError('Para animações, use transcricao_asr.json e, se necessário, marcacoes_acoes.json.')
    if style == 'pictograma':
        return pictogram(root, Namespace(**{**vars(args), 'acao': 'video' if args.renderizar else 'previa',
                                           'plano': None, 'estimar': False}))
    from ilustrado_render import render_preview, render_video

    return render_video(root, args) if args.renderizar else render_preview(root, args.formato)[0]


def image_identity(images):
    return sha256(''.join(images[name]['sha256'] for name in sorted(images)).encode()).hexdigest()


def export_identity(material, project, plan_name, timing_source=None):
    direction = json.dumps(project.get('direcao_visual', {}), sort_keys=True, ensure_ascii=False)
    return {'plano_sha256': sha(material/plan_name),
            'roteiro_sha256': sha(material/'paragrafos.json'),
            'transcricao_sha256': sha(timing_source or material/'transcricao_asr.json'),
            'direcao_sha256': sha256(direction.encode('utf-8')).hexdigest()}


def validate(root, args, style):
    from cenas import Words
    from ancoras import require_reviewed_anchors

    project = config(root)
    material = root/'material'
    fmt = args.formato or project['formato']
    key = fmt.replace(':','x')
    ensure_style_plan(root, style)
    current = {}
    if style == 'pictograma':
        from pictograma import compile_plan, project_context, require_approval
        from pictograma_sincronia import source_path, MANUAL, SOURCE

        _, direction, _, paragraphs, _ = project_context(root, fmt)
        words = Words(paragraphs)
        scenes = compile_plan(read(material/'cenas_pictograma.json'), words, direction)
        require_approval(material, direction, fmt, scenes, words)
        out = root/f'pictograma-{key}'
        if args.video:
            current=export_identity(material,project,'cenas_pictograma.json',source_path(material))
            current['ajustes_sha256']=sha(material/MANUAL) if (material/MANUAL).is_file() else None
            current['previa_sha256']=sha(out/'apresentacao.html')
            current['legenda_fonte_sha256']=sha(material/SOURCE) if (material/SOURCE).is_file() else None
    else:
        from ilustrado import compile_illustrated, load_design
        from ilustrado_imagens import usable_images

        _, _, _, paragraphs, _, cast, _, declarations = load_design(root)
        public = [row['nome_publico'].casefold() for row in cast if 'nome_publico' in row]
        scenes = compile_illustrated(read(material/'cenas_ilustrado.json'), Words(paragraphs),
                                     declarations, project, public)
        if fmt == '9:16' and any(fmt not in scene['enquadramento'] for scene in scenes):
            raise ValueError('Informe o enquadramento 9:16 de cada cena.')
        if args.video:
            current=export_identity(material,project,'cenas_ilustrado.json')
        current['assets_sha256'] = image_identity(usable_images(root, args.video))
        out = root/'ilustrado'/key

    if not (out/'apresentacao.html').is_file():
        raise ValueError('Prévia HTML ausente.')
    result = {'estilo_video':style, 'formato':fmt, 'cenas':len(scenes), 'cobertura_roteiro':True}
    if args.video:
        timeline = read(out/f'timeline_{style}.json')
        current['audio_identidade'] = audio_identity(root,project,paragraphs)
        if (timeline['estimado'] or timeline['formato'] != fmt
                or any(timeline.get(field) != value for field,value in current.items())):
            raise ValueError('Plano, roteiro, imagens ou áudio mudaram após a exportação.')
        require_reviewed_anchors(root,timeline)
        video = out/'video.mp4'
        info = probe(video,binary('ffprobe',args.ffprobe))
        stream = next(row for row in info['streams'] if row['codec_type']=='video')
        if (stream['codec_name'] != 'h264' or stream['avg_frame_rate'] != '30/1'
                or (stream['width'],stream['height']) != FORMATS[fmt]
                or int(stream['nb_frames']) != timeline['quadros']
                or abs(float(info['format']['duration'])-timeline['duracao_s']) > .1):
            raise ValueError('Vídeo com metadados incompatíveis.')
        subprocess.run([binary('ffmpeg',args.ffmpeg),'-v','error','-xerror','-i',str(video),
                        '-map','0:v:0','-map','0:a:0','-f','null','-'],check=True)
        result.update(decodificacao_integral=True,quadros=timeline['quadros'],
                      duracao_s=timeline['duracao_s'],audio_identidade=current['audio_identidade'])
    write(out/'validacao.json',result)
    return result
