# Ferramentas de desenvolvimento

`gerar_patch.py` gera a pasta `dados/` a partir de duas cópias com a estrutura da pasta do jogo:

- `--originais`: os arquivos originais da build 23889775 (por exemplo, `_PTBR_Backup/build-23889775-original` na pasta do jogo);
- `--traduzido`: o pacote traduzido completo, com um `manifest.json` que lista cada arquivo, o SHA-256 original e o traduzido.

Para cada arquivo Unity, o script compara os objetos serializados e grava um bsdiff só dos objetos alterados (ou do arquivo interno inteiro, quando o pacote traduzido adiciona objetos ou tipos, como fontes). O `Assembly-CSharp.dll` recebe um bsdiff do arquivo inteiro. Antes de gravar, o script reconstrói cada arquivo a partir do original e confere o SHA-256 com o pacote traduzido.

O pipeline de tradução que gera o pacote traduzido (roteiro Ink, interface, fontes, DLL e imagens) fica fora deste repositório.
