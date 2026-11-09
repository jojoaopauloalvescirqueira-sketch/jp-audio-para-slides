"""Mede e ajusta voz e trilha no Pictograma."""
from array import array
from itertools import chain
import json
import math
import subprocess

RATE = 48000
CHANNELS = 2
RAMP = .30
SWELL = 3.5
GAP = 13.5


def pcm(ffmpeg, inputs, duration):
    command = [ffmpeg, '-v', 'error', *inputs, '-t', str(duration), '-vn',
               '-ar', str(RATE), '-ac', str(CHANNELS), '-f', 'f32le', '-']
    samples = array('f', subprocess.run(command, check=True, capture_output=True).stdout)
    count = round(duration * RATE) * CHANNELS
    samples.extend(array('f', [0]) * max(0, count - len(samples)))
    return samples[:count]


def intervals(words):
    result = []
    for row in words:
        start, end = row['inicio_s'], row['fim_s']
        if result and start <= result[-1][1] + .06:
            result[-1] = result[-1][0], max(result[-1][1], end)
        else:
            result.append((start, end))
    return result


def rms(samples, windows):
    ranges = [samples[round(a * RATE)*CHANNELS:round(b * RATE)*CHANNELS] for a, b in windows]
    size = sum(map(len, ranges))
    power = sum(value*value for value in chain.from_iterable(ranges))
    if not size or not power:
        raise ValueError('Falta sinal para medir a voz ou a trilha durante a fala.')
    return 10 * math.log10(power / size)


def ramp(time, start, end):
    ratio = min(1., max(0., (time - start) / (end - start)))
    return ratio * ratio * (3 - 2 * ratio)


def loudness(ffmpeg, path, extra=''):
    filt = 'loudnorm=I=-14:TP=-1.35:LRA=11:print_format=json' + extra
    result = subprocess.run([ffmpeg, '-hide_banner', '-nostats', '-i', str(path),
                             '-vn', '-af', filt, '-f', 'null', '-'],
                            check=True, capture_output=True, text=True).stderr
    return json.loads(result[result.rindex('{'):result.rindex('}')+1])


def prepare(ffmpeg, narration, music_input, total, words, scratch, gap=GAP):
    speech = intervals(words)
    gaps = [(a, b) for a, b in zip([0] + [end for _, end in speech],
                                    [start for start, _ in speech] + [total]) if b - a >= 2 * RAMP]
    voice = pcm(ffmpeg, ['-i', str(narration)], total)
    music = pcm(ffmpeg, music_input, total)
    fade_in, fade_out = .22, .45
    for frame in range(len(music)//CHANNELS):
        t = frame / RATE
        fade = ramp(t, 0, fade_in) * (1 - ramp(t, total - fade_out, total))
        for channel in range(CHANNELS):
            music[frame*CHANNELS+channel] *= fade
    voice_db, music_db = rms(voice, speech), rms(music, speech)
    gain_db = voice_db - music_db - gap
    gain = 10 ** (gain_db / 20)
    for index in range(len(music)):
        music[index] *= gain
    for start, end in gaps:
        for frame in range(round(start*RATE), min(len(music)//CHANNELS, round(end*RATE))):
            t = frame / RATE
            boost = SWELL * ramp(t, start, start+RAMP) * (1-ramp(t, end-RAMP, end))
            for channel in range(CHANNELS):
                music[frame*CHANNELS+channel] *= 10 ** (boost/20)
    stem_db = rms(music, speech)
    for index in range(len(voice)):
        voice[index] += music[index]
    mixed = scratch / 'mix-sem-normalizar.wav'
    final = scratch / 'mix-normalizado.wav'
    subprocess.run([ffmpeg, '-v', 'error', '-f', 'f32le', '-ar', str(RATE), '-ac', str(CHANNELS),
                    '-i', '-', '-c:a', 'pcm_f32le', str(mixed)], input=voice.tobytes(), check=True)
    pre = loudness(ffmpeg, mixed)
    gain_loudness = -14 - float(pre['input_i'])
    for _ in range(4):
        subprocess.run([ffmpeg, '-y', '-v', 'error', '-i', str(mixed), '-af',
                        f'aresample=192000,volume={gain_loudness:.4f}dB,'
                        'alimiter=limit=0.835:attack=3:release=60:level=false:latency=1,aresample=48000',
                        '-c:a', 'pcm_f32le', str(final)], check=True)
        error = -14 - float(loudness(ffmpeg, final)['input_i'])
        if abs(error) <= .10:
            break
        gain_loudness += error
    return final, {'fala_intervalos_s': speech, 'trilha_elevada_intervalos_s': gaps,
                   'trilha_elevacao_db': SWELL, 'rampa_s': RAMP, 'voz_rms_dbfs': voice_db,
                   'trilha_rms_dbfs': stem_db, 'diferenca_db': voice_db - stem_db,
                   'trilha_ganho_db': gain_db, 'ganho_master_db':gain_loudness, 'entrada_loudnorm': pre}


def verify(ffmpeg, stage, metrics):
    measured = loudness(ffmpeg, stage)
    lufs, peak = float(measured['input_i']), float(measured['input_tp'])
    metrics.update(aac_lufs=lufs, aac_pico_real_dbtp=peak)
    if not 12 <= metrics['diferenca_db'] <= 15 or abs(lufs + 14) > .5 or peak > -1:
        raise ValueError(f'Mixagem fora da faixa: {lufs:.2f} LUFS, pico {peak:.2f} dBTP.')
