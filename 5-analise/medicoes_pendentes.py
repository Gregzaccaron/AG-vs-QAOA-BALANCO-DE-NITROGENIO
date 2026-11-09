# -*- coding: utf-8 -*-
"""Mede as três coisas que faltam para fechar o texto do artigo.

Criado em 08/11/2026. Cada medição responde a uma pendência marcada no
TCC_2026-11-08.tex e não depende da célula de 24 qubits, por isso pode rodar
depois do experimento, sem competir com ele.

1. Massa de probabilidade fora do subespaço viável, por mixer. O valor antigo
   (0,994 para o mixer X) é anterior à correção da escala e é incompatível com
   as 30 alocações válidas em 30 execuções que o experimento novo mostra.
2. Qual reinício vence, e se isso explica a bimodalidade do mixer X.
3. Quanto o resultado varia ao repetir a MESMA semente. O mixer XY não é
   reprodutível bit a bit, e isso precisa ser declarado em Materiais e Métodos.

Uso:
    python medicoes_pendentes.py            # 16 e 20 qubits
    python medicoes_pendentes.py 4          # só 16 qubits
"""
from __future__ import annotations

import io
import json
import sys
import time

import numpy as np

from parametros import CENARIOS_POR_TAMANHO
from qaoa_rotacao import executar_qaoa
from qubo_rotacao import ModeloQUBO

SAIDA = "resultados/medicoes_pendentes.json"
P = 2
MAXITER = 100
REINICIOS = 3
SHOTS = 4096
THREADS = 8


def massa_inviavel(modelo: ModeloQUBO, mixer: str, seed: int) -> dict:
    """Probabilidade total fora do conjunto das alocações válidas.

    Reconstrói a distribuição exata nos parâmetros ótimos, e soma a
    probabilidade dos estados cuja decodificação não é uma alocação única.
    """
    r = executar_qaoa(modelo, p=P, maxiter=MAXITER, shots=SHOTS, seed=seed,
                      n_reinicios=REINICIOS, metodo_valor_esperado="diagonal",
                      mixer=mixer, threads=THREADS)
    # A distribuição exata não é devolvida pelo resultado; recalcula-se com os
    # mesmos parâmetros ótimos. Para o mixer XY o valor é zero por construção,
    # a menos do erro de Trotter, e serve de controle da medição.
    n = modelo.n_variaveis
    from qiskit import transpile
    from qiskit_aer import AerSimulator
    from qiskit.circuit.library import QAOAAnsatz
    from qaoa_rotacao import (construir_hamiltoniano, mixer_xy,
                              estado_inicial_onehot)

    H = construir_hamiltoniano(modelo)
    escala = float(np.max(np.abs(H.coeffs.real))) or 1.0
    if mixer.upper() == "XY":
        ansatz = QAOAAnsatz(cost_operator=H * (1.0 / escala), reps=P,
                            mixer_operator=mixer_xy(modelo),
                            initial_state=estado_inicial_onehot(modelo))
    else:
        ansatz = QAOAAnsatz(cost_operator=H * (1.0 / escala), reps=P)
    ansatz = ansatz.decompose(reps=4)

    bk = AerSimulator(method="statevector", max_parallel_threads=THREADS)
    circ = ansatz.copy()
    circ.save_statevector()
    circ = transpile(circ, bk)
    ligacoes = [{q: [v] for q, v in zip(ansatz.parameters, r.parametros_otimos)}]
    psi = np.asarray(bk.run(circ, parameter_binds=ligacoes)
                     .result().get_statevector())
    prob = np.abs(psi) ** 2

    # Varre os 2^n estados. Até 20 qubits isto custa menos de um segundo.
    massa = 0.0
    for idx in range(1 << n):
        x = np.array([(idx >> a) & 1 for a in range(n)], dtype=int)
        if not modelo.alocacao_valida(x):
            massa += prob[idx]
    return {
        "mixer": mixer,
        "semente": seed,
        "massa_inviavel": float(massa),
        "massa_viavel": float(1.0 - massa),
        "valor_esperado": float(r.valor_esperado),
        "prob_melhor": float(r.prob_melhor),
        "alocacao_valida_amostrada": bool(modelo.alocacao_valida(r.melhor_x)),
    }


