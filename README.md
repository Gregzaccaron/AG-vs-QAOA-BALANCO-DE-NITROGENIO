# Como rodar

**Comparação entre o algoritmo quântico QAOA e algoritmos genéticos na
otimização do balanço de nitrogênio em rotação de culturas na região da AMESC**
Gregori Rodrigues Zaccaron, Ciência da Computação, UNESC, 2026.

---

## Em dois passos

1. Baixe esta pasta do GitHub (botão verde **Code** → **Download ZIP**) e
   **extraia o conteúdo**. Não rode de dentro do `.zip`.
2. Clique duas vezes em **`COMECAR_AQUI.bat`**.

Pronto. Não é preciso ter Python nem instalar nada à mão.

### O que vai acontecer

O arquivo cuida de tudo sozinho:

| Passo | O que faz |
|---|---|
| 1 | Procura um Python na máquina |
| 2 | Se não houver, baixa o Python 3.14.6 portátil (11 MB) **para dentro desta pasta** |
| 3 | Instala numpy, scipy, matplotlib e qiskit |
| 4 | Abre o menu e espera você escolher |

**Nada é executado sozinho.** O `COMECAR_AQUI.bat` só prepara o ambiente e
abre o menu; quem estiver usando escolhe o que rodar, ou sai sem rodar nada.
Os resultados publicados já vêm na pasta, em `resultados/comparativo.csv`, e
não é preciso executar nada para consultá-los.

Na primeira vez leva de 3 a 6 minutos, quase tudo em download. Depois abre na
hora.

Reserve **cerca de 500 MB de disco**: o Python portátil e as bibliotecas
ocupam uns 390 MB depois de instalados, e ficam todos dentro da pasta.

As versões das bibliotecas são **travadas** em `requirements-travado.txt`, e a
versão do Python portátil é a mesma que produziu os resultados do artigo. Isso
não é capricho: o QAOA não reproduz entre versões diferentes, porque uma
diferença de arredondamento de ordem 1e-15 muda o mínimo local em que o
otimizador clássico cai. O motivo está detalhado na seção 7 do `README.md`.

### Isto mexe no meu computador?

