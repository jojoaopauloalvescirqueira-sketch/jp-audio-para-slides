# Diretor de animação

Ao selecionar Pictograma, leia a fala inteira, a direção narrativa e o guia. O diretor de arte traduz ideias em imagens e movimentos sem acrescentar afirmações à fala. Abra a referência visual quando precisar entender o vocabulário do estilo.

Peça a `diretor-de-animacao` primeiro somente as perguntas. A coordenação as apresenta em uma mensagem com até seis itens e aguarda. Use um exemplo curto da fala real em cada item, explique o efeito de cada opção e marque **Recomendado**. Aproveite escolhas já registradas. Em ambiente sem subagentes, faça a mesma etapa separada antes de propor cenas.

1. **Quem cria as cenas?** Diretor cria todas (recomendado), usuário descreve as principais e o diretor completa, ou usuário descreve todas e o diretor converte.
2. **Tom visual.** Sóbrio e reflexivo, didático e claro (recomendado) ou energético. Escolha junto a densidade de animação. Moderada dá mais respiro, abundante (recomendado) mantém micro-movimento e máxima permite acentos secundários. Mantenha até dois movimentos de destaque simultâneos e preserve a leitura.
3. **Metáfora.** Literal, ilustrativa (recomendado) ou metafórica. Símbolos ilustram a fala e preservam seu sentido.
4. **Personagens e rótulos.** Figuras genéricas sem nomes reais (recomendado), papéis identificados por rótulos como “VOCÊ”, ou nomes reais explicitamente autorizados. Registre os nomes autorizados individualmente.
5. **Texto e legenda.** Palavras-chave cinéticas (recomendado), frases curtas ou sem texto editorial. Escolha separadamente legenda palavra a palavra. Recomende legenda ligada.
6. **Paleta e aprovação.** Escura JP (recomendado), clara ou personalizada. Recomende storyboard antes da animação completa. A opção direta permite aplicar o plano completo após a direção.

Com “decide você”, registre as recomendações como `padrao_assumido`. A preferência de storyboard continua valendo. Grave cada valor, origem e data por `pictograma.py direcao`. Quando o usuário fornecer cenas em texto livre, preserve suas decisões, liste as que a biblioteca não representa e proponha o elemento mais próximo.

A coordenação repassa as respostas ao diretor. Com storyboard, o diretor entrega somente quadros estáticos declarativos. Rode `storyboard` e apresente os PNGs e o HTML. Após aprovação explícita, rode `aprovar-storyboard`. Só então solicite ao diretor o plano completo. Com direção direta, solicite o plano completo depois de registrar as escolhas. Em ambas, o diretor devolve JSON conforme [o contrato](pictograma.md). A coordenação aplica e valida usando o script.

## Direção artística e revisão

Antes do plano, escreva `material/acoes_pictograma.md`. Para cada frase-chave registre ator, verbo, alvo, pose inicial e final, causa, efeito e conferência.

- Ensaie os gestos por etapas. Para sentar, chegar, virar, inclinar, baixar e assentar. Para levantar, inclinar, impulsionar, estender e assentar. Para ajudar, aproximar, parar por 4–6 quadros, alcançar mão com mão, manter o contato por pelo menos quatro quadros, puxar, erguer e assentar. Na entrega, faça contato antes da transferência. Verifique poses, apoios, segmentos e ordem causal.
- Antecipe ações principais por 3–6 quadros. Use trajetórias em arco, atraso de 2–4 quadros entre segmentos, sobrepasso de 3–8% com assentamento de 6–10 quadros e pose legível por 6–12 quadros. Entradas têm seis quadros ou mais, salvo corte deliberado. Caminhada alterna passos. Figuras respiram e a câmera acompanha o foco. Confira na folha de contato.
- Dê à virada ao menos 0,8 s. Preserve a negação até o risco visível e até a nova leitura estar estabelecida. Use 1–3 palavras de conceito no palco e confira três palavras consecutivas repetidas na legenda.
- Enquadre a figura principal com 30% da altura durante a ação. Use até dois destaques simultâneos. Preserve lado, cor e escala nas transições, com deslocamento visível quando houver mudança. Mostre RECEBE nas mãos abertas e FAZ em gesto de entrega. Verifique a composição e a atuação na revisão visual.

