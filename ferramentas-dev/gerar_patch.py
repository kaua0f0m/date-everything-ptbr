"""Gera dados/ a partir dos arquivos originais do jogo e do pacote traduzido.

Uso (na raiz do repositório, com o ambiente do requirements.txt):

    python ferramentas-dev/gerar_patch.py --originais <pasta com os originais>
        --traduzido <pasta do pacote traduzido> [--saida dados]

As duas pastas usam a mesma estrutura relativa da pasta do jogo
("Date Everything_Data/..."). A lista de arquivos e os hashes vêm de
<traduzido>/manifest.json (gerado pelo pipeline de tradução). O resultado é
reconstruído e conferido byte a byte antes de ser gravado.
"""
import argparse
import gc
import json
import os
import shutil
import sys
import zipfile

import bsdiff4
import UnityPy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from deptbr import STEAM_BUILD, VERSAO  # noqa: E402
from deptbr.aplicar import aplicar_patch  # noqa: E402
from deptbr.formato import (ARQUIVO_INTEIRO, INDICE, MANIFESTO, arquivos_serializados,  # noqa: E402
                            bytes_internos, sha256_arquivo, sha256_bytes)


def ler(p):
    with open(p, "rb") as f:
        return f.read()


def diff_unity(orig_path, trad_path):
    eo, et = UnityPy.load(orig_path), UnityPy.load(trad_path)
    so, sto = arquivos_serializados(eo)
    st, stt = arquivos_serializados(et)
    if so.keys() != st.keys() or sto.keys() != stt.keys():
        raise SystemExit(f"{trad_path}: a lista de arquivos internos mudou; formato não suportado.")
    itens, blobs = [], {}

    def item(alvo, nome, objeto, a, b):
        blob = f"{len(blobs)}.bsdiff"
        blobs[blob] = bsdiff4.diff(a, b)
        itens.append({"alvo": alvo, "nome": nome, "objeto": objeto, "original_sha256": sha256_bytes(a),
                      "novo_sha256": sha256_bytes(b), "blob": blob})

    for interno, sf_t in st.items():
        sf_o = so[interno]
        objs_o = {o.path_id: o for o in sf_o.objects.values()}
        objs_t = {o.path_id: o for o in sf_t.objects.values()}
        tipos_iguais = [t.class_id for t in sf_o.types] == [t.class_id for t in sf_t.types]
        if objs_o.keys() != objs_t.keys() or not tipos_iguais:
            if not interno:
                raise SystemExit(f"{trad_path}: objetos/tipos adicionados num .assets avulso; não suportado.")
            item("interno", interno, None, bytes_internos(sf_o), bytes_internos(sf_t))
            continue
        for pid, ot in objs_t.items():
            a, b = objs_o[pid].get_raw_data(), ot.get_raw_data()
            if a != b:
                item("objeto", interno, pid, a, b)
    for nome_stream, r_t in stt.items():
        a, b = bytes_internos(sto[nome_stream]), bytes_internos(r_t)
        if a != b:
            item("stream", nome_stream, None, a, b)
    del eo, et
    gc.collect()
    return itens, blobs


def gravar_zip(destino, itens, blobs):
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_STORED) as z:
        if itens is not None:
            z.writestr(INDICE, json.dumps(itens, ensure_ascii=False, indent=1))
        for nome, dados in blobs.items():
            z.writestr(nome, dados)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--originais", required=True)
    ap.add_argument("--traduzido", required=True)
    ap.add_argument("--saida", default="dados")
    args = ap.parse_args()

    with open(os.path.join(args.traduzido, "manifest.json"), encoding="utf-8-sig") as f:
        origem = json.load(f)
    if str(origem["steam_buildid"]) != STEAM_BUILD:
        raise SystemExit("Build do pacote diferente de deptbr.STEAM_BUILD.")
    temp = args.saida + ".tmp"
    shutil.rmtree(temp, ignore_errors=True)
    os.makedirs(temp)
    manifesto = {"versao": VERSAO, "steam_build": STEAM_BUILD, "arquivos": []}
    for i, e in enumerate(origem["files"]):
        rel = e["relative_path"]
        orig = os.path.join(args.originais, *rel.split("/"))
        trad = os.path.join(args.traduzido, *rel.split("/"))
        assert sha256_arquivo(orig) == e["original_sha256"], f"original inesperado: {rel}"
        assert sha256_arquivo(trad) == e["patched_sha256"], f"traduzido inesperado: {rel}"
        patch = f"{i:02d}.zip"
        unity = not rel.lower().endswith(".dll")
        print(f"[{i + 1}/{len(origem['files'])}] {rel}", flush=True)
        if unity:
            itens, blobs = diff_unity(orig, trad)
            gravar_zip(os.path.join(temp, patch), itens, blobs)
        else:
            gravar_zip(os.path.join(temp, patch), None, {ARQUIVO_INTEIRO: bsdiff4.diff(ler(orig), ler(trad))})
        entrada = {
            "caminho": rel,
            "original_sha256": e["original_sha256"],
            "traduzido_sha256": e["patched_sha256"],
            "versoes_anteriores_sha256": [h for h in e.get("compatible_patched_sha256", []) if h != e["patched_sha256"]],
            "tipo": "unity" if unity else "binario",
            "patch": patch,
        }
        # Reconstrói a partir do original e confere o hash final.
        resultado = aplicar_patch(orig, os.path.join(temp, patch), entrada)
        if sha256_bytes(resultado) != e["patched_sha256"]:
            raise SystemExit(f"Reconstrução diverge do pacote traduzido: {rel}")
        del resultado
        gc.collect()
        tam = os.path.getsize(os.path.join(temp, patch))
        print(f"    patch {tam / 1e6:.2f} MB, reconstrução idêntica", flush=True)
        manifesto["arquivos"].append(entrada)
    with open(os.path.join(temp, MANIFESTO), "w", encoding="utf-8") as f:
        json.dump(manifesto, f, ensure_ascii=False, indent=1)
    shutil.rmtree(args.saida, ignore_errors=True)
    os.replace(temp, args.saida)
    total = sum(os.path.getsize(os.path.join(args.saida, n)) for n in os.listdir(args.saida))
    print(f"Pronto: {args.saida} ({total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
