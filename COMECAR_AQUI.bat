@echo off
REM ===================================================================
REM  COMECAR_AQUI.bat
REM
REM  Baixe esta pasta do GitHub, extraia, e clique duas vezes aqui.
REM  Nao e preciso ter Python nem instalar nada a mao.
REM ===================================================================
REM
REM  ONDE ELE PROCURA UM PYTHON, nesta ordem:
REM
REM    1. _python\         um Python portatil ja montado por uma execucao
REM                        anterior desta mesma pasta.
REM    2. o sistema        py -3, python ou python3, desde que EXECUTEM de
REM                        verdade e tenham pip. O atalho da Microsoft Store
REM                        aparece no "where" mas nao roda nada, por isso o
REM                        teste e por resposta, nao por existencia.
REM    3. _instalador\*.zip   Python portatil guardado na pasta (11 MB).
REM                           Use se a rede do local for ruim.
REM    4. _instalador\*.exe   instalador oficial do Python. E instalado
REM                           DENTRO de _python\, com TargetDir, entao nao
REM                           mexe no sistema nem pede administrador.
REM    5. download         baixa o portatil de python.org (11 MB).
REM
REM  Depois instala as bibliotecas com pip, roda uma demonstracao e abre o
REM  menu.
REM
REM  INTERNET: necessaria na primeira vez, mesmo com instalador na pasta,
REM  porque as bibliotecas (numpy, scipy, qiskit) vem do PyPI e somam uns
REM  150 MB. O Python nao as traz consigo.
REM
REM  PARA DESINSTALAR: apague a pasta. Nada fica no sistema.

setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"
title TCC Gregori Zaccaron - QAOA x Algoritmo Genetico

set "PYVER=3.14.6"
set "PYDIR=%~dp0_python"
set "PYEXE="
set "REQ=documentacao\requirements-travado.txt"
set "ZIPURL=https://www.python.org/ftp/python/%PYVER%/python-%PYVER%-embed-amd64.zip"
set "PIPURL=https://bootstrap.pypa.io/get-pip.py"

REM  O codigo esta em pastas tematicas. Para um Python de sistema, PYTHONPATH
REM  resolve. Para o portatil nao: quando existe um arquivo ._pth, o Python
REM  IGNORA o PYTHONPATH e usa so o que estiver nele. Por isso as mesmas
REM  pastas sao escritas no ._pth mais abaixo.
set "PYTHONPATH=%~dp01-modelo-qubo;%~dp02-algoritmo-genetico;%~dp03-qaoa-quantico;%~dp04-experimento;%~dp05-analise"

cls
echo.
echo  ===================================================================
echo    COMPARACAO ENTRE QAOA E ALGORITMOS GENETICOS
echo    Rotacao de culturas - TCC Gregori Rodrigues Zaccaron - UNESC
echo  ===================================================================
echo.
echo   Preparando o ambiente. Na primeira vez leva alguns minutos.
echo.

REM -------------------------------------------------------------------
REM  1. Python portatil ja montado nesta pasta?
REM -------------------------------------------------------------------
if exist "%PYDIR%\python.exe" (
    call :testar "_python\python.exe"
    if defined PYEXE (
        echo   [1/4] Python portatil ja montado nesta pasta.
        goto tem_python
    )
)

REM -------------------------------------------------------------------
REM  2. Python do sistema que sirva?
REM -------------------------------------------------------------------
call :testar_completo "py -3"
if defined PYEXE goto achou_sistema
call :testar_completo "python"
if defined PYEXE goto achou_sistema
call :testar_completo "python3"
if defined PYEXE goto achou_sistema

REM -------------------------------------------------------------------
REM  3. Zip portatil guardado em _instalador\ ?
REM -------------------------------------------------------------------
set "ZIPLOCAL="
for %%f in ("_instalador\python-*embed*.zip") do set "ZIPLOCAL=%%~ff"
if defined ZIPLOCAL (
    echo   [1/4] Usando o Python portatil de _instalador\
    goto extrair
)

REM -------------------------------------------------------------------
REM  4. Instalador oficial guardado em _instalador\ ?
REM -------------------------------------------------------------------
set "EXELOCAL="
for %%f in ("_instalador\python-*.exe") do set "EXELOCAL=%%~ff"
if defined EXELOCAL goto instalador_local

