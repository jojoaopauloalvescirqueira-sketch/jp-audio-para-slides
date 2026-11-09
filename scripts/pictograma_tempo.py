"""Duração de palco e descanso editorial, sem modificar a narração."""
from math import ceil


def final_frame(seconds):
    """Primeiro quadro cuja apresentação não antecede o tempo indicado."""
    return ceil(round(seconds * 30, 9))


def extend_tail(timeline, input_duration, speech_end, tail):
    end = final_frame(max(input_duration, speech_end + tail)) / 30
    timeline[-1]['fim'] = end
    return end


DURATIONS = {'aparecer':8,'sumir':7,'sentar':14,'levantar':12,'andar':18,'andar_ate':18,
             'destacar':10,'mudar_cor':10,'desenhar':11,'desenhar_linha':11,'trocar_letra':11,
             'anotar':7,'apontar':12,'ajudar_a_levantar':15,'abracar':16,'entregar':15,'contar':20}


def animate_windows(scenes, words, tone):
    scale={'sobrio':1.3,'didatico':1,'energetico':.78}[tone]
    last=0
    for scene in scenes:
        boundary=final_frame(scene['inicio'])
        for event in scene['acoes']:
            frame=words[event['palavra']]['quadro']
            mode=event.get('pousar','inicio')
            steps=max(6,round(DURATIONS[event['acao']]*scale)) if event['acao'] in DURATIONS else 0
            if mode=='pico' and steps and frame<=boundary:
                raise ValueError(f'{event["alvo"]}: o pico precisa de espaço antes da âncora.')
            anticipation=event.get('antecipacao_quadros',3)
            start=frame if mode=='inicio' or not steps else max(boundary,frame-anticipation)
            finish=max(start+steps,frame) if mode=='pico' else start+steps
            if 'palavra_fim' in event:
                finish=words[event['palavra_fim']]['quadro']
                if finish-start<6 or finish<frame:
                    raise ValueError(f'{event["alvo"]}: reserve pelo menos seis quadros para o movimento.')
            event.update(inicio_movimento=start/30,fim_movimento=finish/30,
                         pouso_render=frame/30,quadro_alvo=frame)
            last=max(last,finish)
    return last/30
