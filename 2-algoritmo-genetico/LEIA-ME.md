# 2. O algoritmo genetico (classico)

| Arquivo | O que faz |
|---|---|
| `algoritmo_genetico.py` | O laco evolutivo, em duas variantes. |

As duas variantes sao o eixo horizontal do delineamento fatorial:

- **AG padrao**: ignora a restricao de alocacao unica.
- **AG viavel**: preserva a restricao nos operadores de busca (`preserva_viabilidade` na `ConfiguracaoAG`).

A implementacao e propria, e nao PyGAD ou DEAP, porque a contagem de avaliacoes da funcao objetivo precisa ser exata: e ela que permite comparar dois metodos cujo custo por iteracao difere em seis ordens de grandeza. O contador e o `n_avaliacoes`, auditavel no codigo.
