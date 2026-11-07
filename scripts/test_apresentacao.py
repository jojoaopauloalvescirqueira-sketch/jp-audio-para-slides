"""Consulta sem escrita e cobertura do menu sobre as entradas existentes."""
import ast
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from projeto import sha, write

SCRIPTS = Path(__file__).resolve().parent
REFERENCE = SCRIPTS.parent / 'references' / 'apresentacao.md'


def discover_commands():
    commands = {path.name for path in SCRIPTS.glob('*.mjs')}
    for path in SCRIPTS.glob('*.py'):
        if path.name.startswith('test_'):
            continue
        nodes = list(ast.walk(ast.parse(path.read_text(encoding='utf-8'))))
        cli = any(
            isinstance(node, ast.Call)
            and ((isinstance(node.func, ast.Attribute) and node.func.attr == 'ArgumentParser')
                 or (isinstance(node.func, ast.Name) and node.func.id == 'ArgumentParser'))
            for node in nodes
        )
        if not cli:
            cli = any(
                isinstance(node, ast.Compare)
                and isinstance(node.left, ast.Name) and node.left.id == '__name__'
                and any(isinstance(value, ast.Constant) and value.value == '__main__'
                        for value in node.comparators)
                for node in nodes
            )
        if not cli:
            continue
        subcommands = [
            node.args[0] for node in nodes if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute) and node.func.attr == 'add_parser'
        ]
        for subcommand in subcommands:
            if not isinstance(subcommand, ast.Constant) or not isinstance(subcommand.value, str):
                raise AssertionError(f'Subcomando sem nome literal em {path.name}.')
        commands.update(f'{path.name} {node.value}' for node in subcommands)
        if not subcommands:
            commands.add(path.name)
    return commands


class ProjectStateTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()

    def state(self, *roots):
        args = [sys.executable, str(SCRIPTS / 'fluxo.py'), 'estado']
        for root in roots:
            args.extend(('--root', str(root)))
        result = subprocess.run(args, cwd=self.root, check=True, capture_output=True, text=True)
        return json.loads(result.stdout)

    def project(self, path, **config):
        write(path / 'projeto.json', {'titulo': path.name, **config})
        return path

    def test_no_project(self):
        self.assertEqual(self.state(), {'projetos': [], 'avisos': []})

    def test_single_project_and_read_only(self):
        project = self.project(self.root, titulo='Em produção', estado='aguardando_audio', formato='9:16')
        write(project / 'material/paragrafos.json', [{'id': 'P001', 'texto': 'Fala.'}])

        def snapshot():
            return {p.relative_to(project): (sha(p), p.stat().st_mtime_ns)
                    for p in project.rglob('*') if p.is_file()}

        before = snapshot()
        result = self.state(project / 'projeto.json', project)
        self.assertEqual(result['avisos'], [])
        self.assertEqual(result['projetos'], [{
            'titulo': 'Em produção', 'pasta': str(project), 'estado': 'aguardando_audio',
            'formato': '9:16', 'audio_disponivel': False, 'proximo_passo': 'Retomar — falta o áudio.',
        }])
        self.assertEqual(snapshot(), before)

    def test_order_cap_and_one_level_scope(self):
        for index in range(7):
            folder = self.project(self.root / f'p{index}')
            time = 1000 + index
            os.utime(folder / 'projeto.json', (time, time))
        activity = self.root / 'p0' / 'slides-9x16' / 'apresentacao.html'
        activity.parent.mkdir()
        activity.write_text('prévia', encoding='utf-8')
        os.utime(activity, (2000, 2000))
        self.project(self.root / 'p1' / 'profundo')
        self.project(self.root / '.oculto')
        self.assertEqual([row['titulo'] for row in self.state()['projetos']],
                         ['p0', 'p6', 'p5', 'p4', 'p3'])
        result = self.state(self.root / 'p1')
        self.assertIn('profundo', [row['titulo'] for row in result['projetos']])
        self.assertNotIn('.oculto', [row['titulo'] for row in result['projetos']])

    def test_legacy_and_indicated_manifest(self):
        project = self.project(self.root / 'container' / 'legado', audio='material/audio.wav')
        write(project / 'material/paragrafos.json', [{'id': 'P001', 'texto': 'Fala.'}])
        (project / 'material/audio.wav').write_bytes(b'teste de presenca')
        result = self.state(project / 'projeto.json')['projetos']
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['estado'], 'audio_disponivel')
        self.assertEqual(result[0]['formato'], '16:9')
        self.assertTrue(result[0]['audio_disponivel'])
        self.assertIn('plano visual', result[0]['proximo_passo'])

    def test_missing_or_incomplete_audio_and_unreadable_manifest(self):
        project = self.project(self.root / 'pendente', estado='audio_disponivel', audio='material/partes')
        parts = project / 'material/partes'
        parts.mkdir(parents=True)
        write(project / 'material/paragrafos.json', [{'id': 'P001', 'texto': 'A.'}, {'id': 'P002', 'texto': 'B.'}])
        (parts / 'P001.wav').write_bytes(b'teste')
        broken = self.root / 'ilegivel'
        broken.mkdir()
        (broken / 'projeto.json').write_text('{', encoding='utf-8')
        result = self.state()
        self.assertEqual([row['pasta'] for row in result['avisos']], [str(broken)])
        row = result['projetos'][0]
        self.assertFalse(row['audio_disponivel'])
        self.assertEqual(row['estado'], 'aguardando_audio')
        self.assertIn('completar o áudio', row['proximo_passo'])
        (parts / 'P002.wav').write_bytes(b'teste')
        self.assertTrue(self.state()['projetos'][0]['audio_disponivel'])


class MenuConsistencyTest(unittest.TestCase):
    def test_menu_routes_cover_commands_and_references(self):
        doc = REFERENCE.read_text(encoding='utf-8')
        base, _, detail = doc.partition('## Regras de entrada')
        numbers = re.findall(r'^(\d+)\. \*\*[^\n]+', base, re.M)
        self.assertEqual(numbers, [str(i) for i in range(1, len(numbers) + 1)])
        self.assertTrue(numbers)
        self.assertTrue(base.rstrip().endswith('Qual dessas você quer usar?'))
        rows = re.findall(r'^\| (\d+) \| ([^|]+) \| ([^\n]+)', detail, re.M)
        self.assertEqual([number for number, _, _ in rows], numbers)
        for number, commands, procedures in rows:
            self.assertTrue(re.findall(r'`([^`]+)`', commands), number)
            links = re.findall(r'\]\(([^)]+)\)', procedures)
            self.assertTrue(links, number)
            for link in links:
                path, _, anchor = link.partition('#')
                target = REFERENCE.parent / path
                self.assertTrue(target.is_file(), link)
                if anchor:
                    headers = re.findall(r'^#+ (.+)$', target.read_text(encoding='utf-8'), re.M)
                    self.assertIn(anchor, [re.sub(r'[^\w -]', '', title.casefold()).replace(' ', '-')
                                           for title in headers], link)
        listed = set(re.findall(r'`([^\s`]+\.(?:py|mjs)(?: [\w-]+)?)`', detail.split('## Encaminhamentos', 1)[1]))
        self.assertEqual(listed, discover_commands())
