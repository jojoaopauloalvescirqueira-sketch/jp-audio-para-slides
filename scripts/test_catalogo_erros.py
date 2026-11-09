"""Integridade do catálogo e mutações que os validadores devem reprovar."""
import importlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

from catalogo_erros import ROOT, catalogo, markdown


class CatalogoTests(unittest.TestCase):
    def test_integridade(self):
        rows = catalogo()
        self.assertEqual([row['id'] for row in rows], [f'EC-{i:03}' for i in range(1,117)])
        self.assertEqual(markdown(rows), (ROOT/'references/erros_conhecidos.md').read_text())
        for row in rows:
            with self.subTest(id=row['id']):
                image = ROOT / row['exemplo']
                self.assertTrue(image.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
                self.assertLessEqual(image.stat().st_size, 200_000)
                if row['estado'] != 'resolvido':
                    continue
                file, symbol = row['checagem']['funcao'].split(':')
                body=(ROOT / 'scripts' / file).read_text()
                self.assertRegex(body, rf'\b{re.escape(symbol)}\b')
                module, cls, method = row['teste'].split('.')
                self.assertTrue(callable(getattr(getattr(importlib.import_module(module), cls), method)))

    def js(self, source):
        node = os.environ.get('JP_NODE') or shutil.which('node')
        if not node:
            self.skipTest('Informe JP_NODE para testar as checagens vetoriais.')
        subprocess.run([node, '-e', "const assert=require('node:assert/strict');"
                        "const a=require('node:vm').runInNewContext(require('node:fs').readFileSync("
                        "'auditoria_catalogo.js','utf8')+';window.AuditoriaCatalogo',{window:{}});"+source],
                       cwd=Path(__file__).parent, check=True)

    def test_ombreira_e_emenda(self):
        self.js("""const p={pescoço:true,ombros:[true,true],perfil:[{largo:1.4,cintura:.95,salto:.13}]};
            assert(a.juncoes(p)); assert(!a.juncoes({...p,pescoço:false}));
            assert(!a.juncoes({...p,ombros:[true,false]}));
            assert(!a.juncoes({...p,perfil:[{largo:1.4,cintura:.95,salto:.48}]}));""")

    def test_palma_solteira(self):
        self.js("""const p={ligacoes:[true,true],distancia:45,cabeca:100,altura:30,pouso:true};
            assert(a.palmas(p)); assert(!a.palmas({...p,ligacoes:[true,false]}));
            assert(!a.palmas({...p,distancia:110})); assert(!a.palmas({...p,pouso:false}));""")

    def test_nota_nao_confere(self):
        self.js("""const p={tipo:'maos_em_contato'};
            assert(a.afirmacoes(p,{maos_em_contato:true}));
            assert(!a.afirmacoes(p,{maos_em_contato:false,mao_no_ombro:true}));""")

    def test_mixagem_antiga_bloqueada(self):
        from unittest.mock import patch
        from pictograma_mix import verify
        with patch('pictograma_mix.loudness', return_value={'input_i':'-25.4','input_tp':'-8.2'}):
            with self.assertRaisesRegex(ValueError, 'Mixagem fora'):
                verify('ffmpeg', 'mp4-temporario', {'diferenca_db':22})

    def test_pixels_estaticos_reprovam_mesmo_com_dom_ativo(self):
        from pictograma_pixels import check
        from auditar_animacao import require_pass
        report = {'issues': [], 'metrics': {'S1': {'movimento':1.0}}}
        check(report, 'mp4', {'ativo':{'fracao':.73,'pausa_maxima_quadros':10},
                             'cauda':{'mudancas':4}})
        with self.assertRaisesRegex(ValueError, 'densidade_pixels_mp4'):
            require_pass(report)

    def test_amostra_nao_autoriza_exportacao(self):
        from argparse import Namespace
        import tempfile
        from unittest.mock import patch
        from pictograma_auditoria import prepare_export
        from projeto import sha, write
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preview = root/'apresentacao.html'
            preview.write_text('versão revisada')
            report = {'identidade': {'previa_sha256':sha(preview), 'formato':'9:16'},
                      'modo':'amostrada','sampled':10,'quadros_totais':30,'issues':[]}
            write(root/'material/auditoria_animacao.json',report)
            with patch('pictograma_auditoria.inspect_preview', return_value={
                    'issues':[{'codigo':'falha_em_quadro_11','nivel':'bloqueante'}]}) as rerun:
                with self.assertRaisesRegex(ValueError, 'falha_em_quadro_11'):
                    prepare_export(root, preview,'9:16', Namespace(node='node'))
                self.assertTrue(rerun.call_args.kwargs['integral'])

    def test_catalogo_nao_atribui_aprovacao_sem_medicao(self):
        from catalogo_erros import resumo
        report = {'issues': [{'codigo':'EC-012'}], 'modo':'integral',
                  'checagens_catalogo': {'EC-013':{'quadros':30,'falhas':0}}}
        rows = {row['id']:row['resultado'] for row in resumo(report)}
        self.assertEqual(rows['EC-012'],'reprovado')
        self.assertEqual(rows['EC-013'],'conferido')
        self.assertEqual(rows['EC-010'],'não aferido nesta auditoria')

    def test_mutacoes_no_palco(self):
        import json
        import tempfile
        from catalogo_erros import fixture
        if not os.environ.get('PLAYWRIGHT_MODULE'):
            self.skipTest('Defina PLAYWRIGHT_MODULE para a regressão no navegador.')
        node = os.environ.get('JP_NODE') or shutil.which('node')
        with tempfile.TemporaryDirectory() as directory:
            preview = Path(directory)/'apresentacao.html'
            fixture(preview)
            run = subprocess.run([node, str(ROOT/'scripts/testar_catalogo_palco.mjs'), str(preview)],
                                 capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
        result = {row['id']:row for row in json.loads(run.stdout)}
        for row in catalogo():
            if row['teste'] == 'test_catalogo_erros.CatalogoTests.test_mutacoes_no_palco':
                self.assertTrue(result[row['id']]['ok'])

    def test_mutacoes_efeitos(self):
        from copy import deepcopy
        import json
        from cenas import Words
        from pictograma_biblia import for_project
        from pictograma_efeitos import compile_effects
        from pictograma_efeitos_pixels import effects_only, flash_report, measure_samples

        word = Words([{'id':'P007','texto':'Amar.'}])
        cue = {'virada': {'word':0,'frame':20,'start':3,'end':30,'scene':'S01'}}
        timeline = [{'id':'S01','inicio':0,'fim':3}]
        effect = {'id':'virar','cena':'S01','em':{'p':7,'trecho':'Amar.'},'alvo':'negacao',
                  'momento':'virada','tipo':'virada_tipografica','justificativa':'Distingue verbo de substantivo.',
                  'parametros':{'cor':'acento','intensidade':1,'antes_quadros':17,'depois_quadros':12}}
        raw = {'versao':1,'efeitos':[effect]}
        def check(proposal):
            return compile_effects(proposal,word,timeline,cue,for_project({}),{}, {'acento':'#9cc6a6'},90)
        self.assertEqual(check(raw)['destaques'][0]['pouso'],20)
        for code, field, value in [('EC-074','momento','durante_titulo'),('EC-075','justificativa',' '),
                                   ('EC-082','parametros',{**effect['parametros'],'cor':'#ff1010'})]:
            broken = deepcopy(raw)
            broken['efeitos'][0][field] = value
            with self.assertRaisesRegex(ValueError,code):
                check(broken)
        with self.assertRaisesRegex(ValueError,'EC-077'):
            check({'versao':1,'efeitos':[effect,{**effect,'id':'duplicado'}]})

        node = os.environ.get('JP_NODE') or shutil.which('node')
        if not node:
            self.skipTest('Informe JP_NODE para testar as checagens SVG de efeitos.')
        program = """
const {inspecionar}=await import('./auditar_efeitos.mjs');
const baseline={f:5,same:true,strike:true,direction:true};
const faults=[{f:20,negative:true},{f:10,occlusion:true},{f:11,direction:false},{f:12,missingContact:true}];
const results=inspecionar([baseline,...faults.map(row=>({...baseline,strike:false,...row}))]);
process.stdout.write(JSON.stringify(results.map(row=>row.codigo)));
"""
        output = subprocess.check_output([node,'--input-type=module','-e',program],cwd=ROOT/'scripts',text=True)
        self.assertEqual(json.loads(output),['EC-073','EC-076','EC-079','EC-081'])
        continuity = '''
const {inspecionar}=await import('./auditar_efeitos.mjs');
const heart={id:'coracao-recebido',opacity:1,x:500,y:650};
const state={same:true,expectedHearts:[heart.id]};
const results=inspecionar([{...state,f:0,hearts:[heart]},{...state,f:1,hearts:[]},
 {...state,f:2,hearts:[{...heart,x:240}]}]);
process.stdout.write(JSON.stringify(results.map(row=>row.codigo)));
'''
        output = subprocess.check_output([node,'--input-type=module','-e',continuity],cwd=ROOT/'scripts',text=True)
        self.assertEqual(json.loads(output),['EC-084','EC-084'])

        black, white = bytes([0,0,0]),bytes([255,255,255])
        self.assertFalse(flash_report([black]*30)['issues'])
        fast = [black if f%2 else white for f in range(30)]
        self.assertGreater(flash_report(fast)['gerais'],3)
        rows = [{} for _ in fast]
        self.assertEqual(effects_only(fast,fast,rows,1,1)[0]['gerais'],0)
        self.assertGreater(effects_only(fast,[black]*30,rows,1,1)[0]['gerais'],3)
        red = bytes([255,0,0])
        self.assertGreater(flash_report([black if f%2 else red for f in range(30)])['vermelhos'],3)

        image=bytes([32,32,32])*144
        row = {'shades':[{'lit':[3,3],'shade':[8,8],'bg':[0,0]}],
               'contacts':[{'p':[4,4],'bg':[8,8]}], 'title':[[2,2,8,8]]}
        self.assertEqual({x['codigo'] for x in measure_samples([image],[row],12,12)['issues']},
                         {'EC-080','EC-081','EC-083'})

    def test_acao_com_duracao_zero(self):
        self.js("""assert(a.shortEvent({start:1,end:1,minimum:6}));
            assert(!a.shortEvent({start:1,end:1.3,minimum:6}));""")

    def test_opacidade_instantanea(self):
        self.js("""assert(a.changeOpacity(.1,1));
            assert(!a.changeOpacity(.1,.24));""")

    def test_mutacoes_anatomicas(self):
        import json
        import tempfile
        from folhas_pictograma import approve, render, require
        node = os.environ.get('JP_NODE') or shutil.which('node')
        if not node or not os.environ.get('PLAYWRIGHT_MODULE'):
            self.skipTest('Defina JP_NODE e PLAYWRIGHT_MODULE para a auditoria anatômica.')
        with tempfile.TemporaryDirectory() as scratch:
            folder = Path(scratch)
            render(folder, node, mutations=True)
            data = json.loads((folder/'medicoes.json').read_text())
            self.assertEqual(data['issues'], [], data['issues'][:8])
            results = {row['id']:row['ok'] for row in json.loads((folder/'mutacoes-anatomicas.json').read_text())}
            self.assertEqual(results, {f'EC-{i:03}':True for i in range(43,73)})
            with self.assertRaisesRegex(ValueError,'Aguarde aprovação'):
                require(folder)
            with self.assertRaisesRegex(ValueError,'aprovação explícita'):
                approve(folder, False)
            approve(folder, True)
            require(folder)
            with (folder/'folha-movimento.html').open('a') as handle:
                handle.write('<!-- alterado -->')
            with self.assertRaisesRegex(ValueError,'Aguarde aprovação'):
                require(folder)


class EncenacaoTests(unittest.TestCase):
    def test_pose(self):
        from pictograma_encenacao import pose_changes
        frames=[{'f':i,'actors':[{'id':0,'mode':'repouso','angles':{'cabeca':i*.4}}]} for i in range(10)]
        self.assertEqual(pose_changes(frames,10)[0]['fracao'],0)
        for i, frame in enumerate(frames):
            frame['actors'][0]['angles']['cabeca']=i*4
        self.assertEqual(pose_changes(frames,10)[0]['fracao'],.9)

    def test_beat(self):
        from pictograma_encenacao import beat_coverage
        rows=[{'inicio':i,'fim':i+1,'movimento':{'tipo':'ler'}} for i in range(4)]
        rows[1]['movimento']=None
        self.assertEqual(beat_coverage(rows)['fracao'],.75)
        rows[1]['pausa']='Silêncio na fala'
        self.assertEqual(beat_coverage(rows)['fracao'],1)
        rows[2]['pausa']='Segunda pausa'
        self.assertEqual(beat_coverage(rows)['pausas_invalidas'],[2])

    def test_layout(self):
        from pictograma_encenacao import layout_and_objects
        stage=[{'f':i,'scene':str(i),'matrix':[1,1,i,0],
                'titles':[[300+i,10,400+i,100]],'objects':[]} for i in range(3)]
        poses=[{'actors':[{'box':[600+i,300,800+i,900]}]} for i in range(3)]
        self.assertEqual(layout_and_objects(stage,poses)[0][0]['quadro'],2)
        poses[2]['actors'][0]['box']=[100,300,200,900]
        self.assertFalse(layout_and_objects(stage,poses)[0])

    def test_object(self):
        from pictograma_encenacao import layout_and_objects
        obj={'id':'prop','actor':None,'relation':None,'box':[10,10,60,60]}
        stage=[{'f':0,'scene':'a','matrix':[1,1,0,0],'titles':[],'objects':[obj]}]
        pose=[{'actors':[{'id':0,'box':[300,300,500,900],'head':[310,300,480,429]}]}]
        self.assertTrue(layout_and_objects(stage,pose)[1])
        obj.update(actor='0',relation='segurado')
        self.assertTrue(layout_and_objects(stage,pose)[1])
        obj['box']=[10,10,160,140]
        self.assertFalse(layout_and_objects(stage,pose)[1])

    def test_pixels(self):
        from pictograma_encenacao import changed_pixels
        width=216
        old=bytearray(width*384)
        moved=bytearray(len(old))
        for y in range(50,65):
            for x in range(30,55):
                old[y*width+x]=225
                moved[y*width+x+6]=225
        box=[140,240,330,350]
        self.assertFalse(changed_pixels(old,moved,[1,1,0,0],[1,1,30,0],box))
        self.assertTrue(changed_pixels(old,moved,[1,1,0,0],[1,1,0,0],box))

    def test_private(self):
        from pictograma_legenda import display_tokens, private_hits, rules
        from pictograma_sincronia import caption_groups
        rows=[{'quadro':30,'fim_quadro':34},{'quadro':34,'fim_quadro':40}]
        project={'pessoas_privadas':['Nome'], 'substituicoes_legenda':[
            {'original':'a Nome','substituto':'uma amiga','motivo':'pessoa real privada',
             'origem':'usuario','data':'2026-11-08'}]}
        entries,names=rules(project)
        result,_=display_tokens(['A','Nome.'],entries)
        self.assertEqual(result,['Uma','amiga.'])
        self.assertTrue(private_hits(['A NÓME.'],names))
        self.assertFalse(private_hits(result,names))
        caption_groups(rows,['A','Nome.'],replacements=entries)
        self.assertEqual([r['quadro'] for r in rows],[30,34])
        self.assertEqual([r['texto'] for r in rows],['A','Nome.'])
        self.assertEqual([r['exibicao'] for r in rows],result)

    def test_bench_crossing(self):
        from auditar_mp4_anatomico import bench_issue
        row={'f':282,'banco':[{'ator':0,'pe':'peD','pixels':16}]}
        self.assertEqual(bench_issue(row)[0]['codigo'],'sola_cruza_banco')
        row['banco'][0]['pixels']=2
        self.assertFalse(bench_issue(row))

    def test_private_browser(self):
        import json
        import tempfile
        from auditar_animacao import inspect_preview
        from catalogo_erros import fixture
        node=os.environ.get('JP_NODE') or shutil.which('node')
        if not (node and os.environ.get('PLAYWRIGHT_MODULE')):
            self.skipTest('Informe JP_NODE e PLAYWRIGHT_MODULE.')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            preview=root/'apresentacao.html'
            fixture(preview)
            html=preview.read_text()
            pattern=r'(<script id="dados" type="application/json">)(.*?)(</script>)'
            def allowlist(match):
                data=json.loads(match[2])
                data['pessoas_privadas']=['Nome de teste']
                return match[1]+json.dumps(data,ensure_ascii=False)+match[3]
            html=re.sub(pattern,allowlist,html,flags=re.S)
            inject="""<script>
const originalRender=window.render;
window.render=t=>{
 const id=originalRender(t);
 const label=document.createElementNS('http://www.w3.org/2000/svg','text');
 label.setAttribute('x','450');label.setAttribute('y','630');
 label.textContent='NÔME DE TESTE';
 document.getElementById('palco').appendChild(label);
 return id;
};
</script>"""
            preview.write_text(html.replace('</html>',inject+'</html>'))
            report=inspect_preview(root,preview,'9:16',node,integral=True)
            self.assertIn('EC-092',{i['codigo'] for i in report['issues']})

    def test_body_ignores_elbow_and_counts_knee(self):
        from pictograma_encenacao import pose_changes, beat_coverage
        frames=[{'f':n,'actors':[{'id':0,'mode':'gesto',
                    'angles':{'cotoveloD':n*8,'joelhoD':n*.1}}]} for n in range(10)]
        self.assertEqual(pose_changes(frames,10)[0]['fracao'],.9)
        self.assertEqual(pose_changes(frames,10,body_only=True)[0]['fracao'],0)
        for i,row in enumerate(frames):
            row['actors'][0]['angles']['joelhoD']=i*5
        self.assertEqual(pose_changes(frames,10,body_only=True)[0]['fracao'],.9)
        rows=[{'id':'gesto','movimento':{'tipo':'apontar'},'inicio':0,'fim':3}]
        self.assertEqual(beat_coverage(rows,set())['com_acao'],0)

    def test_verbo_da_fala_e_tentativa_negada(self):
        from pictograma_verbos import apply_cue, find_cue
        self.assertEqual(find_cue('Ele vai levantar.')['acao'],'levantar')
        self.assertEqual(find_cue('Ela não pode se levantar.')['acao'],'tentar_levantar')
        self.assertIsNone(find_cue('O olhar segue o relevo.'))
        row={'id':'batida-1','fala':'E quem não consegue se levantar?','palavra':1,
             'movimento':{'tipo':'recolher'}}
        with self.assertRaisesRegex(ValueError,'EC-098'):
            apply_cue(row,[i/4 for i in range(8)],30,'validar')
        apply_cue(row,[i/4 for i in range(8)],30,'aplicar')
        self.assertEqual(row['movimento']['tipo'],'tentar_levantar')
        self.assertEqual(row['movimento']['palavra'],6)
        apply_cue(row,[i/4 for i in range(8)],30,'validar')


    def test_verbo_hipotetico_nao_vira_afirmacao(self):
        from pictograma_verbos import find_cue, apply_cue
        for phrase in ('Seria melhor começar por mim.', 'Se ela conseguir levantar.',
                       'Em vez de conversar, olhou.', 'Ela não pode se levantar.'):
            with self.subTest(phrase=phrase):
                cue=find_cue(phrase)
                self.assertTrue(cue['precisa_opcoes'])
                self.assertIn(cue['acao'],('recusar','tentar_levantar'))
        phrase='E eu preciso começar por ela, porque seria fácil demais começar por mim.'
        row={'id':'batida','fala':phrase,'palavra':0,'movimento':{'tipo':'passo_mao_no_peito'}}
        times=[i/10 for i in range(16)]
        with self.assertRaisesRegex(ValueError,'EC-098'):
            apply_cue(row,times,30,'validar')
        apply_cue(row,times,30,'aplicar')
        self.assertEqual(row['movimento']['tipo'],'oferecer_e_recusar')
        self.assertEqual(row['movimento']['pouso'],9)
        self.assertEqual(row['movimento']['segundo_pouso'],24)
        self.assertEqual(row['movimento']['alvo'],'outro')


    def test_apoio_e_passagem_apos_ajuda(self):
        CatalogoTests.js(self, """
const pair={atores:2,banco:false,desvio:0,emPe:true};
assert(a.elencoEstavel(pair));
assert(!a.elencoEstavel({...pair,banco:true}));
assert(!a.elencoEstavel({...pair,desvio:120}));
const step={apoio:0,fracao:.5,avanco:45,balanco:18};
assert(a.passoPlantado(step));
assert(!a.passoPlantado({...step,apoio:17}));
assert(!a.passoPlantado({...step,balanco:0}));
assert(!a.passoPlantado({...step,fracao:1,avanco:30}));
const care={dono:1,segura:0,gesto:41,fracao:.5};
assert(a.cuidadoAposEntrega(care));
assert(!a.cuidadoAposEntrega({...care,dono:0}));
assert(!a.cuidadoAposEntrega({...care,segura:24}));
assert(!a.cuidadoAposEntrega({...care,gesto:0}));
""")

    def test_revelacao_da_figura_sem_salto(self):
        from pictograma_pixels import validar_revelacao_figura
        self.assertEqual(validar_revelacao_figura([15,18,26,42,63,87,112,134,151,166,173]),25)
        with self.assertRaisesRegex(ValueError,'EC-116'):
            validar_revelacao_figura([15]*4+[180]*7)

    def test_livro_e_oracao_orientados(self):
        CatalogoTests.js(self, """
const book={leitor:.91,camera:.31,orientados:1};
assert(a.livroOrientado(book));
assert(!a.livroOrientado({...book,camera:1}));
assert(!a.livroOrientado({...book,leitor:-.9}));
const prayer={palmas:2,distancia:12,dedos:[-43,-39]};
assert(a.oracaoVisivel(prayer));
assert(!a.oracaoVisivel({...prayer,distancia:28}));
assert(!a.oracaoVisivel({...prayer,dedos:[-38,25]}));
""")

    def test_atmosferas_e_luz_transferida(self):
        CatalogoTests.js(self, """
const mood={tipo:'chuva',opacidade:1,limite:1287,detalhes:true};
for(const tipo of ['aura','chuva','claridade','partilha'])assert(a.atmosferaVisivel({...mood,tipo}));
assert(!a.atmosferaVisivel({...mood,limite:1400}));
assert(!a.atmosferaVisivel({...mood,detalhes:false}));
assert(a.sombraVisivel({falante:22,ouvinte:25,gestoOuvinte:false}));
assert(!a.sombraVisivel({falante:22,ouvinte:2,gestoOuvinte:false}));
const gift={progress:.8,stage:'recebe',owner:1,donor:0,receiver:1,expected:.8};
assert(a.partilhaVisivel(gift));
assert(!a.partilhaVisivel({...gift,owner:0}));
assert(!a.partilhaVisivel({...gift,stage:'doa'}));
assert(a.partilhaVisivel({...gift,progress:0,stage:'doa',owner:0,expected:0}));
""")

    def test_livro_e_luz_com_apoio_e_sincronia(self):
        CatalogoTests.js(self, """
const book={distancias:[2,6],virada:.42,pagina:true};
assert(a.livroApoiado(book));
assert(!a.livroApoiado({...book,distancias:[29,2]}));
assert(!a.livroApoiado({...book,pagina:false}));
const spotlight={maos:1,feixes:1,opacidadeMao:.54,opacidadeFeixe:.54,limite:1270};
assert(a.luzDaPresenca(spotlight));
assert(!a.luzDaPresenca({...spotlight,maos:0}));
assert(!a.luzDaPresenca({...spotlight,opacidadeFeixe:1}));
assert(!a.luzDaPresenca({...spotlight,limite:1342}));
""")

    def test_ponte_tipografica_rejeita_salto(self):
        from pictograma_pixels import validar_ponte_titulo
        self.assertEqual(validar_ponte_titulo([15,15,16,20,32,49,69,89,106,119,125]),20)
        for frames in ([15]*5+[125]*6,[15]*11):
            with self.assertRaisesRegex(ValueError,'EC-105'):
                validar_ponte_titulo(frames)

    def test_mao_presente_sem_contato_e_com_sustentacao(self):
        CatalogoTests.js(self, """
const action={inicio:10,pouso:20,fim:80,presenca:{alcance:35,sustenta_ate:50}};
const good={quantidade:1,opacidade:1,folga:31,cotovelo:18};
assert(a.presenca(action,35,good));
assert(!a.presenca(action,40,{...good,folga:0}));
assert(!a.presenca(action,40,{...good,cotovelo:-2}));
assert(!a.presenca(action,40,{...good,folga:105}));
assert(!a.presenca(action,40,{...good,opacidade:.2}));
assert(!a.presenca(action,40,{...good,quantidade:0}));
assert(!a.presenca(action,79,good));
assert(a.presenca(action,79,{...good,quantidade:0}));
""")

    def test_enumeracao_antecipada_ou_incompleta(self):
        CatalogoTests.js(self, """
const scene={figuras:[{tipo:'animal',pouso:10},{tipo:'idoso',pouso:30}],
  revelacao_figuras:{entrada_quadros:9,saida_inicio:50,saida_fim:62}};
const animal={tipo:'animal',opacity:1}, elder={tipo:'idoso',opacity:1};
assert(a.enumeracao(scene,[],9));
assert(!a.enumeracao(scene,[animal],9));
assert(a.enumeracao(scene,[animal],25));
assert(!a.enumeracao(scene,[elder],42));
assert(!a.enumeracao(scene,[animal,elder],30));
assert(a.enumeracao(scene,[animal,elder],42));
assert(a.enumeracao(scene,[{...animal,opacity:.5},{...elder,opacity:.5}],56));
assert(!a.enumeracao(scene,[animal,elder],62));
assert(a.enumeracao(scene,[],62));
""")

    def test_gesto_sem_alvo_e_contato_perdido(self):
        from pictograma_gestos import auditar_gestos, validate_gesture
        with self.assertRaisesRegex(ValueError,'EC-099'):
            validate_gesture({'tipo':'carregar','gesto':{
                'intencao':'carregar','alvo':'algo','mao':'D','saida':'repouso'}})
        hand={'posicao':[0,0],'excesso':0,'contato':None,'ativa':False,'autorizada':False}
        base={'f':10,'scene':'escuta','actors':[{'D':hand},{'D':hand}],'action':True}
        self.assertEqual(auditar_gestos(base),[])
        broken={**base,'f':11,'contato_esperado':True,'actors':[{'D':hand},{
            'D':{**hand,'ativa':True,'posicao':[41,0],'contato':14}}]}
        errors=auditar_gestos(broken,base)
        self.assertEqual(len(errors),4)
        self.assertTrue(all(row['codigo']=='EC-099' and row['quadro']==11 for row in errors))


    def test_gestos_expressivos_respeitam_janela_e_apoios(self):
        node=os.environ.get('JP_NODE') or shutil.which('node')
        if not node:
            self.skipTest('Informe JP_NODE para testar os gestos do rig.')
        source=r"""
const fs=require('node:fs'), assert=require('node:assert/strict');
global.window=global;
for(const name of ['figura','rig','acoes']) eval(fs.readFileSync('pictograma-'+name+'.js','utf8'));
const b=JSON.parse(fs.readFileSync('biblia-anatomica-pictograma.json'));
const rig=PictogramaRig, neutral=rig.neutral(b,1);
const fala={tipo:'conversar',gesto:{mao:'D'},inicio:10,pouso:22,fim:40};
const hands=(pose,side)=>pose.joints['punho'+side];
for (const frame of [0,10,40]) {
  const p=PictogramaAcoes.expressive(b,neutral,fala,frame,1);
  assert(rig.distance(hands(p,'D'),hands(neutral,'D'))<.001);
}
const p=PictogramaAcoes.expressive(b,neutral,fala,22,1);
assert(rig.distance(hands(p,'D'),hands(neutral,'D'))>.4);
assert(rig.distance(hands(p,'E'),hands(neutral,'E'))<.001);
const livro={...fala,tipo:'ler',gesto:{mao:'ambas'},sustentar:true};
const reading=PictogramaAcoes.expressive(b,neutral,livro,22,1);
const holding=PictogramaAcoes.expressive(b,neutral,livro,39,1);
for(const side of ['E','D']) {
  assert(rig.distance(hands(reading,side),hands(holding,side))<.001);
  assert(rig.distance(hands(reading,side),hands(neutral,side))>.3);
}
let last;
for(let f=0;f<=30;f++){
  const p=rig.chair(b,f,false,{bracosContinuos:true});
  if(last)for(const side of ['E','D'])assert(rig.distance(hands(p,side),hands(last,side))<.35);
  last=p;
}
assert(last.contacts.some(c=>c.tipo==='assento'));
const [giver,receiver]=rig.help(b,b.ajuda.tracao,{bracosContinuos:true});
assert(rig.distance(giver.contacts.find(c=>c.tipo==='par').real,receiver.contacts.find(c=>c.tipo==='par').real)<.08);
assert(Math.abs(rig.walk(b,0).control.armSwing)>0);
"""
        subprocess.run([node,'-e',source],cwd=ROOT/'assets',check=True)
