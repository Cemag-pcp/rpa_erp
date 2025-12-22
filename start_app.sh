#!/usr/bin/env bash
set -euo pipefail

# Atualiza o repositório
git pull

# Ativa o ambiente virtual
source "$(dirname "$0")/venv/bin/activate"

# Carrega dependências
pip install -r "$(dirname "$0")/requirements.txt"

# Inicia o app principal
uvicorn core.bot_manager:app --reload
