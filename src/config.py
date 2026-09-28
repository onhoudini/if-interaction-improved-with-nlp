from pathlib import Path

from src.similarity.first_strategy import WordNetVerbSimilarityStrategy

SIMILARITY_STRATEGY = WordNetVerbSimilarityStrategy # Place for changing strategies

# -- Server Config --
SERVER_HOST = "localhost"
SERVER_PORT = 2300

# -- Similarity Config -- 
THRESHOLD_SUGGESTION   = 0.60
THRESHOLD_AUTO_CORRECT = 0.89

# -- Autocomplete Config --
AUTOCOMPLETE_ENABLED = True               # TAB complete o verbo (apenas no modo 1)
AUTOCOMPLETE_MIN_PREFIX = 1               # minimo de letras digitadas para o TAB completar
AUTOCOMPLETE_SIMILAR_SUGGESTIONS = False  # sugere verbos parecidos quando nenhum comeca com o prefixo
AUTOCOMPLETE_MAX_SUGGESTIONS = 5          # maximo de sugestoes parecidas exibidas no TAB

# -- Game address --
PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_FILE = PROJECT_ROOT / "frotz-master" / "games" / "zork1-r88-s840726.z3"