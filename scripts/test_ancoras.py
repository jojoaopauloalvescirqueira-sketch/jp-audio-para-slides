import tempfile
import unittest
from pathlib import Path

from ancoras import stamp, tempos_ancoras
from projeto import read, write


class AnchorTests(unittest.TestCase):
    def test_stamp_preserves_recognized_lexical_and_interpolated_methods(self):
        heard=[{'start': i*.5,'end':i*.5+.2} for i in range(4)]
        match={0:0,2:2,4:3}
        self.assertEqual(stamp(0,[0,2,4],match,heard,5,2),(0,'reconhecido',0,0.))
        self.assertEqual(stamp(1,[0,2,4],match,heard,5,2),(.5,'variacao_lexical',1,.8))
        self.assertEqual(stamp(3,[0,2,4],match,heard,5,2)[1],'interpolado')

    def test_estimated_anchors_have_explicit_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            write(root/'projeto.json',{'titulo':'Teste'})
            ps=[{'id':'P001','texto':'Aqui começa.'}]
            times,report=tempos_ancoras(root,[1],ps)
            self.assertEqual(times[1],60/140)
            self.assertEqual(report['ancoras'][0]['metodo'],'estimado')
            self.assertTrue(read(root/'material/marcacoes_acoes.json')['estimado'])
