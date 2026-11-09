"""Audita a ação visível, separando câmera e respiração da atuação."""
from collections import defaultdict, deque
from math import cos, hypot, radians, sqrt
from pathlib import Path
import subprocess

from projeto import read

RELATIONS = {'segurado', 'olhado', 'entregue', 'carregado', 'apoiado'}
DENSITY = .85
BODY_JOINTS = ('pelve','lombar','toracica','cervical','cabeca','quadril','joelho','tornozelo','calcanhar','planta','ponta')


def directional_change(prior, actor, body_only=False):
    threshold=cos(radians(3))
    if 'joints' not in actor or 'joints' not in prior:
        return False
    now,then=actor['joints'],prior['joints']
    for bone in actor.get('bones',()):
        a,b=bone['inicio'],bone['fim']
        if body_only and not b.startswith(BODY_JOINTS):
            continue
        if not all(joint in row for joint in (a,b) for row in (now,then)):
            continue
        u=[v-w for v,w in zip(now[b],now[a])]
        z=[v-w for v,w in zip(then[b],then[a])]
        scale=sqrt(sum(v*v for v in u)*sum(v*v for v in z))
        if scale and sum(v*w for v,w in zip(u,z))<threshold*scale:
            return True
    return False


def pose_changes(poses, active, body_only=False):
    changed = {}
    previous = {}
    count = total = rest = 0
    for frame in poses[:active]:
        actors = {actor['id']:actor for actor in frame['actors']}
        moves = set()
        for name, actor in actors.items():
            total += 1
            rest += actor['mode'] == 'repouso'
            prior = previous.get(name)
            angles=actor['angles']
            old_angles=prior['angles'] if prior else {}
            turn=any(abs((angles[joint]-old_angles[joint]+180)%360-180)>3
                     for joint in angles.keys() & old_angles.keys()
                     if not body_only or joint.startswith(BODY_JOINTS))
            if prior and not frame.get('cut') and (turn or directional_change(prior,actor,body_only)):
                moves.add(name)
        changed[frame['f']] = moves
        count += len(moves)
        previous = actors
    return {'quadros_de_ator':total,'quadros_em_acao':count,'fracao':count/max(1,total),
            'repouso':rest/max(1,total)}, changed


def beat_coverage(scenes, body_scenes=None):
    from pictograma_composicao import ACTIONS
    count = pauses = 0
    issues = []
    for i, scene in enumerate(scenes):
        action = scene.get('movimento') or {}
        pause = scene.get('pausa')
        if pause:
            pauses += 1
            if (not isinstance(pause,str) or not pause.strip() or scene['fim']-scene['inicio']>1.5
                    or any(row.get('pausa') for row in scenes[max(0,i-3):i])):
                issues.append(i)
        elif action.get('tipo') in ACTIONS and (body_scenes is None or scene['id'] in body_scenes):
            count += 1
    total = len(scenes)-pauses
    return {'com_acao':count,'total':total,'pausas':pauses,'pausas_invalidas':issues,
            'fracao':count/max(1,total)}


def unproject(box, matrix):
    x,y,r,b=box
    sx,sy,tx,ty=matrix
    return ((x-tx)/sx,(y-ty)/sy,(r-tx)/sx,(b-ty)/sy)


def center(box):
    return ((box[0]+box[2])/2,(box[1]+box[3])/2)


