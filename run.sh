#!/usr/bin/env bash
#
# Executa o jogo (Zork I) atraves da ferramenta.
#
# Requisitos: Linux ou WSL (no Windows nativo NAO funciona: o interpretador
# frotz-master/dfrotz e um binario ELF de Linux).
#
# Uso:
#   ./run.sh        -> modo com o algoritmo de correcao (padrao)
#   ./run.sh 0      -> modo frotz puro (grupo de controle)
#   ./run.sh 1      -> modo com o algoritmo (explicito)
#
# O script tambem cuida da preparacao do ambiente:
#   - cria o .venv e instala as dependencias, se nao existirem;
#   - da permissao de execucao em frotz-master/dfrotz (chmod u+rwx), que e
#     perdida quando o projeto e baixado como .zip pelo botao "Download ZIP".

set -u

cd "$(dirname "$0")" || exit 1

DFROTZ="frotz-master/dfrotz"
REQUIREMENTS="requirements.txt"

# ---------------------------------------------------------------------------
# 0) Git Bash / Cygwin / MSYS nao servem: o binario do dfrotz e de Linux
# ---------------------------------------------------------------------------
case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*)
        cat <<'MSG'
[ERRO] Este script precisa do Linux (WSL).

       Voce esta rodando pelo Git Bash/Cygwin/MSYS, onde o binario de Linux
       frotz-master/dfrotz (ELF) nao roda, e o Python do Windows tambem nao
       consegue executa-lo.

       Como rodar:
         - no PowerShell/CMD, dentro desta pasta:   wsl bash run.sh
         - ou abra o Ubuntu (WSL), va ate esta pasta e rode:   ./run.sh

       Passo a passo completo no README, secao "Como rodar".
MSG
        exit 1
        ;;
esac

# ---------------------------------------------------------------------------
# 1) Ambiente virtual (precisa ser um venv de LINUX, criado dentro do WSL)
# ---------------------------------------------------------------------------
PYTHON=""
for candidate in ".venv/bin/python" "venv/bin/python"; do
    if [ -x "$candidate" ]; then
        PYTHON="$candidate"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    if [ -e ".venv/Scripts/python.exe" ] || [ -e "venv/Scripts/python.exe" ]; then
        cat <<'MSG'
[ERRO] Encontrei um ambiente virtual do Windows (.venv\Scripts\python.exe),
       mas ele nao serve para este projeto: o interpretador do jogo
       (frotz-master/dfrotz) e um binario de Linux, entao o ambiente virtual
       precisa ser criado DENTRO do WSL/Linux.

       Crie o ambiente virtual de Linux (dentro do WSL, nesta pasta):

           python3 -m venv .venv
           .venv/bin/pip install -r requirements.txt
           ./run.sh
MSG
        exit 1
    fi

    echo "[SETUP] Nenhum ambiente virtual encontrado: criando .venv agora."
    if ! command -v python3 >/dev/null 2>&1; then
        cat <<'MSG'
[ERRO] O comando 'python3' nao existe aqui.

       No WSL, instale-o antes de continuar:

           sudo apt update
           sudo apt install -y python3 python3-venv python3-pip
MSG
        exit 1
    fi

    if ! python3 -m venv .venv; then
        cat <<'MSG'
[ERRO] Nao consegui criar o .venv.

       Se a mensagem acima falar de 'ensurepip' ou 'python3-venv', instale:

           sudo apt install -y python3-venv
MSG
        exit 1
    fi

    .venv/bin/pip install --upgrade pip
    if ! .venv/bin/pip install -r "$REQUIREMENTS"; then
        echo "[ERRO] Falha ao instalar as dependencias de $REQUIREMENTS."
        exit 1
    fi
    PYTHON=".venv/bin/python"
fi

# ---------------------------------------------------------------------------
# 2) frotz-master/dfrotz precisa estar executavel
#    (o .zip do GitHub nao preserva o bit de execucao; sem isso o Python falha
#     com "PermissionError: [Errno 13] Permission denied: '.../dfrotz'")
# ---------------------------------------------------------------------------
if [ ! -f "$DFROTZ" ]; then
    echo "[ERRO] Nao encontrei o interpretador do jogo em: $DFROTZ"
    exit 1
fi

if [ ! -x "$DFROTZ" ]; then
    echo "[SETUP] $DFROTZ estava sem permissao de execucao."
    echo "[SETUP] rodando: chmod u+rwx $DFROTZ"
    if ! chmod u+rwx "$DFROTZ"; then
        echo "[ERRO] Nao consegui dar permissao de execucao em $DFROTZ."
        echo "       Rode manualmente: chmod u+rwx $DFROTZ"
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# 3) Jogo
# ---------------------------------------------------------------------------
"$PYTHON" src/main.py "$@"
status=$?

if [ -t 0 ]; then
    echo
    read -r -p "Pressione Enter para sair..."
fi

exit $status
