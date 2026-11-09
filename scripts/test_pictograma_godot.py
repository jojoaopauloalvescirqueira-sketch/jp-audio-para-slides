from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from pictograma_godot import PUBLISHER, locate, local_path, verify


class GodotLocationTests(unittest.TestCase):
    def test_refuses_executable_under_mobile_documents(self):
        with self.assertRaisesRegex(ValueError, 'fora do iCloud'):
            local_path('/Users/test/Library/Mobile Documents/Projeto/Godot.app/Contents/MacOS/Godot')

    def test_refuses_symlink_into_mobile_documents(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cloud = root / 'Mobile Documents'
            cloud.mkdir()
            godot = cloud / 'Godot'
            godot.touch()
            (root/'local').symlink_to(godot)
            with self.assertRaisesRegex(ValueError, 'Mobile Documents'):
                locate({'JP_GODOT':str(root/'local')},root)

    def test_accepts_local_override(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp)/'Godot.app'
            godot = app/'Contents/MacOS/Godot'
            godot.parent.mkdir(parents=True)
            godot.touch()
            godot.chmod(0o755)
            self.assertEqual(locate({'JP_GODOT':str(app)}, Path(temp)), godot.resolve())


    def test_missing_override_explains_local_install(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, 'Godot indisponível'):
                locate({'JP_GODOT':str(Path(temp)/'ausente')}, Path(temp))

    def test_signature_failure_prevents_execution(self):
        godot = Path('/Users/test/Applications/Godot.app/Contents/MacOS/Godot')
        failure = subprocess.CompletedProcess([], 1, 'invalid signature')
        with patch('pictograma_godot.subprocess.run', return_value=failure), \
                patch('pictograma_godot.subprocess.check_output') as version:
            with self.assertRaisesRegex(ValueError, 'Gatekeeper'):
                verify(godot)
            version.assert_not_called()

    def test_rejects_godot_3_after_successful_verification(self):
        godot = Path('/Users/test/Applications/Godot.app/Contents/MacOS/Godot')
        signed = subprocess.CompletedProcess([], 0, f'origin=Developer ID Application: {PUBLISHER}')
        with patch('pictograma_godot.subprocess.run', return_value=signed), \
                patch('pictograma_godot.subprocess.check_output', return_value='3.6.stable'):
            with self.assertRaisesRegex(ValueError, 'Godot 4.x'):
                verify(godot)
