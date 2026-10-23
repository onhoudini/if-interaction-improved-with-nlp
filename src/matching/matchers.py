"""Decide o que fazer com cada comando digitado pelo jogador.

Ordem das camadas (fixa, sem limiar de correcao):

1. **o jogo conhece a palavra** -> passa intacta;
2. **a palavra esta na tabela de sinonimos** -> troca pela forma do dicionario
   (`data/lexicon/action.csv`) antes de enviar, sem avisar o jogador;
3. **sugestao** -> quando nada acima se aplica, a estrategia de similaridade
   (WordNet) pode sugerir uma palavra parecida: o comando e enviado como
   digitado e o jogador ve `Perhaps, do you mean 'X'?`;
4. caso contrario -> passa intacta.

O unico limiar que sobrou e `SUGGESTION_THRESHOLD` (>= 0.80) e ele vale apenas
para a camada 3. Nenhuma troca acontece por nota de similaridade.
"""

from dataclasses import dataclass
from typing import Optional, Set

from src.config import SUGGESTION_THRESHOLD
from src.lexicon.action_lexicon import ActionLexicon
from src.similarity.base import SimilarityStrategy
from src.utils.tokenizer import tokenize

# status possiveis de um comando (aparecem no log da sessao)
STATUS_OK = "ok"             # palavra conhecida pelo jogo
STATUS_SYNONYM = "sinonimo"  # trocada pela palavra do dicionario
STATUS_SUGGEST = "sugestao"  # sugestao exibida; comando enviado como digitado
STATUS_PASS = "passa"        # nada reconhecido
STATUS_RAW = "puro"          # modo 0: nenhum processamento


@dataclass
class MatchResult:
    original_input: str
    sanitized_input: str
    matched_tokens: list[str]
    status: str
    verb_found: str = ""
    verb_matched: str = ""
    score: float = 0.0


class VerbMatcher:
    """Aplica as camadas de decisao a um comando digitado."""

    def __init__(
        self,
        lexicon: Optional[ActionLexicon],
        game_words: Set[str],
        strategy: Optional[SimilarityStrategy] = None,
        suggestion_threshold: float = SUGGESTION_THRESHOLD,
    ) -> None:
        if not game_words:
            raise ValueError("game_words can't be empty.")
        self.lexicon: ActionLexicon = lexicon or ActionLexicon()
        self.game_words: frozenset[str] = frozenset(game_words)
        self._strategy = strategy
        self.suggestion_threshold = suggestion_threshold

    def _find_verb_index(self, tokens: list[str]) -> int:
        """Indice do token que deve ser tratado como verbo.

        Passa pelos tokens na ordem em que o jogador digitou e devolve o
        primeiro que seja util como verbo:

        1. palavra que o jogo conhece;
        2. sinonimo do lexico (o que sera trocado pela palavra do dicionario);
        3. palavra que a estrategia reconhece como verbo (WordNet);

        Devolve -1 quando nada parece verbo (nesse caso o comando passa
        intacto). A ordem por token e importante: em "stuff the mailbox" quem
        manda e "stuff" (sinonimo), nao o "the" (que o jogo conhece).
        """
        for index, token in enumerate(tokens):
            if token in self.game_words or self.lexicon.canonical_for(token):
                return index
            if self._strategy is not None and self._strategy.has_verb_signal(token):
                return index

        return -1

    def match(self, user_input: str) -> MatchResult:
        """Aplica as camadas e devolve o que deve ser enviado ao jogo."""
        tokens = tokenize(user_input)
        sanitized = " ".join(tokens)

        if not tokens:
            return MatchResult(user_input, sanitized, [], STATUS_PASS)

        verb_index = self._find_verb_index(tokens)
        if verb_index < 0:
            return MatchResult(user_input, sanitized, tokens, STATUS_PASS)

        verb = tokens[verb_index]

        if verb in self.game_words:
            return MatchResult(
                user_input, sanitized, tokens, STATUS_OK, verb, verb, 1.0
            )

        # o lexico troca, em silencio, pela forma que o dicionario do jogo entende
        canonical = self.lexicon.canonical_for(verb)
        if canonical:
            final_tokens = list(tokens)
            final_tokens[verb_index] = canonical
            return MatchResult(
                user_input,
                sanitized,
                final_tokens,
                STATUS_SYNONYM,
                verb,
                canonical,
                1.0,
            )

        # sugestao so quando o jogador nao chegou em nenhuma palavra conhecida
        if any(
            token in self.game_words or self.lexicon.canonical_for(token)
            for token in tokens
        ):
            return MatchResult(
                user_input, sanitized, tokens, STATUS_PASS, verb, "", 0.0
            )

        # sugestao: o comando segue como foi digitado
        suggestion, score = self._best_suggestion(verb)
        if suggestion and score >= self.suggestion_threshold:
            return MatchResult(
                user_input, sanitized, tokens, STATUS_SUGGEST, verb, suggestion, score
            )

        return MatchResult(
            user_input, sanitized, tokens, STATUS_PASS, verb, suggestion, score
        )

    def _best_suggestion(self, verb: str) -> tuple[str, float]:
        """Melhor candidato do lexico para sugerir (0.0 quando nao ha como)."""
        if self._strategy is None or not self.lexicon:
            return "", 0.0
        try:
            return self._strategy.find_best(verb, self.lexicon.canonicals)
        except Exception:
            return "", 0.0


def build_matcher(
    lexicon: Optional[ActionLexicon],
    game_words: Set[str],
    strategy: Optional[SimilarityStrategy] = None,
    suggestion_threshold: float = SUGGESTION_THRESHOLD,
) -> VerbMatcher:
    return VerbMatcher(lexicon, game_words, strategy, suggestion_threshold)