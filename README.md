# JP Roteirização e Slides · 1.6.0

Skill `$jp-roteirizacao-e-slides`: artigo autoral → roteiro → áudio fornecido pelo usuário → slides e vídeo sincronizado. Independente de outras skills. Não gera voz nem acessa serviços pagos.

Ao invocar a skill, escolha uma das cinco funções do [menu de entrada](references/apresentacao.md). Pedidos específicos com os materiais necessários entram diretamente na função escolhida. Use `python3 scripts/fluxo.py estado --root PASTA` para consultar projetos locais sem alterar arquivos.

- Artigo: [direção narrativa](references/direcao_narrativa.md) acordada antes da escrita, roteiros limpo/Studio, guia, mapa didático e conferência de fidelidade. `fluxo.py direcao` registra escolhas e origem, e o validador oferece avisos heurísticos.
- Roteiro sem áudio: preservação da fala e planejamento visual; áudio fica pendente.
- Áudio e roteiro: fluxo direto de slides, HTML e vídeo, compatível com projetos 1.0.

Antes da gravação, escolha se o diretor vocal propõe as tags, se o ElevenLabs as sugere no site ou se a gravação será feita sem tags. Consulte [direção vocal](references/direcao_vocal.md) e [comandos de registro](references/roteiros.md). Para habilitar o papel personalizado, instale também `agents/diretor-vocal.toml` em `~/.codex/agents/`.

Padrão 16:9, 1920×1080 e perfil Editorial JP para projetos novos. O perfil acrescenta mapa visual integral, comparações e diagramas, marca JP Wealth e movimento pontual ligado à fala. Projetos existentes sem perfil mantêm o legado. Alternativas 21:9 e 9:16 configuráveis. Sem PowerPoint por padrão. Projetos novos incluem música de fundo. Use uma faixa própria ou a seleção editorial da [biblioteca local de Mozart](references/trilhas.md). A biblioteca inclui dez faixas e monta sequências para leituras longas.

A produção de vídeo permite escolher Editorial JP, [Pictograma](references/pictograma.md) ou Legado. O Pictograma usa animação vetorial ancorada nas palavras da fala, com 9:16 nativo e recomposição 16:9. Para habilitar o papel personalizado, instale `agents/diretor-de-animacao.toml` em `~/.codex/agents/`.

Copie esta pasta para `~/.codex/skills/jp-roteirizacao-e-slides` ou use o instalador de skills com este repositório privado. O identificador é `jp-roteirizacao-e-slides` e a descoberta automática está habilitada em `agents/openai.yaml`.

Leia [SKILL.md](SKILL.md), [comandos de roteirização e retomada](references/roteiros.md), [contrato visual](references/projeto.md) e [relatório de validação](validation/relatorio.md). Scripts não contêm caminhos desta máquina. Requisitos visuais: Python 3, FFmpeg/ffprobe, Node e Playwright/Chromium. Reconhecimento local opcional usa faster-whisper e um modelo disponível no ambiente.

Testes textuais: `python3 -m unittest discover -s scripts -p 'test_*.py'`. Regressão visual: `python3 scripts/testar.py --help`. Não incluir áudios pessoais, caches ASR ou credenciais no repositório.
