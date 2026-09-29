"""Configuracao da ferramenta: estrategia de sugestao, limiares, autocomplete e
o prompt mostrado ao jogador. Os caminhos do projeto ficam em `src.paths`.
"""

from src.similarity.wordnet_strategy import WordNetVerbSimilarityStrategy

SIMILARITY_STRATEGY = WordNetVerbSimilarityStrategy

SERVER_HOST = "localhost"
SERVER_PORT = 2300

# Nota minima (0 a 1) para a estrategia sugerir uma palavra parecida quando a
# digitada nao esta no dicionario do jogo nem na tabela de sinonimos. Nenhuma
# troca acontece por nota: quem reescreve o comando, em silencio, e o lexico
# (data/lexicon/action.csv).
SUGGESTION_THRESHOLD = 0.80

# True tambem imprime as linhas [SERVER] na tela do jogador (util para depurar).
VERBOSE_SERVER_LINES = False

AUTOCOMPLETE_ENABLED = True
# Letras ja digitadas necessarias para o TAB responder (1 = uma letra basta).
AUTOCOMPLETE_MIN_PREFIX = 1
AUTOCOMPLETE_SIMILAR_SUGGESTIONS = False
AUTOCOMPLETE_MAX_SUGGESTIONS = 5

# Prompt escrito antes de cada comando. Ele e entregue ao `input()` como prompt,
# entao fica fora da linha digitada: nao entra no comando enviado ao jogo nem no
# autocomplete do TAB.
PROMPT_TEXT = "> "

# Silencio (em segundos) do jogo que significa "acabou de responder e esta
# esperando um comando": e o que libera o prompt na tela.
GAME_QUIET_SECONDS = 0.12
# Silencio (em segundos) sem o prompt do interpretador que tambem libera o
# prompt: cobre um jogo que nao termine a resposta com ">".
GAME_IDLE_FALLBACK = 0.60
# Tempo maximo (em segundos) esperando a resposta do jogo antes de mostrar o
# prompt de qualquer forma.
GAME_REPLY_TIMEOUT = 5.0
