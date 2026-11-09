"""Confere solas e contornos nos pixels RGB do MP4 decodificado."""
import math
import subprocess


def bench_issue(row):
    return [{'quadro':row['f'],'codigo':'sola_cruza_banco',**overlap}
            for overlap in row.get('banco',()) if overlap['pixels']>3]


def audit(ffmpeg, video, data):
    import numpy as np

    width, top, height = 1080, 414, 916
    frames = data['frames']
    reference_scale = data['rig']['apoio']['pix_por_cabeca']
    threshold = data['rig']['apoio']['deriva_px']
    issues, observations, contacts = [], [], {}
    visible_overlaps = []
    mask_checks = 0
    max_height = max_drift = 0
    format_args = ['-v','error','-i',str(video),'-map','0:v:0','-an','-vf',
                   f'crop={width}:{height}:0:{top}', '-f','rawvideo','-pix_fmt','rgb24','-']

    def rgb(code):
        return [int(code[i:i+2],16) for i in (1,3,5)]


    def classify(pixels):
        delta = pixels.astype(np.int16)[...,None,:]-colors
        distance = np.sum(delta.astype(np.int32)**2,axis=-1)
        selected = np.argmin(distance,axis=-1)
        best = np.take_along_axis(distance,selected[...,None],axis=-1)[...,0]
        return np.where(best<=26**2,selected,-1)

    def issue(frame, code, **extra):
        issues.append({'quadro':frame,'codigo':code,**extra})

    frame_bytes=width*height*3
    with subprocess.Popen([ffmpeg,*format_args],stdout=subprocess.PIPE) as decoder:
        for row in frames:
            raw=decoder.stdout.read(frame_bytes)
            if len(raw)!=frame_bytes:
                raise ValueError(f'MP4 incompleto no quadro {row["f"]}.')
            f=row['f']
            issues.extend(bench_issue(row))
            seat=row.get('assento_duplo')
            if seat and seat['falha']:
                issue(f,'quadril_fora_do_assento_duplo',apoios=seat['apoios'])
            if row.get('cut'):
                contacts.clear()
            if not row['actors']:
                continue
            inks={foot['ink']:actor['id'] for actor in row['actors'] for foot in actor['feet']}
            palette=list(inks)
            colors=np.asarray([rgb(code) for code in palette],dtype=np.int16)
            actor_types=np.asarray(list(inks.values()),dtype=int)
            pixels=np.frombuffer(raw,dtype=np.uint8).reshape(height,width,3)
            x0,x1,y,stroke=row['floor']
            hint=round(y)-top
            x0=max(0,math.ceil(x0)+3)
            x1=min(width,math.floor(x1)-3)
            stripe=pixels[hint-3:hint+4,x0:x1].astype(np.int16)
            similarity=np.sum(np.max(np.abs(stripe-rgb(stroke)),axis=-1)<=12,axis=-1)
            if similarity.max()<25:
                issue(f,'chao_sem_evidencia_no_mp4')
                continue
            # Brightest matching row establishes the decoded floor reference.
            floor=hint-3+int(np.argmax(similarity))
            live=set()
            for actor in row['actors']:
                for foot in actor['feet']:
                    phase=foot['phase']
                    if phase=='livre':
                        continue
                    key=(actor['id'],foot['side'],phase)
                    live.add(key)
                    l,t,r,b=foot['box']
                    l=max(0,math.floor(l)-4); r=min(width,math.ceil(r)+4)
                    t=max(0,math.floor(t)-top-4); b=min(height,math.ceil(b)-top+5)
                    ink=palette.index(foot['ink'])
                    expected=np.asarray(foot['template'],dtype=int)
                    if len(expected)<10:
                        issue(f,'sola_oculta_ou_sem_pixels',ator=actor['id'],lado=foot['side'])
                        continue
                    bx,by=expected.min(axis=0)-4
                    ex,ey=expected.max(axis=0)+5
                    if bx<0 or ex>width or by<top or ey>top+height:
                        issue(f,'sola_fora_da_amostra',ator=actor['id'],lado=foot['side'])
                        continue
                    chunk=classify(pixels[by-top:ey-top,bx:ex])==ink
                    xx,yy=(expected-[bx,by]).T
                    # A silhueta visível é recalculada para cada ângulo. A diferença
                    # medida vem do contorno de cor no H.264 decodificado.
                    border=(xx==xx.min()) | (xx==xx.max()) | (yy==yy.max())
                    def score(dx,dy):
                        actual=chunk[yy+dy,xx+dx]
                        # Penaliza deslocamentos que invadem o fundo ou escondem uma borda.
                        return (int(actual.sum())+int(actual[border].sum())*.6
                                -.48*(abs(dx)+abs(dy)))
                    dx,dy=max(((x,y) for x in range(-3,4) for y in range(-3,4)),
                              key=lambda xy:score(*xy))
                    agrees=float(chunk[yy+dy,xx+dx].mean())
                    if agrees<.60:
                        issue(f,'sola_oculta_ou_sem_pixels',ator=actor['id'],lado=foot['side'],
                              concordancia=round(agrees,3))
                    # A altura é aferida independentemente do ajuste horizontal:
                    # procura a última faixa contínua da tinta na região do apoio.
                    # Isso rejeita um único pixel de artefato do croma.
                    lower=yy>=yy.max()-4
                    left=max(0,int(xx[lower].min()+dx-2))
                    right=min(chunk.shape[1],int(xx[lower].max()+dx+3))
                    band=chunk[:,left:right]
                    spans=band[:,:-2]&band[:,1:-1]&band[:,2:]
                    found=np.flatnonzero(spans.any(axis=1))
                    bottom=by+int(found.max())-top if len(found) else floor-99
                    x=foot['anchor'][0]+dx
                    scale_x,_,translation,_=foot['transform']
                    world=(x-translation)/scale_x
                    initial=contacts.setdefault(key,world)
                    projected_drift=float(abs(initial-world)*reference_scale)
                    # O registro do contorno trabalha em pixels inteiros: a escala
                    # inversa da câmera não acrescenta resolução ao vídeo decodificado.
                    drift=int(math.floor(projected_drift+.5))
                    delta=float(abs(bottom-floor))
                    max_drift=max(max_drift,drift)
                    max_height=max(max_height,delta)
                    obs={'quadro':f,'ator':actor['id'],'pe':foot['side'],'fase':phase,
                         'x_px':float(x),'sola_y_px':int(bottom+top),'chao_y_px':int(floor+top),
                         'deriva_px':drift,'deriva_projetada_px':projected_drift,'altura_px':delta}
                    observations.append(obs)
                    if drift>threshold:
                        issue(f,'deslizamento_de_sola',**{k:v for k,v in obs.items() if k!='quadro'})
                    if delta>threshold:
                        issue(f,'altura_de_sola',**{k:v for k,v in obs.items() if k!='quadro'})
            contacts={key:value for key,value in contacts.items() if key in live}

            masks=row.get('masks')
            if masks:
                mask_checks+=1
                if masks['fora']>3:
                    issue(f,'interpenetracao_mascaras',pixels=masks['fora'])
                a,z=row['actors']
                overlap_left=math.floor(max(a['box'][0],z['box'][0]))-3
                overlap_right=math.ceil(min(a['box'][2],z['box'][2]))+3
                if overlap_right<=overlap_left:
                    continue
                l=max(0,overlap_left);r=min(width,overlap_right)
                t=max(0,math.floor(max(a['box'][1],z['box'][1]))-top-3)
                b=min(height,math.ceil(min(a['box'][3],z['box'][3]))-top+3)
                if r-l<2 or b-t<2:
                    continue
                identities=classify(pixels[t:b,l:r])
                groups=np.where(identities<0,-1,actor_types[identities])
                a0=groups==0;a1=groups==1
                y1,x1=np.where((a0[:,:-1]&a1[:,1:])|(a1[:,:-1]&a0[:,1:]))
                visible_contact=len(x1)
                outside=np.ones(visible_contact,dtype=bool)
                if row.get('grip'):
                    x,y=row['grip']
                    outside=(x1+l-x)**2+(y1+t+top-y)**2>46**2
                forbidden=int(outside.sum())
                visible_overlaps.append({'quadro':f,'contato_px':visible_contact,'fora_px':forbidden})
                if forbidden>3:
                    issue(f,'contorno_fundido_no_mp4',pixels=forbidden)
                if row.get('grip') and visible_contact<2:
                    issue(f,'pega_sem_contorno_distinto_no_mp4')
        if decoder.stdout.read(1) or decoder.wait():
            raise ValueError('A decodificação não corresponde à contagem esperada do piloto.')

    return {'quadro_mp4':len(frames),'apoios_medidos':len(observations),'quadros_dupla_mascaras':mask_checks,
            'max_deriva_px':max_drift,'max_altura_sola_px':max_height,
            'max_deriva_projetada_px':max((x['deriva_projetada_px'] for x in observations),default=0),
            'metodo':'Registro da silhueta da sola contra RGB nativo decodificado; chão medido na imagem e câmera compensada. Resolução de 1 px. Máscaras isoladas verificam regiões ocluídas.',
            'observacoes':observations,'contornos_mp4':visible_overlaps,'issues':issues}

if __name__ == '__main__':
    import argparse
    import json
    from pathlib import Path
    from pictograma_pixels import measure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    parser.add_argument('--video', required=True, type=Path)
    parser.add_argument('--poses', required=True, type=Path)
    parser.add_argument('--dom', required=True, type=Path)
    parser.add_argument('--saida', required=True, type=Path)
    args = parser.parse_args()
    dom = json.loads(args.dom.read_text())
    report = audit(args.ffmpeg, args.video, json.loads(args.poses.read_text()))
    report['densidade'] = measure(args.ffmpeg, ['-i', str(args.video)], dom['quadros_ativos'],
                                   dom['quadros_totais'])
    args.saida.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    raise SystemExit(bool(report['issues']))
