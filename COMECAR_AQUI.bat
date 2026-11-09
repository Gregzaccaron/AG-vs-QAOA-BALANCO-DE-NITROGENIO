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
REM  Depois instala as bibliotecas com pip e abre o menu. NADA e executado
REM  automaticamente: quem roda escolhe o que fazer, ou sai sem rodar nada.
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
REM  Sem isto a saida do Python fica em buffer e a tela parece travada
REM  durante a demonstracao, que leva cerca de um minuto e meio. A barra de
REM  progresso do progresso.py reescreve a propria linha, e so aparece se a
REM  saida for descarregada na hora.
set "PYTHONUNBUFFERED=1"
set "PYTHONIOENCODING=utf-8"

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
REM  --only-binary=:all: proibe o pip de construir pacote do codigo-fonte.
REM  Sem isso, se faltasse um pacote pronto ele tentaria compilar e pediria o
REM  compilador C++. Com isso, falha na hora e com mensagem util.
%PYEXE% -m pip install -r "%REQ%" --only-binary=:all: --no-warn-script-location
if !ERRORLEVEL! NEQ 0 goto falha_libs
%PYEXE% -c "import numpy,scipy,matplotlib,qiskit,qiskit_aer" >nul 2>nul
if !ERRORLEVEL! NEQ 0 goto falha_libs
echo.
echo         Bibliotecas instaladas.

REM -------------------------------------------------------------------
REM  4. Demonstracao e menu.
REM -------------------------------------------------------------------
:rodar
REM  Nada e executado automaticamente aqui. O .bat so prepara o ambiente e
REM  entrega o menu; quem esta usando decide o que rodar, inclusive nao
REM  rodar nada. A demonstracao que antes comecava sozinha era a opcao 1 com
REM  outro nome, e continua disponivel por escolha.
echo.
echo  ===================================================================
echo   [4/4] AMBIENTE PRONTO
echo  ===================================================================
echo.
echo   Nada sera executado sem voce pedir.
echo.
echo   No menu a seguir:
echo.
echo     opcao 1   teste rapido, uma execucao de cada metodo em 16 e 20
echo               variaveis binarias. Cerca de 1 minuto e meio. E o jeito
echo               mais rapido de ver o QAOA e o algoritmo genetico lado
echo               a lado.
echo     opcao 2   so os algoritmos geneticos, 30 execucoes. Uns 6 s.
echo     opcao 4   o experimento completo do artigo, 480 execucoes.
echo               Cerca de 19 horas.
echo     opcao 8   mostra de novo o que esta maquina aguenta.
echo     opcao 0   sair sem rodar nada.
echo.
echo   Os resultados publicados ja estao em resultados\comparativo.csv, e
echo   nao e preciso rodar nada para consulta-los.
echo.
pause
echo.

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
echo.
echo       NAO e preciso ter Visual Studio Code, nem nenhum editor. Se a
echo       mensagem acima falou em "Microsoft Visual C++ 14.0 or greater
echo       is required", o problema e outro: o pip nao achou um pacote
echo       pronto para este Python e tentou compilar.
echo.
echo       Solucao: apague a pasta _python e rode este arquivo de novo.
echo       Ele vai baixar o Python 3.14.6 portatil, para o qual existem
echo       pacotes prontos de todas as bibliotecas, e nada sera compilado.
echo.
echo       Se persistir, pode ser rede com proxy. Tente de outra rede, ou
echo       rode manualmente para ver a mensagem inteira:
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
REM  Diferente de :testar, aqui nao basta executar: o Python do sistema so
REM  serve se for 3.14 de 64 bits, a mesma versao que produziu os resultados.
REM
REM  Nao e preciosismo. As bibliotecas estao travadas em versoes que so tem
REM  pacote pronto para 3.11 ou mais novo, de 64 bits. Num Python 3.9 ou de
REM  32 bits o pip tentaria COMPILAR numpy e scipy do codigo-fonte e exigiria
REM  o compilador C++ das Build Tools, que quase ninguem tem. Alem disso, o
REM  artigo so reproduz com a mesma versao: ver a secao 7 do README tecnico.
REM
REM  Qualquer outro Python do sistema e ignorado, e o portatil 3.14.6 e usado
REM  no lugar. Nada do que ja estiver instalado na maquina e alterado.
set "CAND=%~1"
set "BOM="
for /f "delims=" %%r in ('%CAND% -c "import sys;v=sys.version_info;print('PYOK' if v[0]==3 and v[1]==14 and sys.maxsize>4294967296 else 'NO')" 2^>nul') do (
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
