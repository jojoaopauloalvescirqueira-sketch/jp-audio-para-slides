"""Compila direção declarativa em cenas e ações no quadro da palavra."""
from collections import Counter

from cenas import ident, only, string

PATTERNS = frozenset(('pergunta','enumeracao','objecao','citacao','conclusao','conceito',
                      'transformacao','comparacao','virada','numero_data','causa_efeito'))
GRAPHICS = {'contraste':(2,2), 'fonte':(1,1), 'relogio':(1,1), 'rede':(2,4), 'enfase':(1,1)}
SCENERIES = frozenset(('esperanca','rua','janela','encontro','decreto','biblioteca','caminho'))
SCENERY_FIGURES = frozenset(('animal','idoso','crianca'))
CONVERSATION_ACCENTS = frozenset(('abrir','precisar','ponderar','recolher'))
ATMOSPHERES = frozenset(('sombra','aura','chuva','claridade','partilha'))
LAYOUTS = frozenset(('centro','esquerda','direita','dupla','percurso'))

SYMBOLS = frozenset(('pergunta','livro','mao','relogio','seta','data','moeda','linha',
                     'casa','pausa','coracao','circulo'))
ACTIONS = frozenset(('andar_ate','sentar','levantar','ajudar_a_levantar','entregar','receber',
                     'apontar','abracar','ajoelhar','cair','carregar','olhar_para','esperar',
                     'tentar_levantar','oferecer_e_recusar','acompanhar_espera','passo_mao_no_peito','pensar','ler','recolher','recusar','conversar','mao_no_peito','mao_presente','sentar_juntos','orar','virar','romper','curvar','agachar','aproximar','afastar','sentar_no_chao','amparar'))


