"""Formato dos patches (compartilhado pelo gerador e pelo instalador).

Cada arquivo do jogo alterado tem uma entrada em dados/manifesto.json:

    {"caminho": "Date Everything_Data/...", "original_sha256": ..., "traduzido_sha256": ...,
     "versoes_anteriores_sha256": [...], "tipo": "unity" | "binario", "patch": "NN.zip"}

tipo "binario": o zip contém "arquivo.bsdiff", diferença do arquivo inteiro.

tipo "unity": o zip contém "indice.json" e um blob por item alterado:
    {"alvo": "objeto" | "interno" | "stream",
     "nome": arquivo interno do bundle ("" para um .assets avulso),
     "objeto": path_id (só para alvo "objeto"),
     "original_sha256": ..., "novo_sha256": ..., "blob": "n.bsdiff"}

"objeto" troca um objeto serializado; "interno" troca o SerializedFile inteiro
(usado quando o patch adiciona objetos ou tipos, como fontes novas); "stream"
troca um arquivo de recursos (.resS/.resource) do bundle.

O texto e as imagens do jogo original não são distribuídos: os blobs bsdiff só
reconstroem o resultado a partir da cópia do jogo do próprio jogador.
"""
import hashlib

MANIFESTO = "manifesto.json"
INDICE = "indice.json"
ARQUIVO_INTEIRO = "arquivo.bsdiff"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_arquivo(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def arquivos_serializados(env):
    """{nome_interno: SerializedFile} e {nome_interno: bytes} dos streams de recursos."""
    from UnityPy.files import SerializedFile
    from UnityPy.streams import EndianBinaryReader

    f = env.file
    if isinstance(f, SerializedFile):
        return {"": f}, {}
    sfs, streams = {}, {}
    for nome, item in f.files.items():
        if isinstance(item, SerializedFile):
            sfs[nome] = item
        elif isinstance(item, EndianBinaryReader):
            streams[nome] = item
    return sfs, streams


def bytes_internos(entrada):
    """Bytes crus (descomprimidos) de um arquivo interno do bundle."""
    from UnityPy.files import SerializedFile

    if isinstance(entrada, SerializedFile):
        return bytes(entrada.reader.bytes)
    return bytes(entrada.bytes)


def salvar_unity(env):
    from UnityPy.files import SerializedFile

    f = env.file
    if isinstance(f, SerializedFile):
        return f.save()
    return f.save(packer="original")
