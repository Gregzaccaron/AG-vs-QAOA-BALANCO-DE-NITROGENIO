# 3. O QAOA (quantico, em simulador)

| Arquivo | O que faz |
|---|---|
| `qaoa_rotacao.py` | Circuito QAOA, conversao do QUBO para Hamiltoniano de Ising, os dois operadores de mistura e o laco hibrido com COBYLA. |
| `qaoa_diagonal.py` | Evolucao do estado aproveitando que o Hamiltoniano de custo e diagonal. Nenhum outro modulo o importa: serve para validar a simulacao e registra um resultado negativo de desempenho. |

Os dois operadores de mistura sao o eixo vertical do delineamento:

- **mixer X**: inversao de bit, percorre o espaco inteiro de 2^n.
- **mixer XY**: troca entre qubits, conserva o peso de Hamming e por isso nunca sai do conjunto de alocacoes validas.

Nao ha execucao em hardware quantico real: tudo roda no simulador de vetor de estado do Qiskit Aer, em condicao ideal e sem ruido, que e a mais favoravel possivel ao metodo quantico.
