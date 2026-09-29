"""Interface minima que uma estrategia de similaridade precisa ter.

O matcher (`src/matching/matchers.py`) usa a estrategia **apenas para sugerir**
uma palavra parecida -- a reescrita do comando do jogador e feita somente pela
tabela de sinonimos (`src/lexicon/action_lexicon.py`).
"""

from __future__ import annotations

from typing import Iterable, Protocol, Tuple


class SimilarityStrategy(Protocol):
    def has_verb_signal(self, word: str) -> bool:
        """True quando a palavra parece um verbo.

        Usado para descobrir qual token da frase esta na posicao de verbo
        quando a palavra nao esta no dicionario do jogo nem no lexico.
        """
        ...

    def find_best(self, word: str, candidates: Iterable[str]) -> Tuple[str, float]:
        """Melhor candidato para a palavra e a nota de similaridade (0 a 1)."""
        ...
