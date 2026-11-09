@echo off
REM ===================================================================
REM  Abre um terminal e inicia o lancador dos experimentos.
REM  Clique duas vezes neste arquivo. Nao precisa saber linha de comando.
REM ===================================================================
REM
REM  Nao e um .exe de verdade, e e melhor assim: um executavel gerado por
REM  PyInstaller pesaria dezenas de megabytes, precisaria ser recompilado a
REM  cada mudanca e costuma ser barrado por antivirus. Este .bat faz o mesmo
REM  e qualquer pessoa pode ler o que ele faz.
REM
REM  Ele resolve, em ordem, os tres jeitos de isto falhar numa maquina nova:
REM
REM   1. Python nao instalado, ou instalado como atalho da Microsoft Store.
REM      O atalho e um programa falso em WindowsApps que abre a loja em vez
REM      de rodar Python. Aqui ele e detectado executando um Python de
REM      verdade e conferindo a resposta, nao so a existencia do arquivo.
REM   2. Python presente mas sem pip. Resolvido com ensurepip.
REM   3. pip presente mas sem as bibliotecas. Oferece instalar.
REM
REM  Antes desta versao, o lancador abria o menu normalmente numa maquina
REM  sem numpy e so quebrava com um "ImportError" cru depois da escolha.

setlocal enabledelayedexpansion
chcp 65001 > nul
cd /d "%~dp0"
title Experimentos QAOA x Algoritmo Genetico

echo.
echo  ===================================================================
echo   QAOA x Algoritmo Genetico - rotacao de culturas
echo  ===================================================================
echo.

REM -------------------------------------------------------------------
REM  1. Achar um Python que REALMENTE execute.
REM -------------------------------------------------------------------
set "PYEXE="

call :testar "py -3"
if defined PYEXE goto achou
call :testar "python"
if defined PYEXE goto achou
call :testar "python3"
if defined PYEXE goto achou

echo  [X] Nao ha Python utilizavel nesta maquina.
echo.
echo      Se ao digitar "python" o Windows abre a Microsoft Store, o que
echo      existe ai e so um atalho, nao o Python.
echo.
echo      O que fazer:
echo        1. Baixe em https://www.python.org/downloads/
echo        2. Na primeira tela do instalador, MARQUE a caixa
echo           "Add python.exe to PATH". E a que costuma passar batido.
echo        3. Conclua, FECHE esta janela e clique de novo neste arquivo.
echo.
echo      Se preferir desligar o atalho da loja: Configuracoes ^> Aplicativos
echo      ^> Aliases de execucao de aplicativo ^> desligue "python.exe".
echo.
goto fim

:achou
for /f "delims=" %%v in ('%PYEXE% -c "import sys; print(sys.version.split()[0])" 2^>nul') do set "PYVER=%%v"
echo  [ok] Python !PYVER! encontrado  ^(%PYEXE%^)

REM -------------------------------------------------------------------
REM  2. O pip funciona?
REM -------------------------------------------------------------------
%PYEXE% -m pip --version >nul 2>nul
if !ERRORLEVEL! EQU 0 goto tem_pip

echo  [!] Este Python esta sem o pip. Tentando instalar...
%PYEXE% -m ensurepip --upgrade >nul 2>nul
%PYEXE% -m pip --version >nul 2>nul
if !ERRORLEVEL! NEQ 0 (
    echo  [X] Nao consegui habilitar o pip.
    echo.
    echo      Reinstale o Python pelo site oficial, marcando "Add python.exe
    echo      to PATH" e deixando a opcao "pip" ligada em Optional Features.
    echo.
    goto fim
)
echo  [ok] pip habilitado.

:tem_pip

REM -------------------------------------------------------------------
REM  3. As bibliotecas estao instaladas?
REM -------------------------------------------------------------------
%PYEXE% -c "import numpy, scipy, matplotlib, qiskit, qiskit_aer" >nul 2>nul
if !ERRORLEVEL! EQU 0 (
    echo  [ok] Dependencias instaladas.
    echo.
    goto lancar
)

echo.
echo  -------------------------------------------------------------------
echo   FALTAM BIBLIOTECAS
echo  -------------------------------------------------------------------
%PYEXE% -c "import importlib.util as u;[print(('    ok     ' if u.find_spec(m) else '    FALTA  ')+m) for m in ['numpy','scipy','matplotlib','qiskit','qiskit_aer']]"
echo.
echo   Sem elas nenhum experimento roda.
echo.
set "RESP="
set /p "RESP=  Instalar agora? [S/n]: "
if /I "!RESP!"=="n" goto recusou

echo.
echo   Instalando. Na primeira vez pode levar alguns minutos.
echo.
%PYEXE% -m pip install -r requirements.txt
if !ERRORLEVEL! NEQ 0 goto falhou

%PYEXE% -c "import numpy, scipy, matplotlib, qiskit, qiskit_aer" >nul 2>nul
if !ERRORLEVEL! NEQ 0 goto falhou
echo.
echo  [ok] Tudo instalado.
echo.
goto lancar

:recusou
echo.
echo   Quando quiser, rode nesta pasta:
echo       %PYEXE% -m pip install -r requirements.txt
echo.
goto fim

:falhou
echo.
echo  [X] A instalacao nao se completou.
echo.
echo      Causas comuns:
echo        - sem conexao com a internet
echo        - antivirus ou proxy bloqueando o pip
echo        - falta permissao: tente
echo              %PYEXE% -m pip install --user -r requirements.txt
echo.
goto fim

:lancar
%PYEXE% rodar.py
goto fim

REM -------------------------------------------------------------------
REM  Sub-rotina: so aceita o comando se um Python de verdade responder.
REM  O atalho da Microsoft Store existe como arquivo e aparece no "where",
REM  mas nao imprime nada util, entao testar a saida e o unico jeito seguro.
REM -------------------------------------------------------------------
:testar
set "CAND=%~1"
for /f "delims=" %%r in ('%CAND% -c "print('PYOK')" 2^>nul') do (
    if "%%r"=="PYOK" set "PYEXE=%CAND%"
)
exit /b

:fim
echo.
echo  Pressione qualquer tecla para fechar.
pause > nul
