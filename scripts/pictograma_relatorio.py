"""Interface da forma de onda e relatório navegável de sincronia."""
from html import escape
from pathlib import Path


def editor():
    script=(Path(__file__).resolve().parents[1]/'assets/pictograma-editor.js').read_text(encoding='utf-8')
    return '''<fieldset id="editor-sincronia"><legend>Editar sincronia</legend>
<canvas id="onda-sincronia" width="396" height="76" style="max-width:100%" aria-label="Forma de onda"></canvas>
<label>Palavra <select id="ancora-sincronia"></select></label><output id="quadro-sincronia"></output>
<p>Use ← ou → para deslocar um quadro. Reimporte o JSON para atualizar o vídeo.</p>
<button id="ancora-menos" type="button">−1 quadro</button><button id="ancora-mais" type="button">+1 quadro</button>
<button id="baixar-sincronia" type="button">Baixar ajustes</button></fieldset><script>'''+script+'</script>'


def sync_report(path, sync, scenes, estimated, choreography=None):
    width=1080
    duration=max(.01,sync['duracao_s'])
    positions=' '.join(f'{width*i/max(1,len(sync["onda"])-1):.2f},{60-50*value:.2f}'
                       for i,value in enumerate(sync['onda']))
    markers=''.join(f'<line x1="{x:.2f}" x2="{x:.2f}" y1="5" y2="115" stroke="#9CC6A6" opacity=".65"/>'
                    for row in sync['palavras'] for x in (width*row['quadro']/30/duration,))
    words=''.join(f'<tr><td>{escape(row["texto"])}</td><td>{row["inicio_s"]:.3f}</td>'
                  f'<td>{row["fim_s"]:.3f}</td><td>{row["quadro"]}</td><td>{escape(row["metodo"])}</td>'
                  f'<td>{escape(", ".join(row["motivos_revisao"]))}</td></tr>' for row in sync['palavras'])
    events=''.join(f'<tr><td>{escape(scene["id"])}</td><td>{escape(row["alvo"])}</td><td>{escape(row["acao"])}</td>'
                   f'<td>{escape(row["em"]["trecho"])}</td><td>{row["quadro_alvo"]}</td>'
                   f'<td>{row["inicio_movimento"]:.3f}–{row["fim_movimento"]:.3f}</td></tr>'
                   for scene in scenes for row in scene['acoes'])
    if choreography:
        for name, cue in choreography['cues'].items():
            anchor=escape(sync['palavras'][cue['word']]['texto'])
            events += (f'<tr><td>{escape(cue["scene"])}</td><td>Coreografia</td><td>{escape(name)}</td>'
                       f'<td>{anchor}</td><td>{cue["frame"]}</td>'
                       f'<td>{cue["start"]/30:.3f}–{cue["end"]/30:.3f}</td></tr>')
    label='Tempos estimados · 140 palavras/min · sem narração' if estimated else 'Tempos alinhados à gravação fornecida'
    notes=''
    if any(row['metodo']=='ancora_frase_srt' for row in sync['palavras']):
        notes=('<p>O SRT forneceu os intervalos de frase. Dentro de cada frase, os inícios das palavras '
               'foram estimados por ataques e vales de energia em quatro bandas, com janela de 20 ms '
               'e passo de 5 ms. Energia baixa indica fronteira pouco distinguível. '
               'A coluna Quadro indica onde a palavra entra na legenda a 30 fps.</p>')
    path.write_text(f'''<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Sincronia do Pictograma</title>
<style>body{{font:16px system-ui;background:#121715;color:#ece6d8;margin:2rem}}table{{border-collapse:collapse}}
td,th{{padding:.55rem;border-bottom:1px solid #52705e;text-align:left}}svg{{max-width:100%}}</style>
<h1>Sincronia do Pictograma</h1><p>{label}</p>{notes}
<svg viewBox="0 0 {width} 120" width="{width}" role="img" aria-label="Forma de onda e âncoras">
<polyline points="{positions}" fill="none" stroke="#52705E" stroke-width="2"/>{markers}</svg>
<h2>Palavras</h2><table><thead><tr><th>Palavra</th><th>Início em s</th><th>Fim em s</th><th>Quadro</th><th>Método</th><th>Revisão</th></tr></thead>
<tbody>{words}</tbody></table>
<h2>Pousos</h2><table><thead><tr><th>Cena</th><th>Elemento</th><th>Ação</th><th>Âncora</th><th>Quadro</th><th>Janela em s</th></tr></thead>
<tbody>{events}</tbody></table></html>''',encoding='utf-8')
