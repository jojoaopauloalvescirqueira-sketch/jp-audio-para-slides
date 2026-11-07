"""Mux, trilha e conferência de MP4 dos dois motores visuais."""
import subprocess
import tempfile
from pathlib import Path

from projeto import FORMATS, ffquote, probe, write
from trilha import prepare as prepare_music, saved_selection


def _unify(root, files, streams, total, ffmpeg, ffprobe):
    preview = root / 'material/narracao-unificada.m4a'
    channels = max(int(stream.get('channels', 1)) for stream in streams)
    with tempfile.TemporaryDirectory(prefix='.audio-normalizada-', dir=root) as directory:
        directory = Path(directory)
        normalized = []
        for index, file in enumerate(files):
            destination = directory / f'{index:06}.wav'
            subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', str(file), '-vn',
                            '-ar', '48000', '-ac', str(channels), '-c:a', 'pcm_s16le',
                            str(destination)], check=True)
            normalized.append(destination)
        tracklist = directory / 'audio.ffconcat'
        tracklist.write_text('ffconcat version 1.0\n' +
                             '\n'.join('file ' + ffquote(file) for file in normalized) + '\n', encoding='utf-8')
        derived = directory / 'unificada.m4a'
        subprocess.run([ffmpeg, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(tracklist),
                        '-c:a', 'aac', '-b:a', '192k', str(derived)], check=True)
        if abs(float(probe(derived, ffprobe)['format']['duration']) - total) > .15:
            raise ValueError('A unificação dos áudios mudou a duração total.')
        derived.replace(preview)
    return preview


def _audio_hash(ffmpeg, file):
    return subprocess.run([ffmpeg, '-v', 'error', '-i', str(file), '-map', '0:a:0',
                           '-c:a', 'copy', '-f', 'hash', '-hash', 'sha256', '-'],
                          check=True, capture_output=True, text=True).stdout.strip()


def export(root, target, fmt, files, infos, total, ff, ffprobe, music, report,
           project, visual_input, threads, tuning=()):
    streams = [next(stream for stream in info['streams'] if stream['codec_type'] == 'audio')
               for info in infos]
    single = len(files) == 1
    narration = files[0] if single else _unify(root, files, streams, total, ff, ffprobe)
    copy_audio = single and streams[0]['codec_name'] == 'aac'
    codec = ['-c:a', 'copy'] if copy_audio or not single else ['-c:a', 'aac', '-b:a', '192k']
    track_record = None
    with tempfile.TemporaryDirectory(prefix='.mix-', dir=root) as scratch:
        audio_input = ['-i', str(narration)]
        audio_map = ['-map', '1:a:0']
        if music:
            music_input, graph, track_record = prepare_music(
                root, music, narration, total, ff, ffprobe, report['audio_identidade'].values(), Path(scratch))
            audio_input += music_input
            audio_map = ['-filter_complex', graph, '-map', '[mix]']
            codec = ['-c:a', 'aac', '-b:a', '192k']
            copy_audio = False
        with tempfile.NamedTemporaryFile(prefix='.render-', suffix='.mp4', dir=target.parent, delete=False) as handle:
            stage = Path(handle.name)
        try:
            subprocess.run([ff, '-y', '-hide_banner', '-loglevel', 'warning', *visual_input, *audio_input,
                            '-map', '0:v:0', *audio_map, '-vf', 'fps=30', '-c:v', 'libx264', '-preset',
                            'veryfast', *tuning, '-crf', '20', '-threads', str(threads), '-pix_fmt',
                            'yuv420p', *codec, '-t', f'{total:.6f}', '-movflags', '+faststart', str(stage)], check=True)
            metadata = probe(stage, ffprobe)
            video = next(stream for stream in metadata['streams'] if stream['codec_type'] == 'video')
            if ((video['width'], video['height']) != FORMATS[fmt] or video['avg_frame_rate'] != '30/1'
                    or int(video['nb_frames']) != round(total * 30)
                    or abs(float(metadata['format']['duration']) - total) > .1):
                raise ValueError('Metadados do vídeo não conferem.')
            subprocess.run([ff, '-v', 'error', '-xerror', '-i', str(stage), '-map', '0:v:0',
                            '-map', '0:a:0', '-f', 'null', '-'], check=True)
            if copy_audio and _audio_hash(ff, narration) != _audio_hash(ff, stage):
                raise ValueError('O áudio copiado não corresponde ao original.')
            stage.replace(target)
        finally:
            stage.unlink(missing_ok=True)

    report.update(video=target.name, decodificacao_integral=True, audio_sem_recompressao=copy_audio)
    if track_record:
        report['trilha'] = track_record
        project['trilha'] = saved_selection(track_record)
    if not single:
        project['audio_previa'] = narration.relative_to(root).as_posix()
    if track_record or not single:
        write(root / 'projeto.json', project)
