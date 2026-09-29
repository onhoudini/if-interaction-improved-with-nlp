"""Classifica palavras do dicionario como verbo usando WordNet (sem dfrotz).

Diferente de `check_for_actions.py`, nao executa o jogo: usa WordNet (`nltk`)
mais ancoras genericas de acao para decidir se a palavra e um verbo.

Uso (da raiz do projeto):

    python tools/verb_recognition.py [palavras.txt]

Sem argumento, as palavras sao extraidas do proprio `.z3`. Saidas em
`tools/output/`: `verbs.txt`, `others.txt` e `unknown.txt`.
"""

import sys
from collections import deque
from pathlib import Path

import nltk
from nltk.corpus import wordnet as wn

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.paths import GAME_FILE, TOOLS_OUTPUT_DIR
from tools.zmachine_dictionary import resolve_words

# Score minimo para considerar a palavra como verbo.
# Valores menores deixam entrar mais falsos positivos.
VERB_SCORE_THRESHOLD = 2.0

# Anchors genericos de acao, para favorecer verbos ligados a acoes.
ACTION_ANCHOR_NAMES = {
    "act.v.01",
    "move.v.02",
    "travel.v.01",
    "change.v.01",
    "change_state.v.01",
    "make.v.01",
    "use.v.01",
    "interact.v.01",
    "touch.v.01",
    "control.v.01",
}


def save_word_list(path: Path, words: list[str]) -> None:
    unique_sorted = sorted(set(words))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(unique_sorted) + ("\n" if unique_sorted else ""), encoding="utf-8"
    )


def ensure_wordnet() -> None:
    try:
        wn.synsets("dog")
    except LookupError:
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
        wn.synsets("dog")


def load_action_anchors() -> set:
    anchors = set()
    for name in ACTION_ANCHOR_NAMES:
        try:
            anchors.add(wn.synset(name))
        except Exception:
            pass
    return anchors


def normalize_for_verb(word: str) -> str:
    word = word.lower().strip()
    lemma = wn.morphy(word, wn.VERB)
    return lemma if lemma else word


def get_verb_synsets(word: str) -> list:
    return wn.synsets(word, pos=wn.VERB)


def get_any_synsets(word: str) -> list:
    return wn.synsets(word)


def reaches_action_anchor(start_synset, action_anchors: set, max_depth: int = 12) -> bool:
    """BFS pelos hypernyms: True se o verbo chega em algum anchor de acao."""
    visited = set()
    queue = deque([(start_synset, 0)])

    while queue:
        synset, depth = queue.popleft()

        if synset in visited:
            continue
        visited.add(synset)

        if synset in action_anchors:
            return True

        if depth >= max_depth:
            continue

        next_nodes = synset.hypernyms() + synset.instance_hypernyms()
        for node in next_nodes:
            if node not in visited:
                queue.append((node, depth + 1))

    return False


def verb_score(word: str, action_anchors: set) -> tuple[float, str]:
    """Nota de "quanto isso parece um verbo" e o lemma a guardar."""
    lemma = normalize_for_verb(word)

    original_verbs = get_verb_synsets(word)
    lemma_verbs = get_verb_synsets(lemma)

    noun_synsets = wn.synsets(word, pos=wn.NOUN)
    adj_synsets = wn.synsets(word, pos=wn.ADJ)

    has_anchor = False
    for syn in lemma_verbs:
        if reaches_action_anchor(syn, action_anchors):
            has_anchor = True
            break

    if not has_anchor:
        for syn in original_verbs:
            if reaches_action_anchor(syn, action_anchors):
                has_anchor = True
                break

    score = 0.0

    if lemma_verbs:
        score += 2.0

    if original_verbs and lemma != word:
        score += 0.5

    if has_anchor:
        score += 2.0

    if noun_synsets and len(noun_synsets) >= len(lemma_verbs) + 2 and not has_anchor:
        score -= 1.5

    if adj_synsets and not lemma_verbs:
        score -= 0.5

    return score, lemma


def classify_words(words: list[str]) -> tuple[list[str], list[str], list[str]]:
    verbs, others, unknown = [], [], []
    action_anchors = load_action_anchors()

    for word in words:
        if not get_any_synsets(word):
            unknown.append(word)
            continue

        score, lemma = verb_score(word, action_anchors)

        if score >= VERB_SCORE_THRESHOLD:
            verbs.append(lemma)
        else:
            others.append(word)

    return verbs, others, unknown


def main() -> None:
    source = sys.argv[1] if len(sys.argv) > 1 else None
    words = resolve_words(source)
    print(f"Palavras  : {len(words)} (fonte: {source or GAME_FILE})")

    ensure_wordnet()
    verbs, others, unknown = classify_words(words)

    save_word_list(TOOLS_OUTPUT_DIR / "verbs.txt", verbs)
    save_word_list(TOOLS_OUTPUT_DIR / "others.txt", others)
    save_word_list(TOOLS_OUTPUT_DIR / "unknown.txt", unknown)

    print(f"Total     : {len(words)}")
    print(f"Verbos    : {len(set(verbs))}")
    print(f"Outros    : {len(set(others))}")
    print(f"Desconhecidas: {len(set(unknown))}")
    print("\nArquivos gerados em:")
    print(f"- {TOOLS_OUTPUT_DIR / 'verbs.txt'}")
    print(f"- {TOOLS_OUTPUT_DIR / 'others.txt'}")
    print(f"- {TOOLS_OUTPUT_DIR / 'unknown.txt'}")


if __name__ == "__main__":
    main()
