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
| 4 | Roda uma demonstração de 1 minuto e abre o menu |

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

## Dois avisos do Windows

**"O Windows protegeu o seu computador"** (tela azul do SmartScreen). Acontece
com qualquer arquivo baixado da internet. Clique em **Mais informações** e
depois em **Executar assim mesmo**.

**O antivírus pode reclamar do download do Python.** É o instalador oficial,
vindo de `python.org`. O endereço completo está escrito no começo do
`COMECAR_AQUI.bat`, que é texto puro e pode ser lido no Bloco de Notas antes de
executar.

---

## Depois da demonstração

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