def compile_direction(plan, words, times, total, fps=30):
    from pictograma_gestos import PROFILE, schedule
    only(plan, 'titulo sensivel quadro_acoes batidas verbos_chave gestual continuidade', 'Direção declarativa')
    gestual=plan.get('gestual')
    continuous=plan.get('continuidade',False)
    if type(continuous) is not bool:
        raise ValueError('continuidade precisa ser um booleano.')
    if gestual not in (None,PROFILE):
        raise ValueError('Perfil de gestos desconhecido.')
    if gestual and plan.get('verbos_chave')=='aplicar':
        raise ValueError('No perfil gestual, revise os verbos antes de declarar a atuação.')
    verb_mode=plan.get('verbos_chave')
    if verb_mode not in (None,'aplicar','validar'):
        raise ValueError('Use aplicar ou validar para verbos_chave.')
    if not isinstance(plan.get('batidas'), list) or not plan['batidas']:
        raise ValueError('Inclua batidas no plano de direção.')
    if type(plan.get('sensivel')) is not bool:
        raise ValueError('Informe se o material exige encenação sensível.')
    if len(times) != len(words.words) or any(a>b for a,b in zip(times,times[1:])):
        raise ValueError('A direção precisa de marcações completas e crescentes.')
    seen=Counter()
    last_title=-4
    result=[]
    for i, row in enumerate(plan['batidas']):
        only(row,'padrao em titulo rotulos simbolos acao layout pausa virada assento grafico cenario_ilustrado atmosfera corte_justificado manter_posse manter_elenco','Batida')
        pattern=row.get('padrao')
        if not isinstance(pattern,str) or pattern not in PATTERNS:
            raise ValueError(f'Padrão indisponível: {pattern}.')
        title=row.get('titulo','')
        if title: string(title,'Título da batida',82)
        layout=row.get('layout')
        if 'assento' in row and (not gestual or type(row['assento']) is not bool):
            raise ValueError('O apoio contínuo deve ser um booleano do perfil gestual.')
        if layout and layout not in LAYOUTS:
            raise ValueError('Layout fora do repertório.')
        labels=row.get('rotulos')
        symbols=row.get('simbolos')
        if not isinstance(labels,list) or len(labels)>3 or not isinstance(symbols,list) or len(symbols)>3:
            raise ValueError('Use até três rótulos e três símbolos por batida.')
        for label in labels:
            string(label,'Rótulo',38)
        if any(not isinstance(s,str) or s not in SYMBOLS for s in symbols):
            raise ValueError('Símbolo fora do repertório.')
        word=words.anchor(row.get('em'))
        if title and layout:
            if times[word]-last_title<4:
                raise ValueError('As entradas de texto grande precisam de pelo menos 4 s de distância.')
            last_title=times[word]
        signature=(pattern,layout,tuple(symbols),(row.get('acao') or {}).get('tipo') if isinstance(row.get('acao',{}),dict) else None)
        seen[signature]+=1
        if seen[signature]>2 and not (gestual and (row.get('acao') or {}).get('tipo') in ('olhar_para','esperar','pensar')):
            raise ValueError('A terceira encenação igual exige variar a composição.')
        if (not result and word!=0) or (result and word<=result[-1]['palavra']):
            raise ValueError('As batidas precisam começar na primeira palavra e avançar em ordem.')
        action=row.get('acao')
        if layout and bool(action)==bool(row.get('pausa')):
            raise ValueError('Em cada batida, declare uma ação ou justifique uma pausa.')
        payload=None
        if action is not None:
            only(action,'tipo ator alvo em objeto relacao acessorio figura gesto segunda_ancora acentos passo_em cuidado_em','Ação')
            kind=action.get('tipo')
            if kind not in ACTIONS:
                raise ValueError(f'Ação fora da biblioteca: {kind}.')
            actor=ident(action.get('ator'),'Ator')
            target=action.get('alvo')
            if actor!='principal' or target not in ('outro',None,'') or (
                    kind=='ajudar_a_levantar' and target!='outro'):
                raise ValueError('A ação exige participantes declarados.')
            if action.get('objeto') is not None and action['objeto'] not in SYMBOLS:
                raise ValueError('Objeto da ação fora do repertório.')
            if plan['sensivel'] and kind in ('cair','ajoelhar'):
                raise ValueError('A ação proposta exige revisão editorial de conteúdo sensível.')
            from pictograma_encenacao import RELATIONS
            if action.get('relacao') and (not action.get('objeto') or action['relacao'] not in RELATIONS):
                raise ValueError('Relação de objeto fora do repertório.')
            if action.get('acessorio') and (not action.get('objeto') or action['acessorio'] not in SYMBOLS):
                raise ValueError('O acessório precisa de um objeto principal e de um tipo conhecido.')
            if action.get('figura') not in (None,'crianca','idoso','animal'):
                raise ValueError('Figura fora do repertório.')
            cue=words.anchor(action.get('em'))
            payload={**action,'palavra':cue,'pouso':round(times[cue]*fps)}
            if 'acentos' in action:
                accents=action['acentos']
                if (not gestual or kind!='conversar' or target!='outro'
                        or not isinstance(accents,list) or not 2<=len(accents)<=3):
                    raise ValueError('EC-102 · Declare dois ou três acentos numa conversa entre figuras.')
                compiled=[]
                for accent in accents:
                    only(accent,'tipo em','Acento de conversa')
                    name=accent.get('tipo')
                    if not isinstance(name,str) or name not in CONVERSATION_ACCENTS:
                        raise ValueError('EC-102 · Tipo de acento desconhecido.')
                    cue=words.anchor(accent.get('em'))
                    compiled.append({**accent,'palavra':cue,'pouso':round(times[cue]*fps)})
                if len({a['tipo'] for a in compiled})!=len(compiled):
                    raise ValueError('EC-102 · Varie a intenção dos acentos na conversa.')
                payload['acentos']=compiled
            for key,action_kind in (('passo_em','levantar'),('cuidado_em','entregar')):
                if key in action:
                    if not gestual or kind!=action_kind or (
                            key=='cuidado_em' and (target!='outro' or action.get('objeto')!='coracao')):
                        raise ValueError('EC-114/115 · Declare uma ação de base compatível com a segunda âncora.')
                    anchor=words.anchor(action[key])
                    if anchor<=payload['palavra']:
                        raise ValueError('EC-114/115 · A ação seguinte deve vir depois da primeira.')
                    payload[key+'_indice']=anchor
            if gestual and kind=='oferecer_e_recusar':
                second=words.anchor(action.get('segunda_ancora'))
                if second<=cue:
                    raise ValueError('EC-099 · A recusa deve vir depois da oferta.')
                payload.update(segunda_palavra=second,segundo_pouso=round(times[second]*fps))
        graphic=row.get('grafico')
        if graphic is not None:
            only(graphic,'tipo textos em','Gráfico animado')
            kind=graphic.get('tipo')
            if not isinstance(kind,str) or kind not in GRAPHICS:
                raise ValueError('Modelo de gráfico indisponível.')
            labels=graphic.get('textos')
            lo,hi=GRAPHICS[kind]
            if not isinstance(labels,list) or not lo<=len(labels)<=hi:
                raise ValueError('Quantidade de rótulos incompatível com o gráfico.')
            for label in labels:
                string(label,'Rótulo do gráfico',38)
            cue=words.anchor(graphic.get('em'))
            graphic={**graphic,'palavra':cue,'pouso':round(times[cue]*fps)}
        scenery=row.get('cenario_ilustrado')
        if scenery is not None:
            only(scenery,'tipo em figuras','Cenário ilustrado')
            style=scenery.get('tipo')
            if not isinstance(style,str) or style not in SCENERIES:
                raise ValueError('Tipo de cenário ilustrado indisponível.')
            cue=words.anchor(scenery.get('em'))
            scenery={**scenery,'palavra':cue,'pouso':round(times[cue]*fps)}
            if 'figuras' in scenery:
                figures=scenery['figuras']
                if style!='rua' or not isinstance(figures,list) or not 1<=len(figures)<=3:
                    raise ValueError('Declare de uma a três figuras no cenário rua.')
                compiled=[]
                for figure in figures:
                    only(figure,'tipo em','Figura do cenário')
                    kind=figure.get('tipo')
                    if not isinstance(kind,str) or kind not in SCENERY_FIGURES:
                        raise ValueError('Tipo de figura do cenário indisponível.')
                    anchor=words.anchor(figure.get('em'))
                    compiled.append({**figure,'palavra':anchor,'pouso':round(times[anchor]*fps)})
                if len({figure['tipo'] for figure in compiled})!=len(compiled):
                    raise ValueError('Tipos de figura do cenário precisam ser distintos.')
                scenery['figuras']=compiled
        mood=row.get('atmosfera')
        if mood is not None:
            only(mood,'tipo em','Atmosfera')
            kind=mood.get('tipo')
            if not isinstance(kind,str) or kind not in ATMOSPHERES:
                raise ValueError('Atmosfera fora do repertório.')
            if kind=='partilha' and not ((payload and payload.get('objeto')=='coracao'
                    and payload['tipo'] in ('entregar','receber')) or row.get('manter_posse')):
                raise ValueError('EC-112 · A luz de partilha exige uma entrega de coração ou posse mantida.')
            cue=words.anchor(mood.get('em'))
            mood={**mood,'palavra':cue,'pouso':round(times[cue]*fps)}
        swap=row.get('virada')
        if swap is not None:
            only(swap,'prefixo antes depois sufixo','Virada tipográfica')
            if set(swap)!={'prefixo','antes','depois','sufixo'} or any(not isinstance(v,str) for v in swap.values()):
                raise ValueError('Declare as quatro partes da palavra na virada.')
            if any(len(swap[key])!=1 for key in ('antes','depois')) or swap['antes']==swap['depois'] or not payload:
                raise ValueError('A virada precisa de dois glifos diferentes e de uma ação ancorada.')
        result.append({'id':f'batida-{i+1}','palavra':word,'inicio':times[word] if i else 0,
                       'saida':'corte','titulo':title,'rotulos':labels,'simbolos':symbols,
                       'padrao':pattern,'virada':swap,**({'grafico':graphic} if graphic else {}),'movimento':payload,'layout':layout,'pausa':row.get('pausa'),**({'assento':bool(row.get('assento'))} if gestual else {})})
        if row.get('manter_elenco') is not None:
            if not continuous or not gestual or type(row['manter_elenco']) is not bool:
                raise ValueError('EC-113 · A continuidade do elenco exige direção gestual.')
            if row['manter_elenco']:
                previous=result[-2] if len(result)>1 else {}
                if ((previous.get('movimento') or {}).get('tipo')!='ajudar_a_levantar'
                        or previous.get('layout')!=layout or (payload or {}).get('tipo')!='olhar_para'
                        or row.get('assento') or row.get('corte_justificado')):
                    raise ValueError('EC-113 · Mantenha o enquadramento e as poses em pé após a ajuda.')
                result[-1]['manter_elenco']=True
        if row.get('manter_posse') is not None:
            if not continuous or type(row['manter_posse']) is not bool:
                raise ValueError('manter_posse exige modo de continuidade e um booleano.')
            result[-1]['manter_posse']=row['manter_posse']
        if row.get('corte_justificado') is not None:
            result[-1]['corte_justificado']=string(row['corte_justificado'],'Motivo do corte',150)
        if scenery:
            result[-1]['cenario_ilustrado']=scenery
        if mood:
            result[-1]['atmosfera']=mood
    if any(row['layout'] for row in result) and not all(row['layout'] for row in result):
        raise ValueError('Indique o layout de todas as batidas declarativas.')
    seated=False
    for i,row in enumerate(result):
        following=result[i+1] if i+1<len(result) else None
        row['fim']=following['inicio'] if following else total
        row['fim_palavra']=following['palavra'] if following else len(words.words)
        row['fala']=words.excerpt(row['palavra'],row['fim_palavra'])
        if verb_mode:
            from pictograma_verbos import apply_cue
            declared=row['movimento']
            apply_cue(row,times,fps,verb_mode)
            if gestual:
                row['movimento']=declared
            if plan['sensivel'] and (row['movimento'] or {}).get('tipo') in ('cair','ajoelhar'):
                raise ValueError('A ação proposta exige revisão editorial de conteúdo sensível.')
        if row['fim']<=row['inicio']:
            raise ValueError('Batida sem duração.')
        mood=row.get('atmosfera')
        if mood and not row['palavra']<=mood['palavra']<row['fim_palavra']:
            raise ValueError('A atmosfera precisa entrar dentro da batida.')
        graphic=row.get('grafico')
        if graphic:
            if not row['palavra']<=graphic['palavra']<row['fim_palavra']:
                raise ValueError('O gráfico precisa pousar dentro da batida.')
            start,end=round(row['inicio']*fps),round(row['fim']*fps)
            graphic['inicio']=start if i==0 else max(start,graphic['pouso']-12)
            graphic['fim']=min(end-1,max(graphic['inicio']+10,graphic['pouso']+18))
            if graphic['fim']-graphic['inicio']<8:
                raise ValueError('A batida não comporta a animação do gráfico.')
        scenery=row.get('cenario_ilustrado')
        if scenery:
            if not row['palavra']<=scenery['palavra']<row['fim_palavra']:
                raise ValueError('O cenário precisa iniciar dentro da batida.')
            scenery['inicio']=round(row['inicio']*fps)
            scenery['fim']=min(round(row['fim']*fps)-1,scenery['pouso']+32)
            if 'figuras' in scenery:
                figures=scenery['figuras']
                landings=[figure['pouso'] for figure in figures]
                if (any(not row['palavra']<=figure['palavra']<row['fim_palavra'] for figure in figures)
                        or any(a>=b for a,b in zip(landings,landings[1:]))):
                    raise ValueError('As figuras precisam de âncoras crescentes dentro da batida.')
                reveal=max(1,round(.30*fps))
                end=round(row['fim']*fps)-1
                fade=end+1-max(2,round(.43*fps))
                if landings[-1]+reveal>fade:
                    raise ValueError('A batida precisa comportar a entrada e a dissolução das figuras.')
                scenery['revelacao_figuras']={'entrada_quadros':reveal,'saida_inicio':fade,'saida_fim':end}
            previous_scenery=result[i-1].get('cenario_ilustrado') if i else None
            if previous_scenery and previous_scenery['tipo']==scenery['tipo']:
                scenery['continuo']=True
            elif scenery['fim']-scenery['pouso']<6:
                raise ValueError('A batida não comporta o movimento do cenário.')
        row['manter_sentado']=seated
        if row['movimento']:
            action=row['movimento']
            if not row['palavra']<=action['palavra']<=action.get('segunda_palavra',action['palavra'])<row['fim_palavra']:
                raise ValueError('A ação precisa pousar dentro da batida.')
            action['inicio']=max(round(row['inicio']*fps),action['pouso']-12)
            action['fim']=min(round(row['fim']*fps),action['pouso']+16)
            if row['layout'] and not gestual:
                action['inicio']=round(row['inicio']*fps)
                action['fim']=round(row['fim']*fps)
            if gestual:
                if action['tipo']=='receber' and action.get('relacao')=='segurado':
                    previous=(result[i-1]['movimento'] or {}) if i else {}
                    if (previous.get('tipo')!='entregar' or previous.get('objeto')!=action.get('objeto')
                            or previous.get('alvo')!=action.get('alvo') or result[i-1]['layout']!=row['layout']):
                        raise ValueError('EC-099 · A recepção sustentada precisa da entrega anterior com os mesmos atores e objeto.')
                start,end=round(row['inicio']*fps),round(row['fim']*fps)
                schedule(action,start,end)
                if 'passo_em_indice' in action:
                    index=action['passo_em_indice']
                    landing=round(times[index]*fps)
                    if not row['palavra']<=index<row['fim_palavra'] or landing-action['inicio']<19 or end-landing<19:
                        raise ValueError('EC-114 · Reserve tempo para levantar e dar o passo.')
                    action['fim']=landing
                    action['passo_final']={'inicio':landing,'fim':min(end-1,landing+20)}
                if 'cuidado_em_indice' in action:
                    index=action['cuidado_em_indice']
                    landing=round(times[index]*fps)
                    if not row['palavra']<=index<row['fim_palavra'] or landing-action['pouso']<20 or end-landing<17:
                        raise ValueError('EC-115 · Reserve tempo para concluir a entrega e reagir.')
                    action['cuidado']={'inicio':landing,'fim':min(end-1,landing+25)}
                if 'acentos' in action:
                    previous_end=start
                    for accent in action['acentos']:
                        accent['inicio']=max(start,accent['pouso']-9)
                        accent['fim']=min(end,accent['pouso']+12)
                        if (not row['palavra']<=accent['palavra']<row['fim_palavra']
                                or accent['inicio']<previous_end or accent['fim']-accent['inicio']<9):
                            raise ValueError('EC-102 · Separe os acentos dentro da batida.')
                        previous_end=accent['fim']
                    action.update(inicio=action['acentos'][0]['inicio'],fim=previous_end)
            if action['tipo']=='sentar':
                if not gestual:
                    action['inicio']=max(round(row['inicio']*fps),action['pouso']-26)
                    action['fim']=action['pouso']
                seated=True
            elif action['tipo']=='levantar':
                seated=False
            if action['fim']-action['inicio']<8:
                raise ValueError('A batida não comporta a ação no intervalo medido.')
    if continuous:
        for previous,current in zip(result,result[1:]):
            before=(previous.get('cenario_ilustrado') or {}).get('tipo')
            after=(current.get('cenario_ilustrado') or {}).get('tipo')
            reason=current.get('corte_justificado')
            if current.get('manter_posse'):
                prior_action=previous.get('movimento') or {}
                action=current.get('movimento') or {}
                inherited=previous.get('manter_posse')
                transfer=(prior_action.get('tipo') in ('entregar','receber')
                          and prior_action.get('objeto'))
                if (not gestual or not (inherited or transfer) or reason or action.get('objeto')
                        or action.get('alvo')!='outro' or prior_action.get('alvo')!='outro'
                        or current['layout']!=previous['layout']):
                    raise ValueError('manter_posse exige a transferência anterior e os mesmos participantes e layout.')
            frames=min(24,max(9,round((current['fim']-current['inicio'])*fps*.70)))
            action=current.get('movimento') or {}
            # Antecipe a chegada da composição se uma pega já precisa estar firme.
            before_start=0
            if not reason and action.get('tipo') in ('entregar','receber') and action.get('relacao')!='segurado':
                start=round(current['inicio']*fps)
                remaining=max(0,action['pouso']-4-start)
                if remaining<9:
                    before_start=min(frames-remaining,
                        max(0,start-round(previous['inicio']*fps)-24))
                    frames=remaining+before_start
                else:
                    frames=min(frames,remaining)
            current['entrada_continua']={
                'tipo':'corte_justificado' if reason else 'camadas' if before!=after else 'pose',
                'quadros':0 if reason else frames,
                **({'preparo_anterior':before_start} if before_start else {}),
                **({'motivo':reason} if reason else {}),
            }
    return result


