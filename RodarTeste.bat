@echo off
REM Abre um terminal e inicia o lancador dos experimentos.
REM Clique duas vezes neste arquivo. Nao precisa saber a linha de comando.
REM
REM Nao e um .exe de verdade, e e melhor assim: um executavel gerado por
REM PyInstaller pesaria dezenas de megabytes, precisaria ser recompilado a
REM cada mudanca e costuma ser barrado por antivirus. Este .bat faz o mesmo
REM e qualquer pessoa pode ler o que ele faz.

chcp 65001 > nul
cd /d "%~dp0"
title Experimentos QAOA x Algoritmo Genetico

echo.
echo  Iniciando o lancador...
echo.

REM Procura um Python utilizavel: primeiro o py launcher, depois o do PATH.
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    py -3 rodar.py
    goto fim
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    python rodar.py
    goto fim
)

echo  Nao encontrei o Python nesta maquina.
echo.
echo  Instale a versao 3.11 ou mais nova em https://www.python.org/downloads/
echo  e marque a opcao "Add Python to PATH" durante a instalacao.
echo.

:fim
echo.
echo  Pressione qualquer tecla para fechar.
pause > nul