## Formas, luz e leitura sem som

Leia a [bíblia visual](biblia_visual_pictograma.md) antes de definir o elenco. Apresente a folha de modelo para aprovação antes do storyboard. Em cada batida, anote em uma linha o que a imagem mostra, por que a escolheu e a metáfora usada. Em cada cena, registre o que deve ficar claro com o som desligado. Faça os efeitos seguirem o gesto e a palavra de mudança. Preserve uma fonte de luz, escala de personagem e proporções do elenco.

Para o piloto P007–P008, planeje as poses, as entradas e os pousos conforme os [quatro erros conhecidos do piloto](auditor_animacao.md#erros-conhecidos-do-piloto-p007p008).

## Catálogo de regressões

Leia [erros conhecidos](erros_conhecidos.md) antes de propor ou corrigir o Pictograma. Registre cada defeito novo no catálogo com exemplo, regra, checagem e teste de reprodução antes da correção. Em batidas com afirmações de contato ou posição, declare `afirmacoes` no storyboard. O auditor geométrico entende `maos_em_contato`, `pes_no_chao`, `sentado_no_banco`, `palmas_no_peito`, `coracao_nas_maos` e `agente_a_esquerda`. Use o quadro em que a condição realmente aparece. Para outra afirmação espacial, indique-a ao revisor visual até que exista uma checagem.

Para conteúdos diferentes, escolha o [padrão de encenação](padroes_pictograma.md) e registre quadro de ações, metáfora, elenco e âncoras antes de compor. O banco guarda a saída do diretor sem correções manuais nas cenas. Ajustes de biblioteca exigem rodar a mesma proposta novamente.

## Ensaiar antes de nomear

Uma batida precisa de um verbo que a figura execute. No quadro de ações, descreva o gesto no começo, no pouso e no assentamento. Descreva o que se entende sem legenda. Admita repouso como pausa justificada de até 1,5 s, no máximo uma a cada quatro batidas. Câmera e respiração complementam a atuação.

- Dê ao objeto escala de pelo menos uma cabeça e um papel no gesto. O ator o segura, olha para ele, carrega, entrega ou apoia. Reserve até um elemento abstrato solto por trecho. Em uma enumeração, encene o uso ou a chegada de cada objeto.
- Alterne composição e posição por motivo narrativo. Uma pergunta pode pôr o ator entre as alternativas. Uma conversa põe duas figuras frente a frente com gestos alternados. Um percurso dá direção à passagem do tempo. Rejeite três layouts equivalentes seguidos e limite o molde de título no alto com objeto à esquerda e figura parada à direita a uma ocorrência.
- Limite as palavras-chave grandes a uma entrada a cada 4 s. Use título vazio quando o gesto bastar. Dê aos rótulos apenas a informação que a imagem não transmite. Em temas sensíveis, use gestos contidos, sem destaque. Antes de personificar uma presença religiosa ou uma pessoa real, apresente a proposta e aguarde autorização. Use figura genérica sem traços identificáveis.
- Examine os textos visíveis com a lista de pessoas privadas do projeto. Mantenha a forma original nas âncoras literais. A exibição da legenda segue somente as substituições autorizadas no projeto.

Compare as poses com P007–P008 para dar nota 4. Mais de metade dos quadros de ator em repouso limita causa e efeito, naturalidade e clareza sem som a 2. A auditoria mede mudanças de ângulo, cobertura das batidas, repetição, tamanho e vínculo do objeto e mudança dos atores e objetos nos pixels do MP4 com câmera compensada.

## Verbo-chave na batida

Antes de escolher a encenação, identifique o verbo central na fala de cada batida. Se houver uma ação correspondente na biblioteca, use-a. Na preparação de planos declarativos novos, use `verbos_chave: "aplicar"` para propor a atuação a partir da fala e `verbos_chave: "validar"` para bloquear uma ação divergente com EC-097. Revise a intenção quando a expressão fugir do vocabulário reconhecido.

Quando a fala descreve uma tentativa que falha, encene a tentativa e o retorno ao apoio. Na conversa, alterne o gesto de quem fala e a inclinação de quem escuta. Confira nos quadros separados o início, a ação e o retorno quando essas fases forem necessárias para ler a cena.

Verifique a modalidade do verbo. Em uma negação, condição ou alternativa rejeitada, mostre a tentativa ou a recusa e ofereça duas opções que preservem a intenção. O compilador registra o EC-098 quando a atuação diverge. A triagem de opções reúne baixa ação corporal, divergência de verbo, falta de segundo ator, repetição e passagens sensíveis. Reúna as perguntas numa só mensagem, com teto de seis por minuto. Acima do teto, registre falha de direção. Registre escolhas por assinatura da fala no `projeto.json`, com data e origem `usuario` ou `padrao_assumido`.

Após compor a prévia declarativa e gerar as poses, rode `python3 scripts/pictograma_opcoes.py --root PROJETO`. Para cada opção, capture o quadro do pouso com a variação correspondente e descreva o que se vê sem som. Use `--resposta "1A, 2B"` para registrar a resposta ou `--assumir` para registrar os padrões nas batidas pendentes. Refaça a composição após o registro.

## Gestos expressivos

Nos novos planos declarativos, use `gestual: "expressivo_intencional"`. Registre `gesto` em cada ação. Inclua `intencao`, `alvo`, `mao` (E, D, ambas ou nenhuma) e `saida` (repouso, apoio ou continua). Use a âncora literal da própria ação. Declare `assento: true` quando a figura já começa e permanece apoiada no banco. Revise o verbo antes de declarar o gesto. A sugestão automática de verbo não substitui essa escolha.

Use a fala para decidir quem gesticula. Quando a outra figura escuta, direcione o olhar e conserve as mãos apoiadas ou relaxadas. Se ela precisar agir, declare sua ação em uma batida própria. Na leitura, sustente o livro. Em marcha, deixe o balanço dos braços acompanhar os passos. Em contato, confira a chegada das mãos, a sustentação e a soltura. Nas passagens abstratas, escolha o olhar, uma mudança de postura ou uma pausa quando o braço não acrescentar sentido.

Para uma oferta seguida de recusa, declare `segunda_ancora` na mesma ação. A primeira âncora conduz a palma ao interlocutor. A segunda liga a mão ao peito e à retirada. O EC-099 verifica mãos ativas, deslocamentos, alcance e contato durante a auditoria.

Para mostrar a recepção como continuação imediata da entrega, use `relacao: "segurado"` na ação `receber`. Mantenha objeto, elenco e layout da batida anterior para conservar a posse do objeto.

Para `mao_presente`, use uma palma aberta que vem do alto em diagonal. O olhar antecede o braço. Mantenha a aproximação sem contato durante a sustentação e recue as duas mãos antes da próxima batida. O EC-101 verifica a folga entre os contornos, a posição do cotovelo e a presença visual durante a sustentação.

Em conversas expressivas com duas figuras, use dois ou três `acentos` em `acao`, cada um com `tipo` e `em` literal. Use `abrir` para oferecer uma ideia, `precisar` para delimitar e `ponderar` para reflexão. Alterne a forma da mão e deixe intervalos de repouso. A reação de escuta fica na cabeça. O EC-102 impede que os acentos repitam a intenção ou se sobreponham.

Na leitura, dê apoio ao livro durante a abertura e a virada. A folha se dobra em torno da lombada e uma mão continua sob a capa. Em `mao_presente`, use o holofote suave apenas durante a entrada, a sustentação e o recuo da palma. EC-103 e EC-104 conferem o apoio e a duração do feixe.

Para a entrada num segmento já aprovado em vídeo, alinhe o último enquadramento e faça a cartela ganhar contraste gradualmente. Use `pictograma_pixels.validar_ponte_titulo` nos níveis medidos nas letras do MP4 decodificado. Preserve os movimentos internos já aprovados.

## Movimento dos elementos da cena

Planeje também o que se move além das figuras. Uma batida aceita `grafico` com `tipo`, `textos` e a âncora literal em `em`. Use `contraste` para ligar duas ideias, `fonte` para abrir uma referência, `relogio` para explicar a espera, `rede` para revelar de dois a quatro conceitos em sequência ou `enfase` para uma palavra decisiva.

Faça o elemento entrar, completar o movimento na janela da fala e ficar legível até o corte. O gráfico ocupa uma faixa superior própria. Preserve o espaço dos atores, dos objetos que eles manipulam e da legenda. Escolha o desenho pela relação narrada. Em uma cena com contato, dê prioridade à leitura da pega ou da transferência.

## Cenários ilustrados

Use `cenario_ilustrado` para situar o gesto em um ambiente quando o espaço ajudar a entender a fala. Informe `tipo` e uma âncora literal em `em`. Os tipos são `esperanca`, `rua`, `janela`, `encontro`, `decreto`, `biblioteca` e `caminho`.

A primeira batida do cenário anima uma propriedade do ambiente e a deixa assentar. Batidas consecutivas com o mesmo tipo herdam essa posição final. O motor recorta o fundo, o plano intermediário e os detalhes mais próximos acima da legenda, atrás das figuras e dos objetos manuseados. Confira a leitura em tamanho de celular.

Em uma enumeração no cenário `rua`, declare até três entradas em `cenario_ilustrado.figuras`. Cada entrada traz `tipo` (`animal`, `idoso` ou `crianca`) e `em` com a palavra que apresenta a figura. Declare as entradas na ordem da fala. As figuras entram em 0,3 s, acumulam no quadro e saem juntas no fim da batida. Posicione o protagonista no lado oposto e verifique a leitura no celular. O EC-100 confere a presença, a ordem e a separação das figuras.

No livro manuseado, use a projeção das páginas voltadas para o leitor. A câmera pode ver a capa, o papel de viés e a espessura do volume. Quando houver oração com as mãos juntas, mantenha os cotovelos baixos, as palmas reunidas diante do peito e os dedos para cima durante a sustentação.

Use `atmosfera` na batida, com `tipo` e âncora `em`, quando a fala pedir mudança de luz. `sombra` acompanha uma mudança de postura dos interlocutores, `aura` envolve a figura, `chuva` esfria o ambiente e `claridade` aquece a ação. `partilha` exige a entrega de um coração ou a posse mantida. Prepare a luz do doador antes do contato e deixe-a crescer no recebedor depois da entrega. A saída do clima usa a transição já compilada.

## Continuidade entre batidas

Ative `continuidade: true` no plano declarativo para reaproveitar a última pose de cada personagem. O plano compilado distingue continuação de pose, troca de cenário em camadas e corte justificado. Mantenha o mesmo layout e elenco quando a fala continua no mesmo lugar. Registre `corte_justificado` na batida de entrada quando a mudança precisar ser imediata.

Em falas curtas, sustente o enquadramento e deixe a legenda marcar a troca. Reserve 0,3 a 0,8 s para a transição. Antecipe a preparação se a próxima pega já precisar estar firme no começo da batida. Preserve apoios e a identidade dos personagens. Para sustentar um objeto recebido numa batida de repouso, use `manter_posse: true` com os mesmos participantes e layout da transferência. Um projeto sem o modo conserva as suas transições originais.

Depois de `ajudar_a_levantar`, use `manter_elenco: true` na batida seguinte de olhar ou repouso. Preserve o mesmo layout e a pose final dos dois. O EC-113 confere o enquadramento, a estabilidade e a ausência de retorno ao banco.

Para encenar um passo depois de levantar, vincule `passo_em` ao verbo que pede a ação. O EC-114 confere o apoio e o avanço. Numa entrega de coração, `cuidado_em` ancora a resposta de quem recebeu com a mão livre e preserva a posse na outra. O EC-115 confere a ação e o apoio.
