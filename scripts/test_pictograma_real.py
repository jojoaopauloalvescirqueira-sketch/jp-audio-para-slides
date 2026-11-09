"""Aceite vertical com a gravação P007–P008 fornecida pelo usuário."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from projeto import read, sha, write

SCRIPT=Path(__file__).resolve().parent
REFERENCE=SCRIPT.parent/'assets/referencia-pictograma'


class RecordedDemoTest(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('JP_AUDIO_TESTE'),
                         'Fase 6 pendente. Defina JP_AUDIO_TESTE com a gravação real de P007–P008.')
    def test_recorded_demo(self):
        self.assertTrue(os.environ.get('JP_PROJETO_TESTE'),
                        'Defina JP_PROJETO_TESTE para conservar os artefatos da revisão.')
        root=Path(os.environ['JP_PROJETO_TESTE']).expanduser().resolve()
        recording=Path(os.environ['JP_AUDIO_TESTE']).expanduser().resolve()
        self.assertTrue(recording.is_file(),'A gravação fornecida precisa estar acessível.')
        ffmpeg=os.environ.get('JP_FFMPEG','ffmpeg')
        ffprobe=os.environ.get('JP_FFPROBE','ffprobe')
        node=os.environ.get('NODE','node')
        base=['--root',str(root)]
        binaries=['--ffprobe',ffprobe,'--ffmpeg',ffmpeg]

        def run(script,*args,python=sys.executable):
            subprocess.run([python,str(SCRIPT/script),*args],check=True)

        if not (root/'projeto.json').is_file():
            run('fluxo.py','iniciar',*base,'--titulo','Deus é amar')
            run('fluxo.py','estilo',*base,'--estilo','pictograma','--salvar')
            with tempfile.TemporaryDirectory() as directory:
                choices=Path(directory)/'direcao.json'
                write(choices,{'aprovacao':{'valor':'direta','origem':'padrao_assumido'}})
                run('pictograma.py','direcao',*base,'--assumir','--respostas',str(choices))
            material=root/'material'
            paragraphs=read(REFERENCE/'paragrafos.json')
            clean=material/'roteiro_limpo.txt'
            clean.write_text('\n\n'.join(row['texto'] for row in paragraphs)+'\n',encoding='utf-8')
            write(material/'paragrafos.json',paragraphs)
            project=read(root/'projeto.json')
            project['roteiro_sha256']=sha(clean)
            write(root/'projeto.json',project)
            write(material/'cenas_pictograma.json',read(REFERENCE/'cenas_pictograma.json'))

        material=root/'material'
        run('fluxo.py','anexar_audio',*base,'--audio',str(recording),'--ffprobe',ffprobe)
        source=os.environ.get('JP_MARCACOES_TESTE')
        if source:
            run('fluxo.py','sincronia',*base,'--fonte',source,*binaries)
        source_path=material/'sincronia_fonte.json'
        if (not source_path.is_file() or read(source_path)['tipo']=='frases') and not (
                material/'transcricao_asr.json').is_file():
            asr_python=os.environ.get('JP_PYTHON_ASR',sys.executable)
            model=os.environ.get('JP_MODELO_ASR','base')
            run('transcrever.py',*base,'--local-only','--model',model,'--ffprobe',ffprobe,python=asr_python)
        run('pictograma.py','auditar',*base,*binaries,'--node',node)
        review=os.environ.get('JP_PARECER_TESTE')
        if not review:
            self.skipTest(f'Prévia medida e auditoria em {root}. Aguardando o parecer visual da gravação.')
        run('pictograma.py','parecer',*base,*binaries,'--parecer',review,'--rodada',
            os.environ.get('JP_RODADA_TESTE','1'))
        run('sincronizar.py',*base,*binaries,'--node',node,'--renderizar')
        run('validar.py',*base,*binaries,'--video')
        output=root/'pictograma-9x16'
        report=read(material/'auditoria_animacao.json')
        self.assertFalse(any(row['nivel']=='bloqueante' for row in report['issues']))
        for filename in ('video.mp4','auditoria.html','sincronia.html'):
            self.assertTrue((output/filename).is_file())
