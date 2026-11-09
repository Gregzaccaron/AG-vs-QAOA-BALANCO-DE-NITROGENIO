# 4. O experimento

| Arquivo | O que faz |
|---|---|
| `rodar.py` | Lancador interativo: mostra o que a maquina aguenta e monta as linhas de comando do artigo. E o que o `COMECAR_AQUI.bat` abre. |
| `experimento_comparativo.py` | Percorre instancias, metodos e repeticoes, e grava o CSV. E o ponto de entrada de verdade. |
| `escalabilidade.py` | Mede tempo e memoria por instancia, sem otimizar nada. |
| `progresso.py` | Barra de progresso das execucoes longas. |

Toda execucao grava DOIS arquivos em `resultados/`: um `.csv` com uma linha por execucao e um `.log` com o rastro. O CSV e gravado linha a linha, entao da para abrir enquanto roda, e interromper com Ctrl+C nao perde o que ja saiu.
