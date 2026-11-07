"""Contrato dos três pontos de entrada, sem rede e sem síntese de voz."""
import tempfile,unittest,wave
from pathlib import Path
from unittest.mock import patch
from fluxo import iniciar,registrar,anexar
from fala import strip_voice,compare_speech
from projeto import read,write,load,audio_identity
from validar_roteiro import validate

class EntryCases(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.base=Path(self.tmp.name);self.root=self.base/'projeto'
  self.clean=self.base/'limpo.txt';self.clean.write_text('A água evapora [1].\n\nO vapor pode condensar.\n')
  self.studio=self.base/'studio.txt';self.studio.write_text('[thoughtful] A água evapora [1].\n\nO vapor pode condensar.\n')
 def init(self):iniciar(self.root,'Ciclo da água');registrar(self.root,self.clean,self.studio)
 def plan(self):write(self.root/'material/slides.json',[{'id':'S001','tipo':'capa','p':1,'frase_gatilho':'A água','title':'Ciclo da água'},{'id':'S002','tipo':'ideia','p':2,'frase_gatilho':'O vapor','title':'Condensação'}])
 def test_article_entry_keeps_source_and_requires_no_audio(self):
  article=self.base/'artigo.md';article.write_text('# Água\nA água evapora e o vapor pode condensar.')
  c=iniciar(self.root,'Ciclo da água',article);self.assertEqual(c['estado'],'roteirizacao');self.assertTrue((self.root/c['artigo']['arquivo']).is_file());self.assertFalse((self.root/'timeline.json').exists())
  registrar(self.root,self.clean,self.studio);self.assertEqual(read(self.root/'projeto.json')['estado'],'aguardando_audio')
 def test_script_entry_can_plan_without_audio(self):
  self.init();self.plan();c,ps,ss,_=load(self.root,require_audio=False);self.assertEqual(len(ps),2);self.assertEqual(ss[-1]['word_end'],8)
  with self.assertRaisesRegex(ValueError,'Áudio pendente'):load(self.root)
 def test_resume_preserves_paragraphs_and_plan(self):
  self.init();self.plan();before=(self.root/'material/paragrafos.json').read_bytes();plan=(self.root/'material/slides.json').read_bytes();f=self.base/'voz.wav';f.write_bytes(b'fixture')
  measured={'format':{'duration':'2.5'},'streams':[{'codec_type':'audio'}]}
  with patch('fluxo.probe',return_value=measured):anexar(self.root,f,'ffprobe');anexar(self.root,f,'ffprobe')
  self.assertEqual(before,(self.root/'material/paragrafos.json').read_bytes());self.assertEqual(plan,(self.root/'material/slides.json').read_bytes());self.assertEqual(read(self.root/'projeto.json')['estado'],'audio_disponivel');load(self.root)
  f.write_bytes(b'other')
  with patch('fluxo.probe',return_value=measured),self.assertRaisesRegex(ValueError,'diferente'):anexar(self.root,f,'ffprobe')
 def test_missing_duplicate_and_invalid_inputs(self):
  self.init()
  with self.assertRaises(ValueError):anexar(self.root,self.base/'ausente','ffprobe')
  d=self.base/'audios';d.mkdir();(d/'P001.wav').write_bytes(b'a');(d/'P001.mp3').write_bytes(b'b')
  with self.assertRaisesRegex(ValueError,'ambíguos'):anexar(self.root,d,'ffprobe')
  self.studio.write_text('Fala diferente.')
  with self.assertRaisesRegex(ValueError,'incompatível'):registrar(self.root,self.clean,self.studio)
 def test_resegmentation_is_rejected(self):
  self.assertFalse(compare_speech('A água.\n\nO vapor.','A água. O vapor.'))
 def test_ssml_quotes_preserve_same_speech(self):
  self.assertFalse(validate("Uma frase. <break time='0.7s' /> Outra frase.",'eleven_multilingual_v2','Uma frase. Outra frase.')['errors'])
 def test_canonical_tampering_is_rejected(self):
  self.init();self.plan();ps=read(self.root/'material/paragrafos.json');ps[0]['texto']='Outra fala.';write(self.root/'material/paragrafos.json',ps)
  with self.assertRaisesRegex(ValueError,'canônica'):load(self.root,require_audio=False)
 def test_literal_brackets_are_preserved(self):
  for literal in ('[1]','[nota do autor]','[Smith, 2020]'):
   self.assertEqual(strip_voice('[curious] Texto '+literal).strip(),'Texto '+literal)
   self.assertFalse(validate('[curious] Texto '+literal,'eleven_v4','Texto '+literal)['errors'])
 def test_known_literal_override_and_declared_control(self):
  self.assertFalse(validate('A palavra [thoughtful].','eleven_v4','A palavra [thoughtful].',literal_tags=['thoughtful'])['errors'])
  self.assertTrue(validate('[measured and firm] Texto.','eleven_v4','Texto.')['errors'])
  self.assertFalse(validate('[measured and firm] Texto.','eleven_v4','Texto.',audio_tags=['measured and firm'])['errors'])
 def test_non_audio_is_rejected(self):
  self.init();f=self.base/'video.mp4';f.write_bytes(b'fixture')
  with patch('fluxo.probe',return_value={'format':{'duration':'2'},'streams':[{'codec_type':'video'}]}),self.assertRaisesRegex(ValueError,'faixa de áudio'):anexar(self.root,f,'ffprobe')
  self.assertIsNone(read(self.root/'projeto.json')['audio'])
 def test_changed_canonical_is_not_silently_replaced(self):
  self.init();self.clean.write_text('Outra fala.')
  with self.assertRaisesRegex(ValueError,'canônica'):registrar(self.root,self.clean)

if __name__=='__main__':unittest.main()
