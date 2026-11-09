"""Orquestra auditoria do palco, relatório e inspeção do vídeo temporário."""
from html import escape
from pathlib import Path
import subprocess

from catalogo_erros import resumo
from projeto import FORMATS, read, sha, write


def inspect_preview(root, preview, fmt, node, integral=False):
    material = root / 'material'
    width, height = FORMATS[fmt]
    output = preview.parent
    script = Path(__file__).with_suffix('.mjs')
    subprocess.run([node, str(script), str(preview), str(output), str(width), str(height),
                    'integral' if integral else 'amostrada'], check=True)
    report = read(output / 'auditoria-dom.json')
    if 'gestos_amostras' in report:
        from pictograma_gestos import auditar_gestos
        samples = report.pop('gestos_amostras')
        before = None
        issues = {}
        for sample in samples:
            for issue in auditar_gestos(sample, before if before and sample['f']==before['f']+1 else None):
                key = (issue['cena'], issue['elemento'], issue['correcao'])
                issues.setdefault(key, issue)
            before = sample
        report['issues'].extend(issues.values())
        report.setdefault('checagens_catalogo', {})['EC-099']={'quadros':len(samples),'falhas':len(issues)}
    report['identidade'] = {'previa_sha256':sha(preview), 'formato':fmt}
    write_report(material, output, report)
    return report


