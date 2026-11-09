# Pictograma

Siga [as perguntas do diretor de animação](diretor_animacao.md) antes de propor cenas. Use os fluxos existentes para preparar a fala, receber áudio, medir e transcrever localmente. A exportação usa H.264 e a biblioteca de Mozart ou faixa indicada.

## Identidade e biblioteca

Use fundo escuro JP `#0B0F0D`, osso `#ECE6D8`, acento verde `#9CC6A6`, texto suave `#89978F` e linhas `#2C3631`. O palco usa Arial ou a sans-serif disponível. A referência [Deus é amar](../assets/referencia-pictograma/cena-deus-e-amar.html) preserva o HTML, SVG e JavaScript da demo. Os elementos do motor são próprios. Use cores claras ou personalizadas quando registradas na direção.

O palco nativo é 1080×1920. Posicione elementos por caixa `x,y,w,h` entre x=64 e x=892 e entre y=440 e y=1320. As faixas restantes da área segura vertical, entre y=370 e y=1430, reservam espaço para progresso, cena e legenda. O formato 16:9 recompõe a caixa de cena para 1920×1080. A marca d’água começa desligada. Para ligar, registre `marca=sim`.

| Tipo | Ações específicas |
| --- | --- |
| `figura` | `sentar`, `levantar`, `andar` para novo x, `destacar` com halo, `mudar_cor` |
| `banco` | Assento vetorial |
| `relogio` | `girar` |
| `reticencias` | `pulsar` |
| `braco`, `linha`, `seta`, `divisoria` | `desenhar` |
| `coluna` | Moldura para comparação |
| `texto` | `palavra`, `trocar_letra`, `anotar` |

Todo tipo aceita `aparecer` e `sumir`. O elemento nasce visível, salvo `visivel:false`. Use `cor` como `osso`, `acento` ou `suave`, `estado` inicial como `em_pe` ou `sentado` e `direcao` de traço como `direita`, `esquerda`, `cima` ou `baixo`. Textos usam `texto` e podem ter `anotacao`. Rótulos de personagem usam o campo `rotulo`, separado do texto editorial. O validador aceita papéis conhecidos no modo de papéis e nomes reais somente na lista explicitamente autorizada. Confira editorialmente os nomes citados no texto da cena.

## Planos ancorados na fala

Registre respostas com `pictograma.py direcao --root PROJETO --respostas respostas.json`. O JSON associa cada escolha a `{"valor": "opção", "origem": "usuario"}`. As opções da interface são `criacao=diretor|colaborativa|usuario`, `tom=sobrio|didatico|energetico`, `metafora=literal|ilustrativa|metaforica`, `personagens=genericos|papeis|nomes`, `texto=palavras|frases|nenhum`, `legenda=sim|nao`, `paleta=escura|clara|personalizada`, `aprovacao=storyboard|direta` e `marca=sim|nao`. Opcionais são `cores` com os tokens `fundo,osso,acento,suave,linha` em hexadecimal, `nomes_autorizados` como lista e `descricoes` com texto livre. Use `--assumir` após delegação para preencher as recomendações pendentes.

O storyboard é um plano estático no mesmo formato do plano final, com cenas sem ações. O plano completo tem `versao:1` e uma lista `cenas`. Cada cena inicia numa âncora literal do roteiro, em ordem, e cobre até a cena seguinte ou o fim da fala. A primeira cobre desde a primeira palavra. Use `ocorrencia` com base 1 quando o trecho se repetir no mesmo parágrafo. O campo `p` aceita o número ou o ID `P007`.

```json
{"versao":1,"cenas":[{"id":"S01","inicio":{"p":7,"trecho":"Eu sento"},
"elementos":[{"id":"eu","tipo":"figura","x":250,"y":720,"w":300,"h":480}],
"acoes":[{"alvo":"eu","acao":"sentar","em":{"p":7,"trecho":"sento"}}]}]}
```

Cada ação usa `alvo`, `acao`, `em` e, conforme o tipo, `valor`. `andar` recebe o x final, `mudar_cor` um token e as ações textuais recebem o texto resultante. A frase de cada cena é extraída da fala. Planeje 2 a 12 s por cena e registre `justificativa_ritmo` quando fugir da faixa. Sem áudio, a prévia usa 140 palavras/min e indica a estimativa. Com áudio, cada âncora de cena e ação precisa corresponder a uma palavra medida. Palavras sem correspondência direta nas legendas podem ser interpoladas. Uma âncora não reconhecida pede conferência do áudio e da transcrição.

## Aprovar e renderizar

```sh
python3 scripts/pictograma.py storyboard --root PROJETO --plano storyboard.json
python3 scripts/pictograma.py aprovar-storyboard --root PROJETO --confirmado
python3 scripts/fluxo.py cenas --root PROJETO --plano cenas_pictograma.json
python3 scripts/transcrever.py --root PROJETO --local-only
python3 scripts/sincronizar.py --root PROJETO --renderizar
```

Rode a aprovação somente após o usuário confirmar os quadros. Se a fala, o storyboard, o formato ou a direção mudarem, faça nova aprovação. O plano aprovado para aplicação fica em `material/cenas_pictograma.json`. Para direção direta, siga para a prévia depois de registrar as escolhas e validar o plano. A prévia HTML tem reprodução, pausa, reinício, barra de tempo e atalhos. `quadros --tempo SEGUNDOS` captura amostras da prévia e pode ser repetido. `sincronizar.py --renderizar` captura PNGs a 30 fps e exporta o MP4 com o encoder compartilhado. O diretório `pictograma-9x16/` ou `pictograma-16x9/` reúne as saídas. Confira `timeline_previa.json` para os tempos da prévia e `timeline_pictograma.json` para os tempos e metadados do vídeo exportado.

