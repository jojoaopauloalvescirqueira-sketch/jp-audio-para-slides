"""Sinal técnico de sincronismo. Nenhum arquivo deste teste é uma narração."""
from array import array
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import wave

from projeto import probe
from video_export import export


class FrameSyncTest(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('JP_FFMPEG') and os.environ.get('JP_FFPROBE'),
                         'Defina JP_FFMPEG e JP_FFPROBE para o teste de cliques e flashes.')
    def test_aac_delay_at_aligned_clicks_and_flashes(self):
        ff, fp=os.environ['JP_FFMPEG'], os.environ['JP_FFPROBE']
        rate=48000
        flash_frames=[7,21,43]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            click=root/'cliques-tecnicos.wav'
            signal=array('h',[0])*(rate*2)
            for frame in flash_frames:
                onset=round(rate*frame/30)
                signal[onset:onset+72]=array('h',[24500,-24500])*36
            with wave.open(str(click),'wb') as output:
                output.setparams((1,2,rate,0,'NONE',''))
                output.writeframes(signal.tobytes())
            movie=root/'sinal-tecnico.mp4'
            source="color=c=black:s=1920x1080:r=30:d=2,drawbox=c=white:t=fill:enable='" + (
                '+'.join(f'eq(n,{frame})' for frame in flash_frames)) + "'"
            export(root,movie,'16:9',[click],[probe(click,fp)],2.,ff,fp,None,{}, {},
                   ['-f','lavfi','-i',source],2)
            command=[ff,'-v','error','-i',str(movie)]
            raster=subprocess.run([*command,'-map','0:v:0','-vf','scale=8:8,format=gray',
                                   '-f','rawvideo','-'],capture_output=True,check=True).stdout
            video=[i//64 for i in range(0,len(raster),64) if sum(raster[i:i+64])>64*190]
            raw=subprocess.run([*command,'-map','0:a:0','-ar',str(rate),'-ac','1',
                                '-f','s16le','-'],capture_output=True,check=True).stdout
            pcm=array('h')
            pcm.frombytes(raw)
            audio=[]
            for i,value in enumerate(pcm):
                if abs(value)>7500 and (not audio or i-audio[-1]>rate//10):
                    audio.append(i)
            self.assertEqual(video,flash_frames)
            self.assertEqual(len(audio),len(video))
            offsets=[round(abs(a/rate-f/30)*1000,3) for a,f in zip(audio,video)]
            self.assertLessEqual(max(offsets),1000/30)
            print(f'Cliques × flashes em MP4 AAC: desvios {offsets} ms; tolerância 33,333 ms.')
