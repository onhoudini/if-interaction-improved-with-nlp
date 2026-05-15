from dataclasses import dataclass
from typing import Set

from src.utils.tokenizer import tokenize


@dataclass
class MatchResult:
    original_input: str
    matched_tokens: list[str]
    score: float
    verb_found: str
    verb_matched: str


class VerbMatcher:
    def __init__(self, game_words: Set[str], strategy):
        if not game_words:
            raise ValueError("game_words can't be empty.")
        self.game_words: frozenset[str] = frozenset(game_words)
        self._strategy = strategy

    def _find_first_verb_index(self, tokens: list[str]) -> int:
        """
        Priority:
        1. first token already present in the game verb list
        2. first token that WordNet recognizes as a verb candidate
        3. no fallback: if nothing looks like a verb, return -1
        """
        for i, token in enumerate(tokens):
            if token in self.game_words:
                return i

        for i, token in enumerate(tokens):
            if self._strategy.has_verb_signal(token):
                return i

        return -1

    def match(self, user_input: str) -> MatchResult:
        tokens = tokenize(user_input)

        if not tokens:
            return MatchResult(
                original_input=user_input,
                matched_tokens=[],
                score=0.0,
                verb_found="",
                verb_matched="",
            )

        verb_index = self._find_first_verb_index(tokens)
        if verb_index < 0:
            return MatchResult(
                original_input=user_input,
                matched_tokens=tokens,
                score=0.0,
                verb_found="",
                verb_matched="",
            )

        verb_candidate = tokens[verb_index]

        if verb_candidate in self.game_words:
            return MatchResult(
                original_input=user_input,
                matched_tokens=tokens,
                score=1.0,
                verb_found=verb_candidate,
                verb_matched=verb_candidate,
            )

        best_verb, score = self._strategy.find_best(verb_candidate, self.game_words)

        corrected_tokens = list(tokens)
        corrected_tokens[verb_index] = best_verb

        return MatchResult(
            original_input=user_input,
            matched_tokens=corrected_tokens,
            score=score,
            verb_found=verb_candidate,
            verb_matched=best_verb,
        )


def build_matcher(game_words: Set[str], strategy) -> VerbMatcher:
    return VerbMatcher(game_words, strategy)