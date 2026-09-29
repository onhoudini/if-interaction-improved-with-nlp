@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo  IF Interaction Improved with NLP - Zork I
echo ============================================================
echo.

rem ---------------------------------------------------------------------------
rem  Este projeto roda SOMENTE no Linux: frotz-master\dfrotz e um binario ELF
rem  de Linux, que o Windows nao executa. Por isso este .bat nao roda o jogo
rem  no Windows: ele abre o jogo dentro do WSL (Windows Subsystem for Linux).
rem ---------------------------------------------------------------------------

where wsl.exe >nul 2>nul
if errorlevel 1 goto :semwsl

set "RAIZ=%~dp0"
if "%RAIZ:~-1%"=="\" set "RAIZ=%RAIZ:~0,-1%"

rem Converte "C:\caminho\do\projeto" no caminho de dentro do WSL
rem ("/mnt/c/caminho/do/projeto").
for /f "usebackq delims=" %%p in (`wsl.exe wslpath "%RAIZ%"`) do set "RAIZ_WSL=%%p"
if not defined RAIZ_WSL goto :semwsl

echo [INFO] Abrindo o jogo dentro do WSL (Linux)...
echo [INFO] pasta no WSL: %RAIZ_WSL%
echo.

wsl.exe bash -lc "cd '%RAIZ_WSL%' && bash run.sh %*"
set "STATUS=%ERRORLEVEL%"

if not "%STATUS%"=="0" goto :falha
exit /b 0

:falha
echo.
echo [ERRO] A execucao dentro do WSL terminou com o codigo %STATUS%.
echo.
echo        Para ver a mensagem completa, rode no WSL:
echo            wsl bash run.sh
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
echo               wsl bash run.sh
echo.
echo        Passo a passo completo no README, secao "Como rodar".
echo.
pause
exit /b 1
