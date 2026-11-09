# Sincronização verificável

A narração vem exclusivamente de arquivo fornecido pelo usuário. Sem ele, o Pictograma oferece storyboard e prévia identificada como estimada. O MP4 exige a narração e seus tempos medidos. Cliques e tons são exclusivos dos testes técnicos.

## Áudio único

```sh
python3 "$SKILL/scripts/transcrever.py" --root "$PROJETO" --model base
python3 "$SKILL/scripts/alinha_audio.py" --root "$PROJETO"
```

O primeiro script mede a duração, reconhece localmente e grava segmentos/palavras com timestamps e identidade SHA-256 dos arquivos. Também aceita pasta de áudios numerados e acumula os tempos medidos. O alinhador associa os tokens do roteiro às palavras reconhecidas monotonicamente. Diferenças de escrita de números reduzem a correspondência textual sem necessariamente representar erro acústico; não trocar os números autorais pela saída ASR.

A saída material/marcacoes_audio.json contém `audio_identidade`, `duracao_s`, `plano_sha256`, `roteiro_sha256`, `slides` e `revisao`. As marcações de slide têm id, texto de entrada, início/fim, método, contexto reconhecido e motivos de revisão. O sincronizador deriva o fim pela próxima entrada; o último cobre a duração medida.

Entradas interpoladas, variações lexicais e baixa correspondência local exigem conferência. Trechos extensos de texto sem correspondência também são registrados e geram pendência GLOBAL; podem indicar diferença entre áudio e roteiro, e não devem ser completados silenciosamente. Poucas âncoras ou ausência de fala reconhecida não autorizam distribuir o tempo total pelo texto. Reconhecer o trecho novamente, ouvir o entorno, usar alinhador mais adequado ou pedir marcações ao usuário quando necessário. Não afirmar precisão por palavra apenas porque há timestamps.

Após verificar um ponto sinalizado, corrigir o início se preciso e acrescentar em `revisao.conferidos`:

```json
{"slide_id":"S003","inicio_s":12.34,"motivo":"Entrada conferida no áudio e no contexto do trecho; justificativa específica."}
```

O início confirmado deve ser igual ao início atual daquele slide. Para pendência GLOBAL, registrar a verificação da correspondência entre áudio e roteiro com slide_id GLOBAL e inicio_s null, só após resolver a causa global. Confirmações não substituem corrigir timestamps inválidos. Não fabricar registros de audição ou preencher motivos genéricos em lote.

## Marcações externas e áudios por parágrafo

Marcações externas devem registrar a identidade dos áudios e a duração medida, além de slides com id, frase-gatilho e início, ou parágrafos P001…PNNN com início/fim contínuos. Validar sua procedência e correspondência antes de associar a identidade dos arquivos; um hash recém-calculado sozinho não comprova que os tempos são corretos.

Sem marcações, uma pasta completa de áudios por parágrafo permite medir cada duração e estimar trocas internas pela posição das palavras. O método é registrado como estimado. Preferir reconhecimento/alinhamento real quando a fala tiver pausas ou contas cuja posição interna precise ser mais precisa.

No perfil Editorial JP, entradas internas exigem marcações por cena com hash do plano, do roteiro e identidade do áudio. Entradas indicadas com `conferir_audio` exigem registro específico em `revisao.conferidos`. A timeline informa a contagem de quadros intermediários por estado.

Áudio ausente, duplicado, marcação incompleta, gatilho ambíguo, intervalos fora da duração e áudio diferente são erros bloqueantes. Não usar a estimativa de 140 palavras/minuto como tempo final.

## Exportar

```sh
python3 "$SKILL/scripts/sincronizar.py" --root "$PROJETO" --renderizar
python3 "$SKILL/scripts/gerar_slides.py" --root "$PROJETO" --html-only
```

O primeiro comando escreve timeline contínua, concatenação e vídeo; o segundo atualiza os botões de áudio da prévia com as entradas reais. Os parâmetros --ffmpeg e --ffprobe aceitam executáveis fora do PATH. Sem --renderizar, gravar somente a timeline.

Sem trilha, AAC compatível pode ser copiado e outros codecs são convertidos para AAC por compatibilidade com MP4. Com trilha, a exportação codifica a mixagem em AAC. Declarar esse resultado em vez de prometer ausência de recompressão. Para áudios individuais, o sincronizador pode criar uma faixa unificada para a prévia; isso não cria voz nova. Conferir o áudio final por comparação de sinal quando houver conversão de codec, além de início/fim e duração.

