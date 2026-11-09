"""Compara tags de direção com tempos observáveis da gravação."""
from statistics import median
import sys

from direcao import update_section
from pausas_audio import syllables
from ancoras import tokens
from projeto import write

PAUSE_BASE_MIN=3


def rate(row):
    duration=row['fim_s']-row['inicio_s']
    if row.get('confianca')!='alta' or duration<=0:
        return None
    return sum(syllables(w) for w,_ in tokens(row['texto']))/duration


def pause_between(previous, following):
    if previous['confianca']!='alta' or following['confianca']!='alta':
        return None
    gap=following['inicio_s']-previous['fim_s']
    return max(0,gap)


def measure(report):
    full=report['frases_completas']
    selected=report['frases']
    low=selected[0]['inicio_palavra']
    high=selected[-1]['fim_palavra']
    ordinary=[]
    for before,after in zip(full,full[1:]):
        if before['texto'].rstrip().endswith('.') and not any(
                tag['tag']=='pausa' and tag['palavra']==after['inicio_palavra'] for tag in after['tags']):
            gap=pause_between(before,after)
            if gap is not None: ordinary.append(gap)
    ordinary_median=median(ordinary) if len(ordinary)>=PAUSE_BASE_MIN else None
    findings=[]
    for i,row in enumerate(full):
        for tag in row['tags']:
            index=tag['palavra']
            if not low<=index<high:
                continue
            key=tag['tag']
            item={**tag,'paragrafo':row['paragrafo'],'frase':row['texto'],
                  'inicio_s':report['palavras'][index]['inicio_s'],'estado':'inconclusivo'}
            if key=='pausa':
                gap=pause_between(full[i-1],row) if i and index==row['inicio_palavra'] else None
                item.update(medida='pausa_s',amostras_referencia=len(ordinary),
                            valor=round(gap,4) if gap is not None else None,
                            referencia=round(ordinary_median,4) if ordinary_median is not None else None)
                if gap is not None and ordinary_median is not None:
                    threshold=max(.05,.20*ordinary_median)
                    item['tolerancia_s']=round(threshold,4)
                    item['estado']='efeito_medido' if gap-ordinary_median>=threshold else 'sem_efeito_distinto'
            elif key=='devagar':
                neighborhood=[r for r in full[max(0,i-2):i]+full[i+1:i+3]
                              if not any(t['tag']=='devagar' for t in r['tags'])]
                speeds=[v for r in neighborhood for v in [rate(r)] if v is not None]
                speed=rate(row) if index==row['inicio_palavra'] else None
                baseline=median(speeds) if len(speeds)>=2 else None
                item.update(medida='silabas_por_segundo',amostras_referencia=len(speeds),
                            valor=round(speed,3) if speed is not None else None,
                            referencia=round(baseline,3) if baseline is not None else None)
                if speed is not None and baseline is not None:
                    item['tolerancia_relativa']=.10
                    item['estado']='efeito_medido' if speed<=.90*baseline else 'sem_efeito_distinto'
            else:
                item['estado']='ouvir'
            if item['estado']=='sem_efeito_distinto':
                item['sugestao']='Se a intenção exigir efeito mais nítido, gere novamente só esta frase no ElevenLabs e compare.'
            findings.append(item)
    return {'origem_tempos':report['origem'],'identidade':report['identidade'],
            'studio_sha256':report['studio_sha256'],'inicio_s':report['inicio_s'],'fim_s':report['fim_s'],
            'efeitos':findings}


def register_effects(material, report):
    result=measure(report)
    write(material/'efeito_tags.json',result)
    lines=[]
    for entry in result['efeitos']:
        text=f'- {entry["paragrafo"]} · [{entry["tag"]}] · {entry["estado"].replace("_"," ")}'
        if entry.get('valor') is not None:
            text+=f' · medido {entry["valor"]} · referência {entry["referencia"]}'
        if entry.get('sugestao'):
            text+=' · '+entry['sugestao']
            print(f'Aviso em {entry["paragrafo"]} [{entry["tag"]}]. {entry["sugestao"]}',file=sys.stderr)
        lines.append(text)
    update_section(material/'guia_producao.md','## Efeito das tags no áudio',
                   '\n'.join(lines) or 'O intervalo alinhado não contém controles vocais.')
    return result
