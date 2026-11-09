"""Mede mudanças de luminância no palco, acima da área de legenda."""
import subprocess
from math import isfinite


def measure(ffmpeg, inputs, active, expected):
    width, height = 216, 384
    command = [ffmpeg, '-v', 'error', *inputs, '-map', '0:v:0', '-an',
               '-vf', f'scale={width}:{height}:flags=area,format=gray',
               '-pix_fmt', 'gray', '-f', 'rawvideo', '-']
    stats = {key: {'comparacoes': 0, 'mudancas': 0, 'pausa_maxima_quadros': 0}
             for key in ('ativo', 'cauda')}
    count = run = 0
    prior = None
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
        while True:
            frame = process.stdout.read(width * height)
            if not frame:
                break
            if len(frame) != width * height:
                raise ValueError('A auditoria de pixels recebeu um quadro incompleto.')
            current = frame[width * 68:width * 267]
            if count == active:
                run = 0
            if prior is not None:
                target = stats['ativo' if count < active else 'cauda']
                changed = sum(abs(a - b) >= 5 for a, b in zip(prior, current))
                moves = changed >= 24
                target['comparacoes'] += 1
                target['mudancas'] += int(moves)
                run = 0 if moves else run + 1
                target['pausa_maxima_quadros'] = max(run, target['pausa_maxima_quadros'])
            prior = current
            count += 1
        if process.wait() or count != expected:
            raise ValueError(f'A auditoria esperava {expected} quadros e decodificou {count}.')
    for row in stats.values():
        row['fracao'] = row['mudancas'] / max(1, row['comparacoes'])
        row['pausa_maxima_s'] = row['pausa_maxima_quadros'] / 30
    return {'quadros': count, 'resolucao_analise': [width, height],
            'faixa_y_analisada': [68, 267], 'delta_luminancia_minimo': 5,
            'pixels_minimos': 24, **stats}


def check(report, key, stats):
    report.setdefault('pixels', {})[key] = stats
    if (stats['ativo']['fracao'] < .85 or stats['ativo']['pausa_maxima_quadros'] > 24
            or stats['cauda']['mudancas'] < 1):
        report['issues'].append(dict(codigo='densidade_pixels_' + key, nivel='bloqueante',
                                     quadro=0, elemento='palco',
                                     correcao='Distribua movimento visível no trecho ativo e na cauda.'))


def validar_ponte_titulo(levels):
    """Valida a rampa da luminância sobre as letras da cartela decodificada."""
    if len(levels)<10 or not all(isfinite(level) for level in levels):
        raise ValueError('EC-105 · Meça a transição inteira da cartela.')
    steps=[b-a for a,b in zip(levels,levels[1:])]
    if min(steps)<-4 or max(steps)>22 or levels[-1]-levels[0]<75:
        raise ValueError('EC-105 · A cartela precisa ganhar contraste sem um salto de luminância.')
    return max(steps)


def validar_revelacao_figura(levels):
    """Confere a revelação no recorte ocupado pela figura, longe da legenda."""
    if len(levels)<10 or not all(isfinite(level) for level in levels):
        raise ValueError('EC-116 · Meça a revelação inteira.')
    steps=[b-a for a,b in zip(levels,levels[1:])]
    if min(steps)<-5 or max(steps)>32 or levels[-1]-levels[0]<100:
        raise ValueError('EC-116 · A figura deve surgir gradualmente antes da aproximação.')
    return max(steps)
