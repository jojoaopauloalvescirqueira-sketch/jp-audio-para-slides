# Editorial JP

## Escolher as mudanças

Leia a fala canônica linha por linha. Separe unidades de sentido nos parágrafos existentes e registre uma decisão por trecho literal em `material/mapa_visual.json`. Uma pausa, conclusão curta ou continuação pode manter o estado. Divida uma passagem longa quando uma comparação, conta, relação ou ressalva pedir evidência nova. A quantidade decorre da fala e do tempo de leitura. Justifique intervalos abaixo de dois segundos ou acima de doze.

```json
[
  {"p": 1, "trecho": "A taxa subiu para quatro por cento.", "decisao": "nova",
   "slide_id": "S001", "motivo": "Tornar visível o primeiro valor narrado."},
  {"p": 1, "trecho": "O período foi de um ano.", "decisao": "manter",
   "slide_id": "S001", "motivo": "A unidade de tempo já está no cartão."}
]
```

Divida cada parágrafo em trechos contíguos na ordem da fala, preservando grafia e pontuação. Espaços entre trechos podem ser omitidos. Cada entrada de cena começa um trecho e usa `nova` ou `revelar`. Os demais trechos usam `manter` com o ID da cena ativa. O gerador valida a cobertura completa e a relação com o gatilho.

## Compor com o tema

- Comparação `comparacao` com `itens` contendo um a três pares `rotulo` e `valor`. Inclua unidade no valor e condições em `body`. Um item reserva o lugar de um segundo para a revelação seguinte. Use proporções gráficas somente com unidade, escala e base comparáveis.
- Cálculo `conta` com as expressões em `lines`. Crie estados separados para fatores, fórmula e resultado quando esses elementos forem enunciados separadamente. Mantenha título, alinhamento e premissas durante a progressão.
- Relação `diagrama` com duas a quatro etapas em `lines`. Setas representam a relação descrita na fala. A sequência não comprova causalidade.
- Figura `figura` com crédito e contexto de eixos, período e unidades. Para detalhe, defina `vistas` no catálogo com a figura completa e um recorte preparado. A figura mantém sua proporção, fica inteira e acompanha o recorte. Para gravura conceitual, catalogue como `natureza: "ilustracao"`; o slide a identifica como ilustração.
- Capa, definição, ideia, síntese e encerramento continuam disponíveis. Preserve a composição larga, as margens e o fundo claro. O modelo reserva a região inferior direita para a marca JP Wealth, com 55% de opacidade, largura de 9% da tela limitada a 160 px. Em vertical a marca termina em y=1430.

Novos projetos recebem `perfil_visual: "editorial_jp"`, a cópia local `material/marca-dagua-jp-wealth.png` e um mapa vazio para preencher. Para adotar o perfil em uma cópia de projeto antigo, acrescente esse campo, copie a marca a partir de `assets/jp-wealth-logo.png` para o caminho acima e construa o mapa. O arquivo de marca veio do ativo JP Wealth da skill JP Slides Didáticos. Projetos legados podem ser iniciados explicitamente com `--perfil-visual legado`.

## Animar a entrada

Em cada estado, declare no máximo um objeto `movimento`, por exemplo `{"tipo":"revelar","alvo":"item-2"}`. Use `item-N` nos cartões, `linha-N` em contas, diagramas e sínteses e `vista` em figuras. `revelar` aumenta a opacidade do elemento, `realcar` faz aparecer seu contorno e `aproximar` amplia em até 6% as imagens da vista preparada. A legenda e a marca ficam fixas.

O PNG final e a prévia HTML mostram o estado estável. A renderização completa gera sete quadros intermediários por efeito. Ao exportar, a timeline substitui os sete primeiros quadros do intervalo pelos intermediários e mantém o PNG final. Intervalos menores que oito quadros usam corte. `render_manifest.json` associa arquivos e hashes às entradas visuais e ao formato. Após alteração de plano ou recurso, gere todos os quadros. `--somente` permite inspeção parcial e exige nova renderização completa antes de exportar.

Indique `conferir_audio: true` em comparações, resultados e ressalvas cuja entrada exija conferência. Use o fluxo de alinhamento e revisão documentada. Para uma exceção de ritmo, acrescente `ritmo_justificativa` ao estado e verifique a ocorrência no relatório de sincronização. Guarde a evidência efetivamente consultada e diferencie reconhecimento local de audição perceptiva.
