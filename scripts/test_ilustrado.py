import copy
import unittest

from cenas import Words
from ilustrado import compile_illustrated, declarations

BIBLE={'paleta':{'fundo':'#122423','osso':'#fefefe','acento':'#83d0b2','suave':'#bedfd5','linha':'#334455'},
       'traco':'Chapado','proporcoes':'Adultos proporcionais','luz':'Luz difusa'}
CAST=[{'id':'voz','descricao':'Figura genérica','roupa':'Túnica','paleta':'Verde','folha':'voz_folha',
       'poses':[{'id':'voz_pe','descricao':'Em pé'},{'id':'voz_sentado','descricao':'Sentado'}]}]
SETTINGS=[{'id':'colina','descricao':'Colina ilustrativa',
           'camadas':[{'id':'colina_fundo','tipo':'fundo','descricao':'Céu'}]}]
PLAN={'versao':1,'cenas':[{'id':'C01','entrada':{'p':1,'trecho':'Eu espero'},'cenario':'colina',
       'camadas':[{'id':'f','asset':'colina_fundo'},{'id':'v','asset':'voz_sentado','escala':.4}],
       'acoes':[{'alvo':'v','acao':'trocar_pose','asset':'voz_pe','em':{'p':1,'trecho':'levanto'}},
                {'alvo':'titulo','acao':'titulo_entra','texto':'AGIR','em':{'p':1,'trecho':'levanto'}}]}]}


class IllustratedDataTest(unittest.TestCase):
    def setUp(self):
        self.words=Words([{'id':'P001','texto':'Eu espero e levanto.'}])
        self.assets=declarations(BIBLE,CAST,SETTINGS,{})

    def test_layers_poses_and_scene(self):
        scenes=compile_illustrated(PLAN,self.words,self.assets,{})
        self.assertEqual(scenes[0]['acoes'][0]['palavra'],3)
        self.assertEqual(self.assets['voz_pe']['referencia'],'voz_folha')

    def test_undeclared_assets_wrong_poses_and_long_titles(self):
        for section,index,key,value,expected in (
            ('camadas',1,'asset','inexistente','asset não declarado'),
            ('acoes',0,'asset','colina_fundo','mesmo personagem'),
            ('acoes',1,'texto','um dois três quatro cinco seis sete','seis palavras'),
            ('acoes',1,'texto','Maria Silva','nome próprio'),
        ):
            proposal=copy.deepcopy(PLAN)
            proposal['cenas'][0][section][index][key]=value
            with self.assertRaisesRegex(ValueError,expected):
                compile_illustrated(proposal,self.words,self.assets,{})

    def test_private_character_requires_explicit_consent(self):
        cast=copy.deepcopy(CAST)
        cast[0]['nome_privado']='Maria Silva'
        with self.assertRaisesRegex(ValueError,'consentimento'):
            declarations(BIBLE,cast,SETTINGS,{})
        allowed={'direcao_visual':{'nomes_autorizados':{'origem':'usuario','valor':['Maria Silva']}}}
        self.assertIn('voz_pe',declarations(BIBLE,cast,SETTINGS,allowed))

    def test_art_direction_records_origin_and_date_in_guide(self):
        import tempfile
        from pathlib import Path
        from ilustrado_direcao import record
        from projeto import read, write
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            write(root/'projeto.json',{'titulo':'Teste','estilo_video':'ilustrado'})
            write(root/'material/paragrafos.json',[{'id':'P001','texto':'Eu espero.'}])
            state=record(root,{'ritmo':{'valor':'calmo','origem':'usuario'}},assume=True)
            self.assertEqual(state['ritmo']['origem'],'usuario')
            self.assertEqual(state['marca']['origem'],'padrao_assumido')
            self.assertTrue(state['marca']['data'])
            self.assertEqual(state,read(root/'projeto.json')['direcao_visual'])
            self.assertIn('Direção visual',(root/'material/guia_producao.md').read_text())

    def test_png_alpha_and_upscale(self):
        import struct
        import tempfile
        from pathlib import Path
        import zlib
        from ilustrado_imagens import inspect_png
        def chunk(name, data):
            return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'a.png'
            entry={'alfa':True,'largura_recomendada':10,'altura_recomendada':10}
            for kind in (6,2):
                colors=4 if kind==6 else 3
                header=struct.pack('>IIBBBBB',1,1,8,kind,0,0,0)
                path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',header)+
                                 chunk(b'IDAT',zlib.compress(bytes(colors+1)))+chunk(b'IEND',b''))
                if kind==6:
                    w,h,alpha,warnings=inspect_png(path,entry)
                    self.assertEqual((w,h,alpha),(1,1,True))
                    self.assertIn('100%',warnings[0])
                else:
                    with self.assertRaisesRegex(ValueError,'alfa'):
                        inspect_png(path,entry)
