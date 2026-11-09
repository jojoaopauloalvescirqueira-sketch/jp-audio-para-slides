import unittest

from pictograma_coreografia import phases, CUES
from pictograma_mix import intervals, ramp
from pictograma_pixels import check


class ChoreographyTests(unittest.TestCase):
    def test_phases_land_on_words_and_reject_conflict(self):
        frames = [18, 30, 73, 148, 168, 246, 266, 323, 384]
        sync = {'palavras': [{'quadro': frame} for frame in frames]}
        indexes = {name: index for index, name in enumerate(CUES)}
        scenes = [{'id':f'S0{index+1}', 'inicio':time} for index,time in enumerate((0, 3.6, 9.97))]
        cues = phases(indexes, sync, scenes, 13.175)['cues']
        self.assertEqual(frames, [item['frame'] for item in cues.values()])
        self.assertGreaterEqual(cues['virada']['end']-cues['virada']['start'], 24)
        sync['palavras'][2]['quadro'] = 50
        with self.assertRaisesRegex(ValueError, 'intervalo medido'):
            phases(indexes, sync, scenes, 13.175)

    def test_pixel_limits(self):
        for fraction, stop, tail in ((.84, 20, 2), (.92, 25, 2), (.92, 5, 0)):
            report = {'issues': []}
            check(report, 'png', {'ativo': {'fracao': fraction, 'pausa_maxima_quadros': stop},
                                  'cauda': {'mudancas': tail}})
            self.assertEqual(report['issues'][0]['codigo'], 'densidade_pixels_png')
        report = {'issues': []}
        check(report, 'mp4', {'ativo': {'fracao': .85, 'pausa_maxima_quadros': 24}, 'cauda': {'mudancas': 2}})
        self.assertEqual(report['issues'], [])

    def test_audio_windows_and_ramp(self):
        self.assertEqual(intervals([{'inicio_s':.25,'fim_s':.75}, {'inicio_s':.77,'fim_s':1.1},
                                    {'inicio_s':1.6,'fim_s':1.9}]), [(.25,1.1),(1.6,1.9)])
        self.assertEqual([ramp(t, 0, .3) for t in (0,.15,.3,1)], [0,.5,1,1])


if __name__ == '__main__':
    unittest.main()
