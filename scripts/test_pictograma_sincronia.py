from argparse import Namespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pictograma_sincronia import (import_timing, json_rows, refine, subtitle_rows, timing,
                                  validate_rows)
from pictograma_tempo import animate_windows, final_frame
from projeto import config, read, write


class WordTimingTest(unittest.TestCase):
    def test_cue_and_character_import(self):
        characters=list('Eu vou.')
        data={'alignment':{'characters':characters,
                           'character_start_times_seconds':[i/10 for i in range(len(characters))],
                           'character_end_times_seconds':[(i+1)/10 for i in range(len(characters))]}}
        words=json_rows(data)
        self.assertEqual([r['texto'] for r in words],['Eu','vou'])
        validate_rows('palavras',words,['eu','vou'],1)
        with self.assertRaisesRegex(ValueError,'diverge'):
            validate_rows('palavras',words,['eu','fui'],1)
        with tempfile.TemporaryDirectory() as temp:
            file=Path(temp)/'fala.vtt'
            file.write_text('WEBVTT\n\n00:00.000 --> 00:01.000\nEu vou.\n')
            self.assertEqual(subtitle_rows(file)[0],'frases')
            file.write_text('WEBVTT\n\n00:00.000 --> 00:01.000\nEu <00:00.470>vou.\n')
            mode, rows=subtitle_rows(file)
            self.assertEqual(mode,'palavras')
            self.assertEqual(rows[1]['inicio_s'],.47)

    def test_frame_ceiling_and_peak(self):
        self.assertEqual(final_frame(1/30),1)
        self.assertEqual(final_frame(.034),2)
        self.assertEqual(final_frame(2.0),60)
        scenes=[{'inicio':0,'acoes':[{'acao':'levantar','alvo':'figura','palavra':0,'pousar':'pico'}]}]
        self.assertEqual(animate_windows(scenes,[{'quadro':30}],'didatico'),39/30)
        self.assertEqual(scenes[0]['acoes'][0]['inicio_movimento'],.9)
        self.assertEqual(scenes[0]['acoes'][0]['pouso_render'],1)

    def test_refinement_only_near_detectable_onset(self):
        signal=[0]*100
        signal[42:48]=[3500]*6
        self.assertEqual(refine(.5,signal,.35,.65),.42)
        self.assertEqual(refine(.8,signal,.65,.95),.8)

    def test_manual_round_trip_changes_action_and_rejects_stale_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            mat=root/'material'
            paragraphs=[{'id':'P007','texto':'Eu levanto.'}]
            write(mat/'paragrafos.json',paragraphs)
            (mat/'entrada.wav').write_bytes(b'identidade de teste')
            write(root/'projeto.json',{'titulo':'Teste','estilo_video':'pictograma','audio':'material/entrada.wav'})
            export=root/'palavras.json'
            write(export,{'words':[{'word':'Eu','start':.1,'end':.3},{'word':'levanto','start':.5,'end':.8}]})
            args=Namespace(ffmpeg='ffmpeg',ffprobe='ffprobe',fonte=export,importar=None)
            with patch('pictograma_sincronia.recording',return_value=([mat/'entrada.wav'],[1.])), \
                    patch('pictograma_sincronia.envelope',return_value=[0,350,0]):
                import_timing(root,args)
                project=config(root)
                before=timing(root,project,paragraphs,False,args.ffmpeg,args.ffprobe)
                edited=root/'marcacoes_ajustadas.json'
                write(edited,{'identidade':before['identidade'],'pontos':[{'palavra':1,'quadro':16}]})
                args.fonte,args.importar=None,edited
                import_timing(root,args)
                after=timing(root,project,paragraphs,False,args.ffmpeg,args.ffprobe)
                self.assertEqual(after['palavras'][1]['metodo'],'conferido_manual')
                self.assertEqual(after['palavras'][1]['quadro'],before['palavras'][1]['quadro']+1)
                for data,expected in ((before,15),(after,16)):
                    scene={'inicio':0,'acoes':[{'acao':'levantar','alvo':'figura','palavra':1}]}
                    animate_windows([scene],data['palavras'],'didatico')
                    self.assertEqual(scene['acoes'][0]['quadro_alvo'],expected)
                (mat/'entrada.wav').write_bytes(b'arquivo diferente')
                with self.assertRaisesRegex(ValueError,'outro áudio'):
                    import_timing(root,args)
                self.assertEqual(read(mat/'sincronia_manual.json')['pontos'][0]['quadro'],16)
