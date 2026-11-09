# 1. O modelo

Aqui o problema agronomico vira matematica.

| Arquivo | O que faz |
|---|---|
| `parametros.py` | Catalogo de culturas e parametros agronomicos, extraidos do Manual de Calagem e Adubacao para RS e SC (2016). Cada valor traz anotada a tabela e a pagina de origem. Define a escada de instancias, de 4 a 8 culturas. |
| `qubo_rotacao.py` | Constroi a matriz `Q` do QUBO. E o unico lugar onde o modelo e definido: os dois algoritmos otimizam exatamente a mesma matriz. |

Para ver o catalogo:

    python 1-modelo-qubo/parametros.py
