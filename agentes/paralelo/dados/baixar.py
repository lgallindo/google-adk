"""Baixa os dados da LAI da CGU e escreve a amostra desta pasta.

FONTE
-----
Portal de Dados Abertos da CGU, base do FalaBR (o sistema por onde entram os
pedidos de Lei de Acesso à Informação do Executivo federal):

    https://dadosabertos-download.cgu.gov.br/FalaBR/Arquivos_FalaBR_Filtrado/

"Filtrado" no nome quer dizer que a CGU já tirou os dados pessoais de quem
pediu. O que sobra é o pedido, a resposta do órgão e a decisão. Em 2025 são
83.827 pedidos concluídos, num zip de 82 MB que vira 423 MB de CSV — grande
demais para o repositório, e é por isso que este script existe em vez de o
CSV estar commitado.

O QUE ELE FAZ
-------------
1. Baixa o zip do ano (com cache em `.cache/`, que o git ignora).
2. Lê `Pedidos` e `Recursos`. Os dois se ligam por `IdPedido`.
3. Sorteia uma amostra equilibrada por tipo de decisão.
4. Tira e-mail, CPF, CNPJ e telefone do texto livre, por precaução.
5. Escreve `pedidos.jsonl`, que é o arquivo pequeno e commitado.

    just dados            # baixa e regera a amostra
    just dados --ano 2024 --n 120

O GABARITO
----------
Cada pedido carrega `houve_recurso`: se a pessoa recorreu da resposta, de
verdade, na base da CGU. Isso é gabarito. Os agentes NUNCA recebem esse
campo — `pedidos.py` o remove antes de entregar o pedido ao modelo. Ele serve
para a turma conferir depois se o parecer de risco acertou.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import unicodedata
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

BASE = "https://dadosabertos-download.cgu.gov.br/FalaBR/Arquivos_FalaBR_Filtrado"
AQUI = Path(__file__).resolve().parent
CACHE = AQUI / ".cache"
SAIDA = AQUI / "pedidos.jsonl"

# Quantos pedidos de cada decisão entram na amostra. A proporção não é a da
# base real (lá 74% é "Acesso Concedido"): para a aula interessa ter negativa
# e concessão parcial em quantidade suficiente para discutir.
COTAS = {
    "Acesso Concedido": 18,
    "Acesso Parcialmente Concedido": 14,
    "Acesso Negado": 14,
    "Informação Inexistente": 6,
    "Órgão não tem competência para responder sobre o assunto": 4,
    "Não se trata de solicitação de informação": 4,
}

# Texto curto demais não dá o que analisar; longo demais estoura o contexto
# de um modelo pequeno como o Qwen3-0.6B.
MIN_PEDIDO, MAX_PEDIDO = 180, 2200
MIN_RESPOSTA, MAX_RESPOSTA = 120, 2800

_SEGREDOS = [
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[e-mail removido]"),
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF removido]"),
    (re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"), "[CNPJ removido]"),
    (re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b"), "[telefone removido]"),
]


def limpar(texto: str) -> str:
    """Tira dado pessoal esquecido no texto livre e normaliza o espaço."""
    texto = unicodedata.normalize("NFC", texto or "")
    for padrao, marca in _SEGREDOS:
        texto = padrao.sub(marca, texto)
    return re.sub(r"\s+", " ", texto).strip()


def baixar_zip(ano: int) -> Path:
    """Baixa o zip do ano, ou reaproveita o que já está em `.cache/`."""
    CACHE.mkdir(exist_ok=True)
    destino = CACHE / f"Arquivos_csv_{ano}.zip"
    if destino.exists() and destino.stat().st_size > 1_000_000:
        print(f"  cache      {destino.name} ({destino.stat().st_size / 1e6:.0f} MB)")
        return destino

    url = f"{BASE}/Arquivos_csv_{ano}.zip"
    print(f"  baixando   {url}")
    with urllib.request.urlopen(url, timeout=900) as resposta:
        total = int(resposta.headers.get("content-length", 0))
        baixado = 0
        with open(destino, "wb") as saida:
            while pedaco := resposta.read(1 << 20):
                saida.write(pedaco)
                baixado += len(pedaco)
                if total:
                    print(f"\r  baixando   {baixado / 1e6:5.0f} / {total / 1e6:.0f} MB",
                          end="", flush=True)
    print()
    return destino


def _abrir(zf: zipfile.ZipFile, sufixo: str):
    """Abre o CSV do zip que termina em `sufixo`. Os arquivos são UTF-16."""
    nomes = [n for n in zf.namelist() if n.endswith(sufixo)]
    if not nomes:
        raise SystemExit(f"ERRO: não achei nenhum arquivo *{sufixo} no zip.")
    import io

    return csv.DictReader(
        io.TextIOWrapper(zf.open(nomes[0]), encoding="utf-16"), delimiter=";"
    )


def montar(caminho_zip: Path, n_alvo: int, semente: int) -> list[dict]:
    csv.field_size_limit(sys.maxsize)
    with zipfile.ZipFile(caminho_zip) as zf:
        print("  lendo      Recursos (o gabarito)")
        recursos: dict[str, int] = Counter()
        for linha in _abrir(zf, "_Recursos_csv_" + caminho_zip.stem[-4:] + ".csv"):
            recursos[linha["IdPedido"].strip()] += 1

        print(f"  lendo      Pedidos ({len(recursos)} pedidos tiveram recurso)")
        baldes: dict[str, list[dict]] = defaultdict(list)
        lidos = 0
        for linha in _abrir(zf, "_Pedidos_csv_" + caminho_zip.stem[-4:] + ".csv"):
            lidos += 1
            decisao = (linha["Decisao"] or "").strip()
            if decisao not in COTAS:
                continue
            pedido = limpar(linha["DetalhamentoSolicitacao"])
            resposta = limpar(linha["Resposta"])
            if not (MIN_PEDIDO <= len(pedido) <= MAX_PEDIDO):
                continue
            if not (MIN_RESPOSTA <= len(resposta) <= MAX_RESPOSTA):
                continue
            id_pedido = linha["IdPedido"].strip()
            baldes[decisao].append(
                {
                    "protocolo": linha["ProtocoloPedido"].strip(),
                    "orgao": limpar(linha["OrgaoDestinatario"]),
                    "esfera": limpar(linha["Esfera"]),
                    "data_registro": limpar(linha["DataRegistro"]),
                    "assunto": limpar(linha["AssuntoPedido"]),
                    "subassunto": limpar(linha["SubAssuntoPedido"]),
                    "resumo": limpar(linha["ResumoSolicitacao"]),
                    "pedido": pedido,
                    "data_resposta": limpar(linha["DataResposta"]),
                    "resposta": resposta,
                    "decisao": decisao,
                    "especificacao_decisao": limpar(linha["EspecificacaoDecisao"]),
                    "detalhamento_decisao": limpar(linha["DetalhamentoDecisao"]),
                    "motivo_negativa": limpar(linha["MotivoNegativaAcesso"]),
                    "foi_prorrogado": limpar(linha["FoiProrrogado"]),
                    # --- gabarito: pedidos.py não entrega isto ao modelo ---
                    "houve_recurso": recursos.get(id_pedido, 0) > 0,
                    "qtd_recursos": recursos.get(id_pedido, 0),
                }
            )
        print(f"  lidos      {lidos} pedidos; {sum(map(len, baldes.values()))} elegíveis")

    rnd = random.Random(semente)
    escala = n_alvo / sum(COTAS.values())
    amostra: list[dict] = []
    for decisao, cota in COTAS.items():
        candidatos = baldes.get(decisao, [])
        # Metade com recurso, metade sem, sempre que a base permitir: assim o
        # gabarito não fica todo do mesmo lado.
        com = [p for p in candidatos if p["houve_recurso"]]
        sem = [p for p in candidatos if not p["houve_recurso"]]
        rnd.shuffle(com)
        rnd.shuffle(sem)
        quero = max(1, round(cota * escala))
        metade = quero // 2
        escolhidos = com[:metade] + sem[: quero - metade]
        if len(escolhidos) < quero:
            resto = [p for p in candidatos if p not in escolhidos]
            rnd.shuffle(resto)
            escolhidos += resto[: quero - len(escolhidos)]
        amostra += escolhidos

    rnd.shuffle(amostra)
    return amostra


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--ano", type=int, default=2025)
    p.add_argument("--n", type=int, default=60, help="tamanho da amostra")
    p.add_argument("--semente", type=int, default=2173)
    args = p.parse_args()

    print(f"\nLAI {args.ano} — CGU/FalaBR\n")
    caminho = baixar_zip(args.ano)
    amostra = montar(caminho, args.n, args.semente)

    with open(SAIDA, "w", encoding="utf-8") as f:
        for pedido in amostra:
            f.write(json.dumps(pedido, ensure_ascii=False) + "\n")

    decisoes = Counter(p["decisao"] for p in amostra)
    recursos = sum(1 for p in amostra if p["houve_recurso"])
    print(f"\n  escrito    {SAIDA.relative_to(AQUI.parent.parent.parent)} "
          f"({SAIDA.stat().st_size / 1024:.0f} KB, {len(amostra)} pedidos)")
    for decisao, quantos in decisoes.most_common():
        print(f"    {quantos:>3}  {decisao}")
    print(f"\n  gabarito   {recursos} dos {len(amostra)} viraram recurso "
          f"({recursos / len(amostra):.0%})\n")


if __name__ == "__main__":
    main()
