# Padrões de encenação do Pictograma

O diretor parte da fala canônica e usa os padrões para escolher a relação visual principal. Cada cena deve mostrar uma ideia. Use os contraexemplos no [catálogo](erros_conhecidos.md) para revisar o desenho e a atuação.

| Padrão | Use quando | Evite | Acerto e erro a conferir |
| --- | --- | --- | --- |
| Virada | Uma negação, troca ou oposição altera o sentido | Fazer a palavra negar tarde ou ficar pendurada | A leitura original dura até a virada. EC-024, EC-025 e EC-073 |
| Transformação | A ação muda o estado, com preparação e consequência | Teleportar ou confundir o ator responsável | Mostre o mesmo personagem antes, durante e depois. EC-034 e EC-035 |
| Comparação | Os dois lados compartilham uma base explícita | Objetos sem unidades, invasão lateral e competição | Dê a cada figura o próprio lado. EC-042 |
| Enumeração | Uma ideia ganha força com exemplos cumulativos | Apresentar todos os símbolos antes da voz | Revele pelo gatilho de cada item. EC-026 e EC-040 |
| Pergunta | A fala interpela ou muda o ponto de vista | Trocar pergunta por uma resposta que a fonte não dá | Use espaço e pausa para sustentar a dúvida. EC-028 |
| Objeção | Há uma tensão interna ou contraexemplo | Caricaturar a objeção ou teatralizar sofrimento | Mantenha contrapontos legíveis e igualmente dignos. EC-022 e EC-076 |
| Citação | A atribuição importa para o argumento | Criar retrato ou acrescentar palavras à citação | Use livro, texto breve e fonte atribuída. EC-017 e EC-030 |
| Conceito | Um símbolo conhecido torna a ideia concreta | Inventar uma afirmação ao ilustrar | Mantenha uma metáfora e repita seu significado. EC-017 |
| Número ou data | A fala ancora um evento ou magnitude | Montar escala falsa ou mostrar data antes da fala | Preserve unidade, base e ressalva. EC-040 |
| Causa e efeito | A ordem e o mecanismo podem ser mostrados | Mostrar a reação antes da causa | Ancore o gesto e o resultado a partes distintas da fala. EC-018 e EC-019 |
| Conclusão | Uma imagem sintetiza a tese ou a dúvida final | Introduzir uma tese nova na cauda | Sustente a conclusão com leitura e gesto final. EC-031 e EC-034 |

Em fé, sofrimento, morte e referências a pessoas reais, use encenação contida e figuras genéricas. Se uma representação religiosa ou histórica for necessária, apresente opções de símbolo, texto ou figura para decisão do usuário. Sem uma boa encenação, explique a dificuldade do trecho antes de propor algo fraco. A terceira repetição idêntica exige variar ação, lado ou enquadramento. Em vídeos longos, guarde elenco, escala, paleta e metáforas na bíblia do projeto e aplique a mesma identidade em todo o vídeo.

A biblioteca anatômica tem ações de marcha, sentar, levantar, ajuda, entrega, recepção, apontar, abraçar, ajoelhar, cair, carregar, olhar, esperar, pensar, ler, recolher e recusar. Os verbos recebem marcações e participantes do plano. O suporte de marcha, banco e ajuda usa o rig, a IK e as travas existentes. Os demais verbos são gestos iniciais em avaliação; contato real com objetos e outros atores precisa de comprovação por cena.

Para a prévia vertical de um projeto com narração e direção, use `pictograma.py compor --root PROJETO --direcao DIRECAO.json`. Com áudio pendente a prévia é estimada. As batidas são dados, e os IDs internos ficam nos controles e nas auditorias.

## Campos para encenação

Em uma batida declarativa, `layout` escolhe centro, esquerda, direita, dupla ou percurso. Deixe `titulo` vazio nas batidas sem palavra-chave. `acao.objeto` e o eventual `acao.acessorio` saem do repertório. A relação do objeto com o ator é `segurado`, `olhado`, `entregue`, `carregado` ou `apoiado`. Em uma pausa declarada, `pausa` descreve a função do silêncio.

O banco compara poses consecutivas, cobertura das ações e os pixels da atuação. Variações de câmera e respiração não pontuam como ação. Os MP4s de candidatos reprovados ficam como material de revisão.