echo   [1/4] Nenhum Python utilizavel. Vou baixar um portatil.
goto baixar

:achou_sistema
echo   [1/4] Python do sistema encontrado e funcionando.
goto tem_python

REM -------------------------------------------------------------------
REM  Instalador oficial, direcionado para DENTRO da pasta.
REM  TargetDir mantem tudo local; InstallAllUsers=0 e PrependPath=0 evitam
REM  pedido de administrador e alteracao do PATH do sistema.
REM -------------------------------------------------------------------
:instalador_local
echo   [1/4] Usando o instalador de _instalador\
echo         Instalando dentro da pasta, sem mexer no sistema...
"%EXELOCAL%" /quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 ^
    Include_test=0 Include_doc=0 AssociateFiles=0 Shortcuts=0 ^
    TargetDir="%PYDIR%"
call :testar "_python\python.exe"
if not defined PYEXE (
    echo.
    echo   [X] O instalador nao concluiu. Apague a pasta _python e tente
    echo       de novo, ou retire o .exe de _instalador\ para que este
    echo       arquivo baixe a versao portatil.
    goto fim
)
echo         Instalado.
goto tem_python

REM -------------------------------------------------------------------
REM  Baixar o portatil.
REM -------------------------------------------------------------------
:baixar
echo.
echo   [2/4] Baixando Python %PYVER% portatil (11 MB)...
where curl >nul 2>nul
if !ERRORLEVEL! NEQ 0 goto sem_curl
curl -L --fail --silent --show-error -o "%TEMP%\py_embed.zip" "%ZIPURL%"
if !ERRORLEVEL! NEQ 0 goto falha_download
set "ZIPLOCAL=%TEMP%\py_embed.zip"

:extrair
echo         Extraindo...
if exist "%PYDIR%" rmdir /s /q "%PYDIR%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -LiteralPath '%ZIPLOCAL%' -DestinationPath '%PYDIR%' -Force" >nul 2>nul
if not exist "%PYDIR%\python.exe" goto falha_download

REM  O portatil vem com 'import site' desligado (sem ele o pip nao roda) e
REM  NAO poe no sys.path nem a pasta do script nem o PYTHONPATH. As linhas
REM  abaixo religam o site e acrescentam a raiz e as pastas de codigo.
REM  Sem isto o erro e "ModuleNotFoundError: No module named qubo_rotacao".
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$alvo='%PYDIR%'; Get-ChildItem \"$alvo\python*._pth\" | ForEach-Object { $c = @(Get-Content $_.FullName) -replace '^#\s*import\s+site','import site'; foreach ($p in @('..','..\1-modelo-qubo','..\2-algoritmo-genetico','..\3-qaoa-quantico','..\4-experimento','..\5-analise')) { if ($c -notcontains $p) { $c += $p } }; if ($c -notcontains 'import site') { $c += 'import site' }; Set-Content $_.FullName $c }" >nul 2>nul

echo         Instalando o pip...
curl -L --fail --silent --show-error -o "%PYDIR%\get-pip.py" "%PIPURL%"
if !ERRORLEVEL! NEQ 0 goto falha_download
"%PYDIR%\python.exe" "%PYDIR%\get-pip.py" --no-warn-script-location >nul 2>nul
call :testar "_python\python.exe"
if not defined PYEXE goto falha_download
%PYEXE% -m pip --version >nul 2>nul
if !ERRORLEVEL! NEQ 0 goto falha_download
echo         Python portatil pronto.

:tem_python
for /f "delims=" %%v in ('%PYEXE% -c "import sys;print(sys.version.split()[0])" 2^>nul') do set "VER=%%v"
echo         Usando Python !VER!

REM -------------------------------------------------------------------
REM  Confere que os modulos do projeto sao alcancaveis.
REM -------------------------------------------------------------------
%PYEXE% -c "import parametros" >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo.
    echo   [X] O Python nao esta enxergando as pastas do projeto.
    echo       Verifique se a pasta foi EXTRAIDA do .zip, e nao esta sendo
    echo       executada de dentro dele.
    goto fim
)

