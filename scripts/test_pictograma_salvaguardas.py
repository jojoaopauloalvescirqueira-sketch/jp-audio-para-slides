"""Regressões genéricas do percurso de aceitação declarativo."""
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zlib

from pictograma_salvaguardas import context, expected_ownership, identity, matrix, plan_checks, require_matrix
from pictograma_verificacao import bench_visible, foot_height, verify_frames

HERE = Path(__file__).resolve().parent


def png(path, pixels, width, height):
    def chunk(tag, data):
        return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data))
    stride=width*3
    scan=b''.join(b'\0'+pixels[i:i+stride] for i in range(0,len(pixels),stride))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',width,height,8,2,0,0,0))
                     +chunk(b'IDAT',zlib.compress(scan))+chunk(b'IEND',b''))


def rect(image, x, y, width, height, color, stride):
    for row in range(y,y+height):
        start=(row*stride+x)*3
        image[start:start+width*3]=bytes(color)*width


class SafeguardTest(unittest.TestCase):
    def js(self, source):
        node=os.environ.get('JP_NODE') or shutil.which('node')
        if not node:
            self.skipTest('Informe JP_NODE para as checagens vetoriais.')
        subprocess.run([node,'-e',
                        "const ok=require('node:assert/strict');"
                        "const a=require('node:vm').runInNewContext(require('node:fs').readFileSync("
                        "'auditoria_catalogo.js','utf8')+';window.AuditoriaCatalogo',{window:{}});"+source],
                       cwd=HERE,check=True)

    def test_sole_is_measured_in_pixels(self):
        width=48
        outline={'box':[12,30,18,10],'floor':40,'ink':'#ece6d8'}
        frame=bytearray(width*width*3)
        rect(frame,12,30,18,10,(236,230,216),width)
        self.assertLessEqual(foot_height(frame,outline,width=width),2)
        elevated=bytearray(len(frame))
        rect(elevated,12,24,18,10,(236,230,216),width)
        self.assertGreater(foot_height(elevated,outline,width=width),2)
        self.assertIsNone(foot_height(bytes(len(frame)),outline,width=width))

    def test_bench_missing_or_confused_with_sole(self):
        width=64
        seat=[6,14,44,6]
        empty=bytearray(width*width*3)
        feet=bytearray(empty)
        rect(feet,31,36,16,10,(236,230,216),width)
        self.assertFalse(bench_visible(feet,seat,width=width))
        rect(feet,6,14,44,6,(160,170,150),width)
        self.assertTrue(bench_visible(feet,seat,width=width))

    def test_label_occluded_or_outside_safe_area(self):
        self.js("ok(a.rotuloVisivel([50,540,100,35],[[55,600,90,30]]));"
                "ok(!a.rotuloVisivel([50,540,100,35],[[55,565,90,30]]));"
                "ok(!a.rotuloVisivel([880,540,100,35],[]));")

    def test_retained_object_requires_expected_owner(self):
        scenes=[{'movimento':{'tipo':'entregar','objeto':'coracao','alvo':'outro','pouso':80}},
                {'manter_posse':True}]
        expected_ownership(scenes)
        self.assertEqual(scenes[1]['posse_esperada']['depois'],1)
        self.js("const h={kind:'coracao',owner:1,opacity:1};"
                "ok(a.objetoComDono([h],'coracao',1));"
                "ok(!a.objetoComDono([{...h,owner:0}],'coracao',1));"
                "ok(!a.objetoComDono([],'coracao',1));"
                "ok(!a.objetoComDono([h,h],'coracao',1));")

    def test_applicability_does_not_depend_on_render_markers(self):
        scene={'id':'batida-1','inicio':0,'fala':'Idosos, animais e crianças esperam.',
               'padrao':'conceito','pausa':'O narrador enumera.',
               'movimento':{'tipo':'sentar','gesto':{'intencao':'exemplo','alvo':'banco','saida':'apoio'},
                            'em':{'trecho':'esperam'}}}
        timeline={'cenas':[scene],'figuras_com_apoio':True}
        self.assertIn('EC-094',context(timeline))
        self.assertIn('EC-086',context(timeline))
        self.assertEqual(plan_checks(timeline)[1][0]['codigo'],'EC-097')
        scene['cenario_ilustrado']={'figuras':[{'tipo':k} for k in ('idoso','animal','crianca')]}
        self.assertEqual(plan_checks(timeline)[1],[])
        evidence=matrix({'checagens_catalogo':{}},timeline,'mp4')
        with self.assertRaisesRegex(ValueError,'EC-086'):
            require_matrix(evidence,'mp4')
        statuses={row['id']:row for row in evidence}
        self.assertEqual(statuses['EC-094']['estado'],'sem_evidencia')
        self.assertEqual(statuses['EC-107']['estado'],'nao_aplicavel')

    def test_conditional_is_not_the_reflexive_pronoun(self):
        action={'tipo':'levantar','gesto':{'intencao':'marcar a ação','alvo':'chão','saida':'apoio'},
                'em':{'trecho':'levanta'}}
        scene={'id':'batida-1','inicio':0,'fala':'A pessoa se levanta e segue.','padrao':'conceito','movimento':action}
        self.assertEqual(plan_checks({'cenas':[scene]})[1],[])
        for speech in ('Se ela se levanta, já vê a janela.', 'Ela não se levanta sozinha.'):
            scene['fala']=speech
            self.assertEqual(plan_checks({'cenas':[scene]})[1][0]['codigo'],'EC-098')

    def test_stale_evidence_after_changes_to_sync_or_plan(self):
        with tempfile.TemporaryDirectory() as path:
            plan,preview=[Path(path)/name for name in ('plano.json','previa.html')]
            plan.write_text('{}')
            preview.write_text('quadro')
            sync={'identidade':{'audio_identidade':{'voz':'A'}},'palavras':[{'quadro':1}]}
            original=identity(plan,preview,sync,[{'sha256':'A','nivel_db':-14}])
            sync['palavras'][0]['quadro']=2
            self.assertNotEqual(original['sincronia_sha256'],identity(plan,preview,sync,[])['sincronia_sha256'])
            plan.write_text('{"nova_cena": true}')
            self.assertNotEqual(original['direcao_sha256'],identity(plan,preview,sync,[])['direcao_sha256'])

    def test_skipped_link_in_another_test_module_is_reported(self):
        from testar_suite import catalog_skips
        result=unittest.TestResult()
        result.skipped=[(self,'Teste de contagem')]
        with patch('testar_suite.linked_tests',return_value={self.id()}):
            self.assertEqual(catalog_skips(result),[(self.id(),'Teste de contagem')])

    def test_pixel_audit_catches_one_or_two_bad_frames(self):
        ffmpeg=os.environ.get('JP_FFMPEG') or shutil.which('ffmpeg')
        if not ffmpeg:
            self.skipTest('Informe JP_FFMPEG para auditar o MP4 decodificado.')
        with tempfile.TemporaryDirectory() as path:
            root=Path(path)
            ref=root/'ref'
            bad=root/'bad'
            ref.mkdir()
            bad.mkdir()
            w,h=1080,1920
            image=bytearray(bytes([22,25,24])*(w*h))
            rect(image,250,1220,65,25,(236,230,216),w)
            rect(image,260,1150,135,20,(158,156,146),w)
            rect(image,180,1355,210,24,(225,221,211),w)
            elevated=bytearray(image)
            rect(elevated,250,1220,65,25,(22,25,24),w)
            rect(elevated,250,1214,65,25,(236,230,216),w)
            hidden=bytearray(image)
            rect(hidden,260,1150,135,20,(22,25,24),w)
            rect(hidden,180,1355,210,24,(22,25,24),w)
            geometry=[{'quadro':i,'feet':[{'box':[250,1220,65,25],'floor':1245,'ink':'#ece6d8'}],
                       'supports':True,'seat':[260,1150,135,20],'crossing':False} for i in range(4)]
            for i,bad_image in enumerate((image,elevated,hidden,hidden)):
                png(ref/f'{i:06}.png',image,w,h)
                png(bad/f'{i:06}.png',bad_image,w,h)
            for source in (ref,bad):
                output=root/(source.name+'.mp4')
                subprocess.run([ffmpeg,'-v','error','-framerate','30','-i',str(source/'%06d.png'),
                                '-c:v','libx264','-crf','10','-pix_fmt','yuv420p',str(output)],check=True)
                checks,failures=verify_frames(ffmpeg,output,ref,geometry,4)
                if source==ref:
                    self.assertEqual(failures,{})
                else:
                    self.assertEqual(failures['EC-086'],1)
                    self.assertEqual(checks['EC-086']['falhas'],1)
                    self.assertEqual(failures['EC-094'],2)
                    self.assertEqual(checks['EC-094']['falhas'],2)
                    self.assertEqual(failures['legenda_codificada'],2)
