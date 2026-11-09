# Ilustrado

Animação de ilustrações detalhadas em camadas. As imagens são PNGs que o usuário gera no ChatGPT com os prompts da skill. O [diretor de arte](diretor_arte.md) pergunta primeiro e propõe a bíblia visual, elenco, cenários e cenas. A coordenação apresenta as propostas e aplica as escolhas. A skill importa os arquivos fornecidos.

## Direção e storyboard

1. Registre a direção com `fluxo.py direcao_ilustrado --root PROJETO --respostas respostas.json`. Cada chave recebe `{"valor":"opção","origem":"usuario"}`. Em caso de delegação, `--assumir` preenche as pendências e marca a origem. Registre `descricao_cenas` quando o usuário fornecer cenas e `nomes_autorizados` para consentimentos explícitos.
2. Use `fluxo.py dados_ilustrado --root PROJETO --proposta proposta.json` com `biblia` (paleta hexadecimal com `fundo,osso,acento,suave,linha`, `traco`, `proporcoes`, `luz`, restrições e objetos opcionais), `elenco` (personagens, roupa, paleta, ID da folha e lista de poses) e `cenarios` (ID, descrição, camadas de fundo, meio ou frente e paralaxe). A skill registra os três JSONs em `material/ilustrado/`.
3. Após confirmação do usuário, use `fluxo.py aprovar_ilustrado --root PROJETO --etapa biblia --confirmado`. Aplique `fluxo.py cenas --root PROJETO --plano cenas_ilustrado.json`. Apresente `material/ilustrado/storyboard.md` e registre a aprovação com `--etapa storyboard --confirmado` antes dos prompts. Se o usuário já escolheu dispensar a aprovação do storyboard, confira o storyboard gerado e siga.

Os campos de direção são `criacao=diretor|colaborativa|usuario`, `estetica=historica|ludica|sobria`, `acento_jp=sim|nao`, `elenco=generico|historico|autorizado`, `nomes_na_tela=sim|nao`, `epoca=generica|referenciada`, `ritmo=calmo|medio|dinamico`, `camera=contida|paralaxe|dinamica`, `texto=titulos|palavras|nenhum`, `legenda=sim|nao`, `storyboard=aprovar|direto` e `marca=sim|nao`. Notas livres opcionais incluem `notas_epoca`, `paleta` e `cenas_por_minuto`. Preserve época, atribuições e ressalvas. Confira nomes reais também no texto editorial antes de exportar.

## Plano de cenas

A primeira cena começa na primeira palavra. Cada intervalo cobre até a próxima entrada ou o fim da fala. Use âncora literal `{p, trecho, ocorrencia}`, com ocorrência de base 1 para trechos repetidos. Ações ficam dentro da fala da cena, e duração de movimento pode ser indicada em `duracao_s`. Registre `justificativa_ritmo` para intervalos fora de 2–12 s. Coordenadas x/y e centro de câmera são normalizados entre 0 e 1. Os PNGs preservam suas proporções. 16:9 é padrão. Em 9:16, forneça `enquadramento` em cada cena e mantenha títulos entre y=370 e 1430, longe da coluna direita. A marca fica desligada inicialmente.

```json
{"versao":1,"formato":"16:9","cenas":[
  {"id":"C01","entrada":{"p":1,"trecho":"A primeira ideia"},"cenario":"patio",
   "camadas":[{"id":"fundo","asset":"patio_fundo","z":0},
              {"id":"figura","asset":"figura_em_pe","x":0.44,"y":0.61,"escala":0.45,"z":2}],
   "acoes":[{"alvo":"figura","acao":"trocar_pose","asset":"figura_sentada","em":{"p":1,"trecho":"senta"}},
            {"alvo":"camera","acao":"camera","zoom":1.15,"centro":[0.44,0.53],"em":{"p":1,"trecho":"espera"}}],
   "enquadramento":{"9:16":{"zoom":1.1,"centro":[0.44,0.55]}},"saida":"fusao"}]}
```

O kit aceita `entrar` (lado, fade ou escala), `sair`, `mover`, `trocar_pose` (fusão curta entre poses do mesmo personagem), `camera` (zoom e pan), `respirar`, `piscar` (precisa da pose com olhos fechados), `titulo_entra`, `titulo_sai`, `destacar`, `surgir_em_grupo` e `transicao` (fusão, corte ou deslize). Títulos são texto do motor, até seis palavras. Rótulos de pessoas privadas exigem consentimento registrado.

## Prompts, importação e vídeo

```sh
python3 scripts/fluxo.py prompts_imagens --root PROJETO
python3 scripts/fluxo.py importar_imagens --root PROJETO --pasta DOWNLOADS
python3 scripts/fluxo.py aprovar_ilustrado --root PROJETO --etapa imagens --confirmado
python3 scripts/fluxo.py cenas --root PROJETO --estimar
python3 scripts/transcrever.py --root PROJETO --local-only
python3 scripts/sincronizar.py --root PROJETO --renderizar
python3 scripts/validar.py --root PROJETO --video
```

Envie `material/ilustrado/prompts_imagens.md`. O usuário gera primeiro as folhas de personagem e as anexa aos pedidos de poses na mesma conversa. As demais imagens são camadas de cenário e objetos. Os PNGs usam os nomes exatos do pacote. A importação verifica resolução, alfa e identidade, registra a origem e gera `ilustrado/folha_contato.html`. Confira consistência e legibilidade, então registre o aceite. Para pedir refação use `--asset ID --refazer` na etapa imagens. Um PNG alterado exige nova importação e revisão.

A prévia usa estimativa de 140 palavras/min se o áudio ainda estiver pendente. Com áudio, alinhe as palavras e confira as entradas indicadas. O MP4 requer todos os PNGs aprovados e palavras medidas. Consulte [sincronização](sincronizacao.md) e [entrega](entregas.md).
