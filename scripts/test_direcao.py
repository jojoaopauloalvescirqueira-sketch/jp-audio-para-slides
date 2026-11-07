"""Direção narrativa persistida, preservação da fala e diagnósticos optativos."""
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from projeto import config
from validar_roteiro import validate


SCRIPTS = Path(__file__).resolve().parent
MODEL = 'eleven_v4'


def direction(**values):
    return {field: {'valor': value} for field, value in values.items()}


class DirectionProjectTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / 'projeto'
        self.flow('iniciar', '--titulo', 'Demonstração', '--perfil-visual', 'legado')
        self.guide = self.root / 'material/guia_producao.md'
        self.clean = self.root.parent / 'fala.txt'
        self.clean.write_text('Eu explico o ciclo da água.\n\nA água pode evaporar.\n', encoding='utf-8')

    def flow(self, command, *options, check=True):
        return subprocess.run([sys.executable, str(SCRIPTS / 'fluxo.py'), command,
                               '--root', str(self.root), *options],
                              capture_output=True, text=True, check=check)

    def test_choices_and_provenance(self):
        self.flow('direcao', '--perspectiva', 'externa', '--estilo', 'professor-didatico',
                  '--registro', 'intermediario', '--assumir', 'registro',
                  '--voz', 'Narrador neutro', '--destino', 'Canal didático',
                  '--cobertura', 'integral', '--duracao-alvo', '90',
                  '--formato', '9:16', '--falas-terceiros', 'indireto', '--sensiveis', 'manter',
                  '--bloco', 'abertura:personagem:', '--vivencia', 'Relato confirmado no artigo')
        project = config(self.root)
        saved = project['direcao_narrativa']
        self.assertEqual(project['formato'], '9:16')
        self.assertEqual(saved['duracao_alvo']['valor'], 90)
        self.assertEqual(saved['registro']['origem'], 'padrao_assumido')
        self.assertEqual(saved['perspectiva']['origem'], 'usuario')
        self.assertEqual(saved['blocos']['abertura']['perspectiva']['valor'], 'personagem')
        self.assertIsNotNone(datetime.fromisoformat(saved['perspectiva']['data']).tzinfo)
        self.assertIn('Estrutura de professor', self.guide.read_text(encoding='utf-8'))

    def test_partial_update_and_guide_are_idempotent(self):
        self.guide.write_text('# Guia\n\n## Objetivos\n\nPreservar.\n\n## Pausas\n\nRitmo.\n', encoding='utf-8')
        self.flow('direcao', '--registro', 'culto', '--formato', '16:9',
                  '--bloco', 'inicio:externa:didatico', '--bloco', 'fim::professor')
        first = config(self.root)['direcao_narrativa']
        self.guide.write_text(self.guide.read_text(encoding='utf-8') + '\n## Áudio\n\nÁudio pendente.\n', encoding='utf-8')
        update = ('direcao', '--registro', 'falado', '--bloco', 'inicio::professor')
        self.flow(*update)
        result = config(self.root)['direcao_narrativa']
        self.assertEqual(result['formato'], first['formato'])
        self.assertEqual(result['blocos']['fim'], first['blocos']['fim'])
        self.assertEqual(result['blocos']['inicio']['perspectiva'], first['blocos']['inicio']['perspectiva'])
        self.assertEqual(result['blocos']['inicio']['estilo']['valor'], 'professor')
        guide = self.guide.read_text(encoding='utf-8')
        self.assertEqual(guide.count('## Direção narrativa'), 1)
        self.assertIn('Preservar.\n\n## Pausas\n\nRitmo.', guide)
        self.assertIn('## Áudio\n\nÁudio pendente.', guide)
        self.flow(*update)
        self.assertEqual(result, config(self.root)['direcao_narrativa'])
        self.assertEqual(guide, self.guide.read_text(encoding='utf-8'))

    def test_invalid_direction_leaves_files_unchanged(self):
        before = (self.root / 'projeto.json').read_bytes()
        for flags in [(), ('--duracao-alvo', 'nan'), ('--assumir', 'formato', '--registro', 'culto'),
                      ('--bloco', 'a::indefinido'), ('--bloco', 'a::didatico', '--bloco', 'a:externa:')]:
            with self.subTest(flags=flags):
                self.assertNotEqual(self.flow('direcao', *flags, check=False).returncode, 0)
                self.assertEqual((self.root / 'projeto.json').read_bytes(), before)
                self.assertFalse(self.guide.exists())

    def test_legacy_registers_unmodified_and_warns(self):
        result = self.flow('registrar_roteiro', '--limpo', str(self.clean))
        self.assertIn('Direção narrativa ausente', result.stderr)
        self.assertNotIn('direcao_narrativa', config(self.root))
        self.assertEqual((self.root / 'material/roteiro_limpo.txt').read_bytes(), self.clean.read_bytes())
        report = json.loads((self.root / 'material/validacao_roteiro.json').read_text(encoding='utf-8'))
        self.assertEqual(report['status'], 'apto_com_avisos')
        self.assertEqual(report['errors'], [])

    def test_registrar_and_standalone_report_same_heuristics(self):
        self.flow('direcao', '--perspectiva', 'externa')
        self.flow('registrar_roteiro', '--limpo', str(self.clean))
        saved = json.loads((self.root / 'material/validacao_roteiro.json').read_text(encoding='utf-8'))
        result = subprocess.run([sys.executable, str(SCRIPTS / 'validar_roteiro.py'),
                                 str(self.clean), '--model', MODEL, '--root', str(self.root)],
                                capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout)['warnings'], saved['warnings'])
        self.assertEqual(saved['status'], 'apto_com_avisos')
        self.assertIn('1 marcas explícitas', saved['warnings'][0])


