from pathlib import Path

from src.similarity.similarity_strategy import WordNetVerbSimilarityStrategy

SIMILARITY_STRATEGY = WordNetVerbSimilarityStrategy # Place for changing strategies

# -- Server Config --
SERVER_HOST = "localhost"
SERVER_PORT = 2300

# -- Similarity Config -- 
THRESHOLD_SUGGESTION   = 0.50
THRESHOLD_AUTO_CORRECT = 0.70

# -- Game address --
PROJECT_ROOT = Path(__file__).resolve().parents[1]
GAME_FILE = PROJECT_ROOT / "frotz-master" / "games" / "zork1-r88-s840726.z3"