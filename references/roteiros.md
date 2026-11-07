# Roteirização, registro e retomada

## Pacote editorial

Criar no mesmo projeto `material/roteiro_limpo.txt`, `roteiro_studio.txt`, `guia_producao.md`, `mapa_didatico.md` e `fidelidade.md`. Conservar o artigo original e seu hash. Produzir os arquivos editoriais pelo trabalho de leitura e escrita do agente; `fluxo.py` organiza e verifica insumos, não resume nem comprova fidelidade sozinho.

A versão limpa contém apenas a fala, com uma linha em branco entre parágrafos. Studio conserva exatamente as mesmas palavras e fronteiras de parágrafo, adicionando somente controles identificados. IDs P001…PNNN ficam em `paragrafos.json`, guia e mapa; não são narrados. Conteúdo literal como `[1]`, `[nota do autor]` ou citações deve permanecer nas duas versões. Declare `--literal-tag thoughtful` se o texto usar literalmente uma palavra também reconhecida como controle.

No percurso por artigo, registrar a [direção narrativa](direcao_narrativa.md) antes de produzir a fala. Preservar a seção **Direção narrativa** no guia. Completar o guia com objetivos de compreensão, voz e modelo recomendados, intenção e ritmo por parágrafo, pronúncias a testar, pausas relativas, números e unidades críticos, instruções para geração externa e estado **áudio pendente**. Pausas qualitativas têm duração a conferir na gravação.

O mapa relaciona cada P a bloco didático, passagem/seção do artigo, conceito, função, exemplo, figura e frase-gatilho exata do slide. Identificar blocos reconstruídos quando não houver plano fornecido. Criar o plano visual `slides.json` conforme o contrato existente. Não substituir créditos ou fontes por tags vocais.

A conferência de fidelidade relaciona afirmações, qualificações, objeções, omissões justificadas e adaptações orais ao artigo. Separar exemplos hipotéticos de evidências. Revisar integralmente a versão limpa: precisão, autonomia da aula, números, unidades e limites. Ausência de artigo impede afirmar que essa conferência foi concluída.

## Comandos

Execute a partir da pasta da skill; `PROJETO` é uma pasta externa de produção. Caminhos abaixo são exemplos relativos, substituíveis.

```sh
python3 scripts/fluxo.py iniciar --root PROJETO --titulo 'Título confirmado' --artigo artigo.pdf
# Registre as escolhas acordadas antes de escrever a fala. Repita --assumir por campo delegado.
python3 scripts/fluxo.py direcao --root PROJETO --perspectiva externa --estilo professor-didatico --registro intermediario --formato 16:9 --assumir formato
# Produza os cinco materiais editoriais; depois registre as duas versões:
python3 scripts/fluxo.py registrar_roteiro --root PROJETO --limpo limpo.txt --studio studio.txt --model eleven_v4
python3 scripts/validar_roteiro.py studio.txt --clean limpo.txt --model eleven_v4 --root PROJETO
# Prepare fontes, mapa e slides; prévia sem áudio não contém tempos medidos:
python3 scripts/gerar_slides.py --root PROJETO --html-only
# Quando o usuário fornecer o áudio:
python3 scripts/fluxo.py anexar_audio --root PROJETO --audio narracao.mp3
```

Para roteiro pronto sem artigo, omita `--artigo` em `iniciar`. `registrar_roteiro --limpo` aceita a versão canônica sem controles; `--studio` é opcional. Para um roteiro marcado, preparar primeiro a cópia limpa com o mesmo conjunto de controles e conferir igualdade. Controles experimentais precisam de `--audio-tag 'tag nova'` em registro e validação; citações desconhecidas são preservadas. Repetir opções para vários controles. Não remover todo conteúdo entre colchetes.

Ao retomar, consulte `projeto.json.direcao_narrativa` antes de pedir alguma escolha. `direcao` atualiza apenas as escolhas fornecidas e sincroniza o guia. O aviso de direção ausente em `registrar_roteiro` permite registrar roteiros prontos e projetos antigos.

Para áudio e roteiro já prontos, continua válido:

```sh
python3 scripts/preparar.py --root PROJETO --audio narracao.mp3 --roteiro studio.txt --titulo 'Título confirmado'
```

Registro repetido idêntico e anexação do mesmo áudio são idempotentes. Fala canônica ou áudio diferentes exigem revisão explícita em outra pasta; isso evita invalidar silenciosamente um plano/alinhamento existente. Ausências, duplicidade P, incompatibilidade textual e arquivos sem áudio interrompem a etapa. Diretório de áudio deve cobrir exatamente os P registrados. Depois de anexar, seguir reconhecimento/alinhamento, revisão e exportação em [sincronização](sincronizacao.md). Hash e medição não comprovam identidade perceptiva da voz; ouvi-la e declarar se não revisada.

Não produzir timeline, marcações ou vídeo na etapa pendente. Manifest visual a 140 palavras/minuto continua sendo **estimativa**; a estimativa do validador textual de 125–160 palavras/minuto também não representa duração medida. `projeto.json.estado` distingue `roteirizacao`, `aguardando_audio` e `audio_disponivel`; este último significa arquivo medido, não alinhamento aprovado. Os relatórios da sincronização documentam suas etapas posteriores.

## Entrega e retomada

Antes do áudio, entregar artigo, roteiros, guia, mapa, fidelidade, fontes e planejamento/preview disponíveis; declarar o que depende do áudio. Após recebê-lo, usar a mesma pasta, preservar P e fala, medir, alinhar e entregar também PNG/HTML, manifest, timeline, MP4 e scripts. Empacotar todos os materiais necessários à reprodução, sem caches, modelos ou segredos. Não gerar voz nem abrir conta ElevenLabs automaticamente.
