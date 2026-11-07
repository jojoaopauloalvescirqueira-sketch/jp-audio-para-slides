# Pictograma

## Escolher o estilo antes de produzir

Ao planejar visuais para vídeo, gerar ou retomar um vídeo, resolva o estilo primeiro. Use o estilo explícito no pedido, `projeto.json.estilo_video`, o perfil implícito dos projetos anteriores ou `JP_ESTILO_VIDEO_PADRAO`, nessa ordem. Se houver estilo resolvido, informe-o em uma linha. Se faltar a escolha, apresente estas opções antes de produzir:

- **Editorial JP** — cartões de texto, figuras, fundo claro e movimento breve.
- **Pictograma** — personagens e símbolos em fundo escuro, com ações ligadas a palavras. Tem mais cenas para revisar e renderização mais demorada.
- **Legado** — composição antiga, sem marca d’água.

Pergunte “Qual estilo você quer usar?”. Integre este item ao questionário que já estiver aberto quando souber que o pedido inclui vídeo ou plano visual. O menu geral continua sendo a escolha de função. Depois da primeira escolha manual, pergunte uma única vez se quer torná-la padrão. Mostre, por exemplo, `export JP_ESTILO_VIDEO_PADRAO=pictograma`, com o ID escolhido. A escolha e o formato podem ser registrados no projeto pelo comando abaixo. O próprio usuário define seu ambiente.

```sh
python3 scripts/pictograma.py estilo --root PROJETO
python3 scripts/pictograma.py estilo --root PROJETO --estilo pictograma --salvar
```

Com Pictograma, siga [as perguntas do diretor](diretor_animacao.md) antes de pedir cenas. Use os fluxos existentes para preparar a fala, receber áudio, medir e transcrever localmente. O Pictograma usa o mesmo alinhamento de palavras e a mesma exportação H.264 com mixagem da biblioteca de Mozart ou faixa indicada.

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
python3 scripts/pictograma.py previa --root PROJETO --plano cenas.json
python3 scripts/transcrever.py --root PROJETO --local-only
python3 scripts/pictograma.py video --root PROJETO
```

Rode a aprovação somente após o usuário confirmar os quadros. Se a fala, o storyboard, o formato ou a direção mudarem, faça nova aprovação. O plano aprovado para aplicação fica em `material/cenas_pictograma.json`. Para direção direta, siga para a prévia depois de registrar as escolhas e validar o plano. A prévia HTML tem reprodução, pausa, reinício, barra de tempo e atalhos. `quadros --tempo SEGUNDOS` captura amostras da prévia e pode ser repetido. `video` captura PNGs a 30 fps e exporta o MP4 com o encoder compartilhado. O diretório `pictograma-9x16/` ou `pictograma-16x9/` reúne as saídas. Confira `timeline_previa.json` para os tempos da prévia e `timeline_pictograma.json` para os tempos e metadados do vídeo exportado.
