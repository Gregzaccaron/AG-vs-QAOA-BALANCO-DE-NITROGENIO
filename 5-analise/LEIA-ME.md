# 5. Analise e saidas

| Arquivo | O que faz |
|---|---|
| `graficos.py` | As figuras do artigo, legiveis em preto e branco. |
| `exportar_xlsx.py` | Converte o CSV em `.xlsx` de duas abas. Sem dependencia externa. |
| `custo_hardware.py` | Estima o custo de rodar o mesmo circuito em hardware quantico real, transpilando para uma malha heavy-hex. Nao executa nada em nuvem. |
| `medicoes_pendentes.py` | Tres medicoes citadas no texto do artigo. |

Rodar a partir da RAIZ da pasta, nao de dentro desta:

    python 5-analise/graficos.py
    python 5-analise/exportar_xlsx.py
