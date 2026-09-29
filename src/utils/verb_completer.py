"""TAB completion restricted to the verb (first word) of the player's command.

The player types on the Python side (see ``src/server/dfrotz_runner.py``), before
the line is matched/rewritten by the lexicon and forwarded to dfrotz. This module
hooks GNU readline (or pyreadline3 on Windows) so TAB completes the *first* token
of the line using the candidates handed over by the caller: as palavras do jogo
e os sinonimos de ``data/lexicon/action.csv`` (ver ``src/main.py``).

Only the first word is completed:

* the candidates are exactly the list handed over by the caller;
* once the player types a space, the current word is no longer the first one, so
  TAB does nothing (objects/nouns are never completed).
"""

from __future__ import annotations

import sys
from typing import Callable, Iterable, Optional, Sequence

try:  # GNU readline (Linux/macOS); Windows needs the pyreadline3 package
    import readline
except ImportError:  # pragma: no cover - platform dependent
    readline = None

RecommendationFn = Callable[[str], Sequence[str]]


class VerbCompleter:
    """readline completer that only answers for the first word of the line."""

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
        """Verbs starting with ``prefix`` (or similar ones, if ``recommend`` is given)."""
        prefix = prefix.strip().lower()
        if len(prefix) < self._min_prefix:
            return []

        found = [verb for verb in self._verbs if verb.startswith(prefix)]
        return found or self._recommendations(prefix)

    def is_verb_position(self, line: str, word_start: int) -> bool:
        """True only when the current word is the first one (nothing before it)."""
        word_start = max(0, word_start)
        return not line[:word_start].strip()

    def complete(self, text: str, state: int) -> Optional[str]:
        """readline protocol: return the state-th candidate, or None when done."""
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
    """Bind TAB to verb completion. Return False when completion is unavailable."""
    stream = sys.stdin if stream is None else stream
    if not getattr(stream, "isatty", lambda: False)():
        return False  # redirected input (pipes/automated runs): TAB makes no sense

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
    readline.parse_and_bind("tab: complete")
    return True
