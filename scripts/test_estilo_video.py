"""Seleção, fronteiras dos estilos e retomada do Ilustrado."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from estado_projetos import scan
from estilo_video import DEFAULT_VAR, STYLES, ensure_style_plan, resolve, save
from projeto import read, write


class StyleTest(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name).resolve()
        self.material = self.root / 'material'

    def project(self, **values):
        write(self.root / 'projeto.json', {'titulo':'Projeto', **values})
        write(self.material / 'paragrafos.json', [{'id':'P001','texto':'Eu espero.'}])

    def test_style_question_and_default(self):
        cmd = [sys.executable, str(Path(__file__).with_name('fluxo.py')), 'estilo']
        env = os.environ.copy()
        env.pop(DEFAULT_VAR, None)
        self.assertIn('"origem": "perguntar"', subprocess.check_output(cmd, env=env, text=True))
        self.assertEqual(STYLES, ('editorial_jp','pictograma','ilustrado','legado'))
        for style in STYLES:
            env[DEFAULT_VAR] = style
            self.assertIn(f'"estilo": "{style}"', subprocess.check_output(cmd, env=env, text=True))
        menu = (Path(__file__).parents[1] / 'references/apresentacao.md').read_text()
        question = menu.split('## Escolha do estilo de vídeo')[1].split('Qual estilo você quer usar?')[0]
        self.assertEqual(question.count('\n- **'), 4)
        self.assertEqual(resolve({'estilo_video':'legado'},'ilustrado',env)['origem'],'pedido')
        self.assertEqual(resolve({'estilo_video':'pictograma'},environ=env)['origem'],'projeto')

    def test_confirm_and_archive_previous_plan(self):
        self.project(estilo_video='pictograma',formato='9:16',direcao_visual={'marca':{'valor':'nao'}})
        plan = self.material / 'cenas_pictograma.json'
        write(plan, {'cenas':['anterior']})
        with self.assertRaisesRegex(ValueError, 'Confirme'):
            save(self.root, 'ilustrado')
        self.assertTrue(plan.is_file())
        result = save(self.root, 'ilustrado', confirm=True)
        archive = self.root / result['historico_estilo']
        self.assertEqual(read(archive / 'material' / plan.name), {'cenas':['anterior']})
        self.assertFalse(plan.exists())
        self.assertNotIn('direcao_visual', result)
        self.assertEqual(result['formato'], '16:9')
        self.assertEqual(result['origem_estilo_video'], 'pedido')

    def test_cross_plan_rejected_in_both_directions(self):
        for style, other in (('pictograma','ilustrado'),('ilustrado','pictograma')):
            self.project(estilo_video=style)
            wrong = self.material / f'cenas_{other}.json'
            with self.assertRaisesRegex(ValueError, f'recusa {wrong.name}'):
                ensure_style_plan(self.root, style, self.root / wrong.name)
            write(wrong,{})
            with self.assertRaisesRegex(ValueError, f'recusa {wrong.name}'):
                ensure_style_plan(self.root, style)
            wrong.unlink()

    def test_illustrated_status_tracks_missing_review_and_audio(self):
        self.project(estilo_video='ilustrado',direcao_visual={'storyboard':{'valor':'aprovar'}})
        folder = self.material / 'ilustrado'
        def step():
            return scan([self.root])['projetos'][0]['proximo_passo']

        write(folder/'biblia.json',{})
        self.assertIn('aprovar a bíblia',step())
        for path in (folder/'aprovacao_biblia.json', self.material/'cenas_ilustrado.json',
                     folder/'aprovacao_storyboard.json'):
            write(path,{})
        asset = dict(id='pose',arquivo='pose.png',prompt_sha256='teste')
        write(folder/'prompts_imagens.json',{'prompts':[asset]})
        self.assertIn('faltam 1 imagens: pose',step())
        png = folder/'imagens/pose.png'
        png.parent.mkdir()
        png.touch()
        write(folder/'assets.json',{'assets':[{**asset,'status':'recebida'}]})
        self.assertIn('aprovar a folha de contato',step())
        write(folder/'assets.json',{'assets':[{**asset,'status':'aprovada'}]})
        self.assertIn('falta o áudio',step())
