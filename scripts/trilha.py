"""Seleciona e mixa trilhas locais sem alterar o tempo da narração."""
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from projeto import probe, read, sha

DEFAULT_LEVEL = -20.0
LIBRARY = Path(__file__).resolve().parents[1] / 'assets' / 'trilhas'
DEFAULT_MOOD = 'reflexiva'
CROSSFADE = 1.5
RATE = 48000


def catalog_metadata(track, mood, method, reason):
    return {
        'origem': 'biblioteca', 'atmosfera': mood, 'metodo': method, 'motivo': reason,
        **{key: track[key] for key in ('compositor', 'fonte', 'credito', 'licenca')},
    }


def measured_track(path, level, name, details, ffprobe):
    if not isinstance(level, (int, float)) or not math.isfinite(level) or not -35 <= level <= -12:
        raise ValueError('O nível relativo da trilha deve ficar entre −35 e −12 dB.')
    info = probe(path, ffprobe)
    if not any(s['codec_type'] == 'audio' for s in info['streams']):
        raise ValueError('O arquivo escolhido precisa conter uma faixa de áudio.')
    duration = float(info['format']['duration'])
    if duration < 1:
        raise ValueError('Escolha uma faixa com pelo menos um segundo de áudio.')
    return path, level, duration, name or path.name, details


def library_file(track):
    path = (LIBRARY / track['arquivo']).resolve()
    if not path.is_relative_to(LIBRARY.resolve()) or not path.is_file() or sha(path) != track['sha256']:
        raise ValueError('Faixa da biblioteca ausente ou alterada. Reinstale o pacote ou use --trilha.')
    return path


def choose_program(catalog, mood, total):
    """Prefere uma faixa inteira; para leituras longas, usa a ordem editorial."""
    if mood not in catalog['atmosferas']:
        raise ValueError('Atmosfera desconhecida. Escolha entre ' + ', '.join(catalog['atmosferas']) + '.')
    profile = catalog['atmosferas'][mood]
    pool = [catalog['faixas'][key] for key in profile['faixas']]
    fitting = next((track for track in pool if track['duracao_s'] >= total), None)
    if fitting:
        return [fitting]
    chosen = []
    duration = 0.
    for track in pool:
        duration += track['duracao_s'] - (CROSSFADE if chosen else 0.)
        chosen.append(track)
        if duration >= total:
            break
    return chosen


def select(root, cfg, selected, level, ffprobe, atmosfera=None, motivo=None, total=0.):
    saved = cfg.get('trilha') or {}
    if selected is not None:
        path = selected.expanduser().resolve()
        if path.parent == LIBRARY.resolve():
            catalog = read(LIBRARY / 'catalogo.json')
            for track_id, track in catalog['faixas'].items():
                if path.name == track['arquivo']:
                    mood = next(key for key, profile in catalog['atmosferas'].items() if track_id in profile['faixas'])
                    details = catalog_metadata(track, mood, 'escolha_do_usuario', 'Faixa indicada para este vídeo.')
                    base = track['nivel_relativo_db'] if level is None else level
                    return [measured_track(library_file(track), base, track['nome'], details, ffprobe)]
        return [measured_track(path, DEFAULT_LEVEL if level is None else level, None,
                               {'origem':'arquivo_indicado'}, ffprobe)]
    if saved:
        tracks = []
        for row in saved.get('faixas', [saved]):
            path = (root / row['arquivo']).resolve()
            if not path.is_relative_to(root) or not path.is_file() or sha(path) != row.get('sha256'):
                raise ValueError('A trilha registrada mudou ou está ausente. Selecione o arquivo com --trilha.')
            base = row.get('nivel_relativo_db', DEFAULT_LEVEL) if level is None else level
            details = row.get('selecao', {'origem':'faixa_registrada'})
            tracks.append(measured_track(path, base, row.get('nome'), details, ffprobe))
        if not tracks:
            raise ValueError('A sequência de trilha registrada está vazia.')
        return tracks
    if os.environ.get('JP_TRILHA_PADRAO'):
        path = Path(os.environ['JP_TRILHA_PADRAO']).expanduser().resolve()
        return [measured_track(path, DEFAULT_LEVEL if level is None else level, None,
                               {'origem':'padrao_do_usuario'}, ffprobe)]
    if not (atmosfera or cfg.get('trilha_obrigatoria')):
        return []
    mood = atmosfera or DEFAULT_MOOD
    catalog = read(LIBRARY / 'catalogo.json')
    program = choose_program(catalog, mood, total)
    method = 'avaliacao_editorial' if atmosfera else 'reserva_reflexiva'
    reason = motivo or (catalog['atmosferas'][mood]['perfil'] if atmosfera else 'Perfil reflexivo usado como reserva.')
    return [
        measured_track(library_file(track), track['nivel_relativo_db'] if level is None else level,
                       track['nome'], catalog_metadata(track, mood, method, reason), ffprobe)
        for track in program
    ]


def mean_level(ffmpeg, path):
    result = subprocess.run([ffmpeg, '-hide_banner', '-nostats', '-i', str(path),
                             '-map', '0:a:0', '-af', 'volumedetect', '-f', 'null', '-'],
                            check=True, capture_output=True, text=True)
    match = re.search(r'mean_volume:\s*(-?\d+(?:\.\d+)?) dB', result.stderr)
    if not match:
        raise ValueError('Não foi possível medir o volume do áudio.')
    return float(match[1])


