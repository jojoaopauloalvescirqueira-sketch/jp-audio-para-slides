# Direção narrativa

## Antes da fala

No percurso por artigo, leia a fonte inteira e recolha do pedido as escolhas já explícitas. Em retomadas, consulte também `projeto.json.direcao_narrativa`. Reúna os pontos pendentes em uma mensagem numerada com no máximo sete perguntas. Em cada uma, marque **Recomendado** e diga o efeito de cada opção. Concentre perguntas dependentes no mesmo item. Aguarde a resposta antes de escrever a fala. Os trechos do questionário são amostras para decisão.

Quando o usuário disser “decide você” ou delegar escolhas específicas, conserve o que ele já definiu e marque cada padrão adotado como `padrao_assumido`. Use as recomendações abaixo, com 16:9 como formato inicial. Escolhas explícitas e recomendações aceitas recebem a origem `usuario`. Se faltarem voz e destino sob delegação, registre “narrador neutro” e “destino a confirmar”. Se a direção já estiver completa, registre-a e avance direto. Roteiro pronto entra no fluxo de preservação da fala, com ou sem áudio.

## Perguntas e escolhas

1. **Quem narra e para onde?** Narrador neutro é a recomendação quando a voz é desconhecida. A voz do autor permite atribuir a ele as posições identificáveis do artigo. A voz de um participante admite vivências confirmadas. Para o perfil de outra pessoa, preserve a autoria do artigo e distinga quem fala de quem publica. Peça que a pessoa identifique a vivência ou posição que a primeira pessoa poderá narrar. Se essa informação faltar após a resposta, resolva só essa lacuna antes de escrever em primeira pessoa.
2. **Perspectiva e estilo.** Recomende narrador externo com clareza didática. Mostre as quatro opções da seção seguinte com versões do mesmo trecho de duas a três frases da fonte. Sob cada versão, indique tom, duração relativa e cuidado de fidelidade. O professor e o explicador podem combinar com as duas perspectivas. Permita direção por bloco quando a mudança ajudar a entender a fala.
3. **Registro.** Recomende o intermediário, com cadência de conversa e termos precisos. Mostre a mesma frase em registro culto, com sintaxe formal própria para voz, falado, com expressões como “pra” e “a gente” quando couberem, e intermediário. Ajuste a frequência dos coloquialismos à voz e ao público.
4. **Cobertura, duração e formato.** Recomende referências preservadas, tempo guiado pelo conteúdo e 16:9. Em cobertura integral, mantenha as referências na fala com atribuição oral e os dados completos nas notas. Cobertura essencial permite propor um recorte, com cortes de referências explicitamente autorizados. Uma meta de tempo orienta palavras e ritmo. Se conflitar com cobertura, mostre a faixa estimada e as referências ou passagens que precisariam sair, e aguarde decisão antes do corte. 9:16 muda a composição visual e pode exigir mais cenas. Use 21:9 quando explicitamente pedido.
5. **Falas de terceiros**, quando presentes. Recomende discurso indireto, que conserva termos relevantes com atribuição e sem aspas. Citação literal preserva palavras verificáveis, com aspas e crédito. Paráfrase adapta a formulação ao público e mantém a ideia atribuída. Distinga a voz de quem narra da voz citada.
6. **Trechos sensíveis**, quando presentes. Recomende manter a formulação e o contexto da fonte. A opção de oferecer alternativa apresenta as duas formulações e seus efeitos antes da troca. Preserve a posição atribuída até o usuário decidir.

## Demonstrar no material real

Escolha uma passagem curta que represente a dificuldade do roteiro. Conserve os fatos e a atribuição nas quatro versões, com as mesmas ressalvas relevantes. Para demonstrar primeira pessoa sem vivência confirmada, rotule a amostra como hipótese e use uma ação de leitura, como “ao olhar a imagem”. Use os exemplos fixos abaixo para explicar as opções enquanto a fonte estiver pendente. Volte ao material real para decidir a direção da fala.

**Trecho de referência da demonstração.** “No centro do afresco, Platão aponta para o alto e Aristóteles estende a mão para baixo. Uma leitura associa os gestos ao mundo das ideias e à observação da natureza.”

- **Terceira pessoa.** “No centro do afresco, Platão aponta para o alto e Aristóteles estende a mão para baixo. Uma interpretação associa o primeiro gesto ao mundo das ideias e o segundo à observação da natureza.”

  **Impacto.** Tom observador, duração de referência. Funciona para conteúdo de terceiros e facilita atribuição. A distância pode reduzir o calor da história. Mantenha a interpretação atribuída como leitura.
- **Narrador-personagem.** “Se eu estivesse observando o afresco, começaria pelas mãos. Platão aponta para cima e Aristóteles, para baixo. A leitura que eu estaria examinando liga um gesto às ideias e o outro à observação da natureza.”

  **Impacto.** Tom próximo, duração um pouco maior. Funciona com uma vivência ou posição identificável. A amostra é hipotética. A fala final só atribui experiências, emoções e memórias confirmadas e identifica personagens fictícios na própria fala.
- **Professor de alto nível.** “Vamos separar a observação da interpretação. Platão aponta para o alto e Aristóteles estende a mão para baixo. A leitura em exame associa um gesto ao mundo das ideias e o outro à observação da natureza, e os gestos por si só deixam essa interpretação em aberto.”

  **Impacto.** Tom analítico, duração maior. Funciona para premissas, objeções e método. Pode soar distante. O rigor é um padrão de exigência, sem alegação de vínculo acadêmico, incluindo com Harvard.
- **Clareza didática.** “Olhe para as mãos. Platão aponta para cima e Aristóteles, para baixo. Uma leitura liga o primeiro gesto às ideias e o segundo ao estudo da natureza.”

  **Impacto.** Tom direto, duração menor. Funciona quando o público precisa visualizar o conceito rapidamente. A simplificação mantém a ressalva de que se trata de uma interpretação.

Registro para o mesmo ponto do exemplo:

- **Culto.** “A observação dos gestos permite compreender essa interpretação do afresco.”
- **Falado.** “Olhando pras mãos, a gente entende de onde vem essa leitura do afresco.”
- **Intermediário.** “Quando olhamos para as mãos, fica mais fácil entender essa leitura do afresco.”

## Registrar e conferir

Use `fluxo.py direcao --root PROJETO` antes da escrita. Consulte `--help` para os valores de cada opção. `--duracao-alvo` recebe segundos positivos ou `livre`. Repita `--assumir CAMPO` para as opções delegadas, com os nomes internos em snake_case, como `duracao_alvo` e `falas_terceiros`. Registre a base verificável da primeira pessoa em `--vivencia`. Use `--bloco ID:PERSPECTIVA:ESTILO` para ajustar um bloco. Deixe um dos campos vazio para manter a escolha existente ou herdar a global. O identificador acompanha o mapa didático.

O relatório textual conta marcas explícitas de primeira pessoa e coloquialismos fora de aspas e linhas de diálogo reconhecidas. Com bloco em primeira pessoa, revise a perspectiva manualmente por bloco, pois o validador recebe a fala sem os IDs dos blocos. Em registro falado, a ferramenta alerta para três ou mais dois-pontos quando a frequência chega a três por cem palavras, e para duas ou mais aberturas com a mesma muleta. Duração usa a faixa existente de palavras por minuto e alerta quando a faixa inteira fica fora da margem de 20% da meta. Esses sinais orientam a revisão humana. Fidelidade, atribuição e qualidade da fala são avaliadas na revisão editorial.