def reinicio_vencedor(modelo: ModeloQUBO, mixer: str,
                      n: int = 10) -> list[dict]:
    """Registra qual reinício venceu, e se a execução achou o ótimo.

    O reinício 0 é o início adiabático, determinístico. Se as execuções que
    falham forem justamente as em que ele vence, a bimodalidade do mixer X se
    explica por ele, e não por condicionamento numérico.
    """
    linhas = []
    for k in range(n):
        r = executar_qaoa(modelo, p=P, maxiter=MAXITER, shots=SHOTS,
                          seed=42 + k, n_reinicios=REINICIOS,
                          metodo_valor_esperado="diagonal", mixer=mixer,
                          threads=THREADS)
        otimo = r.custo_minimo_global
        linhas.append({
            "semente": 42 + k,
            "reinicio_vencedor": int(r.reinicio_vencedor),
            "desvio_pct": float(100.0 * (r.melhor_custo - otimo) / otimo),
            "atingiu_otimo": bool(r.melhor_custo <= otimo + 1e-9),
            "valor_esperado": float(r.valor_esperado),
        })
    return linhas


def repetibilidade(modelo: ModeloQUBO, mixer: str, n: int = 5) -> dict:
    """Repete a MESMA semente e mede a dispersão do resultado."""
    vals, custos = [], []
    for _ in range(n):
        r = executar_qaoa(modelo, p=P, maxiter=MAXITER, shots=SHOTS, seed=42,
                          n_reinicios=REINICIOS,
                          metodo_valor_esperado="diagonal", mixer=mixer,
                          threads=THREADS)
        vals.append(float(r.valor_esperado))
        custos.append(float(r.melhor_custo))
    media = sum(vals) / len(vals)
    return {
        "mixer": mixer,
        "semente": 42,
        "repeticoes": n,
        "valores_esperados": vals,
        "custos": custos,
        "media": media,
        "amplitude": max(vals) - min(vals),
        "amplitude_relativa": (max(vals) - min(vals)) / media if media else 0.0,
        "valores_distintos": len(set(vals)),
        "custos_distintos": len(set(custos)),
    }


def main() -> None:
    quais = [int(a) for a in sys.argv[1:]] or [4, 5]
    tudo: dict = {"gerado_em": time.strftime("%Y-%m-%d %H:%M:%S"),
                  "parametros": {"p": P, "maxiter": MAXITER,
                                 "reinicios": REINICIOS, "shots": SHOTS}}

    for nc in quais:
        modelo = ModeloQUBO(culturas=CENARIOS_POR_TAMANHO[nc])
        rotulo = "%dq" % modelo.n_variaveis
        print()
        print("=" * 68)
        print(" %d culturas, %d qubits" % (nc, modelo.n_variaveis))
        print("=" * 68)
        bloco: dict = {}

        print()
        print("1. Massa fora do subespaco viavel")
        bloco["massa_inviavel"] = []
        for mixer in ("X", "XY"):
            d = massa_inviavel(modelo, mixer, 42)
            bloco["massa_inviavel"].append(d)
            print("   mixer %-3s massa inviavel %.6e   viavel %.6f"
                  % (mixer, d["massa_inviavel"], d["massa_viavel"]))

        print()
        print("2. Reinicio vencedor, 10 sementes, mixer X")
        linhas = reinicio_vencedor(modelo, "X", 10)
        bloco["reinicio_vencedor"] = linhas
        print("   %-8s %-10s %10s %s" % ("semente", "vencedor", "desvio%",
                                         "otimo?"))
        for l in linhas:
            print("   %-8d %-10d %9.2f%% %s"
                  % (l["semente"], l["reinicio_vencedor"], l["desvio_pct"],
                     "sim" if l["atingiu_otimo"] else "NAO"))
        venceu0 = [l for l in linhas if l["reinicio_vencedor"] == 0]
        falhou = [l for l in linhas if not l["atingiu_otimo"]]
        print()
        print("   reinicio 0 (adiabatico) venceu em %d de %d"
              % (len(venceu0), len(linhas)))
        print("   execucoes que NAO acharam o otimo: %d de %d"
              % (len(falhou), len(linhas)))
        if falhou:
            venc = sorted({l["reinicio_vencedor"] for l in falhou})
            print("   nas que falharam, o vencedor foi: %s"
                  % ", ".join(str(v) for v in venc))

        print()
        print("3. Repetibilidade da MESMA semente")
        bloco["repetibilidade"] = []
        for mixer in ("X", "XY"):
            d = repetibilidade(modelo, mixer, 5)
            bloco["repetibilidade"].append(d)
            print("   mixer %-3s %d valores distintos em %d repeticoes, "
                  "amplitude %.3e (%.3f%% da media)"
                  % (mixer, d["valores_distintos"], d["repeticoes"],
                     d["amplitude"], 100 * d["amplitude_relativa"]))
            print("        custo amostrado: %d valor(es) distinto(s)"
                  % d["custos_distintos"])

        tudo[rotulo] = bloco

    io.open(SAIDA, "w", encoding="utf-8", newline="\n").write(
        json.dumps(tudo, indent=2, ensure_ascii=False))
    print()
    print("Gravado em %s" % SAIDA)


if __name__ == "__main__":
    main()
