# Biblioteca de Mozart

Dez faixas somam 43min10s de música. O catálogo em `assets/trilhas/catalogo.json` guarda arquivos locais, compositor, crédito, indicação de domínio público, duração e hashes. Inclui interpretações gravadas e versões de piano produzidas a partir de MIDI.

| Atmosfera | Seleção para vídeos curtos | Ciclo para leituras longas |
|---|---|---:|
| `reflexiva` | K. 545 · II. Andante | 23min34s |
| `acolhedora` | K. 331 · tema do Andante grazioso | 22min35s |
| `didatica` | K. 545 · I. Allegro | 23min36s |
| `dinamica` | K. 545 · III. Rondo | 19min21s |

Leia a fala e considere ritmo, ênfases e pausas. Use `reflexiva` para história, análise e trechos densos, `acolhedora` para conversas e introduções serenas, `didatica` para demonstrações com etapas e `dinamica` para uma narração ágil. Se o tom variar muito, dê prioridade à parte em que a música mais precisa ceder espaço à voz.

A duração medida escolhe a primeira faixa do perfil que cubra o vídeo. Se nenhuma cobrir, o script reúne quantas forem necessárias na ordem editorial. Cada faixa tem volume ajustado à narração e se sobrepõe à próxima por 1,5 segundo. Quando todas as faixas do perfil já tocaram e a leitura continua, o ciclo recomeça com a mesma transição. A última passagem termina junto à narração com saída gradual.

```sh
python3 "$SKILL/scripts/sincronizar.py" --root "$PROJETO" --renderizar \
  --atmosfera reflexiva --motivo-trilha "Leitura histórica longa com dados e ressalvas."
```

A indicação `--trilha` prevalece. A faixa ou sequência registrada no projeto e o padrão pessoal `JP_TRILHA_PADRAO` têm prioridade sobre uma nova avaliação editorial. Para projetos novos exportados diretamente, a atmosfera de reserva é reflexiva.

O catálogo documenta as fontes, e o relatório de cada vídeo inclui os créditos das faixas usadas. Preserve os créditos ao compartilhar a produção, em particular Brendan Kinsella e Musopen nas faixas K. 333, Vadim Chaimovich e Musopen na K. 330 e Musopen Symphony na K. 550. Escute a passagem mais densa e as emendas para decidir se o nível precisa de ajuste.