def preview(root, plan, paragraphs, marks, audio, total, estimated=False, escolhas=None, *, captions=True, safeguards=False):
    from pathlib import Path
    from ancoras import tokens
    from pictograma import ASSETS, player
    from pictograma_biblia import for_project
    from pictograma_sincronia import caption_groups
    from cenas import Words
    from projeto import read, write

    words=Words(paragraphs)
    marks=[dict(mark) for mark in marks]
    if any(mark.get('motivos_revisao') for mark in marks):
        raise ValueError('Confiança baixa. Revise a fala indicada antes de compor.')
    raw=[]
    for paragraph in paragraphs:
        text=paragraph['texto']
        units=tokens(text)
        for i,(word,start) in enumerate(units):
            end=units[i+1][1] if i+1<len(units) else len(text)
            raw.append(word+''.join(c for c in text[start+len(word):end] if c in ',.;:!?…'))
    for i,mark in enumerate(marks):
        mark['palavra']=i
    from pictograma_legenda import rules, display_tokens
    config_path=Path(root)/'projeto.json'
    project=read(config_path) if config_path.is_file() else {}
    replacements,names=rules(project)
    legends=caption_groups(marks,raw,replacements=replacements)
    times=[item['quadro']/30 for item in marks]
    scenes=compile_direction(plan,words,times,total)
    from pictograma_opcoes import stage_choices
    stage_choices(scenes,project.get('escolhas_storyboard',{}) if escolhas is None else escolhas)
    if safeguards:
        from pictograma_salvaguardas import expected_ownership
        expected_ownership(scenes)
    dest=Path(root)/'pictograma-9x16'
    dest.mkdir(parents=True,exist_ok=True)
    project={**project,'titulo':plan['titulo']}
    direction={'paleta':'escura','legenda':'sim' if captions else 'nao','tom':'sobrio' if plan['sensivel'] else 'didatico',
               'marca':'nao','densidade_animacao':'abundante'}
    active=min(total,max(row['fim_quadro'] for row in marks)/30)
    flags={'salvaguardas_declarativas':True} if safeguards else {}
    player(dest/'apresentacao.html',project,direction,'9:16',scenes,words,times,total,estimated,audio,active,
           palavras=marks,legendas=legends,auditoria_sincronia=True,
           pessoas_privadas=names,substituicoes_legenda=display_tokens(raw,replacements)[1],
           composicao_declarativa={'sensivel':plan['sensivel'],'gestual':plan.get('gestual'),
             'assento':any((s['movimento'] or {}).get('tipo')=='sentar' for s in scenes)},bible=for_project({}),
           rig_anatomico=read(ASSETS/'biblia-anatomica-pictograma.json'),**flags)
    write(dest/'timeline_previa.json',{'estimado':estimated,'duracao_s':total,'fim_fala_s':active,'cenas':scenes})
    if safeguards:
        return dest/'apresentacao.html',{'cenas':scenes,'figuras_com_apoio':True,
            'pessoas_privadas':bool(names),'legendas':legends,'palavras':marks}
    return dest/'apresentacao.html'