class DirectionWarningTests(unittest.TestCase):
    def test_explicit_first_person_and_colloquialism_exclude_quotes(self):
        chosen = direction(perspectiva='externa', registro='culto')
        quoted = 'O autor disse “Eu vou pra lá”.\n\n— A gente tá bem, eu vou.'
        self.assertEqual(validate(quoted, MODEL, direction=chosen)['warnings'], [])
        report = validate(quoted + '\n\nA gente explica e eu mostro pra todos.', MODEL, direction=chosen)
        self.assertIn('1 marcas', report['warnings'][0])
        self.assertIn('2 ocorrências', report['warnings'][1])
        self.assertEqual(report['errors'], [])

    def test_mixed_perspective_uses_editorial_review(self):
        chosen = direction(perspectiva='externa')
        chosen['blocos'] = {'relato': direction(perspectiva='personagem')}
        self.assertEqual(validate('Eu acompanhei o encontro.', MODEL, direction=chosen)['warnings'], [])

    def test_register_warnings_count_punctuation_and_repeated_fillers(self):
        text = 'Repare: um. Repare: outro. Guarde: três. Guarde isto. Agora, leia. Agora, ouça.'
        report = validate(text, MODEL, direction=direction(registro='falado'))
        self.assertEqual(len(report['warnings']), 4)
        self.assertTrue(any('3 dois-pontos' in item for item in report['warnings']))
        self.assertTrue(any('“agora” inicia 2' in item for item in report['warnings']))
        self.assertEqual(validate(text, MODEL)['warnings'], [])

    def test_duration_outside_and_at_tolerance(self):
        text = 'palavra ' * 100
        for target in (40, 60, 'livre'):
            with self.subTest(target=target):
                self.assertEqual(validate(text, MODEL, wpm_min=125, wpm_max=125 if target == 40 else 160,
                                          direction=direction(duracao_alvo=target))['warnings'], [])
        for target in (20, 90):
            with self.subTest(target=target):
                report = validate(text, MODEL, direction=direction(duracao_alvo=target))
                self.assertEqual(report['status'], 'apto_com_avisos')
                self.assertIn('fora da margem de 20%', report['warnings'][0])
                self.assertTrue(any('não avaliam qualidade' in item for item in report['limitations']))


if __name__ == '__main__':
    unittest.main()
