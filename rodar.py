# -*- coding: utf-8 -*-
"""Lançador interativo dos experimentos, para quem não conhece o código.

Existe para que a banca, ou qualquer pessoa que clone o repositório, possa
reproduzir os resultados sem precisar montar a linha de comando correta.
O ``experimento_comparativo.py`` tem dezesseis argumentos e vários padrões
que **não** são os do artigo; errar um deles produz resultado plausível e
diferente do publicado. Este arquivo monta os comandos certos.

Uso:

    python rodar.py

Ou, no Windows, clique duas vezes em ``RodarTeste.bat``.

Nada aqui altera o algoritmo. É só diagnóstico de máquina, aritmética de
estimativa e montagem de linha de comando.
"""
from __future__ import annotations

import ctypes
import os
import platform
import shutil
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTO = os.path.join(AQUI, "experimento_comparativo.py")
SAIDAS = os.path.join(AQUI, "resultados")

# ---------------------------------------------------------------------------
# Dados medidos nesta máquina em 08/11/2026, com p=2, 8 threads, precisão
# dupla, 3 reinícios e maxiter 100. Servem apenas para estimar duração antes
# de começar, e por isso estão aqui e não no código do experimento.
# Em outra máquina as estimativas erram proporcionalmente, o que ainda é
# melhor que não ter estimativa nenhuma.
# ---------------------------------------------------------------------------
SEG_POR_EXEC = {
    # n_qubits: {metodo: segundos}
    16: {"AG": 0.007, "AG-VIAVEL": 0.030, "QAOA": 5.47, "QAOA-XY": 10.42},
    20: {"AG": 0.008, "AG-VIAVEL": 0.029, "QAOA": 30.38, "QAOA-XY": 44.64},
    24: {"AG": 0.009, "AG-VIAVEL": 0.030, "QAOA": 914.07, "QAOA-XY": 1245.76},
    # 28 qubits nunca foi executado; a estimativa vem do custo medido por
    # avaliação (123,2 s) multiplicado pelas 300 avaliações de uma execução.
    28: {"AG": 0.010, "AG-VIAVEL": 0.030, "QAOA": 36960.0, "QAOA-XY": 50400.0},
    32: {"AG": 0.011, "AG-VIAVEL": 0.031, "QAOA": None, "QAOA-XY": None},
}

CULTURAS_POR_QUBITS = {16: 4, 20: 5, 24: 6, 28: 7, 32: 8}
BYTES_POR_AMPLITUDE = {"double": 16, "single": 8}

# Folga sobre o tamanho do vetor de estado. O Aer mantém cópias de trabalho
# durante a aplicação das portas e durante o save_statevector.
FOLGA_AER = 2.2


# ---------------------------------------------------------------------------
# Diagnóstico da máquina
# ---------------------------------------------------------------------------
class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def memoria_gb() -> tuple[float | None, float | None]:
    """(total, disponível) em GB. Tenta psutil, cai para a API do Windows."""
    try:
        import psutil  # opcional; não é dependência do projeto
        vm = psutil.virtual_memory()
        return vm.total / 2**30, vm.available / 2**30
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            estado = _MEMORYSTATUSEX()
            estado.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(estado))
            return estado.ullTotalPhys / 2**30, estado.ullAvailPhys / 2**30
        except Exception:
            pass
    try:  # Linux
        with open("/proc/meminfo") as f:
            info = {}
            for linha in f:
                partes = linha.split()
                if len(partes) >= 2:
                    info[partes[0].rstrip(":")] = int(partes[1])
        return info["MemTotal"] / 2**20, info.get(
            "MemAvailable", info["MemFree"]) / 2**20
    except Exception:
        return None, None


def nucleos() -> tuple[int | None, int]:
    """(físicos, lógicos). Físicos pode vir None se não houver como saber."""
    logicos = os.cpu_count() or 1
    fisicos = None
    try:
        import psutil
        fisicos = psutil.cpu_count(logical=False)
    except Exception:
        if sys.platform == "win32":
            try:
                saida = subprocess.run(
                    ["wmic", "cpu", "get", "NumberOfCores", "/value"],
                    capture_output=True, text=True, timeout=10,
                ).stdout
                valores = [int(l.split("=")[1]) for l in saida.splitlines()
                           if l.strip().startswith("NumberOfCores=")]
                if valores:
                    fisicos = sum(valores)
            except Exception:
                pass
    return fisicos, logicos


