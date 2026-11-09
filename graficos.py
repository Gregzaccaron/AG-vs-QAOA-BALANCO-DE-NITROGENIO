"""Gera as figuras da seção de Resultados, em PDF (vetorial) e PNG.

As quatro figuras são as exigidas pela orientação: convergência, desvio em
função do tamanho da instância, tempo em função do tamanho e efeito do número
de camadas do ansatz.

Gramática visual
----------------
As figuras vão para um artigo ABNT que pode ser **impresso em preto e
branco**, então a identidade de cada série nunca depende apenas da cor:

* **cor** = método (azul para o algoritmo genético, laranja para o QAOA)
* **estilo de linha** = conhecimento da restrição
  (**tracejado** ignora a alocação única, **sólido** a preserva)
* **marcador** = terceiro canal redundante (círculo/quadrado, vazado/cheio)

As duas cores foram validadas como par categórico: separação CVD ΔE 24,7
(alvo ≥ 8) e visão normal ΔE 33,6 (piso ≥ 15), ambas com contraste ≥ 3:1
contra o fundo. Usar dois matizes em vez de quatro, e carregar a segunda
dimensão no traço, é o que faz a figura sobreviver à fotocópia.

Uso
---
    python graficos.py                 # todas as figuras
    python graficos.py --so-convergencia
    python graficos.py --sem-historico  # não regera os dados de convergência
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# --- identidade visual ----------------------------------------------------

AZUL = "#2a78d6"
LARANJA = "#eb6834"
TINTA = "#0b0b0b"
TINTA_FRACA = "#52514e"
GRADE = "#e3e3e0"

# --- escala dos paineis lado a lado ---------------------------------------
#
# As figuras ``desvio_por_tamanho`` e ``tempo_por_tamanho`` entram no artigo
# lado a lado, cada uma num ``minipage`` de 0,49 da mancha. Desenha-las com
# 6,3 polegadas e deixar o LaTeX reduzir a 49% encolhia junto TODA a
# tipografia: uma fonte de 9 pt saia com 4,4 pt no papel, e o parecer do
# orientador (09/11/2026) apontou a figura como ilegivel.
#
# A correcao e desenhar ja no tamanho final, de modo que 1 pt aqui seja 1 pt
# impresso. A area ocupada na pagina nao muda em nada -- largura e altura sao
# multiplicadas pelo mesmo 0,49 que o LaTeX aplicaria --, so a letra cresce.

#: Mancha do template UNESC: 21 cm de papel menos 3 cm e 2 cm = 16 cm.
LARGURA_MANCHA_POL = 6.3
#: Fracao da mancha que cada painel ocupa (o ``minipage`` de 0.49).
ESCALA_PAINEL = 0.49
LARGURA_PAINEL_POL = LARGURA_MANCHA_POL * ESCALA_PAINEL  # 3,09 pol

#: Altura NOMINAL de cada painel, em polegadas. Nao e a altura impressa: o
#: ``bbox_inches="tight"`` do ``salvar`` acrescenta o que fica fora dos eixos
#: (legenda, rotulos, titulo). Estes dois valores foram CALIBRADOS para que a
#: altura final do arquivo seja a mesma que as figuras tinham antes de passarem
#: a ser desenhadas em tamanho real: 2,254 pol o painel (a) e 1,666 pol o (b).
#: Mexer na legenda ou nos rotulos exige recalibrar.
ALTURA_NOMINAL_A = 1.90
ALTURA_NOMINAL_B = 1.26

#: Tipografia dos paineis, em pontos JA IMPRESSOS.
PT_ROTULO = 7.5
PT_TICK = 7.0
PT_LEGENDA = 6.5
PT_ANOTACAO = 6.0
PT_NOTA = 6.5

#: Um estilo por método. ``mfc`` vazado marca a variante que ignora a
#: restrição; preenchido, a que a preserva.
ESTILOS: dict[str, dict] = {
    "AG": dict(cor=AZUL, ls="--", marker="o", mfc="white",
               rotulo="AG padrão"),
    "AG-VIAVEL": dict(cor=AZUL, ls="-", marker="o", mfc=AZUL,
                      rotulo="AG viável"),
    "QAOA": dict(cor=LARANJA, ls="--", marker="s", mfc="white",
                 rotulo="QAOA mixer X"),
    "QAOA-XY": dict(cor=LARANJA, ls="-", marker="s", mfc=LARANJA,
                    rotulo="QAOA mixer XY"),
}
ORDEM = ["AG", "AG-VIAVEL", "QAOA", "QAOA-XY"]

#: Deslocamento do rótulo direto do último ponto, em pontos tipográficos.
#: Os dois braços do QAOA terminam ambos em 24 qubits e, em escala
#: logarítmica, 914 s e 1.263 s caem quase na mesma altura: um rótulo sobe,
#: o outro desce, senão colidem.
DESLOC_ROTULO: dict[str, tuple[float, float]] = {
    "QAOA": (2, -7),
    "QAOA-XY": (2, 7),
    "AG": (3, -4),
    "AG-VIAVEL": (3, 4),
}

SAIDA = Path("resultados/figuras")
COMPARATIVO = Path("resultados/comparativo.csv")
HISTORICOS = Path("resultados/historicos.json")


def preparar_estilo() -> None:
    """Tipografia e cromo discretos, compatíveis com o corpo do texto."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "legend.fontsize": 8.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "axes.edgecolor": TINTA_FRACA,
        "axes.labelcolor": TINTA,
        "text.color": TINTA,
        "xtick.color": TINTA_FRACA,
        "ytick.color": TINTA_FRACA,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "figure.dpi": 110,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
    })


