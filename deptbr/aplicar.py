"""Aplica um patch de dados/ sobre um arquivo original do jogo e devolve os bytes traduzidos."""
import gc
import json
import zipfile

import bsdiff4

from .formato import ARQUIVO_INTEIRO, INDICE, arquivos_serializados, bytes_internos, salvar_unity, sha256_bytes


class PatchInvalido(Exception):
    pass


def _aplicar_binario(orig_path, z):
    with open(orig_path, "rb") as f:
        return bsdiff4.patch(f.read(), z.read(ARQUIVO_INTEIRO))


def _aplicar_unity(orig_path, z):
    import UnityPy
    from UnityPy.streams import EndianBinaryReader

    itens = json.loads(z.read(INDICE).decode("utf-8"))
    env = UnityPy.load(orig_path)
    sfs, streams = arquivos_serializados(env)
    objetos = {nome: {o.path_id: o for o in sf.objects.values()} for nome, sf in sfs.items()}
    for item in itens:
        alvo, nome = item["alvo"], item["nome"]
        if alvo == "objeto":
            obj = objetos[nome].get(item["objeto"])
            if obj is None:
                raise PatchInvalido(f"objeto {item['objeto']} não encontrado em {nome}")
            atual = obj.get_raw_data()
        else:
            entrada = env.file.files.get(nome) if nome else None
            if entrada is None:
                raise PatchInvalido(f"arquivo interno {nome} não encontrado")
            atual = bytes_internos(entrada)
        if sha256_bytes(atual) != item["original_sha256"]:
            raise PatchInvalido(f"conteúdo original inesperado em {nome}:{item['objeto']}")
        novo = bsdiff4.patch(atual, z.read(item["blob"]))
        if sha256_bytes(novo) != item["novo_sha256"]:
            raise PatchInvalido("resultado do patch não confere")
        if alvo == "objeto":
            obj.set_raw_data(novo)
        else:
            leitor = EndianBinaryReader(novo)
            leitor.flags = env.file.files[nome].flags
            env.file.files[nome] = leitor
    dados = salvar_unity(env)
    del env, sfs, streams, objetos
    gc.collect()
    return dados


def aplicar_patch(orig_path, patch_path, entrada):
    with zipfile.ZipFile(patch_path) as z:
        if entrada["tipo"] == "binario":
            return _aplicar_binario(orig_path, z)
        return _aplicar_unity(orig_path, z)
