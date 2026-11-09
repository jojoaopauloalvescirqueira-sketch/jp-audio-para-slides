"""Cenários de compatibilidade e integridade, sem geração de áudio."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from validar_roteiro import validate, main


class ProductionCases(unittest.TestCase):
    def test_clone_expressive_script_has_same_clean_speech(self):
        r = validate('[curious] Quem administra a moeda?\n\n[thoughtful] A pergunta exige cuidado.',
                     'eleven_v4', 'Quem administra a moeda?\n\nA pergunta exige cuidado.')
        self.assertFalse(r['errors'])
        self.assertTrue(r['spoken_text_equal_to_clean'])
        self.assertFalse(r['duration_estimate']['audio_measured'])

    def test_unsupported_ssml_on_expressive_models(self):
        for model in ('eleven_v4', 'eleven_v3'):
            with self.subTest(model=model):
                self.assertTrue(validate('Uma promessa. <break time="1s" /> Outra regra.', model)['errors'])

    def test_multilingual_version_uses_its_own_controls(self):
        r = validate('Uma promessa. <break time="0.7s" /> Outra regra.', 'eleven_multilingual_v2',
                     'Uma promessa. Outra regra.')
        self.assertFalse(r['errors'])
        self.assertEqual(r['duration_estimate']['requested_ssml_pause_seconds'], .7)

    def test_v2_rejects_expressive_audio_tags(self):
        self.assertTrue(validate('[curious] Quem paga a conta?', 'eleven_multilingual_v2')['errors'])

    def test_bad_and_oversized_breaks_are_not_approved(self):
        for tag in ('<break time="4s" />', '<break time="700ms" />', '<break time="nan" />', '<prosody rate="slow">'):
            with self.subTest(tag=tag):
                self.assertTrue(validate('Pergunta. '+tag+' Resposta.', 'eleven_multilingual_v2')['errors'])

    def test_editing_directions_cannot_enter_voice_text(self):
        for tag in ('[zoom in]', '[câmera próxima]', '[P01]', '[música suave]'):
            with self.subTest(tag=tag):
                self.assertTrue(validate(tag+' Uma pergunta.', 'eleven_v4')['errors'])

    def test_unknown_auditory_direction_requires_review_not_fake_certification(self):
        r = validate('[measured and firm] Uma pergunta.', 'eleven_v4')
        self.assertFalse(r['errors'])
        self.assertTrue(any('experimental' in w for w in r['warnings']))

    def test_portuguese_interface_tags_need_no_custom_registration(self):
        tags=('pausa','suavemente','devagar','com voz fraca','suspirando',
              'com a voz embargada','rindo baixinho')
        for tag in tags:
            with self.subTest(tag=tag):
                result=validate(f'[{tag}] Uma pergunta.', 'eleven_v4', 'Uma pergunta.')
                self.assertTrue(result['spoken_text_equal_to_clean'])
                self.assertFalse(result['errors'])
                self.assertFalse(any('experimental' in w for w in result['warnings']))
        unknown='[fale com lentidão] Uma pergunta.'
        self.assertFalse(validate(unknown,'eleven_v4','Uma pergunta.')['spoken_text_equal_to_clean'])
        self.assertTrue(validate(unknown,'eleven_v4','Uma pergunta.',
                                 audio_tags=('fale com lentidão',))['spoken_text_equal_to_clean'])

    def test_qualitative_pause_is_not_given_fabricated_seconds(self):
        r = validate('[short pause] Uma pergunta.', 'eleven_v4')
        self.assertEqual(r['duration_estimate']['qualitative_pause_tags'], 1)
        self.assertEqual(r['duration_estimate']['requested_ssml_pause_seconds'], 0)

    def test_changed_clean_claim_fails(self):
        r = validate('A hipótese não foi confirmada.', 'eleven_v4', 'A hipótese foi confirmada.')
        self.assertTrue(r['errors'])
        self.assertFalse(r['spoken_text_equal_to_clean'])

    def test_clean_must_not_keep_controls(self):
        self.assertTrue(validate('[curious] Uma pergunta.', 'eleven_v4', '[curious] Uma pergunta.')['errors'])

    def test_unicode_normalization_and_line_breaks_do_not_change_speech(self):
        import unicodedata
        text = 'A hipótese é uma questão.'
        self.assertFalse(validate('[thoughtful] '+text, 'eleven_v4', unicodedata.normalize('NFD', text))['errors'])

    def test_scene_ids_and_dates_generate_review_warnings(self):
        r = validate('P01: Em 1971, a promessa mudou.', 'eleven_v4')
        self.assertGreaterEqual(len(r['warnings']), 2)

    def test_model_limit_is_not_mistaken_for_whole_studio_project(self):
        r = validate(('Fala. '*500)+'\n\n'+('Outra fala. '*300), 'eleven_v3')
        self.assertFalse(r['errors'])
        self.assertTrue(r['warnings'])
        self.assertTrue(validate('palavra '*800, 'eleven_v3')['errors'])

    def test_empty_and_unclosed_tags_fail(self):
        for text in ('', '[curious]', '[curious Uma pergunta.', '[] Uma pergunta.'):
            with self.subTest(text=text):
                self.assertTrue(validate(text, 'eleven_v4')['errors'])

    def test_invalid_rate_is_not_a_duration(self):
        for low, high in ((0,160),(160,125),(125,float('nan'))):
            with self.subTest(low=low, high=high):
                with self.assertRaises(ValueError): validate('Uma pergunta.', 'eleven_v4', wpm_min=low,wpm_max=high)

    def test_cli_exits_on_incompatibility(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fala.txt';p.write_text('[curious] Uma pergunta.', encoding='utf-8')
            out=io.StringIO()
            with contextlib.redirect_stdout(out): code=main([str(p),'--model','eleven_multilingual_v2'])
            self.assertEqual(code,1)
            self.assertEqual(json.loads(out.getvalue())['status'],'erro')


if __name__ == '__main__':
    unittest.main()