def legacy_scene_data(value, assets):
    """Valida a migração de texto e marcação do formato cinematográfico anterior."""
    from cenas import number
    from projeto import read

    spec=read(assets/'pictograma-legado-cinematico.json')
    only(value,'texto marcas','Encenação')
    for key, kind in (('texto',string),('marcas',number)):
        row=value.get(key)
        only(row,' '.join(spec[key]),key)
        if row.keys()!=spec[key].keys():
            raise ValueError(f'Encenação incompleta em {key}.')
        for name, item in row.items():
            kind(item,name)
    return value



def pattern_scene_data(value):
    """Valida dados dos blocos sem consultar o projeto de referência."""
    from cenas import number
    only(value,'texto marcas','Dados dos padrões')
    text,marks=value.get('texto'),value.get('marcas')
    required_text={'prefixo','sufixo','antes','depois','espera','acao','esquerda','direita'}
    required_marks={'centro_tipo','linha_conceito','divisoria','origem_ator','angulo',
                    'banco_x','banco_comprimento','marcha','cadeira','foco','relogio_x','relogio_y'}
    if not isinstance(text,dict) or not required_text<=text.keys():
        raise ValueError('Faltam textos de virada, atuação ou comparação.')
    if not isinstance(marks,dict) or not required_marks<=marks.keys():
        raise ValueError('Faltam marcas do palco dos padrões.')
    if {'sujeito','copula','negacao'} & text.keys() and (
            not {'sujeito','copula','negacao'}<=text.keys() or 'linha_superior' not in marks):
        raise ValueError('O cabeçalho da virada está incompleto.')
    if {'classe_antes','classe_depois'} & text.keys() and (
            not {'classe_antes','classe_depois'}<=text.keys() or 'linha_classe' not in marks):
        raise ValueError('A classe da virada está incompleta.')
    for key,item in text.items():
        if key in ('prefixo','sufixo') and item=='':
            continue
        string(item,key)
    for key,item in marks.items():
        number(item,key)
    return value
