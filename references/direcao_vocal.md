# Direção vocal

O diretor vocal trabalha como ator e editor. Acione `diretor-vocal` somente no modo `skill`, após registrar a fala canônica e antes de aplicar tags ao Studio. Envie a fala integral, os IDs dos parágrafos e blocos, a direção narrativa, o guia e o catálogo. Peça apenas o JSON da proposta. Onde não houver subagentes, execute a mesma análise como etapa editorial separada. A coordenação grava a proposta e usa o script de aplicação.

Leia a fala inteira. Trace a curva de intensidade de 1 a 5 por bloco. Localize viradas, teses, objeções, citações, humor, clímax e fecho. Respeite a perspectiva, a voz, o público e a fonte. Use tags quando a pontuação e a fala pedirem reforço. Preserve palavras, pontuação e parágrafos.

Posicione a tag antes da frase a que se destina. Evite sequências de tags e o interior de citações. Uma marca de emoção pode persistir além da primeira frase. Quando a frase seguinte pedir outro tom, proponha deslocar a tag para uma fronteira de bloco já existente, omiti-la ou testar os blocos separadamente no Studio com a fala preservada. Indique o trecho a ouvir e o efeito a verificar. Uma pausa é qualitativa. Voz e Efeitos sonoros dependem de autorização explícita.

Use apenas o idioma e as categorias escolhidos, conforme o catálogo. Leve admite até uma tag por 60 palavras, moderada uma por 35 a 60 e expressiva uma por 20 a 35. As faixas indicam ritmo editorial. A fala pode pedir menos tags ou nenhuma.

O JSON segue este contrato:

```json
{
  "versao": 1,
  "idioma": "pt",
  "densidade": "leve",
  "curva": [{"bloco": "B02", "intensidade": 3, "funcao": "virada da tese"}],
  "tags": [
    {"p": "P002", "antes_de": "A medição começa aqui.", "ocorrencia": 1,
     "tag": "[pausa]", "categoria": "entrega", "intencao": "separar exemplo e evidência",
     "alcance": "pontual", "risco": "baixo", "alternativa": "Conservar só a pontuação."}
  ],
  "testes": ["Ouvir a pausa em P002 e conferir a retomada da frase."]
}
```

Copie `antes_de` literalmente da fala canônica. Use `ocorrencia` com base 1 se o trecho aparecer mais de uma vez no mesmo parágrafo. Cada posição recebe uma tag. Se uma proposta falhar, corrija o plano e reaplique.
