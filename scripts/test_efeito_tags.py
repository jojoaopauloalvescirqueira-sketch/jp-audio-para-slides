import unittest

from efeito_tags import measure


class TagEffectTest(unittest.TestCase):
    def measure(self, long_pause, confidence='alta'):
        rows=[]
        now=0.
        for i in range(7):
            duration=1.8 if i==5 else 1.
            tags={4:'pausa',5:'devagar',6:'suspirando'}
            rows.append({'paragrafo':'P001','texto':'Fala muito.','confianca':confidence if i==4 else 'alta',
                         'inicio_palavra':2*i,'fim_palavra':2*i+2,'inicio_s':now,'fim_s':now+duration,
                         'tags':[{'tag':tags[i],'palavra':2*i}] if i in tags else []})
            now+=duration+(long_pause if i==3 else .3)
        report={'frases_completas':rows,'frases':rows,'origem':'pausas_do_audio','inicio_s':0,'fim_s':now,
                'identidade':{},'studio_sha256':'hash','palavras':[{'inicio_s':0}]*14}
        return measure(report)['efeitos']

    def test_measured_speed_pause_and_listening(self):
        pause,slow,emotion=self.measure(.55)
        self.assertEqual((pause['estado'],slow['estado'],emotion['estado']),('efeito_medido','efeito_medido','ouvir'))
        self.assertEqual(pause['referencia'],.3)

    def test_comparable_pause_or_inconclusive(self):
        pause,*_=self.measure(.3)
        self.assertEqual(pause['estado'],'sem_efeito_distinto')
        self.assertIn('só esta frase',pause['sugestao'])
        pause,*_=self.measure(.55,'baixa')
        self.assertEqual(pause['estado'],'inconclusivo')
