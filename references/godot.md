# Godot no piloto do Pictograma

O aplicativo deve ficar numa pasta local, por exemplo `~/Applications/Godot.app`. Se houver um ZIP oficial já autorizado, extraia com `ditto -x -k` numa pasta fora do iCloud. O executável é recusado se o caminho informado ou o destino de um link passar por `Mobile Documents`.

A busca usa `JP_GODOT`, depois `/Applications/Godot.app` e `~/Applications/Godot.app`. Antes de usar o executável, confira `codesign --verify --deep --strict` e `spctl --assess --type execute -vv`. No macOS, o piloto exige que o Gatekeeper confirme a assinatura oficial. Preserve a quarentena. O Movie Maker abre uma janela local e usa o driver de áudio `Dummy`. A narração e a trilha são tratadas pela exportação da skill.

O piloto lê a geometria vetorial e as posições de texto amostradas da prévia no navegador. O Godot rasteriza as formas e desenha o texto com as fontes locais. Essa etapa avalia a troca de renderizador. O navegador continua sendo a referência para calcular as poses e o motor de produção enquanto a paridade é medida.

Use `python3 scripts/pictograma_godot.py` para verificar o executável. Para renderizar os quadros do piloto, use `--poses POSES.json --saida PASTA`. O JSON é produzido por `capturar_godot.mjs PREVIA.html POSES.json LARGURA ALTURA QUADROS`, com o mesmo Node e Chrome da prévia. Arquivos íntegros de uma execução concluída podem ser reutilizados quando o manifesto coincide.
