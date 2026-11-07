# Validação — jp-audio-para-slides 1.1.0

Executada em 6 de novembro de 2026. Identificador preservado; exibição: **JP Roteiros, Slides e Vídeos**. Padrão visual 16:9, 1920×1080 com composição interna larga. A integração não gera voz nem acessa ElevenLabs.

## Implementado

Roteirização e orientação vocal incorporadas com referências próprias, validador e testes locais. Três entradas: artigo, roteiro sem áudio, áudio e roteiro. O helper `fluxo.py` inicializa, registra fala canônica e retoma após receber áudio. Artigo e hash ficam no pacote; o agente produz roteiro, guia, mapa e conferência de fidelidade. As etapas sem áudio não criam timeline medida nem vídeo.

Limpeza compartilhada preserva citações e colchetes literais, admite controles declarados e exceções literais. Comparação considera palavras e fronteiras de parágrafos. Mudanças silenciosas da fala canônica e do áudio são recusadas no fluxo de retomada. Os contratos existentes de slides e marcações permanecem compatíveis. Atualizados metadados, instruções, referências, README e testes.

## Verificações executadas

- **27/27 testes unitários:** 16 cenários transportados e 11 de integração/segurança textual. Incluem perfis vocais, SSML, estimativas sem áudio medido, controles experimentais, citações, igualdade da fala, segmentação, adulteração da fala canônica, ausência/duplicidade de arquivos, arquivo sem faixa de áudio e preservação do material ao retomar.
- **19/19 cenários da regressão visual/técnica:** outro tema (atendimento), três parágrafos, quatro slides; PNG/HTML nos formatos 16:9, 21:9 e 9:16; vídeo H.264 de 180 quadros/6 s; cobertura, continuidade, dimensões, margens e decodificação. Falhas exercitadas: gatilho ausente/ambíguo, hash/duração incompatíveis, revisão pendente, alinhamento insuficiente, áudios ausentes/duplicados e preservação do vídeo anterior em erro.
- **Novos pontos de entrada e retomada:** artigo curto sobre o ciclo da água, roteiro limpo/Studio com dois parágrafos e três cenas; guia, mapa e conferência de fidelidade com fonte explícita. Prévia sem áudio gerada e validada, sem timeline/vídeo. Arquivo de seis segundos medido com ffprobe e anexado à mesma pasta; hashes de fala, parágrafos e plano ficaram iguais. Não se inventaram marcações após a anexação. O teste incluído `testar_entradas.py` repetiu preparação, preview, medição e retomada com áudio sintético.
- **Compatibilidade com o projeto aprovado:** recorte de 1971, seis parágrafos, oito slides, 140,58 s, incluindo capa, figura, definição, cálculo em três etapas, síntese e encerramento. Renderização da 1.1.0 idêntica pixel a pixel aos oito PNGs anteriores. Vídeo existente validado com cobertura integral do recorte, timeline contínua, 1920×1080 e decodificação integral. Não houve modificação do projeto fonte.
- **HTML legado regenerado:** seleção, navegação por teclado, reprodução do áudio, ausência de erros JavaScript e de overflow horizontal passaram.
- **Independência:** os testes usaram os scripts da cópia de desenvolvimento, sem importar a instalação de `jp-tiktok-artigos`. A verificação de importações não encontrou dependência dessa skill. Os hashes da skill original foram conferidos sem alterações.
- **Descoberta e estrutura:** `quick_validate.py` da skill-creator aprovou o pacote. `agents/openai.yaml` conserva invocação implícita habilitada e comando `$jp-audio-para-slides`.

Os JSONs nesta pasta registram regressão técnica e comparação com o recorte legado. Os testes unitários e os dois motores de teste estão incluídos em scripts/ e podem ser executados em uma pasta temporária externa.

## Reprodução dos testes

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/testar_entradas.py --workspace /tmp/jp-entradas-nova-pasta --ffprobe /caminho/ffprobe --node /caminho/node
python3 scripts/testar.py --workspace /tmp/jp-regressao-nova-pasta --ffmpeg /caminho/ffmpeg --ffprobe /caminho/ffprobe --node /caminho/node
```

Os dois últimos comandos requerem Pillow, Node, Playwright/Chromium; `NODE`, `PLAYWRIGHT_MODULE` e `CHROME_PATH` são alternativas para dependências fora do PATH. Usar pastas novas; não reaproveitar a única cópia de um projeto como fixture. O verificador oficial de estrutura usa PyYAML, dependência apenas da ferramenta de verificação.

## Limitações

Os testes com tom/silêncio sintético verificam contratos, arquivos e exportação; não validam reconhecimento acústico ou qualidade vocal. O recorte real reutilizou marcações previamente revisadas: não foi executado novo ASR nem nova audição integral nesta integração. A identidade pixel a pixel cobre oito slides, não todos os 127 do projeto original.

A pequena conferência de fidelidade do exemplo foi manual; o validador textual não audita fatos ou a qualidade pedagógica de artigos arbitrários. Não houve ensaio com alunos, teste de voz clonada ou confirmação de modelo na conta. A documentação oficial de ElevenLabs foi consultada nesta data; recomendações devem ser reconferidas diante de mudanças. Limites de geração não são limites de duração total da aula.

A versão 1.1.0 reúne as instruções e os instrumentos, mas o agente continua responsável por ler o artigo integral, escrever o roteiro e revisar cada produção. Nenhuma publicação de conteúdo ou operação paga é autorizada pela skill.
