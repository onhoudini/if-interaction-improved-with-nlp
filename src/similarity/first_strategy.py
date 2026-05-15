# WordNet

from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable, Set, Tuple

import nltk
from nltk.corpus import wordnet as wn


class WordNetVerbSimilarityStrategy:
    def __init__(
        self,
        semantic_weight: float = 0.9,
        string_weight: float = 0.1,
        use_morphy: bool = True,
    ) -> None:
        self.semantic_weight = semantic_weight
        self.string_weight = string_weight
        self.use_morphy = use_morphy
        self._ensure_wordnet()

    def _ensure_wordnet(self) -> None:
        try:
            wn.synsets("run", pos=wn.VERB)
        except LookupError:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
            wn.synsets("run", pos=wn.VERB)

    def _normalize_for_wordnet(self, word: str) -> str:
        word = word.lower().strip()
        if self.use_morphy:
            lemma = wn.morphy(word, wn.VERB)
            if lemma:
                return lemma
        return word

    def _verb_synsets(self, word: str) -> list:
        normalized = self._normalize_for_wordnet(word)
        return wn.synsets(normalized, pos=wn.VERB)

    def has_verb_signal(self, word: str) -> bool:
        return bool(self._verb_synsets(word))

    def _sequence_score(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _semantic_score(self, source: str, target: str) -> float | None: 
        source_synsets = self._verb_synsets(source)
        target_synsets = self._verb_synsets(target)

        if not source_synsets or not target_synsets:
            return None

        best = None
        for s1 in source_synsets:
            for s2 in target_synsets:
                score = s1.wup_similarity(s2)
                if score is None:
                    continue
                if best is None or score > best:
                    best = score

        return best

    def find_best(self, verb: str, candidates: Set[str]) -> Tuple[str, float]:
        if not candidates:
            raise ValueError("candidates cannot be empty")

        best_candidate = ""
        best_score = -1.0

        for candidate in candidates:
            semantic = self._semantic_score(verb, candidate)
            string_score = self._sequence_score(verb, candidate)

            if semantic is None:
                final_score = string_score
            else:
                final_score = (
                    self.semantic_weight * semantic
                    + self.string_weight * string_score
                )

            if final_score > best_score:
                best_score = final_score
                best_candidate = candidate

        return best_candidate, best_score