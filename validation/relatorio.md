# Validação — jp-audio-para-slides 1.0.0

Skill criada e instalada localmente. Pacote com 19 arquivos, conferido por SHA-256 contra a instalação e verificado por integridade ZIP. Nenhuma outra skill foi modificada e não houve publicação no GitHub.

## Testes executados

- Validador oficial de estrutura: aprovado na cópia de entrega e na instalação.
- Recorte real do projeto aprovado: 6 parágrafos, 8 slides, 140.58 segundos; capa, figura, definição, conta em etapas, síntese e encerramento.
- Reconhecimento local faster-whisper base: cobertura textual 91.1%. Esse valor não representa precisão acústica.
- Entradas comparadas às marcações correspondentes do vídeo aprovado: diferença máxima 0.18 segundo.
- Dois pontos sinalizados foram conferidos pelo contexto reconhecido e pelas marcações de referência do recorte; não foi registrada audição humana inexistente.
- MP4 real: 1920×1080, 30 fps, metadados e decodificação integral aprovados; oito amostras comparadas aos PNGs, erro médio máximo 1,74 em escala de pixels 0–255. Áudio AAC copiado e conferido por hash de pacotes, sem recompressão.
- Prévia HTML: navegação, teclado, áudio e largura testados no Chrome.
- Outro tema, “Atendimento ao cliente”: 3 parágrafos e 4 slides, sem figuras; 19 cenários técnicos aprovados, incluindo os três formatos e falhas de entradas.
- Pasta heterogênea: WAV, MP3 e AAC com taxas diferentes; normalização de cópias, unificação para a prévia, MP4 e decodificação aprovados.
- Lacuna extensa do roteiro: sinalizada para revisão mesmo com cobertura global acima de 65%.
- Execução a partir da pasta instalada, com --root apontando para outro projeto: aprovada.

## Limites dos testes

O segundo tema e a pasta heterogênea usam áudio sintético para verificar contratos e montagem; não comprovam reconhecimento acústico de fala. O reconhecimento real foi exercitado no recorte de 140,58 segundos, sem repetir a renderização integral do projeto longo. Não houve audição humana integral. A fonte visual real foi reutilizada do material já aprovado, sem simular uma nova busca externa.

A instalação foi verificada neste ambiente. Outros computadores precisam de Python, Pillow, Node/Playwright, FFmpeg e, quando necessário, dependências/modelo ASR. Os caminhos locais de testes e os executáveis não foram embutidos na skill.

## Cenários técnicos

- Aprovado: Preparar tema diferente com três parágrafos.
- Aprovado: Áudio único sem marcações é bloqueado.
- Aprovado: Gatilho ausente é rejeitado.
- Aprovado: Gatilho ambíguo é rejeitado.
- Aprovado: Alinhar fixture textual de outro tema.
- Aprovado: Áudio incompatível por hash é rejeitado.
- Aprovado: Duração incompatível é rejeitada.
- Aprovado: Revisão pendente bloqueia exportação.
- Aprovado: Alinhamento sem correspondência é rejeitado.
- Aprovado: Áudio intermediário ausente identificado.
- Aprovado: Duplicidade de áudios identificada.
- Aprovado: Erro preserva a saída anterior.
- Aprovado: Renderizar padrão 16:9 sem fontes fixas.
- Aprovado: Exportar MP4 sintético para verificar o motor.
- Aprovado: Validar vídeo e cobertura.
- Aprovado: Renderizar formato 21:9.
- Aprovado: Validar formato 21:9.
- Aprovado: Renderizar formato 9:16.
- Aprovado: Validar formato 9:16.