REM -------------------------------------------------------------------
REM  3. Bibliotecas.
REM -------------------------------------------------------------------
echo.
%PYEXE% -c "import numpy,scipy,matplotlib,qiskit,qiskit_aer" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    echo   [3/4] Bibliotecas ja instaladas.
    goto rodar
)
echo   [3/4] Instalando bibliotecas. Sao cerca de 150 MB, de 2 a 5 min.
echo         Pode deixar rodando.
echo.
%PYEXE% -m pip install --upgrade pip --quiet --no-warn-script-location >nul 2>nul
%PYEXE% -m pip install -r "%REQ%" --no-warn-script-location
if !ERRORLEVEL! NEQ 0 goto falha_libs
%PYEXE% -c "import numpy,scipy,matplotlib,qiskit,qiskit_aer" >nul 2>nul
if !ERRORLEVEL! NEQ 0 goto falha_libs
echo.
echo         Bibliotecas instaladas.

REM -------------------------------------------------------------------
REM  4. Demonstracao e menu.
REM -------------------------------------------------------------------
:rodar
echo.
echo  ===================================================================
echo   [4/4] AMBIENTE PRONTO
echo  ===================================================================
echo.
echo   Demonstracao: uma execucao de cada metodo em 16 e 20 variaveis
echo   binarias, comparando o algoritmo genetico com o QAOA nos dois
echo   operadores de mistura. Cerca de 1 minuto.
echo.
pause

%PYEXE% 4-experimento\experimento_comparativo.py --execucoes 1 ^
    --ags padrao viavel --mixers X XY --qaoa-p 2 --qaoa-maxiter 100 ^
    --qaoa-reinicios 3 --qaoa-shots 4096 --max-qubits-qaoa 20 ^
    --threads 8 --seed-base 42 --recomecar ^
    --saida resultados/demonstracao.csv --log resultados/demonstracao.log

echo.
echo  ===================================================================
echo   Gravado em resultados\demonstracao.csv
echo.
echo   Compare com resultados\comparativo.csv, que traz as 480 execucoes
echo   publicadas: os custos devem bater exatamente.
echo.
echo   No menu a seguir, a opcao 1 e um teste rapido e a 4 e o
echo   experimento completo do artigo.
echo  ===================================================================
echo.
pause

%PYEXE% 4-experimento\rodar.py
goto fim

REM -------------------------------------------------------------------
REM  Erros
REM -------------------------------------------------------------------
:sem_curl
echo.
echo   [X] Este Windows nao tem curl, o que indica versao anterior a 2018.
echo       Instale o Python de https://www.python.org/downloads/ marcando
echo       "Add python.exe to PATH", e rode este arquivo de novo.
goto fim

:falha_download
echo.
echo   [X] Nao consegui obter o Python.
echo.
echo       Verifique a internet. Se a rede tiver proxy ou firewall
echo       corporativo, tente de outra rede.
echo.
echo       Alternativa sem internet para esta etapa: baixe
echo         %ZIPURL%
echo       em outra maquina e ponha o arquivo em _instalador\
goto fim

:falha_libs
echo.
echo   [X] A instalacao das bibliotecas nao se completou.
echo       Tente de novo (downloads parciais sao retomados), ou rode:
echo         %PYEXE% -m pip install -r %REQ%
goto fim

REM -------------------------------------------------------------------
REM  Sub-rotinas
REM
REM  O comando NAO leva aspas de proposito: dentro de um "for /f" o cmd
REM  repassa a linha a um "cmd /c" e, se ela COMECA com aspas, remove a
REM  primeira e a ultima, quebrando tudo. Como o portatil e sempre
REM  referenciado por _python\python.exe, caminho relativo e sem espaco,
REM  dispensar aspas e seguro. Era por isto que o .bat deixava de
REM  reconhecer o Python que ele mesmo acabara de instalar.
REM -------------------------------------------------------------------
:testar
set "CAND=%~1"
for /f "delims=" %%r in ('%CAND% -c "print('PYOK')" 2^>nul') do (
    if "%%r"=="PYOK" set "PYEXE=%CAND%"
)
exit /b

:testar_completo
set "CAND=%~1"
set "BOM="
for /f "delims=" %%r in ('%CAND% -c "print('PYOK')" 2^>nul') do (
    if "%%r"=="PYOK" set "BOM=1"
)
if not defined BOM exit /b
%CAND% -m pip --version >nul 2>nul
if !ERRORLEVEL! EQU 0 set "PYEXE=%CAND%"
exit /b

:fim
echo.
echo  Pressione qualquer tecla para fechar.
pause > nul