def write_report(material, output, report):
    checks = report.setdefault('catalogo_evidencias', {})
    if report['modo'] == 'integral' and report['sampled'] == report['quadros_totais']:
        checks['EC-033'] = 'conferido'
    if report.get('pixels', {}).keys() >= {'mp4', 'png'}:
        checks['EC-031'] = 'conferido'
    if report.get('mixagem', {}).get('aac_lufs') is not None:
        checks['EC-036'] = 'conferido'
    report['catalogo'] = resumo(report)
    write(material / 'auditoria_animacao.json', report)
    flags = ''.join(f'<li>{escape(row["nivel"])} · quadro {row["quadro"]} · '
                    f'{escape(row["elemento"])} · {escape(row["correcao"])}</li>' for row in report['issues'])
    bars = ''.join(f'<li>{int(second)} s <meter min="0" max="1" '
                   f'value="{row["movimento"]/row["quadros"]}"></meter></li>'
                   for second,row in report['perSecond'].items())
    pictures = ''.join(f'<figure><img src="{escape(row["arquivo"], quote=True)}" loading="lazy" '
                       f'alt="Quadro {row["quadro"]}"><figcaption>Quadro {row["quadro"]} · '
                       f'{row["quadro"]/30:.2f} s</figcaption></figure>' for row in report['tiras'])
    pixels = ''.join(f'<li>{escape(name)} · {row["ativo"]["fracao"]:.1%} no trecho ativo · '
                     f'pausa máxima {row["ativo"]["pausa_maxima_s"]:.2f} s · '
                     f'{row["cauda"]["fracao"]:.1%} na cauda</li>'
                     for name,row in report.get('pixels',{}).items())
    status = 'Prévia estimada' if report['estimated'] else 'Tempos medidos'
    metrics = ''.join(f'<li>{escape(scene)} · {data["movimento"]:.1%} com movimento · '
                      f'{data["pausa_maxima_s"]:.2f} s de pausa máxima · {data["elementos"]} elementos</li>'
                      for scene,data in report['metrics'].items())
    proportions = ''
    if 'proporcoes' in report:
        from relatorio_proporcoes import section
        proportions = section(material, output, report['proporcoes'])
    known = ''.join(f'<li>{row["id"]} · {escape(row["titulo"])} · {row["resultado"]}</li>'
                    for row in report['catalogo'])
    effect_rows = []
    for key, value in report.get('auditoria_efeitos',{}).items():
        combined = value['flash']
        row = (f'{escape(key)} · {value["sombra_propria"]["amostras"]} amostras de sombra própria · '
               f'{value["sombra_contato"]["amostras"]} de contato · '
               f'cena completa {combined["gerais"]} gerais e {combined["vermelhos"]} vermelhos/s')
        if 'flash_so_efeitos' in value:
            effect = value['flash_so_efeitos']
            movement = value['flash_sem_efeitos']
            row += (f' · só efeitos {effect["gerais"]} gerais e {effect["vermelhos"]} vermelhos/s'
                    f' · sem efeitos {movement["gerais"]} gerais e {movement["vermelhos"]} vermelhos/s')
        peak = value.get('escurecimento',{}).get('na_palavra')
        if peak:
            row += f' · redução de luminância no quadro {peak["quadro"]} de {peak["reducao"]:.2%}'
        effect_rows.append(f'<li>{row}.</li>')
    effects = ''.join(effect_rows)
    effects_section = f'<h2>Luz e efeitos nos pixels</h2><ul>{effects}</ul>' if effects else ''
    video = report.get('video')
    post = f'<p>MP4 temporário decodificado · {video["quadros"]} quadros.</p>' if video else ''
    (output/'auditoria.html').write_text(f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8">
<title>Auditoria de animação</title><style>body{{background:#121715;color:#ece6d8;font:16px system-ui;margin:2rem}}
section{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:1rem}}
figure{{margin:0}}img{{width:100%;display:block}}meter{{width:12rem}}</style>
<h1>Auditoria de animação</h1><p>{status} · auditoria {report["modo"]} · {report["sampled"]}/{report["quadros_totais"]} quadros</p>{post}
{proportions}{effects_section}<h2>Catálogo de erros conhecidos</h2><ul>{known}</ul><h2>Densidade em pixels</h2><ul>{pixels}</ul><h2>Cenas</h2><ul>{metrics}</ul><h2>Ocorrências</h2><ul>{flags or '<li>Sem ocorrências.</li>'}</ul>
<h2>Movimento por segundo</h2><ul>{bars}</ul><h2>Tiras de revisão</h2><section>{pictures}</section>''', encoding='utf-8')


def require_pass(report):
    blockers = [row for row in report['issues'] if row['nivel']=='bloqueante']
    if blockers:
        codes=', '.join(sorted({row['codigo'] for row in blockers}))
        raise ValueError(f'A auditoria encontrou {len(blockers)} bloqueantes ({codes}). Consulte auditoria.html.')


def verify_encoded(path, ffmpeg, report, material, output):
    width, height = 216, 384
    size = width * height
    command = [ffmpeg,'-v','error','-i',str(path),'-map','0:v:0','-an',
               '-vf',f'scale={width}:{height}:flags=area,format=gray','-f','rawvideo','-']
    prior=before=None
    index=frozen=longest=0
    flash=[]
    freeze_limit = sum(scene['quadros'] for scene in report['metrics'].values())
    dense = all(scene['movimento']>=.85 and scene['elementos']>=3 for scene in report['metrics'].values())
    with subprocess.Popen(command,stdout=subprocess.PIPE) as process:
        while True:
            frame=process.stdout.read(size)
            if not frame:
                break
            if len(frame)!=size:
                raise ValueError('Quadro decodificado incompleto.')
            if index<freeze_limit:
                # The center excludes the progress bar and the caption baseline.
                current=frame[height*23//100*width:height*69//100*width]
                if prior is not None:
                    changed=sum(abs(a-b)>2 for a,b in zip(prior,current))
                    frozen=frozen+1 if changed<6 else 0
                    longest=max(longest,frozen)
                    if before is not None and changed>len(current)*.05:
                        jump=sum(abs(a-b)>2 for a,b in zip(before,current))
                        if jump<changed*.04:
                            flash.append(index-1)
                before,prior=prior,current
            index+=1
        if process.wait() or not index:
            raise ValueError('A auditoria não conseguiu decodificar o MP4.')
    if dense and longest>24:
        report['issues'].append(dict(codigo='mp4_congelado',nivel='bloqueante',quadro=0,elemento='palco',
                                     correcao='Aumente o movimento visível nos quadros codificados.'))
    for frame in flash:
        report['issues'].append(dict(codigo='mp4_cintilacao',nivel='bloqueante',quadro=frame,elemento='palco',
                                     correcao='Remova o quadro isolado de alto contraste.'))
    if report.get('criterios_artisticos'):
        from pictograma_pixels import check, measure
        check(report, 'mp4', measure(ffmpeg, ['-i', str(path)], report['quadros_ativos'], report['quadros_totais']))
    report['video']={'quadros':index,'pausa_maxima_s':longest/30,'cintilacoes':flash}
    write_report(material,output,report)
    require_pass(report)
