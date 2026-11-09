# Bíblia visual do Pictograma

O desenho e a auditoria usam [a mesma bíblia](../assets/biblia-pictograma.json). As listas de três números guardam o padrão, o mínimo e o máximo. H é a altura da figura em pé. As medidas em cabeças usam a altura da cabeça oval.

- Registre escolhas de proporção em `projeto.json.canon_pictograma`. Campos omitidos usam a bíblia. As escolhas valem para o elenco todo.
- A figura padrão tem seis cabeças, quadril a 47% de H e joelho a 27%. Braço, antebraço, coxa e canela articulam com comprimentos fixos. A largura dos ombros supera a dos quadris. Mãos circulares e pés ovais separam os gestos da silhueta.
- A folha apresenta em pé, inclinado, andando, sentado no banco, sentado no chão e ajoelhado. Confira contorno, contato e leitura em silhueta. A altura sentada é medida no contorno rasterizado em relação à altura em pé.
- Concentre a luz de cima à esquerda, com sombra própria no lado oposto. Use um plano de chão, sombras de contato e contraste de pelo menos 4,5:1 para as figuras e 7:1 para texto. Deixe o halo para a transformação.
- Associe cada efeito ao que a imagem explica. No recorte de referência, o verde marca agir, o relógio marca esperar, o fluxo de setas distingue receber de fazer e o objeto mostra a entrega a alguém.

## Aprovações e auditoria

1. Rode `pictograma.py modelo --root PROJETO`. Apresente a folha e as medições antes de produzir o storyboard. Após aprovação explícita, use `pictograma.py aprovar-modelo --root PROJETO --confirmado`. Mudanças na bíblia, na paleta ou na folha pedem nova aprovação.
2. Com aprovação da folha, apresente um quadro por batida com o que a imagem mostra, a escolha visual, a metáfora e a leitura sem som. Use `storyboard` e `aprovar-storyboard`. Se o usuário pedir para pular essa revisão, registre a direção como `aprovacao: direta`.
3. Confira juntas e contornos, escala, apoio, objetos, sombras e contraste na auditoria integral. Compare as medidas por pose em `material/auditoria_proporcoes.json`. A auditoria de movimento continua medindo a densidade nos PNGs e no MP4 decodificado.
4. O auditor visual inclui proporção e naturalidade, luz e profundidade e clareza sem som nas notas da coreografia. Toda nota precisa ser pelo menos 4/5 para exportação.

O kit da composição `virada_banco_ajuda_v2` usa a bíblia em produção. Planos antigos sem esse modelo continuam passando pelo kit que os gerou.

### Junções e mãos abertas

No kit cinemático do navegador, o pescoço deve sobrepor a cabeça e o tronco por dentro do preenchimento. Desenhe o ombro como uma curva, sem saliência de encaixe; integre o início do braço nessa curva e afunile o tronco na cintura. Use luz contínua na junção, sem riscos de contorno. Em recepção, a palma é a extremidade do mesmo caminho vetorial do braço. As duas mãos ficam próximas, no peito; a luz destaca a dobra do antebraço. O ponto inferior do coração encontra a região entre as mãos. Consulte [EC-012 e EC-013](erros_conhecidos.md#ec-012--ombreiras-e-emendas).

### Comparação FAZ / RECEBE

Na comparação, cada braço fica no lado da própria figura e a seta termina antes da divisória. Só o coração atravessa o corredor livre. Na recepção, os cotovelos ficam abaixo dos punhos e próximos do tronco. Os antebraços se projetam para a frente, em escorço; as duas palmas juntas sustentam o símbolo na altura do peito. Confira os contornos visíveis e o pouso quadro a quadro. Veja [EC-042](erros_conhecidos.md#ec-042--braço-ou-seta-invade-o-lado-da-outra-figura).

### Rig anatômico 1.8

Os comprimentos canônicos e limites são definidos em `assets/biblia-anatomica-pictograma.json`. As folhas usam o mesmo esqueleto em três vistas. O comprimento é conferido no espaço do rig, antes de projetar o perfil ou os três quartos.

A marcha usa coordenadas do palco para plantar e rolar o pé. As poses estáveis usam a projeção do centro de massa e a área dos apoios. A marcha usa a velocidade do centro de massa e a próxima transferência de peso. A subida assistida considera a base conjunta durante a pega. As medidas são estimativas do modelo vetorial. Referências de movimento: [equilíbrio dinâmico](https://pubmed.ncbi.nlm.nih.gov/15519333/) e [fases de levantar](https://pubmed.ncbi.nlm.nih.gov/2217543/).

Gere as duas folhas com `pictograma.py folhas --root PROJETO`. O comando `aprovar-folhas --root PROJETO --confirmado` registra a decisão explícita sobre os artefatos atuais. Alterar qualquer folha, medição ou fonte do rig invalida a aprovação. Esta candidata está no ponto de revisão das folhas.

### Revisão de anatomia e pega

A proporção de 1,49 h para a coxa e 1,30 h para a canela é uma escolha de estilização para este cânone. Não é uma média populacional. Para referência anatômica, consulte [medições radiográficas de adultos](https://www.mdpi.com/2673-4036/1/2/9).

A altura do joelho é medida em repouso. A projeção em três quartos encurta a largura dos ombros e da pelve e distingue os lados pelo afastamento da câmera. O ensaio de ajuda reserva dez quadros à pega antes da tração.

A auditoria da folha rasteriza máscaras separadas das silhuetas durante a pega. As medidas de pé na folha ainda são geométricas. No piloto P007–P008, a entrega precisa de confirmação independente no MP4 decodificado. Medir as solas e o ponto de contato no referencial do chão, compensando a câmera, e verificar a interpenetração de silhuetas fora da região de contato. Exportar divergências com tempo, quadro e recorte. A geometria do rig, sozinha, não libera o piloto.

Em repouso em pé, cada joelho deve ter entre 0° e 5° de flexão, independentemente da vista (EC-072). Na vista de três quartos, a linha dos ombros é horizontal: o lado distante encurta pela projeção e o braço descansa próximo ao flanco. Tórax, pelve e coxas usam a mesma tinta na vista frontal. Na subida assistida, “Estabilizar de mãos dadas” indica apoio ainda compartilhado; “Separar” começa após a soltura.
