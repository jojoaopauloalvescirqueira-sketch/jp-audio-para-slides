# Sincronização verificável

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

Áudio ausente, duplicado, marcação incompleta, gatilho ambíguo, intervalos fora da duração e áudio diferente são erros bloqueantes. Não usar a estimativa de 140 palavras/minuto como tempo final.

## Exportar

```sh
python3 "$SKILL/scripts/sincronizar.py" --root "$PROJETO" --renderizar
python3 "$SKILL/scripts/gerar_slides.py" --root "$PROJETO" --html-only
```

O primeiro comando escreve timeline contínua, concatenação e vídeo; o segundo atualiza os botões de áudio da prévia com as entradas reais. Os parâmetros --ffmpeg e --ffprobe aceitam executáveis fora do PATH. Sem --renderizar, gravar somente a timeline.

AAC compatível é copiado; outros codecs são convertidos para AAC por compatibilidade com MP4. Declarar esse resultado em vez de prometer ausência de recompressão. Para áudios individuais, o sincronizador pode criar uma faixa unificada para a prévia; isso não cria voz nova. Conferir o áudio final por comparação de sinal quando houver conversão de codec, além de início/fim e duração.

Usar arquivo temporário exclusivo e substituição atômica. Verificar resolução, 30 fps, número de quadros, duração e decodificação integral antes de concluir. Não inferir integridade apenas dos metadados.
