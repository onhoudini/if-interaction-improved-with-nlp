"""TAB completa a primeira palavra do comando do jogador (o verbo).

O jogador digita do lado do Python (ver `src/server/dfrotz_runner.py`), antes de a
linha passar pelo lexico e ir para o dfrotz. Este modulo liga o readline para o
TAB completar a *primeira* palavra da linha com os candidatos que o chamador
entrega: as palavras do jogo e os sinonimos de `data/lexicon/action.csv` (ver
`src/main.py`).

So a primeira palavra e completada: depois do primeiro espaco a palavra atual nao
e mais a primeira, entao o TAB nao faz nada (objetos/substantivos nao entram na
lista).
"""

from __future__ import annotations

import sys
from typing import Callable, Iterable, Optional, Sequence

try:  # GNU readline (Linux/macOS); no Windows nativo precisa do pyreadline3
    import readline
except ImportError:  # pragma: no cover - depende da plataforma
    readline = None

RecommendationFn = Callable[[str], Sequence[str]]

# `show-all-if-ambiguous` faz o proprio TAB listar as opcoes na primeira vez que
# ele e apertado; sem isso o readline so lista na segunda vez.
READLINE_BINDINGS = ("tab: complete", "set show-all-if-ambiguous on")


class VerbCompleter:
    """Completer do readline que so responde pela primeira palavra da linha."""

    def __init__(
        self,
        verbs: Iterable[str],
        min_prefix: int = 1,
        recommend: Optional[RecommendationFn] = None,
        max_recommendations: int = 5,
        min_prefix_for_recommendations: int = 3,
        line_provider: Optional[Callable[[], str]] = None,
        word_start_provider: Optional[Callable[[], int]] = None,
    ) -> None:
        self._verbs: tuple[str, ...] = tuple(
            sorted({verb.strip().lower() for verb in verbs if verb and verb.strip()})
        )
        self._min_prefix = max(0, int(min_prefix))
        self._recommend = recommend
        self._max_recommendations = max(1, int(max_recommendations))
        self._min_prefix_for_recommendations = max(1, int(min_prefix_for_recommendations))
        self._line_provider = line_provider
        self._word_start_provider = word_start_provider
        self._pending: list[str] = []

    @property
    def verbs(self) -> tuple[str, ...]:
        return self._verbs

    def matches(self, prefix: str) -> list[str]:
        """Palavras que comecam com o prefixo (ou parecidas, se ha `recommend`)."""
        prefix = prefix.strip().lower()
        if len(prefix) < self._min_prefix:
            return []

        found = [verb for verb in self._verbs if verb.startswith(prefix)]
        return found or self._recommendations(prefix)

    def is_verb_position(self, line: str, word_start: int) -> bool:
        """True so quando a palavra atual e a primeira (nada antes dela)."""
        word_start = max(0, word_start)
        return not line[:word_start].strip()

    def complete(self, text: str, state: int) -> Optional[str]:
        """Protocolo do readline: devolve o candidato numero `state`, ou None."""
        if state == 0:
            self._pending = self._matches_for_current_input(text)
        if 0 <= state < len(self._pending):
            return self._pending[state]
        return None

    def _matches_for_current_input(self, text: str) -> list[str]:
        line = self._line_provider() if self._line_provider else ""
        word_start = self._word_start_provider() if self._word_start_provider else 0
        if not self.is_verb_position(line, word_start):
            return []
        return self.matches(text)

    def _recommendations(self, prefix: str) -> list[str]:
        if not self._recommend or len(prefix) < self._min_prefix_for_recommendations:
            return []
        try:
            similar = list(self._recommend(prefix))
        except Exception:
            return []
        return [verb for verb in similar if verb][: self._max_recommendations]


def enable_verb_autocomplete(
    verbs: Iterable[str],
    min_prefix: int = 1,
    recommend: Optional[RecommendationFn] = None,
    max_recommendations: int = 5,
    stream=None,
) -> bool:
    """Liga o TAB na primeira palavra. False quando nao da para completar."""
    stream = sys.stdin if stream is None else stream
    if not getattr(stream, "isatty", lambda: False)():
        return False  # entrada redirecionada (pipes/execucoes automaticas)

    if readline is None:
        print(
            "[AUTOCOMPLETE] modulo 'readline' nao encontrado: TAB desativado. "
            "No Windows nativo, instale pyreadline3 (pip install pyreadline3)."
        )
        return False

    completer = VerbCompleter(
        verbs,
        min_prefix=min_prefix,
        recommend=recommend,
        max_recommendations=max_recommendations,
        line_provider=readline.get_line_buffer,
        word_start_provider=readline.get_begidx,
    )
    readline.set_completer(completer.complete)
    for binding in READLINE_BINDINGS:
        readline.parse_and_bind(binding)
    return True
