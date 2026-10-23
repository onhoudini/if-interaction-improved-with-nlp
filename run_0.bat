@echo off
setlocal
cd /d "%~dp0"

rem ---------------------------------------------------------------------------
rem  Roda o jogo (Zork I) sempre no modo 0: frotz puro, sem processamento
rem  (grupo de controle).
rem  Tudo e feito por este .bat: cria o .venv (Linux) se faltar, instala as
rem  dependencias, da permissao ao dfrotz e chama src/main.py 0 dentro do WSL.
rem ---------------------------------------------------------------------------

where wsl.exe >nul 2>nul
if errorlevel 1 goto :semwsl

set "RAIZ=%~dp0"
if "%RAIZ:~-1%"=="\" set "RAIZ=%RAIZ:~0,-1%"

rem Converte "C:\caminho\do\projeto" no caminho de dentro do WSL
rem ("/mnt/c/caminho/do/projeto").
for /f "usebackq delims=" %%p in (`wsl.exe wslpath "%RAIZ%"`) do set "RAIZ_WSL=%%p"
if not defined RAIZ_WSL goto :semwsl

echo.

wsl.exe bash -lc "cd '%RAIZ_WSL%' && if [ ! -x .venv/bin/python ]; then echo '[SETUP] criando .venv (Linux)...' && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt; fi && chmod u+rwx frotz-master/dfrotz && .venv/bin/python src/main.py 0"
set "STATUS=%ERRORLEVEL%"

if not "%STATUS%"=="0" goto :falha
exit /b 0

:falha
echo.
echo [ERRO] A execucao dentro do WSL terminou com o codigo %STATUS%.
echo.
echo        Se faltou o Python no WSL, rode no Ubuntu:
echo            sudo apt update ^&^& sudo apt install -y python3 python3-venv python3-pip
echo.
pause
exit /b %STATUS%

:semwsl
echo [ERRO] O WSL nao esta disponivel neste computador.
echo.
echo        O jogo precisa do WSL (Windows Subsystem for Linux), porque o
echo        interpretador frotz-master\dfrotz e um binario de Linux (ELF).
echo        Sem o WSL nao ha como rodar a ferramenta no Windows.
echo.
echo        1) Abra o PowerShell como administrador e rode:
echo               wsl --install -d Ubuntu
echo        2) Reinicie o computador se for pedido e abra o "Ubuntu" para
echo           criar o usuario/senha do Linux.
echo        3) Instale o Python no WSL:
echo               sudo apt update
echo               sudo apt install -y python3 python3-venv python3-pip
echo        4) Volte a esta pasta e rode:
echo               wsl bash run_0.sh
echo.
echo        Passo a passo completo no README, secao "Como rodar".
echo.
pause
exit /b 1
