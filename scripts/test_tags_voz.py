"""Cobertura do registro, aplicação e conferência das tags de voz."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from fala import clean_paragraphs, compare_speech
from projeto import read, sha, write
from validar_roteiro import validate

SCRIPTS = Path(__file__).resolve().parent


def sample(**changes):
    tag = dict(p='P001', antes_de='Começa aqui.', tag='[pausa]', categoria='entrega',
               intencao='Separar ideias', alcance='pontual', risco='baixo', alternativa='')
    tag.update(changes)
    return dict(versao=1, idioma='pt', densidade='leve',
                curva=[dict(bloco='B01', intensidade=2, funcao='Introdução')],
                tags=[tag], testes=['Ouvir a retomada.'])


class TagProjectTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.material = self.root / 'material'
        self.clean = self.root / 'clean.txt'
        self.studio = self.material / 'roteiro_studio.txt'
        self.canonical = self.material / 'roteiro_limpo.txt'
        self.paragraphs = self.material / 'paragrafos.json'
        self.guide = self.material / 'guia_producao.md'
        self.run_flow('iniciar', '--titulo', 'Exemplo', '--perfil-visual', 'legado')

    def run_script(self, name, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPTS / name), *args],
                                capture_output=True, text=True)
        if ok:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def run_flow(self, command, *args, ok=True):
        return self.run_script('fluxo.py', command, '--root', str(self.root), *args, ok=ok)

    def skill_mode(self):
        self.run_flow('direcao', '--tags', 'skill', '--idioma-tags', 'pt', '--densidade-tags', 'leve',
                      '--categorias-tags', 'entrega', '--categorias-tags', 'emocao',
                      '--categorias-tags', 'vocalizacoes', '--assumir', 'tags',
                      '--assumir', 'idioma_tags', '--assumir', 'densidade_tags',
                      '--assumir', 'categorias_tags')

    def register(self, text, studio=None):
        self.clean.write_text(text, encoding='utf-8')
        args = ['--limpo', str(self.clean)]
        if studio is not None:
            path = self.root / 'marcado.txt'
            path.write_text(studio, encoding='utf-8')
            args.extend(['--studio', str(path)])
        self.run_flow('registrar_roteiro', *args)

    def apply(self, plan, ok=True):
        path = self.material / 'plano_tags.json'
        write(path, plan)
        return self.run_flow('aplicar_tags', '--plano', str(path), ok=ok)

    def test_direction_partial_updates_and_explicit_permission(self):
        self.skill_mode()
        cfg = self.root / 'projeto.json'
        first = read(cfg)['direcao_narrativa']
        self.assertTrue(all(entry['origem'] == 'padrao_assumido' for entry in first.values()))
        failure = self.run_flow('direcao', '--categorias-tags', 'voz', '--assumir', 'categorias_tags', ok=False)
        self.assertIn('autorização explícita', failure.stderr)
        self.assertEqual(read(cfg)['direcao_narrativa'], first)
        self.run_flow('direcao', '--categorias-tags', 'voz')
        last = read(cfg)['direcao_narrativa']
        self.assertEqual(last['idioma_tags'], first['idioma_tags'])
        self.assertEqual(last['categorias_tags']['origem'], 'usuario')
        self.assertTrue(last['categorias_tags']['data'])

    def test_clean_studio_and_instructions_for_external_or_no_tags(self):
        for mode in ('elevenlabs', 'nenhuma'):
            with self.subTest(mode=mode):
                self.run_flow('direcao', '--tags', mode)
                self.register('O teste  preserva o texto.\n', '[pausa] O teste  preserva o texto.\n')
                self.assertEqual(self.studio.read_bytes(), self.canonical.read_bytes())
                self.assertEqual('Enhance text' in self.guide.read_text(encoding='utf-8'), mode == 'elevenlabs')

    def test_application_occurrence_and_reapplication_preserve_hashes(self):
        self.skill_mode()
        self.register('Começa aqui. Começa aqui.\n\nFim.\n')
        before = [sha(self.canonical), sha(self.paragraphs)]
        self.apply(sample(ocorrencia=2))
        self.assertEqual(self.studio.read_text(encoding='utf-8'), 'Começa aqui. [pausa] Começa aqui.\n\nFim.\n')
        guide = self.guide.read_bytes()
        self.apply(sample(ocorrencia=2))
        self.assertEqual(self.guide.read_bytes(), guide)
        self.assertIn(b'| P001 |', guide)
        self.assertEqual(before, [sha(self.canonical), sha(self.paragraphs)])
        self.assertTrue(read(self.material / 'validacao_roteiro.json')['spoken_text_equal_to_clean'])
        self.assertEqual(read(self.root / 'projeto.json')['controles_vocais'], ['pausa'])

    def test_invalid_anchor_quote_and_category_keep_previous_studio(self):
        self.skill_mode()
        self.register('Começa aqui. Começa aqui. “Primeira frase. Dentro da fala.”\n')
        original = self.studio.read_bytes()
        repeated_position = sample(ocorrencia=1)
        repeated_position['tags'] *= 2
        for plan, message in (
            (sample(), 'ambígua'),
            (sample(ocorrencia=3), 'inválida'),
            (sample(antes_de='Não existe.'), 'ausente'),
            (sample(antes_de='Dentro da fala.'), 'citação'),
            (sample(ocorrencia=1, tag='[eco]', categoria='efeitos-sonoros'), 'autorização'),
            (repeated_position, 'duplicada'),
        ):
            with self.subTest(message=message):
                self.assertIn(message, self.apply(plan, ok=False).stderr)
                self.assertEqual(self.studio.read_bytes(), original)

    def test_legacy_whitespace_and_literal_preserve_canonical(self):
        legacy = 'Palavra  seguinte [pausa].\n\nFim.\n'
        self.canonical.write_text(legacy, encoding='utf-8')
        write(self.paragraphs, [{'id': 'P001', 'texto': 'Palavra  seguinte [pausa].'}, {'id': 'P002', 'texto': 'Fim.'}])
        cfg = self.root / 'projeto.json'
        write(cfg, dict(read(cfg), roteiro_sha256=sha(self.canonical)))
        before = [sha(self.canonical), sha(self.paragraphs)]
        self.register('Palavra seguinte [pausa].\n\nFim.\n', '[whispers] Palavra seguinte [pausa].\n\nFim.\n')
        self.assertEqual(before, [sha(self.canonical), sha(self.paragraphs)])
        self.assertIn('pausa', read(cfg)['colchetes_literais'])

    def test_external_audio_pauses_before_alignment_and_requires_current_review(self):
        self.run_flow('direcao', '--tags', 'elevenlabs')
        self.register('A horta mede folhas.\n')
        audio = self.material / 'audio.wav'
        audio.write_bytes(b'fixture de identidade')
        cfg = self.root / 'projeto.json'
        write(cfg, dict(read(cfg), audio='material/audio.wav'))
        write(self.material / 'slides.json', [{'id': 'S001', 'p': 1, 'tipo': 'capa',
                                                'frase_gatilho': 'A horta'}])
        transcript = self.material / 'transcricao_asr.json'
        words = [{'word': token, 'start': i, 'end': i + 1} for i, token in enumerate('A horta mede frutas'.split())]
        write(transcript, {'audio_identidade': {'unico': sha(audio)}, 'duracao_s': 4, 'segmentos': [{'words': words}]})
        self.assertIn('divergências', self.run_script('alinha_audio.py', '--root', str(self.root), ok=False).stderr)
        marks = self.material / 'marcacoes_audio.json'
        self.assertFalse(marks.exists())
        diff = read(self.material / 'divergencias_asr.json')
        self.assertEqual(diff['divergencias'][0]['esperado'], 'folhas')
        self.assertEqual(diff['divergencias'][0]['reconhecido'], 'frutas')
        self.assertEqual(diff['divergencias'][0]['inicio_s'], 3)
        review = {'resultado': 'variacao_asr', 'justificativa': 'Fixture para testar a revisão.'}
        for key in ('transcricao_sha256', 'roteiro_sha256'):
            review[key] = diff[key]
        write(self.material / 'revisao_fala_asr.json', review)
        self.run_script('alinha_audio.py', '--root', str(self.root))
        self.assertTrue(marks.is_file())
        transcript.write_bytes(transcript.read_bytes() + b'\n')
        self.run_script('alinha_audio.py', '--root', str(self.root), ok=False)


class TagTextTest(unittest.TestCase):
    def test_catalog_and_whitespace(self):
        clean = 'A fala segue.\n\nOutra linha [nota].'
        studio = 'A fala  [com a voz embargada] segue.\n\n[whispers] Outra linha [nota].'
        self.assertEqual(clean_paragraphs(studio), ['A fala segue.', 'Outra linha [nota].'])
        result = validate(studio, 'eleven_v4', clean, literal_tags=['nota'])
        self.assertTrue(result['spoken_text_equal_to_clean'])
        self.assertFalse(any('experimental' in w for w in result['warnings']))
        self.assertTrue(compare_speech('[pausa] A fala.', '[pausa] A fala.', literal_tags=['pausa']))
        self.assertTrue(any('experimental' in w for w in validate('[aceleração suave] Texto.', 'eleven_v4')['warnings']))

    def test_six_warnings_are_advisory(self):
        report = validate('[com raiva] [com raiva] A fala. [echo]', 'eleven_v4',
                          direction={'densidade_tags': {'valor': 'leve'}})
        for label in ('Densidade', 'vizinhas', 'fim de parágrafo', 'Mistura', 'sem autorização', 'emoção repetida'):
            self.assertTrue(any(label in item for item in report['warnings']), label)
        self.assertEqual(report['errors'], [])
