# JP Roteirização e Slides · 1.1.0

Skill `$jp-roteirizacao-e-slides`: artigo autoral → roteiro → áudio fornecido pelo usuário → slides e vídeo sincronizado. Independente de outras skills. Não gera voz nem acessa serviços pagos.

- Artigo: roteiros limpo/Studio, guia, mapa didático e conferência de fidelidade.
- Roteiro sem áudio: preservação da fala e planejamento visual; áudio fica pendente.
- Áudio e roteiro: fluxo direto de slides, HTML e vídeo, compatível com projetos 1.0.

Padrão: 16:9, 1920×1080, composição larga centralizada em fundo `#FAFAF7`. Alternativas 21:9 e 9:16 configuráveis. Sem PowerPoint por padrão.

Copie esta pasta para `~/.codex/skills/jp-roteirizacao-e-slides` ou use o instalador de skills com este repositório privado. O identificador é `jp-roteirizacao-e-slides` e a descoberta automática está habilitada em `agents/openai.yaml`.

Leia [SKILL.md](SKILL.md), [comandos de roteirização e retomada](references/roteiros.md), [contrato visual](references/projeto.md) e [relatório de validação](validation/relatorio.md). Scripts não contêm caminhos desta máquina. Requisitos visuais: Python 3, FFmpeg/ffprobe, Node e Playwright/Chromium. Reconhecimento local opcional usa faster-whisper e um modelo disponível no ambiente.

Testes textuais: `python3 -m unittest discover -s scripts -p 'test_*.py'`. Regressão visual: `python3 scripts/testar.py --help`. Não incluir áudios pessoais, caches ASR ou credenciais no repositório.