def nome_processador() -> str:
    nome = platform.processor() or ""
    if sys.platform == "win32" and (not nome or "Family" in nome):
        try:
            saida = subprocess.run(
                ["wmic", "cpu", "get", "Name", "/value"],
                capture_output=True, text=True, timeout=10,
            ).stdout
            for linha in saida.splitlines():
                if linha.strip().startswith("Name="):
                    return linha.split("=", 1)[1].strip()
        except Exception:
            pass
    return nome or platform.machine() or "desconhecido"


def versao(modulo: str) -> str:
    try:
        mod = __import__(modulo)
        return getattr(mod, "__version__", "?")
    except Exception:
        return "AUSENTE"


def diagnostico() -> dict:
    fisicos, logicos = nucleos()
    total, disp = memoria_gb()
    return {
        "cpu": nome_processador(),
        "fisicos": fisicos,
        "logicos": logicos,
        "ram_total": total,
        "ram_disp": disp,
        "so": "%s %s" % (platform.system(), platform.release()),
        "python": platform.python_version(),
        "libs": {m: versao(m) for m in ("numpy", "scipy", "qiskit")},
    }


def threads_recomendado(fisicos: int | None, logicos: int) -> int:
    """8 foi o melhor medido em 24 qubits nesta máquina.

    Em máquinas menores, 8 pode ser mais que o disponível; não faz sentido
    pedir mais threads que núcleos físicos.
    """
    teto = fisicos or max(1, logicos // 2)
    return max(1, min(8, teto))


def imprimir_diagnostico(d: dict) -> None:
    print()
    print("=" * 72)
    print(" MÁQUINA")
    print("=" * 72)
    print("  Processador .......... %s" % d["cpu"])
    if d["fisicos"]:
        print("  Núcleos .............. %d físicos, %d threads lógicas"
              % (d["fisicos"], d["logicos"]))
    else:
        print("  Núcleos .............. %d threads lógicas (físicos: não "
              "detectados)" % d["logicos"])
    if d["ram_total"]:
        print("  Memória .............. %.1f GB no total, %.1f GB livres agora"
              % (d["ram_total"], d["ram_disp"]))
    else:
        print("  Memória .............. não detectada")
    print("  Sistema .............. %s" % d["so"])
    print("  Python ............... %s" % d["python"])
    faltando = [m for m, v in d["libs"].items() if v == "AUSENTE"]
    print("  Bibliotecas .......... " + ", ".join(
        "%s %s" % (m, v) for m, v in d["libs"].items()))
    if faltando:
        print()
        print("  ** Falta instalar: %s" % ", ".join(faltando))
        print("     pip install -r requirements.txt")


def imprimir_capacidade(d: dict, precisao: str = "double") -> None:
    """O que esta máquina aguenta, instância por instância."""
    disp = d["ram_disp"] or 0.0
    bpa = BYTES_POR_AMPLITUDE[precisao]
    print()
    print("=" * 72)
    print(" O QUE ESTA MÁQUINA AGUENTA  (precisão %s)" % precisao)
    print("=" * 72)
    print("  %-7s %-9s %9s %9s %11s  %s"
          % ("Qubits", "Culturas", "Vetor", "C/ folga", "1 exec. QAOA",
             "Veredito"))
    print("  " + "-" * 68)
    for q in sorted(CULTURAS_POR_QUBITS):
        vetor = (2 ** q) * bpa / 2**30
        preciso = vetor * FOLGA_AER
        s = SEG_POR_EXEC[q]["QAOA-XY"]
        tempo = fmt_duracao(s) if s else "--"
        if disp and preciso > disp:
            veredito = "não cabe na memória"
        elif s is None:
            veredito = "não medido"
        elif s > 3600:
            veredito = "cabe, mas é inviável"
        else:
            veredito = "ok"
        print("  %-7d %-9d %8.2fG %8.2fG %11s  %s"
              % (q, CULTURAS_POR_QUBITS[q], vetor, preciso, tempo, veredito))
    print()
    print("  A coluna de tempo é por UMA execução do QAOA com mixer XY, o")
    print("  caso mais caro, medido nesta máquina com 8 threads. O artigo usa")
    print("  30 execuções por célula e dois mixers, então a célula inteira")
    print("  custa 30 x (tempo do X + tempo do XY).")
    # 30 x (36.960 s + 50.400 s) = 2.620.800 s = 30,3 dias. A versão anterior
    # deste texto dizia 60 dias, por contar os dois mixers duas vezes.
    s_x = SEG_POR_EXEC[28]["QAOA"]
    s_xy = SEG_POR_EXEC[28]["QAOA-XY"]
    if s_x and s_xy:
        print("  É por isso que 28 qubits cabe na memória e ainda assim não")
        print("  foi executado: a célula custaria %.0f dias de simulação."
              % (30 * (s_x + s_xy) / 86400))
    print()
    print("  O algoritmo genético roda em todas as instâncias em")
    print("  milissegundos: ele não simula estado quântico, logo nada disto")
    print("  o limita, e é por isso que ele cobre as cinco instâncias.")


def fmt_duracao(seg: float) -> str:
    if seg < 90:
        return "%.0f s" % seg
    if seg < 5400:
        return "%.0f min" % (seg / 60)
    return "%.1f h" % (seg / 3600)


# ---------------------------------------------------------------------------
# Estimativa
# ---------------------------------------------------------------------------
def estimar(qubits_max: int, execucoes: int, mixers: list[str],
            ags: list[str], p: int = 2, processos: int = 1) -> float:
    """Segundos de parede previstos. Aproxima o efeito de p linearmente."""
    total = 0.0
    for q in sorted(CULTURAS_POR_QUBITS):
        for metodo in ("AG", "AG-VIAVEL"):
            if metodo == "AG" and "padrao" not in ags:
                continue
            if metodo == "AG-VIAVEL" and "viavel" not in ags:
                continue
            total += SEG_POR_EXEC[q][metodo] * execucoes
        if q > qubits_max:
            continue
        for mixer in mixers:
            chave = "QAOA" if mixer.upper() == "X" else "QAOA-XY"
            s = SEG_POR_EXEC[q][chave]
            if s is None:
                continue
            total += s * execucoes * (p / 2.0)
    return total / max(1, processos)


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------
def rodar(args: list[str], descricao: str) -> int:
    cmd = [sys.executable, EXPERIMENTO] + args
    print()
    print("-" * 72)
    print(" " + descricao)
    print("-" * 72)
    print("  " + " ".join(cmd[1:]))
    print()
    t0 = time.time()
    try:
        cod = subprocess.call(cmd, cwd=AQUI)
    except KeyboardInterrupt:
        print()
        print("  Interrompido. O CSV guarda tudo que já foi gravado; repetir")
        print("  o mesmo comando SEM --recomecar continua de onde parou.")
        return 130
    print()
    print("  Terminou em %s (código %d)" % (fmt_duracao(time.time() - t0), cod))
    return cod


def rodar_paralelo(execucoes: int, qubits_max: int, mixers: list[str],
                   processos: int, threads: int, p: int = 2) -> None:
    """Divide as execuções entre processos isolados, cada um com seu CSV.

    A divisão respeita a semente: o experimento usa ``seed = seed_base + k``,
    então processos com seed_base 42, 42+n, 42+2n cobrem exatamente as mesmas
    sementes que uma execução serial de 42 em diante. As colunas de QUALIDADE
    saem idênticas às da execução serial.

    A coluna de TEMPO não sai idêntica, e é por isso que este modo avisa
    antes de começar.
    """
    por_processo = execucoes // processos
    resto = execucoes % processos
    if por_processo == 0:
        print("  Execuções demais para dividir: %d processos para %d execuções."
              % (processos, execucoes))
        return

    print()
    print("=" * 72)
    print(" MODO PARALELO")
    print("=" * 72)
    print("  %d processos isolados, %d threads cada (%d threads no total)."
          % (processos, threads, processos * threads))
    print("  Cada processo grava o seu próprio CSV, em resultados/parcial_N.csv.")
    print()
    print("  AVISO IMPORTANTE, leia antes de escolher este modo:")
    print()
    print("  As colunas de qualidade (desvio, ótimos, probabilidade) saem")
    print("  IDÊNTICAS às da execução serial, porque a semente de cada")
    print("  execução é a mesma. Já a coluna de tempo NÃO sai comparável: os")
    print("  processos disputam memória e cache, e cada execução fica mais")
    print("  lenta do que ficaria sozinha. Esse atraso não é recuperável por")
    print("  multiplicação, porque não é um fator constante.")
    print()
    print("  Portanto: use este modo para obter qualidade depressa, e meça")
    print("  tempo numa passada separada, com um processo só (opção 3 ou 4 do")
    print("  menu) e poucas execuções. Foi assim que os tempos do artigo")
    print("  foram medidos.")
    print()
    if input("  Entendido? [s/N] ").strip().lower() not in ("s", "sim", "y"):
        print("  Cancelado.")
        return

    os.makedirs(SAIDAS, exist_ok=True)
    procs = []
    base = 42
    for i in range(processos):
        n = por_processo + (1 if i < resto else 0)
        saida = os.path.join("resultados", "parcial_%d.csv" % (i + 1))
        args = [
            "--execucoes", str(n),
            "--seed-base", str(base),
            "--ags", "padrao", "viavel",
            "--mixers", *mixers,
            "--qaoa-p", str(p),
            "--qaoa-maxiter", "100",
            "--qaoa-reinicios", "3",
            "--qaoa-shots", "4096",
            "--max-qubits-qaoa", str(qubits_max),
            "--threads", str(threads),
            "--recomecar",
            "--saida", saida,
            "--log", os.path.join("resultados", "parcial_%d.log" % (i + 1)),
        ]
        cmd = [sys.executable, EXPERIMENTO] + args
        print("  processo %d: sementes %d a %d  ->  %s"
              % (i + 1, base, base + n - 1, saida))
        procs.append(subprocess.Popen(cmd, cwd=AQUI))
        base += n

    print()
    print("  %d processos no ar. Aguardando..." % len(procs))
    t0 = time.time()
    try:
        for pr in procs:
            pr.wait()
    except KeyboardInterrupt:
        print("\n  Interrompendo todos...")
        for pr in procs:
            pr.terminate()
        return
    print("  Todos terminaram em %s." % fmt_duracao(time.time() - t0))
    juntar([os.path.join(SAIDAS, "parcial_%d.csv" % (i + 1))
            for i in range(processos)])


def juntar(arquivos: list[str],
           destino: str | None = None) -> None:
    """Concatena CSVs parciais renumerando a coluna ``execucao``.

    Sem renumerar, os três parciais trariam execucao 0..n-1 cada um, e a
    junção pareceria conter execuções repetidas.
    """
    import csv
    destino = destino or os.path.join(SAIDAS, "comparativo_juntado.csv")
    linhas, cabecalho = [], None
    for arq in arquivos:
        if not os.path.exists(arq):
            print("  (ausente, ignorado) %s" % arq)
            continue
        with open(arq, encoding="utf-8", newline="") as f:
            leitor = csv.DictReader(f)
            cabecalho = leitor.fieldnames
            linhas.extend(list(leitor))
    if not linhas or not cabecalho:
        print("  Nada a juntar.")
        return

    # Renumera por (instancia, metodo), na ordem em que aparecem.
    contador: dict[tuple[str, str], int] = {}
    for linha in linhas:
        chave = (linha.get("instancia", ""), linha.get("metodo", ""))
        linha["execucao"] = str(contador.get(chave, 0))
        contador[chave] = contador.get(chave, 0) + 1

    with open(destino, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=cabecalho)
        escritor.writeheader()
        escritor.writerows(linhas)
    print()
    print("  Juntado em %s" % destino)
    print("  %d linhas. Confira a contagem por célula antes de usar:" % len(linhas))
    for (inst, met), n in sorted(contador.items()):
        print("    %-14s %-10s %d execuções" % (inst, met, n))
    print()
    print("  Lembrete: a coluna tempo_s deste arquivo veio de processos")
    print("  concorrentes e não serve para a comparação de custo do artigo.")


# ---------------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------------
def perguntar_int(rotulo: str, padrao: int, minimo: int = 1,
                  maximo: int = 10**6) -> int:
    # O padrão também é limitado à faixa: numa máquina de poucos núcleos,
    # aceitar o padrão sem conferir devolvia valor fora do permitido.
    padrao = max(minimo, min(padrao, maximo))
    while True:
        bruto = input("  %s [%d]: " % (rotulo, padrao)).strip()
        if not bruto:
            return padrao
        try:
            v = int(bruto)
        except ValueError:
            print("    Precisa ser um número inteiro.")
            continue
        if not (minimo <= v <= maximo):
            print("    Precisa estar entre %d e %d." % (minimo, maximo))
            continue
        return v


def proteger(caminho: str) -> bool:
    """Arquiva um CSV antes de sobrescrevê-lo. Devolve False se o usuário
    desistir.

    Existe porque as opções que regeram o experimento principal usam
    ``--recomecar``, e bastava um teste de uma execução para perder os
    resultados publicados. Arquivar é barato; perder não tem volta.
    """
    if not os.path.exists(caminho):
        return True
    import csv as _csv
    try:
        with open(caminho, encoding="utf-8", newline="") as f:
            n = sum(1 for _ in _csv.DictReader(f))
    except Exception:
        n = -1
    print()
    print("  ATENÇÃO: %s já existe" % os.path.basename(caminho)
          + (" e tem %d execuções gravadas." % n if n >= 0 else "."))
    print("  Começar do zero apaga esse conteúdo.")
    print()
    print("    [a] arquivar uma cópia e começar do zero  (recomendado)")
    print("    [c] continuar de onde parou, sem apagar nada")
    print("    [s] sobrescrever sem arquivar")
    print("    [n] cancelar")
    while True:
        r = input("  Escolha [a/c/s/n]: ").strip().lower()
        if r in ("n", ""):
            print("  Cancelado.")
            return False
        if r == "s":
            return True
        if r == "c":
            return "continuar"           # type: ignore[return-value]
        if r == "a":
            selo = time.strftime("%Y%m%d_%H%M%S")
            destino = os.path.join(
                SAIDAS, "arquivo_%s" % selo)
            os.makedirs(destino, exist_ok=True)
            import shutil as _sh
            for nome in os.listdir(SAIDAS):
                origem = os.path.join(SAIDAS, nome)
                if os.path.isfile(origem):
                    _sh.copy2(origem, os.path.join(destino, nome))
            print("  Arquivado em %s" % destino)
            return True
        print("    Responda a, c, s ou n.")


def confirmar_estimativa(seg: float) -> bool:
    print()
    print("  Duração estimada: %s" % fmt_duracao(seg))
    if seg > 3 * 3600:
        print("  Isto passa de três horas. O CSV é gravado linha a linha,")
        print("  então pode interromper com Ctrl+C e continuar depois.")
    return input("  Começar? [s/N] ").strip().lower() in ("s", "sim", "y")


MENU = """
========================================================================
 O QUE RODAR
========================================================================
  1  Teste rápido ................ 1 execução, até 20 qubits (~1 min)
  2  Só algoritmos genéticos ..... 30 execuções, as 5 instâncias (~1 s)
  3  Principal até 20 qubits ..... 30 execuções, o essencial do artigo
  4  Principal completo .......... inclui a célula de 24 qubits (longa)
  5  Varredura de camadas ........ p = 1 a 4, até 20 qubits
  6  Modo paralelo ............... vários processos isolados
  7  Juntar CSVs parciais ........ depois de usar o modo paralelo
  8  Mostrar o diagnóstico de novo
  0  Sair
"""


def main() -> None:
    if not os.path.exists(EXPERIMENTO):
        print("Não encontrei experimento_comparativo.py em %s" % AQUI)
        print("Rode este arquivo de dentro da pasta do código.")
        sys.exit(1)

    d = diagnostico()
    imprimir_diagnostico(d)
    imprimir_capacidade(d)

    thr = threads_recomendado(d["fisicos"], d["logicos"])
    teto_fisico = d["fisicos"] or max(1, d["logicos"] // 2)
    print()
    print("  Threads por processo recomendadas: %d" % thr)
    print("  (8 foi o melhor medido em 24 qubits; mais que isso num único")
    print("   processo chega a ser mais lento, porque a sincronização entre")
    print("   threads passa a custar mais do que o paralelismo rende.)")
    if teto_fisico >= 2 * thr:
        print()
        print("  Quantos processos em paralelo (opção 6): há duas contas, e a")
        print("  escolha entre elas é empírica, não teórica.")
        print("    - %d processos, se quiser um núcleo FÍSICO por thread"
              % (teto_fisico // thr))
        print("    - %d processos, usando as %d threads LÓGICAS (SMT)"
              % (d["logicos"] // thr, d["logicos"]))
        print("  Simulação de vetor de estado é pesada em operações")
        print("  vetoriais, e duas threads no mesmo núcleo físico disputam a")
        print("  mesma unidade vetorial, de modo que o SMT rende pouco aqui.")
        print("  Mas rende mais que zero, e processos independentes não")
        print("  sincronizam entre si, que é o que degrada um processo só com")
        print("  muitas threads. Na dúvida, meça: rode a opção 1 com um")
        print("  processo, depois com %d, e compare o tempo de parede."
              % (d["logicos"] // thr))

    # numpy e scipy não são opcionais: o algoritmo genético é vetorizado e o
    # teste de Mann-Whitney vem do scipy. Sem eles NENHUMA opção roda, nem a
    # 2. O Qiskit, sim, é opcional, e só desliga o QAOA.
    essenciais = [m for m in ("numpy", "scipy")
                  if d["libs"].get(m) == "AUSENTE"]
    pip_cmd = "%s -m pip install -r requirements.txt" % (
        os.path.basename(sys.executable) or "python")

    if essenciais:
        print()
        print("  " + "=" * 68)
        print("  ** FALTA INSTALAR: %s" % ", ".join(essenciais))
        print("  " + "=" * 68)
        print("     Nenhum experimento roda sem isso. Nesta pasta, execute:")
        print()
        print("         %s" % pip_cmd)
        print()
        print("     Depois abra o lançador de novo. Até lá só as opções")
        print("     8 (diagnóstico) e 0 (sair) respondem.")
    elif d["libs"].get("qiskit") == "AUSENTE":
        print()
        print("  ** Sem Qiskit o QAOA não roda; só as opções 2 e 8 funcionam.")
        print("     Para habilitá-lo: %s" % pip_cmd)

    while True:
        print(MENU)
        escolha = input("  Opção: ").strip()

        if escolha in ("0", "q", ""):
            print("  Até logo.")
            return

        if escolha == "8":
            imprimir_diagnostico(d)
            imprimir_capacidade(d)
            continue

        # Barra a escolha ANTES de abrir o subprocesso. Sem isto o erro só
        # aparecia lá dentro, como traceback, depois de a pessoa esperar.
        if essenciais:
            print()
            print("  Não dá para rodar a opção %s: falta %s."
                  % (escolha or "?", ", ".join(essenciais)))
            print("  Instale primeiro:")
            print("      %s" % pip_cmd)
            continue

        if d["libs"].get("qiskit") == "AUSENTE" and escolha in ("1", "3",
                                                                "4", "5", "6"):
            print()
            print("  A opção %s usa o QAOA, e o Qiskit não está instalado."
                  % escolha)
            print("  Instale com:")
            print("      %s" % pip_cmd)
            print("  Sem ele, a opção 2 (só algoritmos genéticos) funciona.")
            continue

        if escolha == "1":
            seg = estimar(20, 1, ["X", "XY"], ["padrao", "viavel"])
            if confirmar_estimativa(seg):
                rodar([
                    "--execucoes", "1", "--ags", "padrao", "viavel",
                    "--mixers", "X", "XY", "--qaoa-p", "2",
                    "--qaoa-maxiter", "100", "--qaoa-reinicios", "3",
                    "--max-qubits-qaoa", "20", "--threads", str(thr),
                    "--recomecar",
                    "--saida", "resultados/teste_rapido.csv",
                    "--log", "resultados/teste_rapido.log",
                ], "Teste rápido")
            continue

        if escolha == "2":
            n = perguntar_int("Quantas execuções", 30, 1, 1000)
            if confirmar_estimativa(estimar(0, n, [], ["padrao", "viavel"])):
                rodar([
                    "--execucoes", str(n), "--sem-qaoa",
                    "--ags", "padrao", "viavel", "--recomecar",
                    "--saida", "resultados/somente_ag.csv",
                    "--log", "resultados/somente_ag.log",
                ], "Somente algoritmos genéticos")
            continue

        if escolha in ("3", "4"):
            teto = 20 if escolha == "3" else 24
            alvo = os.path.join(SAIDAS, "comparativo.csv")
            decisao = proteger(alvo)
            if decisao is False:
                continue
            n = perguntar_int("Quantas execuções", 30, 1, 1000)
            if confirmar_estimativa(
                    estimar(teto, n, ["X", "XY"], ["padrao", "viavel"])):
                args = [
                    "--execucoes", str(n), "--ags", "padrao", "viavel",
                    "--mixers", "X", "XY", "--qaoa-p", "2",
                    "--qaoa-maxiter", "100", "--qaoa-reinicios", "3",
                    "--qaoa-shots", "4096",
                    "--max-qubits-qaoa", str(teto),
                    "--threads", str(thr), "--seed-base", "42",
                    "--saida", "resultados/comparativo.csv",
                    "--log", "resultados/execucao.log",
                ]
                # Só acrescenta --recomecar quando o usuário pediu para começar
                # do zero. Em "continuar", a ausência da chave faz o
                # experimento retomar e completar apenas o que falta.
                if decisao != "continuar":
                    args.append("--recomecar")
                rodar(args, "Experimento principal, QAOA até %d qubits%s"
                      % (teto, ", continuando"
                         if decisao == "continuar" else ""))
            continue

        if escolha == "5":
            n = perguntar_int("Execuções por valor de p", 5, 1, 100)
            total = sum(estimar(20, n, ["X", "XY"], [], p=p)
                        for p in (1, 2, 3, 4))
            if confirmar_estimativa(total):
                for p in (1, 2, 3, 4):
                    cod = rodar([
                        "--execucoes", str(n), "--qaoa-p", str(p),
                        "--mixers", "X", "XY", "--max-qubits-qaoa", "20",
                        "--threads", str(thr), "--recomecar",
                        "--saida", "resultados/varredura_p%d.csv" % p,
                        "--log", "resultados/varredura_p.log",
                    ], "Varredura, p = %d" % p)
                    if cod == 130:
                        break
            continue

        if escolha == "6":
            maximo = max(1, teto_fisico // 1)
            print()
            print("  Esta máquina tem %d núcleos físicos e %d threads lógicas."
                  % (teto_fisico, d["logicos"]))
            procs = perguntar_int("Quantos processos", 3, 2, maximo)
            thr_p = perguntar_int("Threads por processo", thr, 1,
                                  max(1, d["logicos"]))
            if procs * thr_p > d["logicos"]:
                print("    Aviso: %d threads pedidas contra %d lógicas."
                      % (procs * thr_p, d["logicos"]))
            teto = perguntar_int("Qubits máximos no QAOA", 20, 16, 32)
            n = perguntar_int("Total de execuções, a dividir", 30, procs, 1000)
            seg = estimar(teto, n, ["X", "XY"], ["padrao", "viavel"],
                          processos=procs)
            print()
            print("  Estimativa otimista (supõe ganho proporcional, que não")
            print("  se realiza por inteiro): %s" % fmt_duracao(seg))
            rodar_paralelo(n, teto, ["X", "XY"], procs, thr_p)
            continue

        if escolha == "7":
            achados = []
            if os.path.isdir(SAIDAS):
                # Ordem NUMÉRICA, não alfabética: com dez processos ou mais,
                # ordenar como texto põe parcial_10 antes de parcial_2 e a
                # renumeração de ``execucao`` deixa de seguir as sementes.
                def indice(nome: str) -> int:
                    miolo = nome[len("parcial_"):-len(".csv")]
                    return int(miolo) if miolo.isdigit() else 10**6
                achados = [
                    os.path.join(SAIDAS, f)
                    for f in sorted(
                        (f for f in os.listdir(SAIDAS)
                         if f.startswith("parcial_") and f.endswith(".csv")),
                        key=indice)
                ]
            if not achados:
                print("  Nenhum resultados/parcial_*.csv encontrado.")
                continue
            print("  Encontrados:")
            for a in achados:
                print("    %s" % os.path.basename(a))
            if input("  Juntar estes? [s/N] ").strip().lower() in (
                    "s", "sim", "y"):
                juntar(achados)
            continue

        print("  Opção não reconhecida.")


if __name__ == "__main__":
    if shutil.which(sys.executable) is None and not os.path.exists(sys.executable):
        print("Interpretador Python não localizado.")
        sys.exit(1)
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Encerrado.")
