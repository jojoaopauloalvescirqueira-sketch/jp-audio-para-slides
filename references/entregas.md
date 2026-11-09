# Entrega e aceite

## Pacote padrão após receber áudio

- video.mp4 em 16:9; formatos alternativos têm nomes distintos.
- slides/png/S001.png… e slides/apresentacao.html, com navegação, texto correspondente e botões de áudio depois de existir marcação.
- slides/manifest.csv: slide_id, arquivo_png, paragrafo_inicio, paragrafo_fim, frase_gatilho, tipo, figura_artigo, duracao_estimada_s. A última coluna é explicitamente estimada a 140 palavras/minuto.
- slides/timeline.csv, intervalos_roteiro.json, concat.ffconcat e sincronizacao.json: tempos, quadros, métodos e identidade dos áudios.
- material/ com originais preservados, roteiro limpo, metadados e fontes; referências locais e URLs em FONTES.md, incluindo páginas e limitações dos gráficos.
- No perfil Editorial JP, entregar o mapa visual, o manifesto de renderização e os quadros intermediários junto aos PNGs.
- scripts/ e assets/ necessários para reproduzir, requisitos e LEIAME.md com comandos reais. Copiar os scripts desta skill para o projeto; os comandos já usam --root, sem depender da instalação original.
- Plano de aula e mapa de parágrafos fornecidos ou reconstruídos, com função didática, fontes e entradas.

Fornecer ZIP quando útil. Não incluir caches, bibliotecas, modelos ASR, executáveis, arquivos temporários ou materiais de outro projeto. Informar tamanho se o áudio tornar o pacote grande.

Antes do áudio, entregar os materiais de [roteirização](roteiros.md), planejamento visual e prévias disponíveis, com estado explícito. Timeline medida e vídeo permanecem pendentes.

## Pacote para vídeos animados

Inclua narração, fala canônica, prévia HTML, plano, storyboard, timeline, MP4, referências e scripts. No Pictograma, inclua o storyboard de quadros-chave e as amostras finais. No Ilustrado, inclua a bíblia, elenco, cenários, prompts, inventário, PNGs aprovados, folha de contato, revisões e `FONTES.md`. Mantenha os caminhos relativos. Exclua do ZIP as sequências de renderização (`.render/quadros/` e `ilustrado/<formato>/quadros/`) e caches. Os PNGs de origem e os quadros-chave para revisão fazem parte da entrega.

## Conferência

```sh
python3 "$SKILL/scripts/validar.py" --root "$PROJETO" --video
```

O verificador confere cobertura, figuras referenciadas, dimensões, margem, continuidade e decodificação. Não comprova veracidade dos números, semântica do gráfico nem correção perceptiva de todas as trocas.

Conferir editorialmente título, unidades e qualificações; calcular independentemente as contas exibidas. Inspecionar a montagem completa, todos os gráficos densos e cálculos, além de cinco slides aleatórios em resolução final (todos se houver menos de cinco). Verificar que recortes não removem dados ou créditos e que a legenda corresponde ao que se ouve.

Comparar amostras de cada slide no vídeo com os PNGs nos tempos da timeline. Conferir o áudio por hash de pacotes quando houver cópia ou por comparação de sinal/envelope quando houver conversão; preservar o áudio fonte. Conferir as entradas das contas no contexto do áudio. Para vídeo longo, distinguir esse procedimento de audição humana integral.

Ajustar o que falhar e repetir apenas as verificações afetadas. Exportação com pendência não resolvida não deve ser anunciada como sincronização verificada. Relatar limitações concretas, sem notas genéricas nem alegações de aprovação que não tenham sido feitas.

A validação da instalação usa quick_validate.py da skill-creator. Testar os scripts com recorte real e outro tema; o teste técnico com áudio sintético não comprova alinhamento acústico de fala. Manter resultados de testes separados dos exemplos visuais e não transportá-los como validação de futuros projetos.
