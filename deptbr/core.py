"""Localização do jogo, dados do patch, backup, instalação e restauração."""
import json
import os
import re
import shutil
import sys

from . import STEAM_APPID, STEAM_BUILD
from .aplicar import PatchInvalido, aplicar_patch
from .formato import MANIFESTO, sha256_arquivo, sha256_bytes

PASTA_JOGO = "Date Everything"
EXE = "Date Everything.exe"
DATA = "Date Everything_Data"
BACKUP = os.path.join("_PTBR_Backup", f"build-{STEAM_BUILD}-original")
TEMP = ".ptbr-tmp"


class ErroInstalacao(Exception):
    pass


def dados_dir():
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "dados")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dados")


def carregar_manifesto():
    p = os.path.join(dados_dir(), MANIFESTO)
    if not os.path.isfile(p):
        raise ErroInstalacao("Pasta 'dados' não encontrada. Baixe o zip completo na aba Releases do GitHub.")
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jogo_valido(p):
    return bool(p) and os.path.isfile(os.path.join(p, EXE)) and os.path.isdir(os.path.join(p, DATA))


def _bibliotecas_steam():
    raizes = []
    if sys.platform == "win32":
        try:
            import winreg
            for hive, chave in ((winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam"),
                                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")):
                try:
                    with winreg.OpenKey(hive, chave) as k:
                        for nome in ("SteamPath", "InstallPath"):
                            try:
                                raizes.append(winreg.QueryValueEx(k, nome)[0])
                            except OSError:
                                pass
                except OSError:
                    pass
        except ImportError:
            pass
    for pf in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
        if pf:
            raizes.append(os.path.join(pf, "Steam"))
    libs = []
    for r in raizes:
        r = os.path.normpath(r)
        libs.append(r)
        vdf = os.path.join(r, "steamapps", "libraryfolders.vdf")
        if os.path.isfile(vdf):
            try:
                with open(vdf, encoding="utf-8", errors="replace") as f:
                    for m in re.finditer(r'"path"\s+"([^"]+)"', f.read()):
                        libs.append(os.path.normpath(m.group(1).replace("\\\\", "\\")))
            except OSError:
                pass
    vistos, out = set(), []
    for lib in libs:
        if lib.lower() not in vistos:
            vistos.add(lib.lower())
            out.append(lib)
    return out


def procurar_jogo():
    achados = []
    for lib in _bibliotecas_steam():
        p = os.path.join(lib, "steamapps", "common", PASTA_JOGO)
        if jogo_valido(p) and p not in achados:
            achados.append(p)
    return achados


def build_steam(game):
    """Build informada pela Steam (appmanifest), ou None."""
    acf = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(game))), f"appmanifest_{STEAM_APPID}.acf")
    try:
        with open(acf, encoding="utf-8", errors="replace") as f:
            m = re.search(r'"buildid"\s+"(\d+)"', f.read())
            return m.group(1) if m else None
    except OSError:
        return None


def _caminho(base, rel):
    return os.path.join(base, *rel.split("/"))


def _planejar(game, manifesto, log):
    """Confere todos os arquivos antes de alterar qualquer coisa."""
    plano = []
    for e in manifesto["arquivos"]:
        alvo = _caminho(game, e["caminho"])
        bk = _caminho(os.path.join(game, BACKUP), e["caminho"])
        if not os.path.isfile(alvo):
            raise ErroInstalacao(f"Arquivo do jogo não encontrado: {e['caminho']}")
        atual = sha256_arquivo(alvo)
        bk_ok = os.path.isfile(bk) and sha256_arquivo(bk) == e["original_sha256"]
        if atual == e["traduzido_sha256"]:
            estado, fonte = "ok", None
        elif atual == e["original_sha256"]:
            estado, fonte = "aplicar", alvo
        elif atual in e["versoes_anteriores_sha256"] and bk_ok:
            estado, fonte = "atualizar", bk
        elif bk_ok:
            raise ErroInstalacao(
                f"{e['caminho']} foi alterado por outro programa ou por uma atualização. "
                "Restaure (opção 2) ou verifique a integridade na Steam e tente de novo.")
        else:
            raise ErroInstalacao(
                f"Versão inesperada de {e['caminho']}. Esta tradução é para a build {STEAM_BUILD} da Steam; "
                "se o jogo foi atualizado, veja o README no GitHub.")
        plano.append({"e": e, "alvo": alvo, "bk": bk, "bk_ok": bk_ok, "estado": estado, "fonte": fonte})
    return plano


def instalar(game, log=print):
    manifesto = carregar_manifesto()
    plano = _planejar(game, manifesto, log)
    pendentes = [p for p in plano if p["estado"] != "ok"]
    if not pendentes:
        log("A tradução já está instalada e todos os arquivos conferem.")
        return 0
    for p in plano:
        if p["estado"] == "ok" and not p["bk_ok"]:
            log(f"  aviso: sem backup do original de {p['e']['caminho']} (para desinstalar, use a Steam)")
    try:
        for i, p in enumerate(pendentes, 1):
            e = p["e"]
            log(f"  [{i}/{len(pendentes)}] {e['caminho'].split('/')[-1]}")
            if not p["bk_ok"]:
                os.makedirs(os.path.dirname(p["bk"]), exist_ok=True)
                shutil.copy2(p["alvo"], p["bk"])
                if sha256_arquivo(p["bk"]) != e["original_sha256"]:
                    raise ErroInstalacao("Falha ao conferir o backup.")
                p["bk_ok"] = True
            try:
                dados = aplicar_patch(p["fonte"], os.path.join(dados_dir(), e["patch"]), e)
            except PatchInvalido as ex:
                raise ErroInstalacao(f"{e['caminho']}: {ex}") from ex
            if sha256_bytes(dados) != e["traduzido_sha256"]:
                raise ErroInstalacao(f"{e['caminho']}: o arquivo gerado não confere com o esperado.")
            with open(p["alvo"] + TEMP, "wb") as f:
                f.write(dados)
            del dados
    except BaseException:
        for p in pendentes:
            try:
                os.remove(p["alvo"] + TEMP)
            except OSError:
                pass
        raise
    # Só troca os arquivos depois que todos foram gerados e conferidos.
    trocados = []
    try:
        for p in pendentes:
            os.replace(p["alvo"] + TEMP, p["alvo"])
            trocados.append(p)
        for p in plano:
            if sha256_arquivo(p["alvo"]) != p["e"]["traduzido_sha256"]:
                raise ErroInstalacao("Falha na verificação final.")
    except BaseException:
        for p in trocados:
            shutil.copy2(p["bk"], p["alvo"])
        raise
    return len(pendentes)


def restaurar(game, log=print):
    manifesto = carregar_manifesto()
    n = 0
    for e in manifesto["arquivos"]:
        alvo = _caminho(game, e["caminho"])
        bk = _caminho(os.path.join(game, BACKUP), e["caminho"])
        if os.path.isfile(alvo) and sha256_arquivo(alvo) == e["original_sha256"]:
            continue
        if os.path.isfile(bk) and sha256_arquivo(bk) == e["original_sha256"]:
            shutil.copy2(bk, alvo)
            n += 1
        else:
            log(f"  sem backup válido: {e['caminho']} (use Verificar integridade na Steam)")
    return n
