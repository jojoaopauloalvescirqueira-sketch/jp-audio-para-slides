import random
import unittest

from pausas_audio import acoustic, aligned, phrases, speech_blocks, word_boundaries


def noise_signal(lengths):
    rng=random.Random(270)
    signal=[]
    for i,n in enumerate(lengths):
        signal.extend([rng.uniform(850,1250) if i%2 else 0 for _ in range(n)])
    return signal


class PauseAlignmentTest(unittest.TestCase):
    def test_measured_noise_blocks(self):
        rms=noise_signal([20,40,17,40,23])
        blocks=speech_blocks(rms,rms)
        self.assertEqual(blocks,[(20,60),(77,117)])
        clauses=phrases([{'id':'P001','texto':'Uma frase. Outra frase.'}])
        report=aligned(clauses,blocks,rms,0,4)
        self.assertEqual(report['confianca'],'alta')
        self.assertEqual([(r['inicio_s'],r['fim_s']) for r in report['frases']],[(.2,.6),(.77,1.17)])

    def test_missing_strong_pause_and_ambiguous_assignment(self):
        clauses=phrases([{'id':'P001','texto':'Uma frase. Outra frase.'}])
        rms=noise_signal([20,80,20])
        missing=aligned(clauses,speech_blocks(rms,rms),rms,0,4)
        self.assertEqual(missing['confianca'],'baixa')
        self.assertEqual(missing['pontuacoes_sem_silencio'][0]['tipo'],'forte')
        rms=noise_signal([20,40,25,40,25,40,20])
        ambiguous=aligned(clauses,speech_blocks(rms,rms),rms,0,4)
        self.assertEqual(ambiguous['confianca'],'baixa')

    def test_internal_boundary_uses_energy(self):
        # A short dip within the phrase is too short to become a sentence pause.
        rms=noise_signal([20,20,5,40,20])
        rows=word_boundaries(('que','Deus','fala'),.2,.85,rms)
        self.assertEqual(rows[1]['metodo'],'refinado_energia')
        self.assertTrue(.40<=rows[1]['inicio_s']<=.45,rows)
