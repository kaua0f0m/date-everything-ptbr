# Date Everything! — Tradução PT-BR

Tradução para português do Brasil do jogo **Date Everything!** (Sassy Chap Games / Team17, Steam).

> Tradução de fãs, sem fins lucrativos e sem vínculo com a Sassy Chap Games ou a Team17, **feita por IA (Codex, da OpenAI) com curadoria do criador** nos nomes, no tom e nas imagens. Você precisa ter o jogo original na Steam; o instalador **não contém nem distribui nenhum arquivo do jogo**, ele altera a sua cópia local. O jogo não é recomendado para menores de 14 anos - ele tem humor adulto, palavrões e duplos sentidos, e a tradução não suaviza nada disso.

## Estado: primeira passada (v0.1.0)

- **Roteiro inteiro em primeira passada:** 113.110 fragmentos do roteiro Ink, incluindo todas as rotas, fichas do Date-a-Dex, pistas, descrições de objetos da casa e telas de carregamento.
- **Nomes localizados:** os 102 personagens principais ganharam nomes em português (por exemplo, Parker → Ludo Estrela, Dorian → Pedro Portelo, Lucinda → Amara Abundante), aplicados nas falas, nas fichas e nas caixas de diálogo.
- **Interface:** menus, configurações, controles, galeria, objetivos, conquistas e confirmações de salvar/carregar. Os atributos SPECS viram Sagacidade, Postura, Empatia, Charme e Sarcasmo, inclusive nos requisitos das opções (`[Sagacidade 20/55]`).
- **Acentos funcionando:** as fontes do jogo receberam os caracteres acentuados que faltavam.
- **Imagens redesenhadas:** ficha de candidatura, botões do menu principal e os selos de status **Amor**, **Amizade** e **Ódio**.

A **segunda passada** (revisão dos trocadilhos difíceis e das concordâncias de gênero) ainda não foi feita. A aparência em jogo ainda não foi conferida tela por tela. Encontrou algo estranho? Abra uma *issue* com um print.

## Instalação (Windows)

1. Baixe o `DateEverything-PTBR-vX.Y.Z.zip` na aba **Releases** e extraia.
2. Feche o jogo.
3. Execute `Instalar-DateEverything-PTBR.exe` e escolha **1 — Instalar**. Leva alguns minutos, porque o pacote de texturas tem cerca de 300 MB.
4. Abra o jogo normalmente pela Steam.

O instalador encontra o jogo sozinho (biblioteca Steam); se não achar, ele pede a pasta que contém `Date Everything.exe`.

**Desinstalar:** rode o instalador de novo e escolha **2 — Restaurar**, ou use *Propriedades > Arquivos instalados > Verificar integridade* na Steam.

### Aviso do Windows / antivírus

O `.exe` não é assinado digitalmente. O Windows SmartScreen pode mostrar "O Windows protegeu o computador": clique em **Mais informações > Executar assim mesmo**. Alguns antivírus marcam programas empacotados com PyInstaller por engano. Se preferir não rodar o `.exe`, use o código-fonte abaixo, que faz exatamente a mesma coisa.

## Versão do jogo

A tradução é para a **build 23889775** da Steam. O instalador confere o SHA-256 de cada um dos 19 arquivos antes de mexer em qualquer coisa; se o jogo tiver sido atualizado, ele para sem alterar nada.

Se o jogo for atualizado e a tradução parar de instalar, dá para baixar a versão compatível pelos depots da Steam (App `2201320`, build `23889775`) com o [DepotDownloader](https://github.com/SteamRE/DepotDownloader), ou fazer um fork e refazer os patches com `ferramentas-dev/gerar_patch.py`.

## Rodando pelo código-fonte

Requer Python 3.12 no Windows. Os patches (`dados/`) não ficam no repositório: copie a pasta `dados` do zip da Release para a raiz do projeto.

```bash
pip install -r requirements.txt
python instalar.py                 # menu interativo
python instalar.py instalar --jogo "D:\SteamLibrary\steamapps\common\Date Everything"
python instalar.py restaurar
```

Para gerar o `.exe`: `compilar.bat`.

## Como funciona

O jogo é Unity (Mono). A tradução altera 19 arquivos: o roteiro Ink compilado, os textos serializados da interface em `resources.assets` e nos bundles do Addressables, as fontes, as texturas redesenhadas e o `Assembly-CSharp.dll` (nomes nas caixas de diálogo, rótulos SPECS e textos fixos do código).

Os patches em `dados/` são diferenças binárias (bsdiff) **por objeto Unity**: o instalador abre o arquivo original do jogador com o [UnityPy](https://github.com/K0lb3/UnityPy), troca só os objetos traduzidos, regrava o arquivo e confere se o resultado bate byte a byte com o SHA-256 esperado. Nenhum arquivo é trocado antes de todos os 19 serem gerados e conferidos. O texto e as imagens originais do jogo não são distribuídos.

Os originais ficam em `_PTBR_Backup/build-23889775-original` dentro da pasta do jogo (cerca de 560 MB, por causa do pacote de texturas).

## Créditos

- Criador e curadoria: kaua0f0m
- Tradução: Codex (OpenAI)
- Selo "Amor": letreiro na fonte [Lobster](https://github.com/google/fonts/tree/main/ofl/lobster) (SIL Open Font License)
- Jogo original: Sassy Chap Games, publicado pela Team17

Licença da tradução: CC BY-NC 4.0 (`LICENSE-TRADUCAO.txt`). Código do instalador: MIT (`LICENSE`).
