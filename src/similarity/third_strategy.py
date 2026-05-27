# SBert (all-mini-lm-v-6)
# Atualmente sem uso
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Set, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer


class SBertVerbSimilarityStrategy:
    def __init__(
        self,
        semantic_weight: float = 0.9,
        string_weight: float = 0.1,
        model_name: str = "all-mini-lm-v6",
    ) -> None:
        self.semantic_weight = semantic_weight
        self.string_weight = string_weight
        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def has_verb_signal(self, word: str) -> bool:
        # SBERT can always embed a token, so treat as always "has signal"
        return bool(word.strip())

    def _normalize(self, word: str) -> str:
        return word.lower().strip()

    def _sequence_score(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a, b).ratio()

    def _semantic_score(self, source: str, target: str) -> float | None:
        s = self._normalize(source)
        t = self._normalize(target)
        if not s or not t:
            return None
        vecs = self._model.encode([s, t], normalize_embeddings=True)
        # cosine similarity in [-1, 1] because embeddings are normalized
        return float(np.dot(vecs[0], vecs[1]))

    def _normalize_similarity(self, score: float) -> float:
        return (score + 1.0) / 2.0

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
                sem = self._normalize_similarity(semantic)
                final_score = (self.semantic_weight * sem) + (
                    self.string_weight * string_score
                )

            if final_score > best_score:
                best_score = final_score
                best_candidate = candidate

        return best_candidate, best_score