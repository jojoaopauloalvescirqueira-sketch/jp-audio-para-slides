import tempfile
import unittest
from pathlib import Path

from cenas import Words, compile_plan, derive_slides, schedule, validate_box
from projeto import read


class SceneTests(unittest.TestCase):
    def setUp(self):
        self.words = Words([{'id':'P001','texto':'Eu ando. Eu paro.'}])
        self.plan = {'versao':1,'cenas':[{'id':'A','entrada':{'p':1,'trecho':'Eu','ocorrencia':1},
                                         'elementos':[{'id':'X','tipo':'forma','x':90,'y':470,'w':40,'h':40}],
                                         'acoes':[{'alvo':'X','acao':'exibir','em':{'p':1,'trecho':'paro'}}]}]}

    def compile(self):
        return compile_plan(self.plan,self.words,{'forma':['exibir']},lambda row:row,lambda row,target:row)

    def test_coverage_derived_slides_and_schedule(self):
        scenes=self.compile()
        timeline=schedule(scenes,[0,.6,1.2,1.8],2.4)
        self.assertEqual(timeline[0]['acoes'][0]['tempo'],1.8)
        self.assertEqual(timeline[0]['fala'],'Eu ando. Eu paro.')
        with tempfile.TemporaryDirectory() as tmp:
            derive_slides(tmp,scenes,self.words)
            self.assertEqual(read(Path(tmp)/'slides.json')[0]['frase_gatilho'],'Eu')
        self.plan['cenas'][0]['entrada']['ocorrencia']=2
        with self.assertRaisesRegex(ValueError,'cobrir'):
            self.compile()

    def test_ambiguity_rhythm_and_geometry(self):
        with self.assertRaisesRegex(ValueError,'justificativa_ritmo'):
            schedule(self.compile(),[0,.2,.4,.6],.9)
        del self.plan['cenas'][0]['entrada']['ocorrencia']
        with self.assertRaisesRegex(ValueError,'ambígua'):
            self.compile()
        layer=self.plan['cenas'][0]['elementos'][0]
        validate_box(layer,(64,440,892,1320))
        with self.assertRaisesRegex(ValueError,'área segura'):
            validate_box(dict(layer,x=880),(64,440,892,1320))

    def test_core_has_no_style_names(self):
        base=Path(__file__).resolve().parents[1]
        for path in ('assets/motor-cenas.js','scripts/cenas.py','scripts/ancoras.py','scripts/renderizar_cenas.mjs'):
            source=(base/path).read_text().casefold()
            self.assertNotIn('pictograma',source)
            self.assertNotIn('ilustrado',source)
