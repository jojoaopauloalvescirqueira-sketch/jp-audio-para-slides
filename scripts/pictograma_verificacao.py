"""Evidência dos quadros e da legenda do Pictograma no MP4 decodificado."""
from contextlib import contextmanager
import math
import re
import subprocess

from projeto import probe, sha


@contextmanager
def decoder(command):
    with subprocess.Popen(command,stdout=subprocess.PIPE) as process:
        try:
            yield process.stdout
            if process.wait():
                raise ValueError('A decodificação do MP4 falhou.')
        finally:
            if process.poll() is None:
                process.kill()


def verify_media(ffprobe, path, count):
    data=probe(path,ffprobe)
    video=[s for s in data['streams'] if s['codec_type']=='video']
    audio=[s for s in data['streams'] if s['codec_type']=='audio']
    if (len(video)!=1 or len(audio)!=1 or video[0]['codec_name']!='h264'
            or audio[0]['codec_name']!='aac'
            or (video[0]['width'],video[0]['height'],video[0]['avg_frame_rate'])!=(1080,1920,'30/1')
            or int(video[0]['nb_frames'])!=count
            or abs(float(data['format']['duration'])-count/30)>.04
            or abs(float(audio[0]['duration'])-count/30)>.04):
        raise ValueError('Duração, quadros, formato ou faixa de áudio incompatíveis.')
    return data


INK_MASK = bytes(int(value > 92) for value in range(256))


def caption_matches(reference, video):
    """Compare light glyphs using the green channel in the subtitle strip."""
    a=reference[1::3].translate(INK_MASK)
    b=video[1::3].translate(INK_MASK)
    xor=int.from_bytes(a,'little') ^ int.from_bytes(b,'little')
    return xor.to_bytes(len(a),'little').count(1)<=max(9,a.count(1)*.013)


def pixel_distance(left, right):
    return max(abs(a-b) for a,b in zip(left,right))


def foot_height(image, geometry, offset=0, width=1080):
    box,floor,ink=(geometry[key] for key in ('box','floor','ink'))
    if ink.startswith('#') and len(ink)==7:
        color=[int(ink[i:i+2],16) for i in (1,3,5)]
    else:
        color=[int(x) for x in re.findall(r'\d+',ink)[:3]]
    if len(color)!=3:
        return None
    x,y,w,h=box
    left=max(0,int(x)-1)
    right=min(width,math.ceil(x+w)+1)
    expected=y+h
    top=max(0,math.floor(min(expected,floor))-7-offset)
    bottom=min(len(image)//(width*3),math.ceil(max(expected,floor))+9-offset)
    for row in range(bottom-1,top-1,-1):
        matching=0
        start=(row*width+left)*3
        for i in range(start,start+(right-left)*3,3):
            matching=matching+1 if pixel_distance(image[i:i+3],color)<=35 else 0
            if matching>=3:
                return round(abs(row+offset-floor))
    return None


def bench_visible(image, seat, offset=0, width=1080):
    x,y,w,h=seat
    left=max(0,int(x+w*.15))
    right=min(width,int(x+w*.85))
    inside=round(y+h*.55)-offset
    outside=round(y-4)-offset
    if right-left<5 or not 0<=outside<inside<len(image)//(width*3):
        return False
    count=0
    for column in range(left,right):
        a,b=(inside*width+column)*3,(outside*width+column)*3
        count+=pixel_distance(image[a:a+3],image[b:b+3])>8
    return count>=(right-left)*.15


def verify_frames(ffmpeg, path, frames, geometry, count):
    """Compare all output frames with the signed render and read contact pixels."""
    if len(geometry)!=count or any(item['quadro']!=i for i,item in enumerate(geometry)):
        raise ValueError('A geometria da prévia deve cobrir todos os quadros.')
    images=['-framerate','30','-i',str(frames/'%06d.png')]
    commands=[ffmpeg,'-v','error','-i',str(path),*images]
    # PSNR catches changed/reordered material in the entire stage. A separate
    # native-resolution strip catches short glyph and contact regressions.
    small='scale=270:480:flags=area,format=yuv420p'
    process=subprocess.run([*commands,'-filter_complex',
        f'[0:v]{small}[a];[1:v]{small}[b];[a][b]psnr=stats_file=-',
        '-an','-f','null','-'],text=True,check=True,capture_output=True)
    values=[float(x) for x in re.findall(r'psnr_avg:([\d.]+|inf)',process.stdout)]
    if len(values)!=count:
        raise ValueError('O MP4 e os quadros renderizados têm contagens diferentes.')
    checks={code:{'quadros':0,'falhas':0} for code in (
        'EC-086','EC-094','legenda_codificada','identidade_render')}
    first={}
    def record(code,frame,ok):
        checks[code]['quadros']+=1
        if not ok:
            checks[code]['falhas']+=1
            first.setdefault(code,frame)

    top,height,width=1000,448,1080
    filt=f'crop={width}:{height}:0:{top},format=rgb24'
    graph=f'[0:v]{filt}[a];[1:v]{filt}[b];[a][b]hstack=shortest=1[out]'
    cmd=[*commands,'-filter_complex',graph,'-map','[out]','-an','-c:v','rawvideo',
         '-threads','1','-f','rawvideo','-pix_fmt','rgb24','-']
    size=width*2*height*3
    stride=width*6
    end=width*3
    with decoder(cmd) as pipe:
        for i,row in enumerate(geometry):
            raw=pipe.read(size)
            if len(raw)!=size:
                raise ValueError(f'Quadro decodificado incompleto em {i}.')
            reference=b''.join(raw[y+end:y+end+930*3] for y in range(329*stride,size,stride))
            captions=b''.join(raw[y:y+930*3] for y in range(329*stride,size,stride))
            record('identidade_render',i,values[i]>=34)
            record('legenda_codificada',i,caption_matches(reference,captions))
            got=b''.join(raw[y:y+end] for y in range(0,size,stride)) if row['feet'] or row['supports'] else b''
            if row['feet']:
                errors=[foot_height(got,foot,top) for foot in row['feet']]
                record('EC-086',i,all(error is not None and error<=2 for error in errors))
            if row['supports'] or row['crossing']:
                record('EC-094',i,bool(row['seat']) and not row['crossing'] and bench_visible(got,row['seat'],top))
        if pipe.read(1):
            raise ValueError('Há quadros além da cobertura do plano.')
    return checks,first


def render_identity(directory,count):
    from pictograma_salvaguardas import digest
    return digest({'manifesto':sha(directory/'render_manifest.json'),
                   'png':[sha(directory/f'{i:06}.png') for i in range(count)]})
