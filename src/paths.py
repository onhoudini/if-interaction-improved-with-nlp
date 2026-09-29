"""Caminhos do projeto em um lugar so: quem precisar de um caminho importa de
`src.paths`.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Dados (entrada curada e saida)
DATA_DIR = PROJECT_ROOT / "data"
LEXICON_DIR = DATA_DIR / "lexicon"
LEXICON_FILE = LEXICON_DIR / "action.csv"   # tabela de sinonimos (palavra,sinonimo1,sinonimo2)
LOGS_DIR = DATA_DIR / "logs"                # sessoes de jogo (nao versionadas)

# Interpretador e jogo
DFROTZ = PROJECT_ROOT / "frotz-master" / "dfrotz"
GAME_FILE = PROJECT_ROOT / "frotz-master" / "games" / "zork1-r88-s840726.z3"

# Scripts offline
TOOLS_DIR = PROJECT_ROOT / "tools"
TOOLS_OUTPUT_DIR = TOOLS_DIR / "output"
