"""Mede contraste, sombra e flashes em RGB real dos PNGs ou do MP4."""
from base64 import b64decode
from bisect import bisect_left
from collections import deque
import subprocess
from statistics import median


def linear(c):
    c = c/255
    return c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4


LUT = tuple(linear(c) for c in range(256))
RED, GREEN, BLUE = tuple(tuple(c*weight for c in LUT) for weight in (.2126, .7152, .0722))


def luminance(r, g, b):
    return RED[r] + GREEN[g] + BLUE[b]


def contrast(a, b):
    return (max(a,b)+.05)/(min(a,b)+.05)


def red_uv(r,g,b):
    r,g,b = LUT[r],LUT[g],LUT[b]
    saturated = r+g+b > 0 and r/(r+g+b) >= .8
    x = .4124*r+.3576*g+.1805*b
    y = .2126*r+.7152*g+.0722*b
    z = .0193*r+.1192*g+.9505*b
    denom = x+15*y+3*z
    return saturated, 4*x/denom if denom else 0, 9*y/denom if denom else 0


def flash_report(frames, fps=30, wide_limit=.10, silhouettes=None):
    """Conta pares opostos por posição em janelas móveis; sem dispensa por área."""
    previous = previous_mask = None
    moving_edges = 0
    histories = {}
    maxima = {'gerais':0,'vermelhos':0,'area_brusca':0.0}
    issues = []
    hotspots = {}
    for frame, pixels in enumerate(frames):
        mask = next(silhouettes) if silhouettes is not None else None
        # RGB reamostrado em uma grade regular da tela.
        current = [(luminance(r,g,b), (r,g,b)) for r,g,b in zip(pixels[::3],pixels[1::3],pixels[2::3])]
        if previous is not None:
            large = 0
            for i, ((value,rgb),(before,old_rgb)) in enumerate(zip(current,previous)):
                delta = value-before
                large += abs(delta)>=.10
                state = histories.get(i)
                if state is None:
                    state = [[before,0,0,deque()], [old_rgb,0,0,deque()]]
                    histories[i] = state
                for key, track in enumerate(state):
                    peak, direction, unmatched, counts = track
                    if key == 0:
                        # Uma borda móvel revela ou oculta a mesma tinta sem piscar.
                        # Confirme a causa pela máscara do SVG sem luz, na mesma posição.
                        if mask and previous_mask:
                            j = 2*i
                            lum, alpha = mask[j:j+2]
                            old_lum, old_alpha = previous_mask[j:j+2]
                            change_alpha = (alpha-old_alpha)/255
                            # O FFmpeg faz a média espacial dos canais sRGB antes
                            # de converter a amostra para luminância relativa.
                            current_mix = LUT[round((lum*alpha+14*(255-alpha))/255)]
                            prior_mix = LUT[round((old_lum*old_alpha+14*(255-old_alpha))/255)]
                            expected = current_mix-prior_mix
                            if (abs(change_alpha)>.065 and abs(delta)>.045 and delta*change_alpha>0
                                    and abs(expected-delta)<.105):
                                track[:3]=[value,0,0]
                                moving_edges += 1
                                continue
                        change = value-peak
                        strong = abs(change)>=.10 and min(value,peak)<.80
                        val = value
                    else:
                        if rgb == peak or (max(rgb[0],peak[0])<=max(min(rgb[1],rgb[2]),min(peak[1],peak[2]))):
                            continue
                        if not (rgb[0]>=4*(rgb[1]+rgb[2]) or peak[0]>=4*(peak[1]+peak[2])
                                or (rgb[0]>max(rgb[1:])*1.8 or peak[0]>max(peak[1:])*1.8)):
                            continue
                        sat,u,v = red_uv(*rgb)
                        sat0,u0,v0 = red_uv(*peak)
                        change = (1 if sat and not sat0 else -1 if sat0 and not sat else u-u0)
                        strong = (sat or sat0) and (u-u0)**2+(v-v0)**2>.04
                        val = rgb
                    new_direction = 1 if change>0 else -1
                    if strong and new_direction!=direction:
                        if unmatched:
                            counts.append(frame)
                            unmatched=0
                        else:
                            unmatched=1
                        direction=new_direction
                        track[:3]=[val,direction,unmatched]
                    elif not direction or new_direction==direction:
                        # Acumula uma rampa até cruzar o limiar e segue o extremo na direção vigente.
                        if direction:
                            track[0]=val
                    while counts and frame-counts[0]>=fps:
                        counts.popleft()
                    category = 'gerais' if key==0 else 'vermelhos'
                    if len(counts)>maxima[category]:
                        maxima[category]=len(counts)
                        hotspots[category]={'pixel':i,'quadros':list(counts)}
            area = large/max(1,len(current))
            maxima['area_brusca']=max(maxima['area_brusca'],area)
            if area>=wide_limit:
                issues.append({'codigo':'EC-078','quadro':frame,'area':area})
        previous,previous_mask=current,mask
    for category in ('gerais','vermelhos'):
        if maxima[category]>3:
            issues.append({'codigo':'EC-078','tipo':category,'flashes_s':maxima[category]})
    return {**maxima,'limite_area':wide_limit,'arestas_em_movimento':moving_edges,'picos':hotspots,'issues':issues}


