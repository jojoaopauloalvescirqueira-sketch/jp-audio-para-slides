from argparse import Namespace
from pathlib import Path
import tempfile
import unittest

from auditar_animacao import require_pass
from pictograma_auditoria import register_review, prepare_export
from projeto import sha, write


class AnimationAuditTest(unittest.TestCase):
    def test_audit_blockers_and_visual_review_are_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            material=root/'material'
            material.mkdir()
            preview=root/'apresentacao.html'
            preview.write_text('versão da prévia')
            identity={'previa_sha256':sha(preview),'formato':'9:16'}
            report={'identidade':identity,'issues':[],'modo':'integral','sampled':10,'quadros_totais':10}
            write(material/'auditoria_animacao.json',report)
            with self.assertRaisesRegex(ValueError,'parecer visual'):
                prepare_export(root,preview,'9:16',Namespace())
            source=root/'parecer.json'
            write(source,{'resultado':'aprovado','ocorrencias':[]})
            with self.assertRaisesRegex(ValueError,'três rodadas'):
                register_review(root,preview,'9:16',source,None,None,4)
            register_review(root,preview,'9:16',source,None,None,1)
            report['issues']=[{'codigo':'salto','nivel':'bloqueante'}]
            write(material/'auditoria_animacao.json',report)
            with self.assertRaisesRegex(ValueError,'salto'):
                prepare_export(root,preview,'9:16',Namespace())
            require_pass({'issues':[{'codigo':'risco','nivel':'atencao'}]})
            write(material/'auditoria_animacao.json',{'identidade':identity,'issues':[],'modo':'integral','sampled':10,'quadros_totais':10})
            preview.write_text('prévia modificada')
            with self.assertRaisesRegex(ValueError,'outra prévia'):
                register_review(root,preview,'9:16',source,None,None,2)
