"""Escolhas de cânone e vínculo da folha de modelo com a aprovação."""
from pathlib import Path
import tempfile
import unittest

from pictograma_biblia import for_project
from pictograma_direcao import PALETTES
from pictograma_modelo import approve_model, model_dir, model_identity, require_model, write_sheet
from projeto import write


class VisualBibleTest(unittest.TestCase):
    def test_project_canon_in_range(self):
        self.assertEqual(for_project({})['canon']['cabecas'], 6)
        project = {'canon_pictograma': {'cabecas': 6.5, 'quadril_ao_chao': .48}}
        self.assertEqual(for_project(project)['canon']['cabecas'], 6.5)
        self.assertEqual(for_project(project)['canon']['ombros'], 1.8)
        for value in (4, 8, True, float('nan')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                for_project({'canon_pictograma': {'cabecas': value}})
        with self.assertRaises(ValueError):
            for_project({'canon_pictograma': {'joelho': 1}})

    def test_approval_requires_current_model(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            palette = PALETTES['escura']
            folder = model_dir(root)
            with self.assertRaisesRegex(ValueError, 'aguarde aprovação'):
                require_model(root, {}, palette)
            write_sheet(folder/'folha-de-modelo.html', {'titulo':'Cânone'}, palette)
            (folder/'folha-de-modelo.png').write_bytes(b'fixture')
            write(folder/'medicoes-modelo.json', {'issues':[{'codigo':'defeito'}]})
            write(folder/'identidade.json', model_identity(root, {}, palette))
            with self.assertRaisesRegex(ValueError, 'bloqueantes'):
                approve_model(root, {}, palette)
            write(folder/'medicoes-modelo.json', {'issues':[]})
            write(folder/'identidade.json', model_identity(root, {}, palette))
            approve_model(root, {}, palette)
            require_model(root, {}, palette)
            with self.assertRaisesRegex(ValueError, 'mudou'):
                require_model(root, {'canon_pictograma':{'cabecas':6.5}}, palette)
            (folder/'folha-de-modelo.png').write_bytes(b'alterado')
            with self.assertRaisesRegex(ValueError, 'mudou'):
                require_model(root, {}, palette)
