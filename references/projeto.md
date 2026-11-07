# Contrato do projeto e comandos

Requer Python 3.10+, Pillow, Node, Playwright/Chromium e FFmpeg/ffprobe. O reconhecimento opcional usa faster-whisper/PyAV, localmente. Usar o ambiente disponível; `NODE`, `PLAYWRIGHT_MODULE` e `CHROME_PATH` permitem indicar runtimes fora do PATH. Downloads de modelos não enviam o áudio, mas exigem acesso à rede; `--local-only` usa só o cache existente.

Nos comandos abaixo, `SKILL` é o caminho real da instalação e `PROJETO` é uma pasta de trabalho separada. Não executar esses nomes literalmente sem substituí-los.

```sh
python3 "$SKILL/scripts/preparar.py" --root "$PROJETO" --audio /caminho/narracao.mp3 --roteiro /caminho/roteiro.txt --titulo "Título exato" --autor "Autor"
```

O preparador mede as entradas com ffprobe, copia o material, produz roteiro limpo e IDs P001…PNNN, mas deixa slides.json vazio para a decisão editorial do agente. Não entrega esse estado vazio ao usuário.

Para um ambiente separado, instalar `requirements.txt`; para ASR, também `requirements-asr.txt`. Instalar o pacote Node do projeto com o package.json incluído e o navegador Playwright. Preferir dependências já disponíveis. O renderizador procura Playwright junto ao script, no projeto e em PLAYWRIGHT_MODULE, nessa ordem. Não incluir node_modules ou modelos no ZIP final.

## Arquivos

`projeto.json`: `titulo`, `subtitulo`, `autor`, `marca`, `cta_rotulo`, `cta_url`, `capa` (caminho relativo opcional), `audio` (arquivo ou pasta relativa), `formato` (16:9 padrão), `idioma` (pt padrão), `fps` (30). Campos de autoria, capa e CTA vazios são válidos; não os preencher com dados de outro projeto. `audio_previa` é usado quando o sincronizador unifica uma pasta de áudios.

`material/paragrafos.json`: lista de objetos `{"id":"P001","texto":"fala integral"}`. Preservar a segmentação do roteiro original. Se a fala estiver em MD ou contiver metadados, separar editorialmente fala e instruções antes de numerar; não presumir que todo título ou tabela de produção é falado.

`material/slides.json`: lista em ordem, com IDs únicos e as chaves:

```json
{
  "id": "S001", "p": 1, "tipo": "capa",
  "frase_gatilho": "Primeiras palavras exatas da fala",
  "title": "Título exato", "body": "Subtítulo",
  "lines": [], "figura": null, "bloco": "B01", "nota": "", "fonte": ""
}
```

Tipos: capa, figura, ideia, conta, definicao, sintese, final. `p` é base 1; `end` é opcional e deve corresponder ao intervalo real até o próximo slide. `frase_gatilho` deve existir literalmente; se se repetir, informar `ocorrencia` base 1. O início de cada slide é definido pelo parágrafo e gatilho, não pela contagem de slides. O intervalo final é exclusivo. O primeiro slide precisa cobrir o início da fala.

`material/fontes_figuras.json`: lista opcionalmente vazia. Cada figura tem `id` (número ou texto), `arquivo` (relativo à pasta do projeto), `credito`, e pode registrar `url_original`, `referencias`, `pagina_imagem`, `pagina_legenda`, `ressalvas`. O campo figura do slide referencia esse id. As fontes visuais devem ter origem rastreável; cálculos do autor devem ser identificados como tais.

Para vistas densas, adicionar `vistas: {"21:9": [[x0,y0,x1,y1], ...]}` com coordenadas de 0 a 1 e caixas válidas. A vista larga também serve ao padrão 16:9. Para vertical, usar a chave 9:16 ou preparar mais slides com gatilhos próprios. O arquivo integral permanece no material.

## Geração

```sh
python3 "$SKILL/scripts/gerar_slides.py" --root "$PROJETO"
python3 "$SKILL/scripts/gerar_slides.py" --root "$PROJETO" --formato 21:9
python3 "$SKILL/scripts/gerar_slides.py" --root "$PROJETO" --formato 9:16
```

Usar `--html-only` para atualizar a prévia depois do alinhamento sem recriar PNGs. Formato padrão grava em slides/; alternativas em slides-21x9/ e slides-9x16/. O renderizador interrompe a geração quando encontra problemas geométricos e registra o diagnóstico para correção.

Reconstruir o plano de aula e mapa de parágrafos em material/ quando não forem fornecidos. Seus nomes e quantidade de blocos são livres; os IDs em slides.json devem manter rastreabilidade.
