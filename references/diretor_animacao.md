# Diretor de animação

Ao selecionar Pictograma, leia a fala inteira, a direção narrativa e o guia. O diretor de arte traduz ideias em imagens e movimentos sem acrescentar afirmações à fala. Abra a referência visual quando precisar entender o vocabulário do estilo.

Peça a `diretor-de-animacao` primeiro somente as perguntas. A coordenação as apresenta em uma mensagem com até seis itens e aguarda. Use um exemplo curto da fala real em cada item, explique o efeito de cada opção e marque **Recomendado**. Aproveite escolhas já registradas. Em ambiente sem subagentes, faça a mesma etapa separada antes de propor cenas.

1. **Quem cria as cenas?** Diretor cria todas (recomendado), usuário descreve as principais e o diretor completa, ou usuário descreve todas e o diretor converte.
2. **Tom visual.** Sóbrio e reflexivo, didático e claro (recomendado) ou energético. Ajuste quantidade de movimento, ritmo e intensidade do acento.
3. **Metáfora.** Literal, ilustrativa (recomendado) ou metafórica. Símbolos ilustram a fala e preservam seu sentido.
4. **Personagens e rótulos.** Figuras genéricas sem nomes reais (recomendado), papéis identificados por rótulos como “VOCÊ”, ou nomes reais explicitamente autorizados. Registre os nomes autorizados individualmente.
5. **Texto e legenda.** Palavras-chave cinéticas (recomendado), frases curtas ou sem texto editorial. Escolha separadamente legenda palavra a palavra. Recomende legenda ligada.
6. **Paleta e aprovação.** Escura JP (recomendado), clara ou personalizada. Recomende storyboard antes da animação completa. A opção direta permite aplicar o plano completo após a direção.

Com “decide você”, registre as recomendações como `padrao_assumido`. A preferência de storyboard continua valendo. Grave cada valor, origem e data por `pictograma.py direcao`. Quando o usuário fornecer cenas em texto livre, preserve suas decisões, liste as que a biblioteca não representa e proponha o elemento mais próximo.

A coordenação repassa as respostas ao diretor. Com storyboard, o diretor entrega somente quadros estáticos declarativos. Rode `storyboard` e apresente os PNGs e o HTML. Após aprovação explícita, rode `aprovar-storyboard`. Só então solicite ao diretor o plano completo. Com direção direta, solicite o plano completo depois de registrar as escolhas. Em ambas, o diretor devolve JSON conforme [o contrato](pictograma.md). A coordenação aplica e valida usando o script.
