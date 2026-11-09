import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from cenas import Words
from pictograma_banco import LIMITS, VISUAL, cmu_adoption, evaluate, stamps
from pictograma_composicao import compile_direction


class BancoTests(unittest.TestCase):
    def test_local_excerpt_clock(self):
        words=[{'texto':'início','inicio_s':395.3,'fim_s':395.8}]
        result=stamps(words,395.3)[0]
        self.assertEqual(result['inicio_s'],0)
        self.assertAlmostEqual(result['fim_s'],.5)
        self.assertEqual((result['quadro'],result['fim_quadro']),(0,15))
        self.assertEqual(words[0]['inicio_s'],395.3)

    def test_low_confidence_blocks_and_grade_drop_blocks(self):
        evidence={'video':'v.mp4','video_sha256':'x','auditoria_integral':True,'bloqueantes':0,
                  'reimplementacao_declarativa':True,'notas':dict.fromkeys(VISUAL,4),
                  'medicoes':{**{k:v[0] for k,v in LIMITS.items()},'sombra_propria':True,'legenda_exata':True}}
        self.assertFalse(evaluate(evidence))
        self.assertTrue(evaluate({**evidence,'confianca':'baixa','divergencias':['fim da frase']}))
        self.assertTrue(evaluate(evidence,{'notas':{**evidence['notas'],'texto':5}}))
        self.assertTrue(evaluate({**evidence,'medicoes':{**evidence['medicoes'],'sola_px':3}}))

    def test_cmu_requires_improved_motion_and_passing_bank(self):
        base={'naturalidade_movimento':4,'prova_sha256':'base'}
        candidate={**base,'prova_sha256':'nova','video':'v.mp4','video_sha256':'new',
                   'auditoria_integral':True,'bloqueantes':0,'notas':dict.fromkeys(VISUAL,4),
                   'medicoes':{**{k:v[0] for k,v in LIMITS.items()},'sombra_propria':True,'legenda_exata':True}}
        self.assertFalse(cmu_adoption(base,candidate))
        self.assertTrue(cmu_adoption(base,{**candidate,'naturalidade_movimento':5}))
        self.assertFalse(cmu_adoption(base,{**candidate,'naturalidade_movimento':5,'bloqueantes':1}))

    def test_repeated_staging_and_invalid_actor(self):
        words=Words([{'id':'P053','texto':'primeira segunda terceira'}])
        plan={'titulo':'Ensaio','sensivel':False,'quadro_acoes':[],
              'batidas':[{'titulo':word,'padrao':'pergunta','rotulos':[],'simbolos':['pergunta'],
                         'em':{'p':53,'trecho':word}} for word in ('primeira','segunda','terceira')]}
        with self.assertRaisesRegex(ValueError,'terceira encenação'):
            compile_direction(plan,words,[0,3,6],9)
        plan['batidas']=plan['batidas'][:2]
        plan['batidas'][1]['acao']={'tipo':'olhar_para','ator':'intruso','em':{'p':53,'trecho':'segunda'}}
        with self.assertRaisesRegex(ValueError,'participantes'):
            compile_direction(plan,words,[0,3,6],9)

    def test_continuidade_opt_in_camadas_e_corte(self):
        words=Words([{'id':'P001','texto':'Primeira segunda terceira quarta'}])
        rows=[
            {'padrao':padrao,'rotulos':[],'simbolos':[],'em':{'p':1,'trecho':trecho}}
            for padrao,trecho in zip(('conceito','pergunta','comparacao','conclusao'),
                                     ('Primeira','segunda','terceira','quarta'))
        ]
        rows[1]['cenario_ilustrado']={'tipo':'rua','em':rows[1]['em']}
        rows[2]['cenario_ilustrado']={'tipo':'rua','em':rows[2]['em']}
        rows[3]['corte_justificado']='Muda o ponto de vista narrativo.'
        plan={'titulo':'Ensaio','sensivel':False,'quadro_acoes':[],'batidas':rows}
        args=(words,[0,1,2,3],4)
        self.assertFalse(any('entrada_continua' in scene for scene in compile_direction(plan,*args)))
        scenes=compile_direction({**plan,'continuidade':True},*args)
        self.assertEqual([scene['entrada_continua']['tipo'] for scene in scenes[1:]],
                         ['camadas','pose','corte_justificado'])
        self.assertEqual([scene['entrada_continua']['quadros'] for scene in scenes[1:]],[21,21,0])

    def test_continuidade_audita_pulso_do_mesmo_personagem_em_outro_indice(self):
        from pictograma_gestos import auditar_gestos
        def actor(x):
            return {'D':{'excesso':0,'contato':None,'ativa':False,'posicao':[x,400]}}
        before={'f':10,'scene':'a','ids':['principal','interlocutor'],'actors':[actor(100),actor(500)]}
        current={'f':11,'scene':'b','ids':['interlocutor'],'actors':[actor(542)],'transicao':True}
        self.assertIn('na transição',auditar_gestos(current,before)[0]['correcao'])
        current['actors']=[actor(510)]
        self.assertFalse(auditar_gestos(current,before))

    def test_acentos_conversa_alinhados_e_distintos(self):
        words=Words([{'id':'P001','texto':'Agora pergunta e responde'}])
        accents=[{'tipo':'abrir','em':{'p':1,'trecho':'pergunta'}},
                 {'tipo':'ponderar','em':{'p':1,'trecho':'responde'}}]
        plan={'titulo':'Conversa','sensivel':False,'quadro_acoes':[],
              'gestual':'expressivo_intencional','batidas':[
                  {'padrao':'conceito','layout':'dupla','em':{'p':1,'trecho':'Agora'},
                   'rotulos':[],'simbolos':[],'acao':{
                       'tipo':'conversar','ator':'principal','alvo':'outro',
                       'em':{'p':1,'trecho':'pergunta'},'acentos':accents,
                       'gesto':{'mao':'D','alvo':'interlocutor','intencao':'conversar','saida':'repouso'}}}]}
        args=(plan,words,[0,1,1.5,2],3)
        stages=compile_direction(*args)[0]['movimento']['acentos']
        self.assertEqual([r['pouso'] for r in stages],[30,60])
        self.assertLess(stages[0]['fim'],stages[1]['inicio'])
        accents[1]['tipo']='abrir'
        with self.assertRaisesRegex(ValueError,'Varie a intenção'):
            compile_direction(*args)
        accents[1]['tipo']='ponderar'
        accents[1]['em']['trecho']='e'
        with self.assertRaisesRegex(ValueError,'Separe os acentos'):
            compile_direction(*args)

    def test_mao_presente_tem_tempo_para_sustentar_e_sair(self):
        from pictograma_gestos import schedule
        action={'tipo':'mao_presente','pouso':20,
                'gesto':{'mao':'D','alvo':'palma','intencao':'acolher','saida':'repouso'}}
        schedule(action,0,100)
        self.assertEqual(action['presenca'],{'olhar':14,'alcance':35,'sustenta_ate':51})
        self.assertEqual(action['fim'],85)
        with self.assertRaisesRegex(ValueError,'EC-101'):
            schedule(action,0,39)

    def test_figuras_cenario_usam_ancoras_da_batida(self):
        words=Words([{'id':'P001','texto':'Introdução animal idoso criança fechamento'}])
        row={'padrao':'enumeracao','rotulos':[],'simbolos':[],'em':{'p':1,'trecho':'Introdução'}}
        scene={'tipo':'rua','em':row['em'],'figuras':[
            {'tipo':name,'em':{'p':1,'trecho':name}}
            for name in ('animal','idoso')
        ]}
        plan={'titulo':'Ensaio','sensivel':False,'quadro_acoes':[],'batidas':[
            {**row,'cenario_ilustrado':scene},
            {**row,'padrao':'conclusao','em':{'p':1,'trecho':'fechamento'}}]}
        args=(plan,words,[0,1,2,3,4],5)
        compiled=compile_direction(*args)[0]['cenario_ilustrado']
        self.assertEqual([f['pouso'] for f in compiled['figuras']],[30,60])
        self.assertEqual(compiled['revelacao_figuras'],
                         {'entrada_quadros':9,'saida_inicio':107,'saida_fim':119})
        scene['figuras'].reverse()
        with self.assertRaisesRegex(ValueError,'âncoras crescentes'):
            compile_direction(*args)
        scene['figuras'][0]['em']['trecho']='fechamento'
        scene['figuras'].reverse()
        with self.assertRaisesRegex(ValueError,'dentro da batida'):
            compile_direction(*args)

    def test_generic_runtime_has_no_literals_of_pilot(self):
        assets=Path(__file__).resolve().parents[1]/'assets'
        for filename in ('kit-pictograma-declarativo.js','pictograma-acoes.js'):
            source=(assets/filename).read_text()
            self.assertNotRegex(source,r'\b(?:P\d{3}|S\d{2}|DEUS|RECEBE|AGIR|FAZ)\b')
            self.assertNotIn('virada_banco_ajuda',source)
        node=os.environ.get('JP_NODE') or shutil.which('node')
        if not node:
            self.skipTest('Informe JP_NODE.')
        program="""
const fs=require('fs'); global.window=global;
for(const f of ['pictograma-figura.js','pictograma-rig.js','pictograma-acoes.js'])eval(fs.readFileSync(f,'utf8'));
const b=JSON.parse(fs.readFileSync('biblia-anatomica-pictograma.json','utf8'));
for(const type of process.argv.slice(1)){
 const poses=PictogramaAcoes.resolve(b,{tipo:type,inicio:0,fim:30},15);
 if(!poses.length||poses.some(p=>p.bones.some(s=>!Number.isFinite(s.real)))) throw Error(type);
}
"""
        from pictograma_composicao import ACTIONS
        subprocess.run([node,'-e',program,*sorted(ACTIONS)],cwd=assets,check=True)

    def test_confirmed_cut_is_bound_to_audio_and_selected_intervals(self):
        from unittest.mock import patch
        from pictograma_banco import confirm_cut
        phrase={'texto':'fronteira','inicio_s':1.0,'fim_s':2.0}
        alignment={**phrase,'frases':[{**phrase,'inicio_palavra':4,'fim_palavra':5,'confianca':'baixa'}]}
        project={'confirmacao_corte':{'audio_sha256':'hash','inicio_s':.96,'fim_s':2.04,'frases':[phrase]}}
        words=[{'texto':'fronteira'}]
        with self.assertRaisesRegex(ValueError,'outra gravação'):
            confirm_cut(project,'outro hash',alignment,words,4,[])
        refined=[{'texto':'fronteira','inicio_s':1.02}]
        with patch('pausas_audio.word_boundaries',return_value=refined):
            self.assertEqual(confirm_cut(project,'hash',alignment,words,4,[]),(.96,2.04))
        self.assertEqual(words,refined)

    def test_anatomical_player_loads_library_without_cinematic_kit(self):
        from tempfile import TemporaryDirectory
        from types import SimpleNamespace
        from pictograma import ASSETS, player
        from pictograma_biblia import for_project
        from projeto import read
        template=read(ASSETS/'referencia-pictograma/fixture-catalogo.json')
        core=template['coreografia']
        frames={'sentar':88,'levantar':238,'ajudar':310,'receber':420,'fazer':460}
        for name,frame in frames.items():
            core['cues'][name]['frame']=frame
        core['corte']=46
        core['encenacao']=read(ASSETS/'pictograma-legado-cinematico.json')
        direction={'marca':'nao','legenda':'nao','paleta':'escura','tom':'didatico',
                   'densidade_animacao':'abundante'}
        with TemporaryDirectory() as directory:
            path=Path(directory)/'previa.html'
            player(path,{'titulo':'Ensaio'},direction,'9:16',template['cenas'],
                   SimpleNamespace(words=[]),[],20,True,coreografia=core,
                   bible=for_project({}),rig_anatomico=read(ASSETS/'biblia-anatomica-pictograma.json'))
            html=path.read_text()
        self.assertIn("registrarKit('pictograma-biblioteca'",html)
        self.assertNotIn("registrarKit('pictograma-cinematico'",html)
        self.assertNotIn('window.PictogramaAtuacao',html)
        self.assertEqual(core['sequencia']['intervalos'][0],{'tipo':'marcha','de':46,'ate':62})

    def test_shared_patterns_keep_pixel_positions_in_parameters(self):
        import re
        from pictograma import ASSETS
        for file in ('pictograma-blocos.js','pictograma-virada.js'):
            with self.subTest(file=file):
                source=(ASSETS/file).read_text()
                # Decimal easing and proportions are allowed. Absolute pixel positions
                # must come from parameters, including positions in transform strings.
                self.assertFalse(re.findall(r'(?<![\w.])-?\d{3,}(?![\w.])',source))
        declarative=(ASSETS/'kit-pictograma-declarativo.js').read_text()
        cinematic=(ASSETS/'pictograma-blocos.js').read_text()
        self.assertIn('window.PictogramaVirada(api)',declarative)
        self.assertIn('window.PictogramaVirada(api)',cinematic)

    def test_body_library_preserves_bone_lengths_and_grounds_kneeling(self):
        node=os.environ.get('JP_NODE') or shutil.which('node')
        if not node:
            self.skipTest('Informe JP_NODE.')
        assets=Path(__file__).resolve().parents[1]/'assets'
        program="""
const fs=require('fs');
global.window=global;
for(const name of ['pictograma-figura','pictograma-rig','pictograma-acoes']){
  eval(fs.readFileSync(name+'.js','utf8'));
}
const bible=JSON.parse(fs.readFileSync('biblia-anatomica-pictograma.json','utf8'));
const actions=['ajoelhar','curvar','virar','aproximar','afastar','agachar','sentar_no_chao','abracar','amparar','carregar'];
for(const tipo of actions){
  for(let frame=0;frame<=32;frame++){
    const pose=PictogramaAcoes.resolve(bible,{tipo,corpo:true,inicio:0,fim:32,pouso:16},frame)[0];
    if(pose.bones.some(bone=>Math.abs(bone.real-bone.nominal)>.001))throw Error(tipo+' '+frame);
    if(tipo==='ajoelhar'&&frame===16&&Math.abs(pose.joints.joelhoE[1])>.15)throw Error('Joelho suspenso.');
  }
}
"""
        subprocess.run([node,'-e',program],cwd=assets,check=True)

    def test_storyboard_batches_budget_and_preserves_explicit_choices(self):
        from pictograma_opcoes import options, resolve_choices
        phrase='Se ela puder levantar.'
        row={'id':'batida-1','fala':phrase,'padrao':'conceito',
             'layout':'centro','movimento':{'tipo':'recusar'}}
        short=options([row],5,[])
        self.assertTrue(short['falha'])
        with self.assertRaisesRegex(ValueError,'reduzir'):
            resolve_choices({},short,'1B')
        plan=options([row],10,[])
        project={}
        self.assertEqual(resolve_choices(project,plan,'1B')['batida-1']['origem'],'usuario')
        self.assertEqual(resolve_choices(project,plan,automatic=True)['batida-1']['opcao'],'A')
        self.assertEqual(resolve_choices(project,plan)['batida-1']['opcao'],'B')

    def test_grafico_exige_rotulos_e_ancora_da_batida(self):
        words=Words([{'id':'P001','texto':'Esperar e depois agir.'}])
        start={'p':1,'trecho':'Esperar'}
        graph={'tipo':'contraste','textos':['ESPERA','AÇÃO'],'em':{'p':1,'trecho':'agir'}}
        row={'padrao':'comparacao','em':start,'rotulos':[],'simbolos':[],'grafico':graph}
        plan={'titulo':'Ensaio','sensivel':False,'batidas':[row]}
        result=compile_direction(plan,words,[0,.4,1,1.6],3)[0]['grafico']
        self.assertEqual(result['pouso'],48)
        self.assertLess(result['inicio'],result['pouso'])
        self.assertGreater(result['fim'],result['pouso'])
        graph['textos']=['ESPERA']
        with self.assertRaisesRegex(ValueError,'rótulos incompatível'):
            compile_direction(plan,words,[0,.4,1,1.6],3)
        graph['textos'].append('AÇÃO')
        graph['em']['trecho']='palavra ausente'
        with self.assertRaises(ValueError):
            compile_direction(plan,words,[0,.4,1,1.6],3)

    def test_cenario_ilustrado_ancorado_e_continuo(self):
        words = Words([{'id':'P001','texto':'Olhe a rua. Veja o banco.'}])
        first = {'p':1,'trecho':'Olhe'}
        second = {'p':1,'trecho':'Veja'}
        def beat(anchor):
            return {'padrao':'comparacao','em':anchor,'rotulos':[],'simbolos':[],
                    'cenario_ilustrado':{'tipo':'rua','em':anchor}}
        plan = {'titulo':'Ensaio','sensivel':False,'batidas':[beat(first),beat(second)]}
        times = [0,.15,.3,1,1.15,1.4]
        compiled = compile_direction(plan,words,times,2)
        self.assertEqual(compiled[0]['cenario_ilustrado']['pouso'],0)
        self.assertTrue(compiled[1]['cenario_ilustrado']['continuo'])
        plan['batidas'][0]['cenario_ilustrado']['em'] = second
        with self.assertRaisesRegex(ValueError,'dentro da batida'):
            compile_direction(plan,words,times,2)
        plan['batidas'][0]['cenario_ilustrado']['tipo'] = 'inexistente'
        with self.assertRaisesRegex(ValueError,'indisponível'):
            compile_direction(plan,words,times,2)