def patch(rgb, width, height, point):
    x,y = map(round,point)
    samples = []
    for yy in range(max(0,y-1),min(height,y+2)):
        for xx in range(max(0,x-1),min(width,x+2)):
            i = 3*(yy*width+xx)
            samples.append(luminance(*rgb[i:i+3]))
    return median(samples) if samples else 0


def text_samples(rgb,width,height,box):
    x,y,w,h = box
    vals = []
    for yy in range(max(0,int(y)),min(height,int(y+h)+1),2):
        for xx in range(max(0,int(x)),min(width,int(x+w)+1),2):
            i=3*(yy*width+xx)
            vals.append(luminance(*rgb[i:i+3]))
    if not vals:
        return None
    vals.sort()
    return contrast(vals[int(.96*(len(vals)-1))],vals[int(.24*(len(vals)-1))])


def measure_samples(frames, geometry, width, height, shadow_reference=None):
    issues, shades, shadows, texts = [],[],[],[]
    def issue(code,frame,value,**extra):
        issues.append({'codigo':code,'quadro':frame,'valor':round(value,5),**extra})
    for frame, (rgb,row) in enumerate(zip(frames,geometry)):
        reference = next(shadow_reference) if shadow_reference is not None else None
        for obj in row['shades']:
            light,dark,bg = (patch(rgb,width,height,obj[k]) for k in ('lit','shade','bg'))
            difference = (light-dark)/max(.001,light)
            shades.append(difference)
            if not .08<=difference<=.12:
                issue('EC-080',frame,difference)
            if (value:=min(contrast(light,bg),contrast(dark,bg)))<4.5:
                issue('EC-083',frame,value,alvo='figura')
        for obj in row['contacts']:
            a = patch(rgb,width,height,obj['p'])
            b = patch(reference,width,height,obj['p']) if reference is not None else patch(rgb,width,height,obj['bg'])
            shadows.append(b-a)
            # Pelo menos um nível de sinal em luminância no entorno imediato do apoio.
            if b-a<.0004:
                issue('EC-081',frame,b-a,alvo=obj.get('alvo'))
        for box in row['title']:
            value = text_samples(rgb,width,height,box)
            if value is not None:
                texts.append(value)
                if value<7:
                    issue('EC-083',frame,value,alvo='texto')
    if shadow_reference is not None:
        next(shadow_reference, None)
    return {'sombra_propria':{'amostras':len(shades),'min':min(shades,default=None),'max':max(shades,default=None)},
            'sombra_contato':{'amostras':len(shadows),'min':min(shadows,default=None),'max':max(shadows,default=None)},
            'contraste_texto':{'amostras':len(texts),'min':min(texts,default=None)},'issues':issues}


