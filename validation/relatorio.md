# Validação da candidata 1.2.0

O perfil Editorial JP passou pelo recorte de 1971 de 140,58 s. A montagem passou de 8 para 28 estados, com 35 trechos literais no mapa visual. O maior intervalo sem troca passou de 36,14 s para 11,52 s. Dois estados abaixo de dois segundos foram justificados no relatório de ritmo.

Os MP4 anterior e novo têm 4.217 quadros, 1920×1080 e 30 fps. Os pacotes AAC correspondem entre ambos e à narração de origem. A nova montagem decodificou integralmente. Foram gerados 77 quadros intermediários para 11 efeitos. As amostras decodificadas conferiram com o PNG anterior, o início, o meio e o estado estável do efeito nas trocas do detalhe do gráfico, do realce dos eixos e dos três números.

- +4% entra em 78,54 s.
- +6% entra em 81,24 s.
- O resultado aproximado −1,89% entra em 89,66 s, depois de a fórmula ficar visível.

A conferência da fala usou uma transcrição local integral e uma segunda passagem por recortes da narração, incluindo a ressalva em que a primeira passagem perdeu o prefixo de “independe”. Treze entradas têm evidência específica em `revisao.conferidos`. A segunda passagem usou o mesmo modelo base com parâmetros e recortes diferentes. A precisão perceptiva e o conforto do ritmo ainda devem ser avaliados por audição humana na prévia antes de adotar a candidata.

Passaram a renderização e a geometria dos 28 estados e 77 intermediários em 16:9, 21:9 e 9:16, com verificações da marca, margem, texto e separação das vistas. O MP4 de aceite é 16:9. A prévia HTML foi verificada com navegação e áudio. No recorte legado, os oito PNGs renderizados com a candidata permaneceram idênticos pixel a pixel.

Passaram 27 testes unitários, 19 cenários de regressão, entrada por artigo sem áudio e retomada. Foram exercitados os bloqueios de identidade de áudio incompatível, marcações somente por parágrafo para trocas internas, revisão crítica ausente, plano alterado, quadro intermediário ausente e mapa incompleto. O teste com intervalo inferior a oito quadros usou corte.

O JSON `aceite-editorial-jp.json` contém as medidas do recorte, amostras dos efeitos e casos de falha. Os JSONs de validação anteriores a 1.2.0 permanecem como evidência histórica.

## Candidata 1.2.1 com trilha

A escolha por vídeo, a faixa padrão local e a reutilização da escolha salva foram testadas em exportações reais com tons sintéticos. Mediram-se −20,00 dB e −25,02 dB em relação à voz sintética para os ajustes de −20 e −25 dB. Passaram os fades, a repetição, a preservação do MP4 anterior quando falta uma faixa válida e a contagem de 180 quadros em seis segundos. Os resultados detalhados estão em `mixagem.json`. Os tons são recursos de teste. A faixa definitiva será a escolhida pelo usuário.

A exportação com uma faixa sintética no recorte de 1971 manteve 140,58 s, 4.217 quadros e os 77 intermediários. A mixagem passou pela decodificação integral. O recorte de comparação da versão 1.2.0 continua disponível para referência visual.

## Candidata 1.2.2 com biblioteca local

As quatro faixas de Mozart foram conferidas por formato, duração e hash. A procedência e a indicação de domínio público estão vinculadas a cada arquivo no catálogo.

Passaram as quatro exportações com seleção por atmosfera, a reserva reflexiva, a precedência da faixa registrada e do padrão pessoal, a troca manual e a reprodução de projeto antigo sem trilha. O recorte de 1971 selecionou o Andante com justificativa editorial e manteve 140,58 s e 4.217 quadros. A exportação passou pela decodificação integral. A adequação emocional continua sendo uma decisão editorial. As verificações automáticas confirmam a escolha do arquivo e a mixagem.

## Candidata 1.2.3 para leituras longas

A biblioteca passou de quatro para dez faixas, com 43min10s de material distinto. Os dez áudios conferiram por hash e decodificação integral.

Um ensaio de mixagem com voz sintética cobriu 57min27s, com cinco faixas no perfil reflexivo. A sequência teve 1.413,682 s por ciclo e entrou em seu terceiro ciclo. A mixagem AAC manteve 3.447,000 s e decodificou integralmente. Amostras antes e depois das repetições indicaram presença de música abaixo do tom sintético. O arquivo `leitura-longa.json` contém as medidas e os créditos usados.

Também passaram a exportação MP4 curta com sequência e crossfade, a troca explícita por uma faixa, a reserva reflexiva e a exportação de um projeto legado. A verificação da leitura longa foi de áudio, com avaliação perceptiva das transições reservada à prévia de cada produção.
