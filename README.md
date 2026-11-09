# JP Roteirização e Slides · candidata 1.8.0

Veja o [changelog](CHANGELOG.md) e o [catálogo de erros do Pictograma](references/erros_conhecidos.md).

Skill `$jp-roteirizacao-e-slides`: artigo autoral → roteiro → áudio fornecido pelo usuário → slides e vídeo sincronizado. Independente de outras skills. Não gera voz nem acessa serviços pagos.

Ao invocar a skill, escolha uma das cinco funções do [menu de entrada](references/apresentacao.md). Pedidos específicos com os materiais necessários entram diretamente na função escolhida. Use `python3 scripts/fluxo.py estado --root PASTA` para consultar projetos locais sem alterar arquivos.

- Artigo: [direção narrativa](references/direcao_narrativa.md) acordada antes da escrita, roteiros limpo/Studio, guia, mapa didático e conferência de fidelidade. `fluxo.py direcao` registra escolhas e origem, e o validador oferece avisos heurísticos.
- Roteiro sem áudio: preservação da fala e planejamento visual; áudio fica pendente.
- Áudio e roteiro: fluxo direto de slides, HTML e vídeo, compatível com projetos 1.0.

Antes da gravação, escolha se o diretor vocal propõe as tags, se o ElevenLabs as sugere no site ou se a gravação será feita sem tags. Consulte [direção vocal](references/direcao_vocal.md) e [comandos de registro](references/roteiros.md). Para habilitar o papel personalizado, instale também `agents/diretor-vocal.toml` em `~/.codex/agents/`.

O perfil Editorial JP usa 16:9, 1920×1080 por padrão. O perfil acrescenta mapa visual integral, comparações e diagramas, marca JP Wealth e movimento pontual ligado à fala. Projetos existentes sem perfil mantêm o legado. Alternativas 21:9 e 9:16 configuráveis. Sem PowerPoint por padrão. Projetos novos incluem música de fundo. Use uma faixa própria ou a seleção editorial da [biblioteca local de Mozart](references/trilhas.md). A biblioteca inclui dez faixas e monta sequências para leituras longas.

Ao planejar ou produzir vídeo, escolha Editorial JP, [Pictograma](references/pictograma.md), [Ilustrado](references/ilustrado.md) ou Legado. Registre por projeto com `fluxo.py estilo`; para preferir um estilo em novos projetos, defina `JP_ESTILO_VIDEO_PADRAO`. Os dois estilos animados usam o mesmo motor determinístico e exportador, com planos e bibliotecas separados.

- Pictograma — biblioteca SVG local, ações ancoradas na fala e storyboard de quadros-chave. O padrão é 9:16, com recomposição em 16:9. A composição coreografada de virada, banco e ajuda usa revisão visual por notas e densidade medida em pixels. A composição com [bíblia visual](references/biblia_visual_pictograma.md) tem folha de modelo, storyboard por batida e auditoria de proporções e luz. A exportação verifica a mixagem de voz e trilha no AAC decodificado.
- Pictograma declarativo — use `pictograma.py auditar|parecer|video --direcao` para vincular revisão, áudio, plano e quadros. O MP4 temporário passa por decodificação e pela matriz de salvaguardas antes da promoção. Consulte a [liberação declarativa](references/pictograma.md#liberação-do-vídeo-declarativo).
- Ilustrado — bíblia visual, storyboard textual, prompts e importação manual de PNGs do ChatGPT, com folha de contato. O padrão é 16:9; a alternativa 9:16 usa enquadramento por cena.

Instale `agents/diretor-de-animacao.toml` e `agents/diretor-de-arte.toml` em `~/.codex/agents/` para usar os diretores separados.

Copie esta pasta para `~/.codex/skills/jp-roteirizacao-e-slides` ou use o instalador de skills com este repositório privado. O identificador é `jp-roteirizacao-e-slides` e a descoberta automática está habilitada em `agents/openai.yaml`.

Leia [SKILL.md](SKILL.md), [comandos de roteirização e retomada](references/roteiros.md), [contrato visual](references/projeto.md) e [relatório de validação](validation/relatorio.md). Scripts não contêm caminhos desta máquina. Requisitos visuais: Python 3, FFmpeg/ffprobe, Node e Playwright/Chromium. Reconhecimento local opcional usa faster-whisper e um modelo disponível no ambiente.

Testes textuais: `python3 -m unittest discover -s scripts -p 'test_*.py'`. Regressão visual: `python3 scripts/testar.py --help`. Não incluir áudios pessoais, caches ASR ou credenciais no repositório.

Para rodar os testes do catálogo em Python 3.9, execute `python3 scripts/testar_suite.py --catalogo --exigir-catalogo`. Configure `JP_NODE`, `PLAYWRIGHT_MODULE` e, quando necessário, `CHROME_PATH` para incluir as mutações no navegador. A fixture é muda e não exige credenciais, áudio ou um projeto externo.

Use `python3 scripts/testar_suite.py --exigir-catalogo` na validação da instalação. O resumo destaca testes de catálogo pulados e essa opção impede aceitar cobertura incompleta.

O candidato de consistência do Pictograma inclui o [inventário de migração](banco_de_provas/inventario.md), os [padrões declarativos](references/padroes_pictograma.md) e o comando para gerar o relatório do banco de provas. Rode `pictograma.py banco-de-provas` para refazer o relatório e validar a barreira. `--preparar --fontes-v7 PASTA --economia MATERIAL` prepara os recortes, `--renderizar` recaptura o necessário e `--render-longo --economia MATERIAL` roda o ensaio de 61 s.