## Conferência para exportar

A exportação exige a auditoria integral e o parecer visual da prévia correspondente. Use `pictograma.py auditar --root PROJETO --integral` para conferir todos os quadros antecipadamente. A prévia pode ser amostrada e o relatório indica o modo. Os IDs internos aparecem nos controles da apresentação e ficam fora do palco.

## Composição coreografada

O modelo opcional `coreografia.modelo: virada_banco_ajuda_v1` encena uma virada tipográfica, a ação no banco e a ajuda seguida de comparação. Ele usa três cenas com corte casado e gestos próprios. As chaves `negacao`, `conceito`, `virada`, `sentar`, `esperar`, `levantar`, `ajudar`, `receber` e `fazer` em `coreografia.ancoras` seguem a mesma sintaxe literal de `entrada`. O validador confere ordem, cena e espaço temporal para a atuação. Outros roteiros podem usar o vocabulário declarativo da biblioteca.

O parecer do modelo registra oito notas, com mínimo de 4 em cada critério. A exportação vincula a revisão ao plano e ao manifesto dos quadros. A comparação de luminância exclui a faixa de legendas e mede o trecho ativo e a cauda nos PNGs e no MP4.

Na exportação do Pictograma, a trilha fica 13,5 dB abaixo da voz em média nos intervalos de fala. Para ajustar, use `--nivel-trilha-db` entre −15 e −12. Pausas de pelo menos 0,6 s permitem duas rampas de 0,3 s. O MP4 é medido após a codificação AAC, com alvo de −14 LUFS integrados e teto de −1 dBTP.

A composição `virada_banco_ajuda_v2` usa a [bíblia visual](biblia_visual_pictograma.md), com folhas de modelo e auditoria de juntas, contorno e luz. O plano registra `enquadramento` com a altura de figura e a linha do chão, e `storyboard` com uma nota, leitura sem som e âncora literal por batida.

Para testar outro renderizador, leia [Godot no piloto do Pictograma](godot.md). Valide o caminho e a assinatura do aplicativo antes da primeira execução.


A composição de piloto `virada_banco_ajuda_v3` usa o rig anatômico de seis cabeças. Confira as duas folhas com `pictograma.py folhas --root PROJETO` e registre a aprovação com `pictograma.py aprovar-folhas --root PROJETO --confirmado`. A identidade inclui o rig, as ferramentas e os arquivos das folhas. O diagnóstico só aparece na prévia quando ativado. O ensaio de pixels desse piloto usa `medir_palco_anatomico.mjs` e `auditar_mp4_anatomico.py` (NumPy do runtime disponível) para conferir solas e sobreposição no MP4 vertical decodificado, além da auditoria de SVG. A medição distingue o contato mão com mão da interpenetração fora da região autorizada.

## Liberação do vídeo declarativo

Use o mesmo plano e a mesma seleção de trilha nas três etapas. A narração deve ser fornecida e ter marcações verificadas. Sem áudio, use `compor` para a prévia estimada.

```sh
python3 scripts/pictograma.py auditar --root PROJETO --direcao PROJETO/material/direcao_pictograma.json
python3 scripts/pictograma.py parecer --root PROJETO --direcao PROJETO/material/direcao_pictograma.json --parecer parecer.json --rodada 1
python3 scripts/pictograma.py video --root PROJETO --direcao PROJETO/material/direcao_pictograma.json
```

O `parecer.json` tem `resultado` (`aprovado` ou `corrigir`), `ocorrencias`, as oito `notas` descritas na revisão artística, `modos` (`com_som`, `sem_som` e `celular`) e `evidencias`. Cada evidência indica `cena`, `quadros` em ordem e `observacao`. Abra as tiras da auditoria, reproduza a sequência com e sem som e anote onde o peso, o gesto, o texto e a passagem ficam legíveis. Cite entrada, pose-chave, contato e soltura quando houver. A skill corrige e repete a revisão em até três rodadas. Consulte o usuário quando o sentido da fala ou uma escolha reservada continuar em dúvida.

A matriz `material/salvaguardas.json` registra `aprovada`, `reprovada`, `nao_aplicavel` com motivo ou `sem_evidencia`. Regras obrigatórias exigem medição da etapa correspondente. As checagens especializadas de outros percursos continuam indicadas no catálogo. A geometria do navegador sustenta as checagens de encenação. A decodificação confronta todos os quadros com o render, verifica a faixa da legenda e mede sola e assento nos quadros em que o plano os exige.

Para substituições parciais, `video --direcao PLANO --candidato MONTAGEM.mp4` valida a montagem inteira e a faixa AAC contra o render e a mixagem do plano autorizado. Conserve a montagem anterior até a promoção. Inserções históricas sem render compatível precisam da evidência do percurso em que foram aprovadas. Guarde o arquivo aprovado por SHA-256 e mantenha seus resultados separados dos do banco de provas.

Antes de corrigir um defeito novo, registre a cena e o quadro, o contraexemplo, a regra de decisão e a checagem proposta. Só marque o erro como resolvido depois de a mutação falhar, a correção passar e a checagem estar ligada à etapa em que precisa atuar.
