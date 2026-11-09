"""A saída de vídeo usa exclusivamente gravações fornecidas."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from projeto import write


class AudioInputTest(unittest.TestCase):
    def test_production_has_no_voice_synthesis_route(self):
        root = Path(__file__).resolve().parents[1]
        route = re.compile(
            r'https?://[^\s\'"]+/v1/text-to-speech|\b(?:AVSpeechSynthesizer|pyttsx3|edge_tts|gTTS)\b|'
            r'\b(?:synthesizer|speechSynthesis)\.speak\b|[\'"](?:say|espeak(?:-ng)?|piper)[\'"]',
            re.I)
        for folder in ('scripts', 'assets'):
            for source in (root / folder).rglob('*'):
                if source.suffix in ('.py', '.js', '.mjs', '.html') and not source.name.startswith('test_'):
                    self.assertIsNone(route.search(source.read_text(encoding='utf-8')), str(source))

    def test_no_recording_blocks_export_and_allows_estimated_preview(self):
        from pictograma_direcao import DEFAULTS
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            material = root / 'material'
            material.mkdir()
            choices = {key: {'valor': value} for key, value in {**DEFAULTS, 'aprovacao': 'direta'}.items()}
            write(root / 'projeto.json', {'titulo':'Teste','estilo_video':'pictograma','formato':'9:16',
                                        'direcao_visual':choices})
            write(material / 'paragrafos.json', [{'id':'P001','texto':'A fala canônica.'}])
            write(material / 'cenas_pictograma.json', {'versao':1,'cenas':[{
                'id':'S01','entrada':{'p':1,'trecho':'A fala'},
                'elementos':[{'id':'fig','tipo':'figura','x':200,'y':700,'w':220,'h':420}],
                'justificativa_ritmo':'Trecho curto de teste.'}]})
            common = ['--root', str(root)]
            scripts = Path(__file__).resolve().parent
            env = {**os.environ, 'PYTHONDONTWRITEBYTECODE':'1'}
            result = subprocess.run([sys.executable,str(scripts/'sincronizar.py'),*common,'--renderizar'],
                                    env=env,capture_output=True,text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('narração fornecido', result.stderr)
            self.assertEqual(list(root.rglob('*.mp4')), [])
            subprocess.run([sys.executable,str(scripts/'fluxo.py'),'cenas',*common],
                           env=env,capture_output=True,text=True,check=True)
            self.assertIn('Prévia estimada', (root/'pictograma-9x16/apresentacao.html').read_text())
