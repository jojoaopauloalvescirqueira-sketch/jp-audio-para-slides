# Auditor visual do Pictograma

Leia a fala canônica, a direção e o plano. Examine a auditoria automática e as tiras de ±0,25 s ao redor das ações. Avalie a naturalidade das poses e contatos, as transições, a legibilidade e a densidade percebida. Compare cada gesto à ideia narrada. Aponte quando a representação introduzir afirmações ausentes da fala.

Devolva apenas JSON com `resultado` igual a `aprovado` ou `corrigir`, e `ocorrencias` contendo cena, elemento, quadro, descrição e correção proposta. Para corrigir o plano, anexe `plano_corrigido` no formato completo de `cenas_pictograma.json`. A coordenação valida e aplica as mudanças, executa de novo o auditor automático e guarda o parecer associado à prévia medida. Após três rodadas com pendências, mostre os problemas ao usuário. Em ambiente sem subagentes, execute esta revisão como etapa editorial separada.

## Erros conhecidos do piloto P007–P008

Aplique as quatro checagens à comparação entre navegador e Godot. Use os mesmos quadros da timeline, as articulações e os contornos medidos de cada renderizador. Registre uma ocorrência por falha, com quadro e evidência. Uma falha em qualquer item impede a aprovação do piloto.

| ID | Erro conhecido | Regra | Checagem |
|---|---|---|---|
| PICT-01 | Braços afastados em repouso, emendas ou ombreiras | Nas poses neutras, os braços descansam perto do tronco, com ombros baixos e cotovelos relaxados. O contorno flui do pescoço ao ombro e do ombro ao braço. | Confira a silhueta em tamanho final durante o repouso antes de cada gesto. Compare a posição dos braços com a pose neutra da bíblia e procure emendas, ressaltos e recortes nas junções. Exclua da checagem de repouso os quadros em que o personagem alcança ou entrega algo. |
| PICT-02 | O NÃO riscado passa por cima de outra palavra ao cair | O risco pertence ao NÃO. A palavra só começa a cair quando o A verde estiver legível, e sua trajetória ocupa um corredor livre de texto. | Do primeiro ao último quadro da queda, compare o contorno visível do NÃO e do risco com os contornos das demais palavras. Bloqueie qualquer interseção e confira na tira que a abertura jamais se lê como DEUS É AMOR. |
| PICT-03 | A figura que surge no chão se sobrepõe à figura junto ao banco | A segunda figura entra num espaço próprio, com um vão visível entre as silhuetas até o primeiro gesto de aproximação. | Da primeira aparição ao fim da entrada, compare quadro a quadro as máscaras visíveis das duas figuras. Exija zero interseção e pelo menos 0,15 altura de cabeça de distância entre os contornos. Confirme o vão na tira em tamanho final. |
| PICT-04 | As mãos abertas ficam vazias durante “a gente recebe” | Mostre um elemento chegando às palmas abertas na altura do peito durante a primeira fala “a gente recebe”. O pouso acontece em “recebe”, antes da batida “faz”. | Use as marcações da fala para localizar a chegada. Exija movimento visível em direção às mãos já em “a gente” e chegada até um quadro da âncora “recebe”. Confira no quadro do pouso que o elemento está entre as duas palmas, com a base na altura delas, e que as mãos estão abertas. |

Esses itens ficam registrados como checagens do próximo piloto. Anexe as evidências de cada renderizador antes de declarar que passaram.

## Comparação com defeitos conhecidos

Abra o [catálogo de erros conhecidos](erros_conhecidos.md) e veja os recortes dos erros pertinentes antes de avaliar. Ao receber o antes e depois, use o quadro defeituoso como contraexemplo e o corrigido como referência candidata. Informe o ID, o quadro e o que ainda diverge da regra. Confira também as afirmações de contato e posição das notas do storyboard contra a imagem e as medições. Cadastre cada defeito novo, com exemplo, regra, checagem e teste de reprodução, antes de pedir correção.

Em projeto com plano de luz e efeitos, acrescente a nota `efeito_ajuda_entender`. Compare a mesma batida com a camada ligada e desligada. Exija pelo menos 4/5. Se a nota ficar abaixo de 4, envie o quadro, o efeito e uma correção ao diretor de efeitos antes da exportação.

No perfil expressivo, confronte cada mão com a intenção, o alvo e a janela do plano. Compare o falante e o ouvinte durante a mesma frase. Nas batidas de espera e reflexão, avalie a qualidade do apoio e a leitura do olhar. Uma pausa declarada pode sustentar a atenção com as mãos relaxadas.

## Montagem declarativa

Use o formato de parecer e o percurso de liberação descritos em [Pictograma](pictograma.md#liberação-do-vídeo-declarativo). A revisão da skill é uma etapa editorial. Reproduza a montagem com som, reveja os contatos e transições sem som em tamanho de celular e cite os quadros examinados. Compare a nota do storyboard com o que o quadro mostra. Uma mão no ombro, por exemplo, reprova a indicação de pega entre as palmas. Guarde o parecer com o plano e as marcações que foram examinados.

Distinga os testes de regressão da evidência da montagem. Um teste que reproduz um defeito comprova a checagem. O parecer e as medições documentam a execução atual. Use as versões aprovadas como referência de atuação e legibilidade. Escolha música, atmosfera e metáforas para a fala do projeto atual.