**Não.** O Python é instalado dentro da própria pasta, em `_python\`. Não pede
senha de administrador, não altera o `PATH`, não aparece em "Adicionar ou
remover programas" e não conflita com um Python que já exista.

**Para remover tudo, apague a pasta.** Não sobra nada.

Se a máquina já tiver um Python funcionando, ele é aproveitado e o download de
11 MB nem acontece.

---

## O que tem em cada pasta

Na raiz fica só o `COMECAR_AQUI.bat`. O resto está separado por assunto, e
cada pasta tem o seu próprio `LEIA-ME.md` explicando o que há dentro.

| Pasta | O que é |
|---|---|
| `1-modelo-qubo/` | O problema agronômico virando matemática: catálogo de culturas e a matriz `Q` do QUBO |
| `2-algoritmo-genetico/` | O método clássico, nas duas variantes comparadas |
| `3-qaoa-quantico/` | O método quântico, nos dois operadores de mistura |
| `4-experimento/` | O que percorre instâncias e repetições e grava os dados |
| `5-analise/` | Figuras, planilha e as estimativas de custo em hardware real |
| `resultados/` | Os dados publicados: as 480 execuções do artigo |
| `documentacao/` | Documentação técnica e as versões travadas das bibliotecas |
| `_instalador/` | Opcional: o instalador do Python, se você não quiser que ele seja baixado |

Os dois algoritmos comparados estão em `2-` e `3-`, e ambos otimizam
**exatamente a mesma matriz `Q`**, construída em `1-modelo-qubo/`. É isso que
torna a comparação legítima.

---

---

## O que faz cada arquivo

### `1-modelo-qubo/` — o problema vira matemática

| Arquivo | O que faz |
|---|---|
| `parametros.py` | Catálogo de culturas e parâmetros agronômicos, tirados do Manual de Calagem e Adubação para RS e SC (2016). Cada valor traz anotada a tabela e a página de origem. Define a escada de instâncias, de 4 a 8 culturas (16 a 32 variáveis binárias). Rode `python 1-modelo-qubo/parametros.py` para ver o catálogo. |
| `qubo_rotacao.py` | Constrói a matriz `Q` do QUBO, com os sete termos da função objetivo. É o **único** lugar onde o modelo é definido: os dois algoritmos otimizam exatamente a mesma matriz, e é isso que torna a comparação legítima. |

### `2-algoritmo-genetico/` — o método clássico

| Arquivo | O que faz |
|---|---|
| `algoritmo_genetico.py` | O laço evolutivo, em duas variantes: **AG padrão**, que ignora a restrição de alocação única, e **AG viável**, que a preserva nos operadores de busca. A implementação é própria, e não PyGAD ou DEAP, porque a contagem de avaliações da função objetivo precisa ser exata e auditável: é ela que permite comparar métodos cujo custo por iteração difere em seis ordens de grandeza. |

### `3-qaoa-quantico/` — o método quântico

| Arquivo | O que faz |
|---|---|
| `qaoa_rotacao.py` | O circuito QAOA: conversão do QUBO para Hamiltoniano de Ising, os dois operadores de mistura e o laço híbrido com COBYLA. O **mixer X** inverte bits e percorre todo o espaço de 2^n; o **mixer XY** troca qubits, conserva o peso de Hamming e por isso nunca sai do conjunto de alocações válidas. |
| `qaoa_diagonal.py` | Evolução do estado aproveitando que o Hamiltoniano de custo é diagonal na base computacional. Nenhum outro módulo o importa: serve para validar a simulação e registra um resultado negativo de desempenho. |

Não há execução em hardware quântico real. Tudo roda no simulador de vetor de
estado do Qiskit Aer, sem ruído, que é a condição mais favorável possível ao
método quântico.

### `4-experimento/` — o que gera os dados

| Arquivo | O que faz |
|---|---|
| `rodar.py` | O lançador interativo. Mostra o que a máquina aguenta, instância por instância, e monta as linhas de comando do artigo. É o menu que aparece no fim. |
| `experimento_comparativo.py` | O ponto de entrada de verdade: percorre instâncias, métodos e repetições, e grava o CSV. |
| `escalabilidade.py` | Mede tempo e memória por instância, sem otimizar nada. |
| `progresso.py` | Barra de progresso das execuções longas, que chegam a horas. |

### `5-analise/` — o que produz as saídas

| Arquivo | O que faz |
|---|---|
| `graficos.py` | As figuras do artigo. Legíveis impressas em preto e branco: a identidade de cada série nunca depende só da cor. |
| `exportar_xlsx.py` | Converte o CSV em `.xlsx` de duas abas, sem nenhuma dependência externa. |
| `custo_hardware.py` | Estima o custo de rodar o mesmo circuito em hardware quântico real, transpilando para uma malha *heavy-hex* de verdade. Não executa nada em nuvem. |
| `medicoes_pendentes.py` | Três medições citadas no texto do artigo. |

Os scripts de análise rodam a partir da **raiz** da pasta, não de dentro dela:

    python 5-analise/graficos.py
    python 5-analise/exportar_xlsx.py

---

---

## Preciso instalar mais alguma coisa?

**Não.** Nem Visual Studio Code, nem Anaconda, nem Git, nem compilador. Só
clicar no `COMECAR_AQUI.bat`. Ele cuida do Python e das bibliotecas sozinho.

O **Visual Studio Code é um editor de texto** e não participa de nada aqui.
Se alguém disser que precisa dele, está confundindo com outra coisa, que vale
a pena explicar porque o nome é parecido:

### O erro do "Microsoft Visual C++ 14.0"

Em alguns computadores a instalação das bibliotecas falha assim:

```
error: Microsoft Visual C++ 14.0 or greater is required.
Get it with "Microsoft C++ Build Tools"
```

Isso **não é o Visual Studio Code**. É um compilador de C++, programa
diferente, de uns 6 GB. E **você não precisa instalá-lo.**

O que acontece é o seguinte: as bibliotecas (numpy, scipy, qiskit) são
distribuídas prontas, já compiladas, para cada versão de Python. Quando o pip
não encontra a versão pronta que serve para o Python da máquina, ele tenta
construir a biblioteca do zero, e aí precisa do compilador. Isso ocorre quando
o Python instalado é antigo demais (anterior ao 3.11) ou é de 32 bits.

**A solução é não usar aquele Python.** O `COMECAR_AQUI.bat` agora faz isso
sozinho: ele só aproveita um Python que já exista na máquina se for a versão
3.14 de 64 bits, a mesma que produziu os resultados do artigo. Qualquer outra,
ele ignora e baixa o Python 3.14.6 portátil para dentro da pasta, para o qual
todas as bibliotecas têm versão pronta. Nada é compilado em momento nenhum.

Se mesmo assim der erro, apague a pasta `_python` e rode o
`COMECAR_AQUI.bat` de novo.

### Isso estraga o Python que eu já tenho?

Não. O Python portátil fica em `_python\`, dentro desta pasta. Não altera o
`PATH`, não mexe no registro, não aparece em "Adicionar ou remover programas"
e não conversa com nenhum outro Python da máquina. Para remover, apague a
pasta.

---

## Dois avisos do Windows

**"O Windows protegeu o seu computador"** (tela azul do SmartScreen). Acontece
com qualquer arquivo baixado da internet. Clique em **Mais informações** e
depois em **Executar assim mesmo**.

**O antivírus pode reclamar do download do Python.** É o instalador oficial,
vindo de `python.org`. O endereço completo está escrito no começo do
`COMECAR_AQUI.bat`, que é texto puro e pode ser lido no Bloco de Notas antes de
executar.

---

## O menu

O menu oferece:

| Opção | O que faz | Tempo |
|---|---|---|
| 1 | Teste rápido, 1 execução até 20 qubits | ~1 min |
| 2 | Só os algoritmos genéticos, 30 execuções | ~6 s |
| 3 | Experimento principal até 20 qubits, 30 execuções | ~45 min |
| 4 | Experimento completo, inclui 24 qubits | ~19 h |
| 5 | Varredura do número de camadas | ~1 h |

A **opção 1** já exercita o caminho inteiro: a formulação QUBO, o algoritmo
genético nas duas variantes e o QAOA nos dois operadores de mistura.

A **opção 4** é a que gera a Tabela 1 do artigo por completo, com as 480
execuções. Não precisa rodá-la: os resultados dela já vêm na pasta, em
`resultados/comparativo.csv`.

### Onde os resultados aparecem

Toda execução grava dois arquivos em `resultados/`: um `.csv` com uma linha por
execução e um `.log` com o rastro. O CSV é gravado linha a linha, então dá para
abrir no Excel enquanto roda, e interromper com Ctrl+C não perde o que já saiu.

> **Cuidado com as opções 3 e 4:** elas escrevem em `resultados/comparativo.csv`,
> que contém as 480 execuções publicadas. O programa detecta isso e pergunta o
> que fazer. A resposta segura é **`a`** (arquiva uma cópia antes) ou **`n`**
> (cancela). As opções 1, 2 e 5 gravam em arquivos próprios e não correm risco.

---

## Conferindo que reproduz

A pasta já traz os dados publicados em `resultados/comparativo.csv`, com as 480
execuções. Para verificar que a sua máquina chega aos mesmos números, rode a
**opção 1** e compare a saída com estas linhas, de 16 variáveis binárias:

| Método | Custo esperado |
|---|---|
| AG viável | 384,68 |
| QAOA mixer X | 750,00 |
| QAOA mixer XY | 384,68 |

O algoritmo genético é determinístico: mesma semente, mesmo resultado, bit a
bit. O QAOA também reproduz, desde que a versão das bibliotecas seja a mesma,
que é o que o `requirements.txt` fixa.

---

## Se alguma coisa falhar

O `COMECAR_AQUI.bat` diz em qual dos quatro passos parou e o que fazer. As duas
causas mais comuns:

- **Sem internet, ou rede com proxy.** O download do Python ou das bibliotecas
  falha. Tente de outra rede.
- **Windows anterior a 2018.** Falta o `curl`. Nesse caso instale o Python de
  <https://www.python.org/downloads/>, marcando **"Add python.exe to PATH"**, e
  rode o `COMECAR_AQUI.bat` de novo.

A documentação técnica completa, com o modelo, as decisões de implementação e o
comando exato que gerou os resultados publicados, está em `documentacao/README.md`.
