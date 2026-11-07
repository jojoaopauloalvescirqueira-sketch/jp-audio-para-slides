"""Contrato do Pictograma, direção e resolução por palavra."""
import copy
from pathlib import Path
import tempfile
import unittest

from estilo_video import resolve, save
from fluxo import iniciar
from pictograma import APPROVAL, BOARD, approval_keys, require_approval
from pictograma_direcao import DEFAULTS, record, settings
from pictograma_plano import Words, compile_plan, measured_times, schedule
from projeto import read, write


class PictogramTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.words = Words([{'id': 'P007', 'texto': 'Eu sento. Eu espero.'},
                            {'id': 'P008', 'texto': 'Agora eu levanto.'}])
        self.direction = {**DEFAULTS, 'nomes_autorizados': []}
        self.scene = {'id': 'S01', 'inicio': {'p': 7, 'trecho': 'Eu', 'ocorrencia': 1},
                      'elementos': [{'id': 'eu', 'tipo': 'figura', 'x': 150, 'y': 550, 'w': 200, 'h': 450}],
                      'acoes': [{'alvo': 'eu', 'acao': 'sentar', 'em': {'p': 'P007', 'trecho': 'sento'}}]}
        self.plan = {'versao': 1, 'cenas': [self.scene]}

    def test_style_priority_and_pending_question(self):
        self.assertEqual(resolve({'estilo_video': None}, environ={})['origem'], 'perguntar')
        env = {'JP_ESTILO_VIDEO_PADRAO': 'pictograma'}
        self.assertEqual(resolve({'estilo_video': None}, environ=env), {'estilo': 'pictograma', 'origem': 'ambiente'})
        self.assertEqual(resolve({'estilo_video': 'editorial_jp'}, environ=env)['estilo'], 'editorial_jp')
        self.assertEqual(resolve({'estilo_video': 'editorial_jp'}, 'legado', env)['estilo'], 'legado')
        self.assertEqual(resolve({'titulo': 'Antigo', 'perfil_visual': 'legado'}, environ=env)['estilo'], 'legado')
        with self.assertRaisesRegex(ValueError, 'inválido'):
            resolve(None, environ={'JP_ESTILO_VIDEO_PADRAO': 'x'})

    def test_direction_and_default_watermark(self):
        iniciar(self.root, 'Teste')
        save(self.root, 'pictograma')
        with self.assertRaisesRegex(ValueError, 'direção visual'):
            settings(read(self.root / 'projeto.json'))
        direction = record(self.root, {}, assume=True)
        self.assertTrue(all(item['origem'] == 'padrao_assumido' and item['data'] for item in direction.values()))
        self.assertEqual(read(self.root / 'projeto.json')['formato'], '9:16')
        self.assertEqual(direction['marca']['valor'], 'nao')
        self.assertIn('Direção visual', (self.root/'material/guia_producao.md').read_text())
        with self.assertRaisesRegex(ValueError, 'autorização explícita'):
            record(self.root, {'nomes_autorizados': {'valor': ['Pessoa Real'], 'origem': 'padrao_assumido'}})

    def test_literal_anchor_scope_and_ambiguity(self):
        self.assertEqual(self.words.anchor({'p': 7, 'trecho': 'Eu', 'ocorrencia': 2}), 2)
        with self.assertRaisesRegex(ValueError, 'ambígua'):
            self.words.anchor({'p': 7, 'trecho': 'Eu'})
        with self.assertRaisesRegex(ValueError, 'ausente'):
            self.words.anchor({'p': 7, 'trecho': 'levant'})
        self.scene['inicio'] = {'p': 7, 'trecho': 'sento'}
        with self.assertRaisesRegex(ValueError, 'cobrir'):
            compile_plan(self.plan, self.words, self.direction)

    def test_library_safe_area_and_person_labels(self):
        for key, value, error in (
                ('tipo', 'terceiros', 'tipo'), ('x', 810, 'área segura'),
                ('rotulo', 'Pessoa Real', 'sem autorização')):
            plan = copy.deepcopy(self.plan)
            plan['cenas'][0]['elementos'][0][key] = value
            with self.assertRaisesRegex(ValueError, error):
                compile_plan(plan, self.words, self.direction)
        self.scene['elementos'][0]['rotulo'] = 'Pessoa Real'
        compile_plan(self.plan, self.words, {**self.direction, 'personagens': 'nomes',
                                           'nomes_autorizados': ['Pessoa Real']})
        self.scene['acoes'][0]['acao'] = 'girar'
        with self.assertRaisesRegex(ValueError, 'ação fora'):
            compile_plan(self.plan, self.words, {**self.direction, 'personagens': 'nomes',
                                                'nomes_autorizados': ['Pessoa Real']})

    def test_measured_time_required_and_rhythm(self):
        scenes = compile_plan(self.plan, self.words, self.direction)
        heard = [{'start': t} for t in (.13, .57, 1.4, 1.72, 2.41, 2.77, 3.03)]
        times = measured_times(heard, {i: i for i in range(7)}, 7, {0, 1})
        timeline = schedule(scenes, times, 3.66)
        self.assertEqual(timeline[0]['acoes'][0]['tempo'], .57)
        self.assertEqual(timeline[0]['fala'], 'Eu sento. Eu espero. Agora eu levanto.')
        with self.assertRaisesRegex(ValueError, 'reconhecida'):
            measured_times(heard, {0: 0, 2: 2}, 7, {0, 1})
        with self.assertRaisesRegex(ValueError, 'justificativa_ritmo'):
            schedule(scenes, times, 1.8)

    def test_storyboard_approval_is_bound_to_direction_and_plan(self):
        material = self.root / 'material'
        write(material / 'paragrafos.json', [{'id': 'P007', 'texto': 'Fixture'}])
        board = copy.deepcopy(self.plan)
        del board['cenas'][0]['acoes']
        write(material / BOARD, board)
        scenes = compile_plan(self.plan, self.words, self.direction)
        with self.assertRaisesRegex(ValueError, 'aprovação explícita'):
            require_approval(material, self.direction, '9:16', scenes, self.words)
        write(material / APPROVAL, approval_keys(material, '9:16', self.direction))
        require_approval(material, self.direction, '9:16', scenes, self.words)
        with self.assertRaisesRegex(ValueError, 'alterados'):
            require_approval(material, self.direction, '16:9', scenes, self.words)
