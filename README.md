# JP Áudio para Slides

Skill para transformar **áudio de narração e roteiro já concluídos** em slides didáticos, apresentação HTML navegável e vídeo sincronizado. Ela começa depois da roteirização e da geração de voz.

O padrão visual foi validado no projeto de vídeo “1971: Fim do Padrão Ouro, a História não contada”: fundo claro, tipografia sóbria, composição central, gráficos originais e contas reveladas durante a fala.

## Resultado padrão

- Vídeo em **16:9, 1920×1080, 30 fps**, preservando a composição larga em 21:9 com preenchimento claro.
- Slides PNG e apresentação HTML com roteiro e pontos de entrada do áudio.
- Manifest com estimativas, timeline com tempos medidos, fontes e materiais reproduzíveis.
- Formatos alternativos 21:9 e 9:16, quando solicitados.

Não gera voz, não reescreve a narração e não publica conteúdo automaticamente. Artigo/PDF, referências, capa e plano de aula são complementos opcionais; áudio e roteiro são necessários.

## Instalar no Codex

Copie ou clone este repositório para uma pasta chamada `jp-audio-para-slides` dentro de `~/.codex/skills/`:

```sh
git clone https://github.com/jojoaopauloalvescirqueira-sketch/jp-audio-para-slides.git ~/.codex/skills/jp-audio-para-slides
```

Se essa pasta já existir, preserve a instalação atual antes de substituí-la. A descoberta automática está habilitada em `agents/openai.yaml`.

Para usar, forneça os arquivos e peça:

> Use $jp-audio-para-slides com este áudio e este roteiro.

O agente usa as instruções de [SKILL.md](SKILL.md) e cria o projeto em uma pasta separada da instalação.

## Dependências

Python 3.10+, Pillow, Node.js, Playwright/Chromium e FFmpeg/ffprobe. O reconhecimento local opcional usa faster-whisper/PyAV. Preferir runtimes já disponíveis no ambiente. As bibliotecas, executáveis e modelos não estão incluídos neste repositório.

- [Contrato do projeto e comandos](references/projeto.md)
- [Direção visual](references/visual.md)
- [Sincronização e revisão](references/sincronizacao.md)
- [Entregas e conferência](references/entregas.md)

## Validação

A versão 1.0.0 foi exercitada com um recorte real de seis parágrafos e oito slides, outro tema com três parágrafos e quatro slides, 19 cenários técnicos e uma pasta com WAV, MP3 e AAC em taxas diferentes. A saída real passou por decodificação integral e comparação dos slides com os PNGs; o áudio AAC foi conferido por hash.

O reconhecimento real foi testado no recorte, sem repetir a renderização integral do vídeo longo. Os testes sintéticos verificam contratos e montagem, sem comprovar reconhecimento acústico. Consulte [o relatório e seus limites](validation/relatorio.md).

## Organização

`SKILL.md` contém o fluxo; `scripts/`, os utilitários; `references/`, os contratos e critérios; `assets/`, apenas a referência visual aprovada. Não há áudios, PDFs, projetos completos, credenciais ou caches neste repositório.

A amostra visual tem função de referência de estilo. Ela não fornece dados para novas apresentações nem transfere direitos sobre gráficos de terceiros. A publicação deste repositório não implica uma licença de redistribuição desses materiais.
