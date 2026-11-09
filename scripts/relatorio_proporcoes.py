"""Apresenta as medições de contorno e juntas no relatório de auditoria."""
from collections import defaultdict
from html import escape
import os
from statistics import median

from projeto import write


def section(material, output, proportions):
    rows = proportions['medicoes']
    by_pose, by_actor = defaultdict(list), defaultdict(list)
    for row in rows:
        by_pose[row['id'], row['pose']].append(row)
        by_actor[row['id']].append(row)
    summaries = []
    for (actor, pose), items in by_pose.items():
        fields = {'altura_contorno_px': 'altura_px', 'altura_em_cabecas': 'cabecas',
                  'altura_relativa': 'altura_relativa', 'pernas_relativo': 'pernas',
                  'tronco_relativo': 'tronco', 'escala': 'escala'}
        values = {key: median(row[src] for row in items) for src, key in fields.items()}
        summaries.append({'personagem': actor, 'pose': pose, 'quadros': len(items), **values})
    write(material/'auditoria_proporcoes.json', {**proportions, 'resumo_por_pose': summaries})
    summaries_html = ''.join(
        f'<tr><td>{escape(row["personagem"])}</td><td>{escape(row["pose"])}</td>'
        f'<td>{row["quadros"]}</td><td>{row["altura_px"]:.1f}</td><td>{row["cabecas"]:.2f}</td>'
        f'<td>{row["altura_relativa"]:.1%}</td><td>{row["pernas"]:.1%}</td>'
        f'<td>{row["tronco"]:.1%}</td><td>{row["escala"]:.1f}</td></tr>'
        for row in summaries)
    maximum_frame = max((row['quadro'] for row in rows), default=1)
    height_max = max((row['altura_contorno_px'] for row in rows), default=1)
    graph = []
    for (actor, items), color in zip(by_actor.items(), ('#ECE6D8', '#9CC6A6', '#B6C89B')):
        points = ' '.join(f'{30+810*row["quadro"]/max(1,maximum_frame):.1f},'
                          f'{245-204*row["altura_contorno_px"]/height_max:.1f}' for row in items)
        graph.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{points}">'
                     f'<title>{escape(actor)}</title></polyline>')
    models = material/'modelo_pictograma'/'folha-de-modelo.png'
    model_link = escape(os.path.relpath(models, output), quote=True)
    failed = ', '.join(str(frame) for frame in sorted({x['quadro'] for x in proportions['quadros_reprovados']}))
    return f'''<h2>Proporções e luz</h2><p><a href="{model_link}">Folha de modelo</a>.
Altura do contorno rastreada em pixels ao longo do tempo. Escala desconta o zoom de câmera.</p>
<svg viewBox="0 0 875 265" width="875" style="max-width:100%" role="img" aria-label="Altura por quadro">
<path d="M30 34V245H840" fill="none" stroke="#53685d"/>{''.join(graph)}</svg>
<table><thead><tr><th>Figura</th><th>Pose</th><th>Quadros</th><th>Altura px</th><th>Cabeças</th><th>Altura relativa</th>
<th>Quadril ao chão</th><th>Tronco</th><th>Escala px</th></tr></thead><tbody>{summaries_html}</tbody></table>
<p>Quadros com bloqueios. {failed or 'Nenhum.'}</p>'''