def pixels(ffmpeg, inputs, width, height, expected):
    command = [ffmpeg,'-v','error',*inputs,'-map','0:v:0','-an',
               '-vf',f'scale={width}:{height}:flags=area+accurate_rnd+full_chroma_int,format=rgb24',
               '-threads','1','-f','rawvideo','-']
    n = width*height*3
    with subprocess.Popen(command,stdout=subprocess.PIPE) as proc:
        for frame in range(expected):
            data=proc.stdout.read(n)
            if len(data)!=n:
                raise ValueError(f'Pixels incompletos no quadro {frame}.')
            yield data
        if proc.stdout.read(1) or proc.wait():
            raise ValueError('Contagem de quadros divergente na auditoria de efeitos.')


def effects_only(frames, controls, geometry, width, height):
    """Mede o resíduo entre imagens no mesmo tempo e a luminância longe do foco."""
    dim = []
    points = [(int(width*x),int(height*y)) for x in (.68,.76,.84) for y in (.34,.44,.57)]
    def residual():
        for frame, (image, control, row) in enumerate(zip(frames,controls,geometry)):
            if row.get('dimStrength'):
                on,off = ([patch(source,width,height,pt) for pt in points] for source in (image,control))
                darkening = 1-sum(on)/max(.0001,sum(off))
                dim.append({'quadro':frame,'reducao':round(darkening,5),'pico':row.get('dimPeak'),
                            'palavra':row.get('onLift')})
            result = bytearray(len(image))
            for i in range(0,len(image),3):
                r,g,b = image[i],image[i+1],image[i+2]
                cr,cg,cb = control[i],control[i+1],control[i+2]
                value = .40+luminance(r,g,b)-luminance(cr,cg,cb)
                # Red flashing is evaluated on colors newly introduced by the layer.
                saturated,u,v = red_uv(r,g,b) if r>1.8*max(g,b) else (False,0,0)
                if saturated:
                    base,ub,vb = red_uv(cr,cg,cb)
                    if not base or (u-ub)**2+(v-vb)**2>.04:
                        result[i:i+3]=image[i:i+3]
                        continue
                level = bisect_left(LUT,min(1,max(0,value)))
                result[i]=result[i+1]=result[i+2]=level
            yield result
    flash = flash_report(residual())
    for key in ('gerais','vermelhos'):
        if 0 < flash[key] <= 3:
            flash['issues'].append({'codigo':'EC-078','tipo':'efeitos_'+key,'flashes_s':flash[key]})
    peak = next((row for row in dim if row['palavra']),None)
    values = [row['reducao'] for row in dim if row['pico']]
    issues=[]
    if peak and not .15<=peak['reducao']<=.20:
        issues.append({'codigo':'escurecimento_fora_da_faixa','quadro':peak['quadro'],'valor':peak['reducao']})
    return flash, {'alvo':'luminância média em 9 pontos fora do protagonista',
                   'quadros':len(dim),'pico_quadros':len(values),'na_palavra':peak,
                   'faixa_no_pico':[min(values),max(values)] if values else [],
                   'serie':dim},issues


def audit(ffmpeg, inputs, geometry, wide_limit=.10, shadow_inputs=None, control_inputs=None):
    rows=geometry['rows']
    width,height=geometry['dimensions']
    count=len(rows)
    reference=pixels(ffmpeg,shadow_inputs,width,height,count) if shadow_inputs else None
    measured=measure_samples(pixels(ffmpeg,inputs,width,height,count),rows,width,height,reference)
    silhouettes = (b64decode(row['motion']) for row in rows) if all('motion' in row for row in rows) else None
    def sample(source):
        return pixels(ffmpeg,source,108,192,count)
    flash=flash_report(sample(inputs),wide_limit=wide_limit,silhouettes=silhouettes)
    result={**measured,'flash':flash,'issues':geometry['issues']+measured['issues']+flash['issues']}
    if control_inputs:
        movement=flash_report(sample(control_inputs),wide_limit=wide_limit,
                              silhouettes=(b64decode(row['motion']) for row in rows))
        isolated, dim, failures=effects_only(sample(inputs),sample(control_inputs),rows,108,192)
        result.update(flash_sem_efeitos=movement,flash_so_efeitos=isolated,escurecimento=dim)
        result['issues']+=isolated['issues']+failures
    return result
