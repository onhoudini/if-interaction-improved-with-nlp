"""Configuracao da ferramenta.

Os caminhos do projeto ficam em `src.paths`; aqui so as escolhas de
comportamento (estrategia de sugestao, limiares, autocomplete).
"""

from src.similarity.wordnet_strategy import WordNetVerbSimilarityStrategy

# -- Estrategia de sugestao (ponto de troca de estrategia) --
SIMILARITY_STRATEGY = WordNetVerbSimilarityStrategy

# -- Server Config --
SERVER_HOST = "localhost"
SERVER_PORT = 2300

# -- Sugestao (unico limiar do projeto) --
# Nota minima (0 a 1) para a estrategia SUGERIR uma palavra parecida quando a
# palavra digitada nao esta no dicionario do jogo nem na tabela de sinonimos.
# Nada e reescrito por nota: a reescrita silenciosa e feita apenas pelo lexico
# (data/lexicon/action.csv).
SUGGESTION_THRESHOLD = 0.80

# -- Log --
# True tambem imprime as linhas [SERVER] na tela do jogador (util para depurar).
# A troca de sinonimo continua invisivel de qualquer forma; o padrao (False)
# deixa na tela apenas a sugestao "Perhaps, do you mean 'X'?".
VERBOSE_SERVER_LINES = False

# -- Autocomplete Config --
AUTOCOMPLETE_ENABLED = True               # TAB completa a 1a palavra (apenas no modo 1)
AUTOCOMPLETE_MIN_PREFIX = 2               # minimo de letras digitadas para o TAB completar
AUTOCOMPLETE_SIMILAR_SUGGESTIONS = False  # sugere palavras parecidas quando nada comeca com o prefixo
AUTOCOMPLETE_MAX_SUGGESTIONS = 5          # maximo de sugestoes parecidas exibidas no TAB