Usar arquivo temporário exclusivo e substituição atômica. Verificar resolução, 30 fps, número de quadros, duração e decodificação integral antes de concluir. Não inferir integridade apenas dos metadados.


## Vídeos animados

Em [Pictograma](pictograma.md) e [Ilustrado](ilustrado.md), o plano identifica as entradas das cenas e ações por trechos literais. `fluxo.py cenas` deriva as entradas de alinhamento em `material/slides.json`. Forneça áudio e uma transcrição com tempos por palavra e hash compatível (`transcrever.py --local-only` ou transcrição verificada).

`sincronizar.py --root PROJETO --renderizar` mede os intervalos, captura o palco quadro a quadro e usa a mesma exportação com trilha e verificação de integridade. Confira o relatório `material/marcacoes_acoes.json` e associe a revisão ao áudio, roteiro e transcrição atuais antes de exportar. Sem áudio, gere uma prévia estimada com `fluxo.py cenas --estimar`. No Ilustrado, aprove também os PNGs na folha de contato.

## Trilha e mixagem

A escolha do usuário vale por vídeo ou como padrão reutilizável. A ordem é `--trilha`, faixa registrada no projeto, arquivo local indicado por `JP_TRILHA_PADRAO` e [biblioteca da skill](trilhas.md). Use `--atmosfera` e `--motivo-trilha` para a seleção editorial da biblioteca. Exportação direta de projeto novo sem classificação usa a reserva reflexiva. Projetos antigos podem optar pela biblioteca com `--atmosfera`.

```sh
python3 "$SKILL/scripts/sincronizar.py" --root "$PROJETO" --renderizar --trilha /caminho/faixa.mp3
```

O nível inicial da música é de 20 a 24 dB abaixo do nível médio medido da voz conforme o catálogo, com ganho limitado e limitador de pico. Ajuste o nível relativo com `--nivel-trilha-db -25` para uma trilha mais discreta. A biblioteca prioriza uma faixa compatível com a duração. Para leituras mais longas, encadeia peças do mesmo perfil com sobreposição gradual de 1,5 s, inclusive na fronteira do ciclo quando ele é repetido. A música acompanha o fim do vídeo e recebe entrada e saída suaves. Uma faixa avulsa indicada pelo usuário pode ser repetida conforme a duração.

O MP4 carrega a mixagem. A transcrição, o alinhamento e a escuta de entrada da prévia HTML usam a narração. O projeto conserva a faixa usada em `material/trilhas/` com sua identidade SHA-256 e registra a escolha para novas exportações. O relatório de sincronização indica a faixa ou sequência, origens, nível, ganho, repetição e fades. Em uma sequência, as fontes locais são registradas em ordem e o ciclo derivado é temporário. A duração e os quadros do vídeo continuam definidos pela narração.

## Localizar um trecho no Pictograma

Com a narração completa e o roteiro canônico no projeto, use `fluxo.py sincronia --root PROJETO --trecho P007-P008`. As opções `--de` e `--ate` selecionam trechos literais quando a entrada ou a saída está dentro do parágrafo. A saída inclui `material/marcacoes_frases.json`, SRT relativo ao recorte e `material/trecho_narracao.wav` para uma gravação de origem em arquivo único. A narração completa permanece como entrada do projeto.

Importe marcações com `--fonte` e declare `--origem elevenlabs` quando vierem do serviço. SRT e VTT comuns ficam identificados como fornecidos pelo usuário. Sem uma fonte externa, o Pictograma usa reconhecimento disponível localmente ou analisa pausas do áudio. O localizador usa janelas de 10 ms, silêncios a partir de 120 ms e ritmo estimado por sílabas. As fronteiras internas de palavras recebem a classificação da evidência acústica. Quando o encaixe do trecho for ambíguo, confira as divergências e forneça marcações, um recorte manual ou autorização para Whisper.

Execute `fluxo.py sincronia --root PROJETO` para localizar a fala do projeto inteiro e registrar o efeito das tags quando houver roteiro Studio. Com `--trecho`, o JSON e o guia registram os efeitos no intervalo escolhido, usando as frases comparáveis do restante da gravação como referência. Para revisar só um trecho estimado, use a prévia estimada do Pictograma.