def stage_track(root, selection, voice_db, ffmpeg, voice_hashes):
    path, relative_db, duration, name, details = selection
    digest = sha(path)
    if digest in voice_hashes:
        raise ValueError('Escolha uma trilha diferente do arquivo da narração.')
    music_db = mean_level(ffmpeg, path)
    if music_db < -70:
        raise ValueError('A faixa escolhida está silenciosa ou quase silenciosa.')
    gain = min(24., max(-60., voice_db - music_db + relative_db))
    folder = root / 'material' / 'trilhas'
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (digest + path.suffix.lower())
    if not target.exists():
        with tempfile.NamedTemporaryFile(dir=folder, prefix='.trilha-', delete=False) as temp:
            partial = Path(temp.name)
        try:
            shutil.copyfile(path, partial)
            if sha(partial) != digest:
                raise ValueError('A faixa mudou enquanto era copiada.')
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    if sha(target) != digest:
        raise ValueError('A cópia local da trilha está corrompida.')
    return {'arquivo':target.relative_to(root).as_posix(), 'nome':name, 'sha256':digest,
            'nivel_relativo_db':relative_db, 'selecao':details, 'ganho_aplicado_db':round(gain,3),
            'duracao_faixa_s':duration}


def assemble(root, tracks, total, ffmpeg, ffprobe, scratch):
    """Gera uma sequência finita, com costura também na fronteira do ciclo."""
    if any(track['duracao_faixa_s'] <= 2*CROSSFADE for track in tracks):
        raise ValueError('Cada faixa da sequência precisa ter mais de três segundos.')
    joined = sum(track['duracao_faixa_s'] for track in tracks) - CROSSFADE*(len(tracks)-1)
    cyclic = joined < total
    inputs = tracks + tracks[:1] if cyclic else tracks
    args = [ffmpeg, '-y', '-v', 'error']
    filters = []
    for i, track in enumerate(inputs):
        args += ['-i', str(root / track['arquivo'])]
        trim = f',atrim=end_sample={round(CROSSFADE*RATE)}' if cyclic and i==len(tracks) else ''
        filters.append(f'[{i}:a:0]aresample={RATE},aformat=channel_layouts=stereo,'
                       f'volume={track["ganho_aplicado_db"]:.3f}dB{trim},asetpts=PTS-STARTPTS[t{i}]')
    current = 't0'
    for i in range(1, len(inputs)):
        out = f'x{i}'
        filters.append(f'[{current}][t{i}]acrossfade=d={CROSSFADE}[{out}]')
        current = out
    if cyclic:
        # End with the blended first head; restart at its following sample.
        filters.append(f'[{current}]atrim=start_sample={round(CROSSFADE*RATE)},asetpts=PTS-STARTPTS[ciclo]')
        current = 'ciclo'
    path = scratch / 'sequencia.flac'
    subprocess.run(args+['-filter_complex',';'.join(filters),'-map',f'[{current}]',
                         '-c:a','flac','-compression_level','1',str(path)],check=True)
    duration = float(probe(path,ffprobe)['format']['duration'])
    expected = joined - (CROSSFADE if cyclic else 0.)
    if abs(duration-expected)>.25:
        raise ValueError('A duração da sequência musical não corresponde ao plano.')
    return path, duration


def prepare(root, selection, narration, total, ffmpeg, ffprobe, voice_hashes, scratch):
    voice_db = mean_level(ffmpeg, narration)
    tracks = [stage_track(root, track, voice_db, ffmpeg, voice_hashes) for track in selection]
    if len(tracks)==1:
        record = tracks[0]
        path = root / record['arquivo']
        duration = record['duracao_faixa_s']
        gain = record['ganho_aplicado_db']
    else:
        path, duration = assemble(root, tracks, total, ffmpeg, ffprobe, scratch)
        gain = 0.
        record = {'modo':'sequencia', 'nome':'Sequência Mozart', 'selecao':tracks[0]['selecao'],
                  'faixas':tracks, 'duracao_ciclo_s':duration, 'transicao_s':CROSSFADE,
                  'ciclos':math.ceil(total/duration)}
    fade_in, fade_out = min(1., total/4), min(1.5, total/4)
    graph = (
        '[1:a:0]aresample=48000,aformat=channel_layouts=stereo[voz];'
        '[2:a:0]aresample=48000,aformat=channel_layouts=stereo,'
        f'atrim=duration={total:.6f},asetpts=PTS-STARTPTS,volume={gain:.3f}dB,'
        f'afade=t=in:st=0:d={fade_in:.6f},'
        f'afade=t=out:st={total-fade_out:.6f}:d={fade_out:.6f}[musica];'
        '[voz][musica]amix=inputs=2:duration=first:normalize=0,'
        'alimiter=limit=0.95:level=false:latency=1[mix]'
    )
    record.update(repetida=duration<total,fade_in_s=fade_in,fade_out_s=fade_out)
    loop = ['-stream_loop','-1'] if duration<total else []
    return [*loop,'-i',str(path)], graph, record


def saved_selection(record):
    keys = ('arquivo','nome','sha256','nivel_relativo_db','selecao')
    if record.get('modo')=='sequencia':
        return {'modo':'sequencia','nome':record['nome'],'selecao':record['selecao'],
                'faixas':[{key:row[key] for key in keys} for row in record['faixas']]}
    return {key:record[key] for key in keys}