def layout_and_objects(stage, poses):
    frames=defaultdict(list)
    failures={}
    abstracts=set()
    for frame, pose in zip(stage, poses):
        if pose['actors']:
            frames[frame['scene']].append((frame,pose))
        matrix=frame['matrix']
        heads={str(a['id']):a['head'][3]-a['head'][1] for a in pose['actors'] if a.get('head')}
        if not heads:
            continue
        for item in frame['objects']:
            x,y,r,b=item['box']
            if r<=x or b<=y:
                continue
            key=(frame['scene'],item['id'])
            if item.get('abstract'):
                abstracts.add(key)
                continue
            bound=heads.get(str(item['actor']),next(iter(heads.values())))
            if (str(item['actor']) not in heads or item['relation'] not in RELATIONS
                    or b-y<bound*.99):
                failures.setdefault(key,{'quadro':frame['f'],'cena':frame['scene'],
                                         'objeto':item['id'],'altura_px':round(b-y,1),
                                         'cabeca_px':round(bound,1),'relacao':item['relation']})
    repeated=[]
    mold=[]
    prior=None
    run=[]
    for scene, samples in frames.items():
        frame,pose=samples[len(samples)//2]
        obj=frame['objects']
        names=(pose['actors'][0]['box'],frame['titles'][0] if frame['titles'] else None,
               obj[0]['box'] if obj else None)
        cells=tuple(center(unproject(box,frame['matrix'])) if box else None for box in names)
        actor_box,title_box,object_box=cells
        if (title_box and object_box and actor_box[0]>580 and title_box[1]<560
                and object_box[0]<actor_box[0]-140
                and all(actors['actors'][0]['mode']=='repouso' for _,actors in samples
                        if 'mode' in actors['actors'][0])):
            mold.append(scene)
            if len(mold)>1:
                repeated.append({'cenas':list(mold),'quadro':samples[0][0]['f'],'molde_antigo':True})
        def close(a,b):
            return (a is None and b is None) or (a is not None and b is not None
                                                and abs(a[0]-b[0])<=95 and abs(a[1]-b[1])<=150)
        if prior is not None and all(close(a,b) for a,b in zip(prior,cells)):
            run.append(scene)
            if len(run)>2:
                repeated.append({'cenas':list(run),'quadro':samples[0][0]['f']})
        else:
            prior=cells
            run=[scene]
    return repeated,list(failures.values()),len(abstracts)


def changed_pixels(old,new,old_matrix,new_matrix,box,width=216,height=384):
    # Amostra os mesmos pontos do mundo nos dois quadros do MP4 decodificado.
    x,y,r,b=box
    def index(u,v,m):
        sx,sy,tx,ty=m
        return round((u*sx+tx)/5),round((v*sy+ty)/5)
    count=0
    for v in range(max(0,round(y)),min(1920,round(b)),10):
        for u in range(max(0,round(x)),min(1080,round(r)),10):
            i,j=index(u,v,old_matrix)
            k,l=index(u,v,new_matrix)
            if not (0<=i<width and 0<=k<width and 0<=j<height and 0<=l<height):
                continue
            before,after=old[j*width+i],new[l*width+k]
            if max(before,after)>=95 and abs(before-after)>=14:
                count+=1
                if count>=4:
                    return True
    return False


def motion_pixels(ffmpeg, video, stage, poses, changes, active):
    width,height=216,384
    command=[ffmpeg,'-v','error','-i',str(video),'-an','-vf','scale=216:384:flags=area,format=gray',
             '-pix_fmt','gray','-f','rawvideo','-']
    motion=compared=0
    history=deque(maxlen=15)
    with subprocess.Popen(command,stdout=subprocess.PIPE) as proc:
        for f, (frame,pose) in enumerate(zip(stage,poses)):
            current=proc.stdout.read(width*height)
            if len(current)!=width*height:
                raise ValueError('MP4 não corresponde à geometria de encenação.')
            if history and f<active:
                previous,old,old_actors=history[0]
                cut=frame['scene']!=old['scene']
                recent={actor for i in range(old['f']+1,f+1) for actor in changes.get(i,())}
                now=frame['matrix']; before=old['matrix']
                moved=[]
                for actor in pose['actors']:
                    old_box=old_actors.get(actor['id'])
                    if not old_box:
                        continue
                    box=unproject(actor['box'],now)
                    former=unproject(old_box,before)
                    travel=hypot(*(a-b for a,b in zip(center(box),center(former))))
                    if actor['id'] in recent or travel>4:
                        moved.append(box)
                old_objects={o['id']:unproject(o['box'],before) for o in old['objects']}
                for obj in frame['objects']:
                    if not (obj['relation'] in RELATIONS and obj['id'] in old_objects):
                        continue
                    box=unproject(obj['box'],now)
                    former=old_objects[obj['id']]
                    if max(abs(a-b) for a,b in zip(box,former))>2:
                        moved.append(box)
                compared+=1
                motion+=not cut and any(changed_pixels(previous,current,before,now,box) for box in moved)
            if history and frame['scene']!=history[-1][1]['scene']:
                history.clear()
            history.append((current,frame,{a['id']:a['box'] for a in pose['actors']}))
        if proc.stdout.read(1) or proc.wait():
            raise ValueError('Número de quadros diferente no MP4 de encenação.')
    return {'comparacoes':compared,'mudancas':motion,'fracao':motion/max(1,compared),'janela_s':.5}


def analyze(poses, stage, ffmpeg, video, active=None, reference=False):
    frames=stage['frames']
    if len(poses)!=len(frames) or any(p['f']!=s['f'] for p,s in zip(poses,frames)):
        raise ValueError('A geometria e as poses precisam cobrir os mesmos quadros.')
    active=min(active if active is not None else stage['active'],len(frames))
    actor,changes=pose_changes(poses,active)
    body,body_frames=pose_changes(poses,active,body_only=True)
    body_scenes={row['scene'] for row in frames[:active] if body_frames.get(row['f'])}
    beats=beat_coverage(stage['scenes'],body_scenes) if not reference else None
    labels=[{'quadro':row['f'],'cena':row['scene'],'rotulos':row['labelOcclusion']}
            for row in frames if row.get('labelOcclusion')]
    repeated,objects,abstract=layout_and_objects(frames,poses)
    pixel=motion_pixels(ffmpeg,video,frames,poses,changes,active)
    flags={}
    if body['fracao']<.25: flags['EC-095']='Corpo em ação abaixo de 25%, sem contar os braços.'
    if labels: flags['EC-096']='Rótulo encoberto pela figura ou cortado no palco.'
    if actor['fracao']<.30: flags['EC-087']='Pose em ação abaixo de 30%.'
    if beats and (beats['fracao']<.80 or beats['pausas_invalidas']):
        flags['EC-088']='Batidas com ação abaixo de 80% ou pausa fora do contrato.'
    if repeated: flags['EC-089']='O layout se repete em mais de duas batidas seguidas.'
    if objects or abstract>1: flags['EC-090']='Objeto solto, menor que uma cabeça ou excesso de exceções.'
    if pixel['fracao']<DENSITY: flags['EC-091']='Movimento significativo abaixo de 85%.'
    return {'pose':actor,'corpo':body,'rotulos_encobertos':labels,'batidas':beats,'layouts_repetidos':repeated,'objetos_invalidos':objects,
            'abstratos':abstract,'pixels_acao':pixel,'bloqueios':flags}


def measure_stage(node, preview, path):
    subprocess.run([node,str(Path(__file__).with_name('medir_encenacao.mjs')),str(preview),str(path)],check=True)
    return read(path)


def calibrate(ratings, pose):
    if not pose or pose['repouso']<=.5:
        return ratings
    capped={'clareza_sem_som','causa_e_efeito','proporcao_e_naturalidade'}
    return {key:min(value,2) if key in capped else value for key,value in ratings.items()}


def append_report(report,result):
    report['encenacao']=result
    checks=report.setdefault('checagens_catalogo',{})
    for code in ('EC-087','EC-088','EC-089','EC-090','EC-091','EC-095','EC-096'):
        reason=result['bloqueios'].get(code)
        checks[code]={'quadros':report['quadros_totais'],'falhas':int(bool(reason))}
        if reason:
            frames={'EC-089':result['layouts_repetidos'],'EC-090':result['objetos_invalidos'],
                    'EC-096':result['rotulos_encobertos']}.get(code,[])
            report['issues'].append({'codigo':code,'nivel':'bloqueante','elemento':'encenação',
                                     'quadro':frames[0]['quadro'] if frames else 0,'correcao':reason})
