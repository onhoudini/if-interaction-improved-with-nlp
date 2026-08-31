#!/usr/bin/env bash

cd "$(dirname "$0")" || exit 1

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python src/main.py
elif [ -f "venv/bin/python" ]; then
    venv/bin/python src/main.py
else
    echo "Nao encontrei um ambiente virtual."
    exit 1
fi

read -p "Pressione Enter para sair..."