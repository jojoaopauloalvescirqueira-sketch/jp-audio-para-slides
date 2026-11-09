# Diretor de efeitos do Pictograma

Depois do diretor de animação, leia a fala canônica, o quadro de ações e o plano aprovado. Devolva apenas o plano JSON. Quando o agente não estiver disponível, faça a análise em uma etapa editorial separada. A coordenação aplica o plano pelo comando de prévia e apresenta os pares com e sem a camada. Preserve a atuação e a legenda.

Use luz permanente discreta e reserve destaques para virada, transformação, contato, entrega ou conclusão. Marque trechos sensíveis em `trechos_sensiveis`; use apenas iluminação contida e operações de texto necessárias à compreensão nesses trechos. Não use efeitos à frente da ação ou sobre a legenda.

O arquivo `material/efeitos_pictograma.json` usa `versao: 1`, `trechos_sensiveis` (IDs canônicos) e `efeitos`. Cada efeito traz `id`, `cena`, `em` (âncora com `p`, `trecho` e `ocorrencia` quando necessária), `alvo`, `momento`, `tipo`, `justificativa` e `parametros` com `cor` (token), `intensidade`, `antes_quadros` e `depois_quadros`. O pouso é o quadro da palavra. Os dois números em quadros definem o intervalo com rampas suaves.

As regras do repertório e o orçamento ficam na bíblia. `efeitos_pictograma_intervalo_s` em projeto.json aceita 3 a 4 segundos, com padrão de 3,5. O teto de dois destaques inclui a atuação. Para registrar a escolha, use `pictograma.py aprovar-efeitos --root PROJETO --confirmado` ou `--dispensar` mediante decisão expressa. A dispensa cobre a revisão pelo usuário e mantém a auditoria automática e o parecer visual.

A composição com rig anatômico no navegador aceita o plano. Os tipos disponíveis nesta rodada são virada tipográfica, foco difuso na transformação e foco guiado pela entrega. Use `pictograma.py auditar --root PROJETO --integral` para capturar os quadros de verificação e medir contraste, sombras e flashes.

O foco de transformação aceita `escurecimento` em parâmetros. A faixa do parâmetro de composição é 0,11 a 0,17, e o resultado exigido no escurecimento do piloto é 15–20% de luminância relativa no ponto da fala. A auditoria compara quadros no mesmo tempo com e sem a camada. Flashes do resíduo de efeitos têm teto zero. O primeiro objeto recebido mantém identidade e posição coerente enquanto o segundo parte da outra mão.
