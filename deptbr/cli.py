"""Instalador da tradução PT-BR de Date Everything!"""
import argparse
import os
import sys
import time

from . import STEAM_BUILD, VERSAO
from .core import BACKUP, ErroInstalacao, build_steam, instalar, jogo_valido, procurar_jogo, restaurar

TITULO = f"Date Everything! - Tradução PT-BR  v{VERSAO}"


def _console():
    if sys.platform == "win32":
        os.system("chcp 65001 >nul")
    for f in (sys.stdout, sys.stderr):
        try:
            f.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _pausa(args):
    if not args.sem_pausa and sys.stdin and sys.stdin.isatty():
        try:
            input("\nPressione Enter para fechar...")
        except EOFError:
            pass


def _escolher_jogo(args):
    if args.jogo:
        if not jogo_valido(args.jogo):
            raise SystemExit(f"'{args.jogo}' não parece ser a pasta do Date Everything! (falta 'Date Everything.exe').")
        return args.jogo
    achados = procurar_jogo()
    if len(achados) == 1:
        print(f"Jogo encontrado: {achados[0]}")
        return achados[0]
    if len(achados) > 1:
        for i, p in enumerate(achados, 1):
            print(f"  [{i}] {p}")
        r = input("Qual instalação? ").strip()
        if r.isdigit() and 1 <= int(r) <= len(achados):
            return achados[int(r) - 1]
    print("Não encontrei o Date Everything! automaticamente.")
    p = input("Cole aqui o caminho da pasta do jogo (a que contém 'Date Everything.exe'): ").strip().strip('"')
    if not jogo_valido(p):
        raise SystemExit("Pasta inválida.")
    return p


def _checar_jogo_aberto():
    if sys.platform != "win32":
        return
    import subprocess
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Date Everything.exe"],
                             capture_output=True, text=True).stdout
    except Exception:
        return
    if "Date Everything.exe" in out:
        raise SystemExit("O Date Everything! está aberto. Feche o jogo e execute de novo.")


def _instalar(game):
    _checar_jogo_aberto()
    build = build_steam(game)
    if build and build != STEAM_BUILD:
        print(f"Aviso: a Steam informa a build {build}; esta tradução foi feita para a build {STEAM_BUILD}.")
        print("O instalador confere cada arquivo e não altera nada se a versão não bater.\n")
    t0 = time.time()
    print("\nConferindo e traduzindo os arquivos (pode levar alguns minutos)...")
    n = instalar(game)
    if n:
        qtd = "1 arquivo traduzido e conferido" if n == 1 else f"{n} arquivos traduzidos e conferidos"
        print(f"\nPronto! {qtd} em {time.time() - t0:.0f}s.")
    print("Abra o jogo normalmente pela Steam.")
    print(f"Os originais ficam em '{BACKUP}' dentro da pasta do jogo.")


def _restaurar(game):
    _checar_jogo_aberto()
    n = restaurar(game)
    print(f"\n{n} arquivos restaurados para o inglês original.")


def main(argv=None):
    _console()
    ap = argparse.ArgumentParser(description=TITULO)
    ap.add_argument("acao", nargs="?", choices=["instalar", "restaurar"], help="o que fazer (padrão: pergunta)")
    ap.add_argument("--jogo", help="pasta do jogo (a que contém 'Date Everything.exe')")
    ap.add_argument("--sem-pausa", action="store_true", help="não esperar Enter ao final")
    args = ap.parse_args(argv)
    print("=" * len(TITULO))
    print(TITULO)
    print("=" * len(TITULO))
    print("Criador: kaua0f0m | Tradução: Codex (OpenAI), com curadoria do criador")
    print("Você precisa ter o Date Everything! original instalado pela Steam.\n")
    try:
        acao = args.acao
        if not acao:
            print("  [1] Instalar a tradução")
            print("  [2] Restaurar o jogo original (inglês)")
            r = input("Escolha (1/2): ").strip()
            acao = "restaurar" if r == "2" else "instalar"
        game = _escolher_jogo(args)
        if acao == "instalar":
            _instalar(game)
        else:
            _restaurar(game)
    except ErroInstalacao as e:
        print(f"\nErro: {e}\nNenhum arquivo do jogo foi alterado.")
        _pausa(args)
        return 1
    except SystemExit as e:
        if e.code not in (None, 0):
            print(f"\nErro: {e.code}")
            _pausa(args)
            return 1
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 1
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\nErro inesperado: {e}\nOs originais continuam em '{BACKUP}' dentro da pasta do jogo; "
              "use a opção 2 (Restaurar) se algo ficou estranho.")
        _pausa(args)
        return 1
    _pausa(args)
    return 0
