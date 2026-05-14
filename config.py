from similarity_strategy import WordNetVerbSimilarityStrategy

SIMILARITY_STRATEGY = WordNetVerbSimilarityStrategy # Place for changing strategies

# -- Server Config --
SERVER_HOST = "localhost"
SERVER_PORT = 2300

# -- Similarity Config -- 
THRESHOLD_SUGGESTION   = 0.50
THRESHOLD_AUTO_CORRECT = 0.70

# -- Game address --
GAME_FILE = "./frotz-master/zork1-r119-s880429.z3"