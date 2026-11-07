# ElevenLabs Studio — perfil de produção

Consulta: **6 de novembro de 2026**. Antes de recomendar recurso/modelo novo, ou quando a interface divergir, confira a documentação oficial específica. Estas notas não comprovam a configuração da conta.

## Modelo e controles

| Modelo | Texto | Cuidado |
|---|---|---|
| `eleven_v4` | Tags auditivas, pontuação e parágrafos | Sem SSML, Speed ou Style; controles de identidade dependem da voz. |
| `eleven_v3` | Tags auditivas, pontuação e parágrafos | Sem pausas SSML; testar a voz clonada. |
| `eleven_multilingual_v2` | Pontuação e `<break time="0.7s" />` quando necessário | Sem tags expressivas de v4/v3; pausas solicitadas de até 3 s. |

V4 é alvo recomendado, não seleção realizada. A documentação específica informa clones instantâneos/profissionais, controles Stability/Similarity e, para clones profissionais, Clone Strength. Não prescrever ajuste numérico como ideal universal. [V4](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/eleven-v4).

Studio pode iniciar com outro modelo. Conferir voz e modelo no projeto/parágrafo antes de gerar: uma tag no roteiro não altera a seleção da interface. [Studio](https://elevenlabs.io/docs/eleven-creative/products/studio).

## Tags e pausas

Exemplos documentados: `[curious]`, `[thoughtful]`, `[surprised]`, `[whispers]`, `[sighs]`, `[short pause]`, `[long pause]`. Não são lista fechada nem garantia de obediência. [Tags](https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-audio-tags-work-with-eleven-v3-and-v4) e [prompting](https://elevenlabs.io/docs/overview/capabilities/text-to-speech/best-practices).

Direção descritiva inédita deve ser rotulada nas notas como **experimental**, não controle certificado. Comece com sugestões documentadas. Se uma tag for falada, ignorada ou afetar identidade, simplifique, confira o modelo e teste o trecho; não aumente tags automaticamente.

Pausas qualitativas não têm segundos garantidos. Para silêncio exato de edição, orientar timeline e conferir o áudio. Não inserir SSML em v4/v3 nem usar prosódia ou fonemas XML indiscriminadamente. [Pausas](https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-can-i-add-pauses).

## No Studio

Blocos terminam ideias e preservam contexto. Identificá-los como P01, P02 etc. no guia, não no arquivo de fala. Manter a voz clonada entre blocos salvo pedido diferente. Usar guia para atribuição de voz/modelo, direção e revisão por parágrafo.

Para interpretação difícil, propor Actor Mode com gravação do próprio autor. Preparar regras de pronúncia no editor, confirmando suporte por modelo e testando nomes/siglas. Usar painel de legendas e timeline para alinhar ao áudio aprovado. Ajustar uma pausa da voz não deve ser confundido com pausar música/vídeo. [Studio](https://elevenlabs.io/docs/eleven-creative/products/studio).

Quando houver áudio autorizado, conferir identidade, pronúncia, pausas, omissões/inserções e transições. Só depois medir duração e sincronizar legendas. Sem áudio: **texto validado; interpretação e sincronização não testadas**.

## Limites e estimativas

Referência por geração: v4 10.000 caracteres, v3 5.000, Multilingual v2 10.000. Isso não é limite de projeto com vários parágrafos. Reconsultar antes de submeter um bloco próximo do limite. [Modelos](https://elevenlabs.io/docs/overview/models).

O validador assume 125–160 palavras/minuto como hipótese editorial, sem calibração da voz. Conta pausas SSML solicitadas separadamente e não inventa segundos para tags qualitativas. Ajustar a hipótese após amostra medida. Não chamar estimativa de duração ideal comprovada.
