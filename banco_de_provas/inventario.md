# Inventário do piloto aprovado

A referência de imagem e som é o MP4 aprovado com luz e efeitos. O vídeo e os relatórios originais permanecem na pasta do piloto. O manifesto do banco fixa os hashes.

| Área | Específico de P007–P008 | Reaproveitável |
| --- | --- | --- |
| Seleção de composição | `virada_banco_ajuda_v3` e a ordem fixa de três cenas no compilador Python | Resolução de âncoras literais, áudio medido, quadros a 30 fps, validação de área segura |
| Texto | DEUS, É, NÃO, AM–O/A–R, substantivo/verbo, ESPERAR, AGIR, FAZ e RECEBE dentro do kit cinematográfico | Tipografia Archivo e Atkinson, encaixe pelo tamanho do texto, virada de letra, corredor da negação, legendas por palavra |
| Atuação | Encadeamento marcha → banco → ajuda → comparação; deslocamentos −2,37 e −1,73; enquadramento de dois atores com lados fixos | Rig anatômico, IK de dois ossos, travas e contatos, ciclos de marcha e transferência de peso |
| Apoio e transição | Banco e seus intervalos de entrada e saída, câmera e posição de divisória ajustados àquela fala | Primitivas de banco e chão, curvas suaves, transição por troca de apoio |
| Ações | Dicionário fixo de âncoras e offsets dependentes do piloto, perfis próprios da entrega dos dois corações | Palavras literais e ocorrência, relações ator–alvo–objeto, interpolação e continuidade de identidade |
| Luz | Centro do foco no tronco e trajeto da entrega ligados à encenação piloto | Bíblia de cor, duas tonalidades, sombras de apoio, recorte, foco, botão de alternância e análise de pixels |
| Auditoria | Checagens do NÃO, palmas, banco e duas identidades dos corações com marcações específicas | Verificação integral, testes por mutação, bloqueio pré-exportação, contraste, densidade e A/B de flashes |

A rotina v3 está em `assets/kit-pictograma-cinematico.js`, `assets/pictograma-atuacao.js` e `scripts/pictograma_coreografia.py`. `assets/kit-pictograma-coreografia.js` é a geração anterior. A migração deve separar a descrição do projeto da mecânica sem usar a reprodução da versão antiga como evidência da versão nova.