def estilo_painel() -> None:
    """Tipografia para figura desenhada no tamanho final impresso.

    Vale para os dois paineis lado a lado. Como nao ha reducao pelo LaTeX,
    os pontos aqui sao os pontos que saem no papel.
    """
    preparar_estilo()
    plt.rcParams.update({
        "font.size": PT_ROTULO,
        "axes.labelsize": PT_ROTULO,
        "axes.titlesize": PT_ROTULO,
        "legend.fontsize": PT_LEGENDA,
        "xtick.labelsize": PT_TICK,
        "ytick.labelsize": PT_TICK,
        "xtick.major.size": 2.0,
        "ytick.major.size": 2.0,
        "xtick.major.pad": 2.0,
        "ytick.major.pad": 2.0,
        "axes.labelpad": 2.0,
    })


def enfeitar(ax, *, eixo_grade: str = "y") -> None:
    """Grade em fio sólido, nunca tracejada, e sem molduras supérfluas."""
    ax.grid(axis=eixo_grade, color=GRADE, linewidth=0.6, linestyle="-")
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)


def salvar(fig, nome: str) -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        caminho = SAIDA / f"{nome}.{ext}"
        fig.savefig(caminho, dpi=200 if ext == "png" else None,
                    bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print(f"  {SAIDA / nome}.pdf  +  .png")


# --- leitura dos dados ----------------------------------------------------

def ler_comparativo() -> list[dict]:
    if not COMPARATIVO.exists():
        raise SystemExit(f"{COMPARATIVO} não existe. Rode o experimento antes.")
    with COMPARATIVO.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ler_varredura() -> list[dict]:
    """Junta os CSVs da varredura de p, cada um gravado num arquivo próprio.

    A chave de retomada do experimento é (instância, método, execução) e não
    inclui o ``p``; rodar a varredura num único arquivo faria a segunda
    chamada pular tudo. Daí um arquivo por valor de p.
    """
    linhas = []
    for caminho in sorted(Path("resultados").glob("varredura_p*.csv")):
        achado = re.search(r"varredura_p(\d+)", caminho.name)
        if not achado:
            continue
        p = int(achado.group(1))
        with caminho.open(encoding="utf-8", newline="") as f:
            for linha in csv.DictReader(f):
                linha["p_varredura"] = p
                linhas.append(linha)
    return linhas


def agregar(linhas: list[dict], chave) -> dict:
    """Média do desvio e do tempo, e contagem de acertos, por chave."""
    grupos = defaultdict(list)
    for linha in linhas:
        grupos[chave(linha)].append(linha)
    saida = {}
    for k, v in grupos.items():
        desvios = [float(r["desvio_percentual"]) for r in v
                   if r["desvio_percentual"]]
        saida[k] = {
            "n": len(v),
            "desvio": float(np.mean(desvios)) if desvios else float("nan"),
            "desvio_dp": float(np.std(desvios, ddof=1)) if len(desvios) > 1
            else 0.0,
            "tempo": float(np.mean([float(r["tempo_s"]) for r in v])),
            "acertos": sum(int(r["atingiu_otimo"] or 0) for r in v),
        }
    return saida


# --- dados de convergência ------------------------------------------------

def gerar_historicos(n_culturas: int = 4) -> dict:
    """Roda UMA execução de cada método e guarda o histórico de convergência.

    O CSV guarda só escalares por execução; a trajetória interna não é
    persistida. Como a instância de 16 qubits custa segundos, é mais simples
    regerá-la aqui do que inflar o CSV principal.
    """
    from algoritmo_genetico import ConfiguracaoAG, executar_ag
    from parametros import CENARIOS_POR_TAMANHO
    from qaoa_rotacao import executar_qaoa
    from qubo_rotacao import ModeloQUBO

    modelo = ModeloQUBO(culturas=CENARIOS_POR_TAMANHO[n_culturas],
                        n_periodos=4)
    _x, otimo = modelo.otimo_global()
    dados = {"n_qubits": modelo.n_variaveis, "otimo": float(otimo),
             "series": {}}

    for rotulo, viavel in (("AG", False), ("AG-VIAVEL", True)):
        r = executar_ag(modelo,
                        cfg=ConfiguracaoAG(preserva_viabilidade=viavel),
                        seed=42)
        # O histórico do AG é o melhor custo por geração; o eixo x é
        # convertido para avaliações da função objetivo, que é a unidade
        # comparável entre os dois métodos.
        por_geracao = max(1, r.n_avaliacoes // max(1, len(r.historico)))
        dados["series"][rotulo] = {
            "x": [(i + 1) * por_geracao for i in range(len(r.historico))],
            "y": [float(v) for v in r.historico],
            "grandeza": "melhor custo encontrado",
        }
        print(f"  {rotulo}: {len(r.historico)} gerações, "
              f"{r.n_avaliacoes} avaliações, melhor {r.melhor_custo:.2f}")

    for rotulo, mixer in (("QAOA", "X"), ("QAOA-XY", "XY")):
        r = executar_qaoa(modelo, p=2, maxiter=100, n_reinicios=3, seed=42,
                          mixer=mixer, threads=8)
        # ``r.historico`` JÁ vem na escala do custo QUBO: o executar_qaoa
        # aplica ``para_escala_qubo`` a cada valor antes de devolver. A versão
        # anterior multiplicava de novo por max|coef|, e o resultado ficava
        # 1.107 vezes maior que o verdadeiro. Dava para perceber pelo próprio
        # gráfico: a série do QAOA ia de 7,3e6 a 1,09e7 numa instância cuja
        # energia máxima possível é 30.164,88. Corrigido em 08/11/2026.
        dados["series"][rotulo] = {
            "x": list(range(1, len(r.historico) + 1)),
            "y": [float(v) for v in r.historico],
            "grandeza": "valor esperado da energia",
        }
        print(f"  {rotulo}: {len(r.historico)} avaliações, "
              f"melhor {r.melhor_custo:.2f}")

    HISTORICOS.parent.mkdir(parents=True, exist_ok=True)
    HISTORICOS.write_text(json.dumps(dados, indent=1), encoding="utf-8")
    return dados


# --- figuras --------------------------------------------------------------

def fig_convergencia(dados: dict) -> None:
    """Dois painéis, porque as duas grandezas NÃO são a mesma coisa.

    O algoritmo genético tem um incumbente: o melhor indivíduo já encontrado,
    uma escada monotonicamente decrescente. O QAOA não tem incumbente durante
    a otimização -- o que o otimizador clássico enxerga é o **valor esperado**
    da energia, uma média sobre toda a distribuição, que não é monotônica e
    não é o custo de nenhuma solução específica. Colocar as duas no mesmo eixo
    seria comparar grandezas diferentes; daí dois painéis, cada um com seu
    rótulo de ordenada.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.3, 2.9),
                                   gridspec_kw={"wspace": 0.42})
    otimo = dados["otimo"]

    for ax, metodos, titulo, rotulo_y in (
        (ax1, ("AG", "AG-VIAVEL"), "Algoritmo genético",
         "Melhor custo encontrado"),
        (ax2, ("QAOA", "QAOA-XY"), "QAOA",
         "Valor esperado da energia"),
    ):
        for metodo in metodos:
            s = dados["series"].get(metodo)
            if not s:
                continue
            e = ESTILOS[metodo]
            ax.plot(s["x"], s["y"], color=e["cor"], linestyle=e["ls"],
                    linewidth=1.8, marker=e["marker"], markersize=4.5,
                    markerfacecolor=e["mfc"], markeredgecolor=e["cor"],
                    markeredgewidth=1.1, markevery=max(1, len(s["x"]) // 7),
                    label=e["rotulo"], clip_on=True)
        # A linha do ótimo só cabe no painel do AG: ali a ordenada é o custo
        # de uma solução concreta. No painel do QAOA a ordenada é a média da
        # energia sobre toda a distribuição, penalidades incluídas, uma
        # grandeza que não é comparável com o custo do melhor plano.
        # A escala do painel do QAOA é de 10^3 a 10^4, e não 10^6 como dizia
        # este comentário: os 10^6 eram efeito da multiplicação dupla pela
        # escala, corrigida em 08/11/2026 na função gerar_historicos.
        if ax is ax1:
            ax.axhline(otimo, color=TINTA_FRACA, linewidth=0.8)
            ax.annotate(f"ótimo = {otimo:.2f}".replace(".", ","),
                        xy=(0.98, otimo), xycoords=("axes fraction", "data"),
                        xytext=(0, 4), textcoords="offset points",
                        ha="right", va="bottom", fontsize=7.5,
                        color=TINTA_FRACA)
        else:
            ax.set_yscale("log")
        ax.set_xscale("log")
        ax.set_xlabel("Avaliações da função objetivo")
        ax.set_ylabel(rotulo_y)
        ax.set_title(titulo, color=TINTA)
        enfeitar(ax)
        # No painel do QAOA as duas curvas ocupam o alto e o pé do quadro;
        # a legenda cabe no miolo à esquerda, onde não há dado nenhum.
        ax.legend(frameon=False,
                  loc="upper right" if ax is ax1 else "center left",
                  fontsize=8)

    fig.suptitle(f"Convergência em {dados['n_qubits']} qubits", y=1.04,
                 fontsize=10)
    salvar(fig, "convergencia")


def fig_desvio(agg: dict, tamanhos: list[int]) -> None:
    """Desvio do ótimo por tamanho, em dois painéis com a mesma abscissa.

    Um painel só não resolve. O QAOA com mixer X chega a 361,6 % em 24
    qubits, enquanto o AG padrão fica entre 1,6 % e 7,3 %. Num eixo que
    precisa alcançar 361, a diferença entre 1,6 e 7,3 tem meio pixel de
    altura -- e é justamente ela que mostra o AG se degradando conforme a
    instância cresce. Daí os dois painéis: em cima a escala inteira, em
    baixo a faixa onde vivem três das quatro séries.

    Isto não é um eixo quebrado. São duas vistas completas dos mesmos
    dados, cada uma com o seu eixo rotulado de ponta a ponta, e as barras
    que estouram o painel de detalhe trazem o próprio valor impresso.

    Escala linear e não logarítmica: duas das quatro séries valem
    exatamente zero, que não existe em escala log.
    """
    estilo_painel()
    fig, (ax_todo, ax_zoom) = plt.subplots(
        2, 1,
        figsize=(LARGURA_PAINEL_POL, ALTURA_NOMINAL_A), sharex=True,
        gridspec_kw={"height_ratios": [1.0, 1.15], "hspace": 0.22})
    largura = 0.2
    base = np.arange(len(tamanhos))

    # Teto do painel de detalhe: folga sobre a maior barra que não é QAOA-X.
    miudas = [agg[(n, m)]["desvio"] for n in tamanhos for m in ORDEM
              if m != "QAOA" and (n, m) in agg]
    teto = max(miudas) * 1.45 if miudas else 1.0

    for ax in (ax_todo, ax_zoom):
        for i, metodo in enumerate(ORDEM):
            e = ESTILOS[metodo]
            alturas, posicoes = [], []
            for j, n in enumerate(tamanhos):
                d = agg.get((n, metodo))
                alturas.append(d["desvio"] if d else np.nan)
                posicoes.append(base[j] + (i - 1.5) * largura)
            vazado = e["mfc"] == "white"
            ax.bar(posicoes, alturas, largura * 0.88,
                   facecolor="white" if vazado else e["cor"],
                   edgecolor=e["cor"], linewidth=1.2,
                   label=e["rotulo"] if ax is ax_todo else "_nolegend_",
                   hatch="///" if vazado else None, zorder=3)
            for x, h in zip(posicoes, alturas):
                if np.isnan(h):
                    continue
                if h < 1e-9 and ax is ax_zoom:
                    # Barra de altura zero: sem rótulo direto, não se vê.
                    # Só no painel de detalhe -- na escala completa o
                    # rótulo flutuaria solto, longe de qualquer barra.
                    ax.annotate("0,00", xy=(x, 0), xytext=(0, 2),
                                textcoords="offset points", ha="center",
                                va="bottom", fontsize=PT_ANOTACAO,
                                rotation=90, color=e["cor"])
                elif ax is ax_zoom and h > teto:
                    # Barra que estoura o detalhe: diz o próprio valor,
                    # dentro da barra para não ser cortado pelo topo.
                    ax.annotate(f"{h:,.0f} %".replace(",", "."),
                                xy=(x, teto * 0.52), ha="center",
                                va="center", fontsize=PT_ANOTACAO,
                                rotation=90, color=e["cor"], zorder=4,
                                bbox=dict(facecolor="white", pad=0.8,
                                          edgecolor="none"))
        enfeitar(ax)
    # Um rótulo para os dois painéis: ver o comentário em ``estilo_painel``.
    fig.supylabel("Desvio do ótimo (%)", fontsize=PT_ROTULO, x=0.015)

    ax_zoom.set_ylim(0, teto)
    for ax, texto in ((ax_todo, "Escala completa"),
                      (ax_zoom, f"Detalhe: 0 a {teto:.0f} %")):
        ax.text(0.998, 0.97, texto, transform=ax.transAxes, va="top",
                ha="right", fontsize=PT_NOTA, color=TINTA_FRACA)

    ax_zoom.set_xticks(base)
    ax_zoom.set_xticklabels([f"{n}" for n in tamanhos])
    ax_zoom.set_xlabel("Variáveis binárias (qubits)")
    ax_todo.legend(frameon=False, ncols=2, loc="lower center",
                   bbox_to_anchor=(0.5, 1.0), fontsize=PT_LEGENDA,
                   columnspacing=1.0, handlelength=1.5,
                   handletextpad=0.5, labelspacing=0.3, borderpad=0.0)
    salvar(fig, "desvio_por_tamanho")
    preparar_estilo()


def fig_tempo(agg: dict, tamanhos: list[int]) -> None:
    """Tempo por execução, ordenada logarítmica.

    Log porque os valores cobrem cinco ordens de grandeza, de 8 ms a 620 s.
    Em escala linear as quatro curvas do AG colapsariam sobre o eixo.
    """
    estilo_painel()
    fig, ax = plt.subplots(
        figsize=(LARGURA_PAINEL_POL, ALTURA_NOMINAL_B))

    for metodo in ORDEM:
        e = ESTILOS[metodo]
        xs = [n for n in tamanhos if (n, metodo) in agg]
        ys = [agg[(n, metodo)]["tempo"] for n in xs]
        if not xs:
            continue
        ax.plot(xs, ys, color=e["cor"], linestyle=e["ls"], linewidth=1.2,
                marker=e["marker"], markersize=3.6, markerfacecolor=e["mfc"],
                markeredgecolor=e["cor"], markeredgewidth=0.9,
                label=e["rotulo"])
        # Rótulo direto apenas no último ponto de cada série.
        v = ys[-1]
        if v >= 100:
            txt = f"{v:,.0f}".replace(",", ".")
        elif v >= 1:
            txt = f"{v:.1f}".replace(".", ",")
        else:
            txt = f"{v:.4f}".rstrip("0").replace(".", ",")
        ax.annotate(txt + " s",
                    xy=(xs[-1], v), xytext=DESLOC_ROTULO.get(metodo, (3, 0)),
                    textcoords="offset points", va="center",
                    fontsize=PT_ANOTACAO, color=e["cor"])

    ax.set_yscale("log")
    ax.set_xticks(tamanhos)
    ax.set_xlim(min(tamanhos) - 1.2, max(tamanhos) + 5.5)
    ax.set_xlabel("Variáveis binárias (qubits)")
    ax.set_ylabel("Tempo por execução (s)")
    enfeitar(ax)
    # Legenda acima dos eixos: dentro do quadro ela colidia com os rótulos
    # diretos do último ponto de cada série, à direita.
    # O 1,0 encostava a legenda no rótulo direto de "1.263 s". O painel (b)
    # é o mais baixo do float e sobra altura, então a legenda sobe.
    ax.legend(frameon=False, ncols=2, loc="lower center",
              bbox_to_anchor=(0.5, 1.10), fontsize=PT_LEGENDA,
              columnspacing=1.0, handlelength=1.8,
              handletextpad=0.5, labelspacing=0.3, borderpad=0.0)
    salvar(fig, "tempo_por_tamanho")
    preparar_estilo()


def fig_camadas(linhas: list[dict]) -> None:
    """Efeito de p. Cor = tamanho da instância, traço = mixer."""
    if not linhas:
        print("  (sem CSVs de varredura de p -- figura omitida)")
        return

    fig, ax = plt.subplots(figsize=(6.3, 3.1))
    cores = {16: AZUL, 20: LARANJA}
    marcadores = {16: "o", 20: "s"}

    grupos = defaultdict(list)
    for r in linhas:
        if r["metodo"].startswith("QAOA"):
            grupos[(int(r["n_variaveis"]), r["metodo"],
                    r["p_varredura"])].append(r)

    for n in sorted(cores):
        for metodo, ls, cheio in (("QAOA", "--", False), ("QAOA-XY", "-", True)):
            ps = sorted({k[2] for k in grupos if k[0] == n and k[1] == metodo})
            if not ps:
                continue
            ys = [float(np.mean([float(r["desvio_percentual"])
                                 for r in grupos[(n, metodo, p)]]))
                  for p in ps]
            nome = "mixer X" if metodo == "QAOA" else "mixer XY"
            ax.plot(ps, ys, color=cores[n], linestyle=ls, linewidth=1.8,
                    marker=marcadores[n], markersize=6,
                    markerfacecolor=cores[n] if cheio else "white",
                    markeredgecolor=cores[n], markeredgewidth=1.3,
                    label=f"{n} qubits, {nome}")

    # As duas séries do mixer XY valem exatamente 0,00 % em todo p, nas duas
    # instâncias: ficam perfeitamente sobrepostas e a de baixo desaparece.
    # Sem este aviso o leitor conta três curvas numa legenda de quatro.
    ax.annotate("mixer XY: 0,00 % em todo $p$, nas duas instâncias "
                "(curvas sobrepostas)",
                xy=(0.5, 0.0), xycoords=("axes fraction", "data"),
                xytext=(0, 5), textcoords="offset points",
                ha="center", va="bottom", fontsize=7.5, color=TINTA_FRACA)

    ax.set_xticks(sorted({k[2] for k in grupos}))
    ax.set_xlabel("Camadas do ansatz ($p$)")
    ax.set_ylabel("Desvio do ótimo (%)")
    enfeitar(ax)
    ax.legend(frameon=False, loc="center right")
    salvar(fig, "efeito_das_camadas")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gera as figuras da seção de Resultados."
    )
    parser.add_argument("--sem-historico", action="store_true",
                        help="Não regera os dados de convergência; usa o "
                             "JSON existente, se houver.")
    parser.add_argument("--so-convergencia", action="store_true")
    args = parser.parse_args()

    preparar_estilo()

    if not args.sem_historico or not HISTORICOS.exists():
        print("Gerando dados de convergência (16 qubits):")
        dados = gerar_historicos()
    else:
        dados = json.loads(HISTORICOS.read_text(encoding="utf-8"))

    print("\nFiguras:")
    fig_convergencia(dados)
    if args.so_convergencia:
        return

    linhas = ler_comparativo()
    agg = agregar(linhas, lambda r: (int(r["n_variaveis"]), r["metodo"]))
    tamanhos = sorted({int(r["n_variaveis"]) for r in linhas})
    fig_desvio(agg, tamanhos)
    fig_tempo(agg, tamanhos)
    fig_camadas(ler_varredura())

    print(f"\nPronto. Use no LaTeX com, por exemplo:\n"
          f"  \\includegraphics[width=\\textwidth]"
          f"{{Figs/tempo_por_tamanho.pdf}}")


if __name__ == "__main__":
    main()
